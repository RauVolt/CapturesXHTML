import ctypes
import os
import unittest
from ctypes import wintypes as w
from PIL import Image, ImageChops
from cursor_capture import local_position, draw_cursor, native


class CursorGeometryTests(unittest.TestCase):
    def test_negative_monitor_origin_and_hotspot(self):
        self.assertEqual(local_position((-1800,120),(8,12),(-1920,0,0,1080)), (112,108))

    def test_cursor_on_another_monitor_is_omitted(self):
        self.assertIsNone(local_position((10,10),(0,0),(-1920,0,0,1080)))
        self.assertIsNone(local_position((1920,10),(0,0),(0,0,1920,1080)))

    def test_hotspot_can_clip_at_left_top_edge(self):
        self.assertEqual(local_position((0,0),(8,12),(0,0,1920,1080)),(-8,-12))

    def test_hidden_cursor_leaves_image_unchanged(self):
        with Image.new('RGB',(100,100),'white') as image:
            self.assertIs(draw_cursor(image,(0,0,100,100),None),image)


@unittest.skipUnless(os.name == 'nt', 'Windows cursor rendering')
class NativeCursorTests(unittest.TestCase):
    def test_native_arrow_and_text_cursor_render_at_expected_position(self):
        user,gdi=native()
        user.LoadCursorW.argtypes=[w.HINSTANCE,ctypes.c_void_p]
        user.LoadCursorW.restype=w.HANDLE
        # Load shared system cursors, never change or move the user's pointer.
        for resource in (32512,32513):
            handle=user.LoadCursorW(None,ctypes.c_void_p(resource))
            self.assertTrue(handle)
            for background in ('white','#182b3c'):
                with Image.new('RGB',(200,160),background) as image:
                    result=draw_cursor(image,(-200,0,0,160),(handle,(-150,50),(0,0)))
                    try:
                        box=ImageChops.difference(image,result).getbbox()
                        self.assertIsNotNone(box)
                        self.assertGreaterEqual(box[0],50)
                        self.assertGreaterEqual(box[1],50)
                        self.assertLess(box[2],150)
                        self.assertLess(box[3],150)
                    finally:
                        result.close()

    def test_native_cursor_crossing_image_border_is_clipped(self):
        user,_=native()
        user.LoadCursorW.argtypes=[w.HINSTANCE,ctypes.c_void_p]
        user.LoadCursorW.restype=w.HANDLE
        handle=user.LoadCursorW(None,ctypes.c_void_p(32512))
        with Image.new('RGB',(100,100),'white') as image:
            result=draw_cursor(image,(0,0,100,100),(handle,(99,99),(0,0)))
            self.assertEqual(result.size,image.size)
            result.close()
