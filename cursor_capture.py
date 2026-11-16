"""Draw the actual Windows pointer onto captured pixels, including XOR cursors."""
import ctypes
from ctypes import wintypes as w
from contextlib import contextmanager
from PIL import Image


class CURSORINFO(ctypes.Structure):
    _fields_ = [('cbSize', w.DWORD), ('flags', w.DWORD),
                ('hCursor', w.HANDLE), ('ptScreenPos', w.POINT)]


class ICONINFO(ctypes.Structure):
    _fields_ = [('fIcon', w.BOOL), ('xHotspot', w.DWORD), ('yHotspot', w.DWORD),
                ('hbmMask', w.HANDLE), ('hbmColor', w.HANDLE)]


class BITMAPINFOHEADER(ctypes.Structure):
    _fields_ = [('biSize', w.DWORD), ('biWidth', w.LONG), ('biHeight', w.LONG),
                ('biPlanes', w.WORD), ('biBitCount', w.WORD), ('biCompression', w.DWORD),
                ('biSizeImage', w.DWORD), ('biXPelsPerMeter', w.LONG),
                ('biYPelsPerMeter', w.LONG), ('biClrUsed', w.DWORD), ('biClrImportant', w.DWORD)]


def native():
    user = ctypes.WinDLL('user32', use_last_error=True)
    gdi = ctypes.WinDLL('gdi32', use_last_error=True)
    user.GetCursorInfo.argtypes = [ctypes.POINTER(CURSORINFO)]
    user.GetCursorInfo.restype = w.BOOL
    user.CopyIcon.argtypes = [w.HANDLE]
    user.CopyIcon.restype = w.HANDLE
    user.GetIconInfo.argtypes = [w.HANDLE, ctypes.POINTER(ICONINFO)]
    user.GetIconInfo.restype = w.BOOL
    user.DestroyIcon.argtypes = [w.HANDLE]
    user.DestroyIcon.restype = w.BOOL
    user.DrawIconEx.argtypes = [w.HDC, ctypes.c_int, ctypes.c_int, w.HANDLE,
                               ctypes.c_int, ctypes.c_int, w.UINT, w.HBRUSH, w.UINT]
    user.DrawIconEx.restype = w.BOOL
    gdi.CreateCompatibleDC.argtypes = [w.HDC]
    gdi.CreateCompatibleDC.restype = w.HDC
    gdi.DeleteDC.argtypes = [w.HDC]
    gdi.DeleteDC.restype = w.BOOL
    gdi.CreateDIBSection.argtypes = [w.HDC, ctypes.POINTER(BITMAPINFOHEADER), w.UINT,
                                    ctypes.POINTER(ctypes.c_void_p), w.HANDLE, w.DWORD]
    gdi.CreateDIBSection.restype = w.HANDLE
    gdi.SelectObject.argtypes = [w.HDC, w.HANDLE]
    gdi.SelectObject.restype = w.HANDLE
    gdi.DeleteObject.argtypes = [w.HANDLE]
    gdi.DeleteObject.restype = w.BOOL
    gdi.GdiFlush.argtypes = []
    gdi.GdiFlush.restype = w.BOOL
    return user, gdi


def local_position(position, hotspot, bounds):
    x, y = position
    left, top, right, bottom = bounds
    # Only show the pointer when its active point is on the chosen monitor.
    if not (left <= x < right and top <= y < bottom):
        return None
    return x - left - hotspot[0], y - top - hotspot[1]


@contextmanager
def cursor_snapshot():
    user, gdi = native()
    info = CURSORINFO()
    info.cbSize = ctypes.sizeof(info)
    handle = None
    try:
        if not user.GetCursorInfo(ctypes.byref(info)):
            raise ctypes.WinError(ctypes.get_last_error())
        if not info.flags & 1:  # CURSOR_SHOWING; do not invent hidden pointers.
            yield None
            return
        handle = user.CopyIcon(info.hCursor)
        if not handle:
            raise ctypes.WinError(ctypes.get_last_error())
        icon = ICONINFO()
        if not user.GetIconInfo(handle, ctypes.byref(icon)):
            raise ctypes.WinError(ctypes.get_last_error())
        try:
            yield (handle, (info.ptScreenPos.x, info.ptScreenPos.y),
                   (icon.xHotspot, icon.yHotspot))
        finally:
            if icon.hbmMask:
                gdi.DeleteObject(icon.hbmMask)
            if icon.hbmColor:
                gdi.DeleteObject(icon.hbmColor)
    finally:
        if handle:
            user.DestroyIcon(handle)


def draw_cursor(image, bounds, snapshot):
    if snapshot is None:
        return image
    handle, position, hotspot = snapshot
    point = local_position(position, hotspot, bounds)
    if point is None:
        return image
    user, gdi = native()
    width, height = image.size
    header = BITMAPINFOHEADER()
    header.biSize = ctypes.sizeof(header)
    header.biWidth, header.biHeight = width, -height  # top-down BGRA surface
    header.biPlanes, header.biBitCount = 1, 32
    dc, bitmap, previous = None, None, None
    try:
        dc = gdi.CreateCompatibleDC(None)
        if not dc:
            raise ctypes.WinError(ctypes.get_last_error())
        bits = ctypes.c_void_p()
        bitmap = gdi.CreateDIBSection(dc, ctypes.byref(header), 0, ctypes.byref(bits), None, 0)
        if not bitmap or not bits.value:
            raise ctypes.WinError(ctypes.get_last_error())
        previous = gdi.SelectObject(dc, bitmap)
        if not previous or previous == ctypes.c_void_p(-1).value:
            previous = None
            raise OSError('Impossible de préparer le dessin du curseur.')
        with image.convert('RGB') as rgb:
            pixels = rgb.tobytes('raw', 'BGRX')
        ctypes.memmove(bits, pixels, len(pixels))
        if not user.DrawIconEx(dc, point[0], point[1], handle, 0, 0, 0, None, 3):
            raise ctypes.WinError(ctypes.get_last_error())
        gdi.GdiFlush()
        return Image.frombytes('RGB', (width, height), ctypes.string_at(bits, width*height*4), 'raw', 'BGRX')
    finally:
        if previous:
            gdi.SelectObject(dc, previous)
        if bitmap:
            gdi.DeleteObject(bitmap)
        if dc:
            gdi.DeleteDC(dc)


def grab_with_cursor(bounds, grab):
    # Snapshot shape and location immediately before the screen image.
    with cursor_snapshot() as snapshot:
        image = grab(bbox=bounds, all_screens=True)
        try:
            result = draw_cursor(image, bounds, snapshot)
        except Exception:
            image.close()
            raise
        if result is not image:
            image.close()
        return result
