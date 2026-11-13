"""Capture d'un moniteur Windows vers un document XHTML autonome."""
import base64
import ctypes
import html
import os
import queue
import re
import tempfile
import threading
import time
import sys
import json
import xml.parsers.expat
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime
from pathlib import Path
from tkinter import filedialog, messagebox, ttk
import tkinter as tk

from PIL import ImageGrab
from screeninfo import get_monitors

VK_SNAPSHOT = 0x2C
WH_KEYBOARD_LL = 13
WM_KEYDOWN, WM_SYSKEYDOWN = 0x100, 0x104
WM_KEYUP, WM_SYSKEYUP = 0x101, 0x105
WM_QUIT = 0x12


class PrintScreenHook:
    """Hook clavier bas niveau Windows; avale Impr écran pendant une session."""
    def __init__(self, on_press):
        self.on_press = on_press
        self.enabled = threading.Event()
        self.ready = threading.Event()
        self.error = None
        self.thread_id = None
        self._thread = None
        self._callback = None

    def start(self):
        self._thread = threading.Thread(target=self._run, name='PrintScreenHook', daemon=True)
        self._thread.start()
        self.ready.wait(timeout=5)
        return self.ready.is_set() and self.error is None

    def _run(self):
        from ctypes import wintypes
        user32 = ctypes.WinDLL('user32', use_last_error=True)
        kernel32 = ctypes.WinDLL('kernel32', use_last_error=True)
        ULONG_PTR = wintypes.WPARAM

        class KBDLLHOOKSTRUCT(ctypes.Structure):
            _fields_ = [('vkCode', wintypes.DWORD), ('scanCode', wintypes.DWORD),
                        ('flags', wintypes.DWORD), ('time', wintypes.DWORD),
                        ('dwExtraInfo', ULONG_PTR)]

        CALLBACK = ctypes.WINFUNCTYPE(ctypes.c_ssize_t, ctypes.c_int, wintypes.WPARAM, wintypes.LPARAM)
        user32.SetWindowsHookExW.argtypes = [ctypes.c_int, CALLBACK, wintypes.HINSTANCE, wintypes.DWORD]
        user32.SetWindowsHookExW.restype = wintypes.HHOOK
        user32.CallNextHookEx.argtypes = [wintypes.HHOOK, ctypes.c_int, wintypes.WPARAM, wintypes.LPARAM]
        user32.CallNextHookEx.restype = ctypes.c_ssize_t
        user32.UnhookWindowsHookEx.argtypes = [wintypes.HHOOK]
        user32.UnhookWindowsHookEx.restype = wintypes.BOOL
        user32.GetMessageW.argtypes = [ctypes.POINTER(wintypes.MSG), wintypes.HWND, wintypes.UINT, wintypes.UINT]
        user32.GetMessageW.restype = ctypes.c_int
        user32.PostThreadMessageW.argtypes = [wintypes.DWORD, wintypes.UINT, wintypes.WPARAM, wintypes.LPARAM]
        user32.PostThreadMessageW.restype = wintypes.BOOL
        kernel32.GetCurrentThreadId.restype = wintypes.DWORD
        self.thread_id = kernel32.GetCurrentThreadId()
        pressed = False

        def callback(ncode, wparam, lparam):
            nonlocal pressed
            if ncode >= 0 and self.enabled.is_set():
                data = ctypes.cast(lparam, ctypes.POINTER(KBDLLHOOKSTRUCT)).contents
                if data.vkCode == VK_SNAPSHOT:
                    if wparam in (WM_KEYDOWN, WM_SYSKEYDOWN):
                        if not pressed:
                            pressed = True
                            self.on_press()
                    elif wparam in (WM_KEYUP, WM_SYSKEYUP):
                        # Certains claviers n'envoient que le relâchement de cette touche.
                        if not pressed:
                            self.on_press()
                        pressed = False
                    return 1  # Empêche le traitement normal lorsque le hook est appelé.
            return user32.CallNextHookEx(None, ncode, wparam, lparam)

        self._callback = CALLBACK(callback)
        hook = user32.SetWindowsHookExW(WH_KEYBOARD_LL, self._callback, None, 0)
        if not hook:
            self.error = f'Installation du raccourci impossible (Windows {ctypes.get_last_error()}).'
            self.ready.set()
            return
        self.ready.set()
        try:
            msg = wintypes.MSG()
            while user32.GetMessageW(ctypes.byref(msg), None, 0, 0) > 0:
                pass
        finally:
            user32.UnhookWindowsHookEx(hook)

    def stop(self):
        self.enabled.clear()
        if self.thread_id:
            ctypes.windll.user32.PostThreadMessageW(self.thread_id, WM_QUIT, 0, 0)
        if self._thread:
            self._thread.join(timeout=2)


def valid_xml_file(path):
    """Analyse XML en flux, sans charger les images Base64 en mémoire."""
    parser = xml.parsers.expat.ParserCreate()
    with open(path, 'rb') as stream:
        while block := stream.read(128 * 1024):
            parser.Parse(block, False)
        parser.Parse(b'', True)


def export_xhtml(path, name, captures):
    target = Path(path)
    # Fichier provisoire à côté de la destination : remplacement atomique final.
    fd, partial = tempfile.mkstemp(prefix='.captures-', suffix='.xhtml.tmp', dir=target.parent)
    os.close(fd)
    try:
        with open(partial, 'w', encoding='utf-8', newline='\n') as out:
            out.write('<?xml version="1.0" encoding="UTF-8"?>\n')
            out.write('<html xmlns="http://www.w3.org/1999/xhtml" xml:lang="fr"><head>')
            out.write('<meta http-equiv="Content-Type" content="application/xhtml+xml; charset=UTF-8" />')
            out.write(f'<title>{html.escape(name)}</title>')
            out.write('<style type="text/css">body{font-family:Arial,sans-serif;margin:32px;color:#222}'
                      'h1{border-bottom:2px solid #333;padding-bottom:12px}'
                      'section{margin:28px 0 40px;page-break-inside:avoid}'
                      'h2{margin-bottom:5px}.date{color:#555;font-size:0.9em}'
                      'img{max-width:100%;height:auto;border:1px solid #ccc}</style></head><body>')
            out.write(f'<h1>{html.escape(name)}</h1>')
            for i, (stamp, image_path) in enumerate(captures, 1):
                date = datetime.fromisoformat(stamp).strftime('%d/%m/%Y %H:%M:%S')
                out.write(f'<section><h2>Capture {i}</h2><p class="date">{html.escape(date)}</p>')
                out.write(f'<img alt="Capture {i}" src="data:image/png;base64,')
                with open(image_path, 'rb') as image:
                    while block := image.read(3 * 65536):
                        out.write(base64.b64encode(block).decode('ascii'))
                out.write('" /></section>')
            out.write('</body></html>')
        valid_xml_file(partial)
        os.replace(partial, target)
    finally:
        if os.path.exists(partial):
            os.unlink(partial)


class CaptureApp:
    def __init__(self, root):
        self.root = root
        root.title('CapturesXHTML 1.2.0')
        root.geometry('610x350')
        self.events = queue.Queue()
        self.pool = ThreadPoolExecutor(max_workers=1, thread_name_prefix='CaptureWorker')
        self.session = None
        self.captures = []
        self.pending = 0
        self.capture_sequence = 0
        self.active = False
        self.finishing = False
        self.monitors = []
        self.document = tk.StringVar()
        self.monitor_choice = tk.StringVar()
        self.status = tk.StringVar(value='Prêt à démarrer')
        frame = ttk.Frame(root, padding=18)
        frame.pack(fill='both', expand=True)
        ttk.Label(frame, text='Nom du document').pack(anchor='w')
        self.name_entry = ttk.Entry(frame, textvariable=self.document)
        self.name_entry.pack(fill='x', pady=(3, 12))
        ttk.Label(frame, text='Écran à capturer').pack(anchor='w')
        self.combo = ttk.Combobox(frame, textvariable=self.monitor_choice, state='readonly')
        self.combo.pack(fill='x', pady=(3, 12))
        self.refresh_btn = ttk.Button(frame, text='Actualiser les écrans', command=self.refresh_monitors)
        self.refresh_btn.pack(anchor='w')
        buttons = ttk.Frame(frame)
        buttons.pack(fill='x', pady=14)
        self.start_btn = ttk.Button(buttons, text='Démarrer', command=self.start)
        self.start_btn.pack(side='left')
        self.end_btn = ttk.Button(buttons, text='Terminer', command=self.finish, state='disabled')
        self.end_btn.pack(side='left', padx=12)
        ttk.Label(frame, textvariable=self.status, wraplength=570).pack(anchor='w')
        ttk.Label(frame, text='Pendant la session : Impr. écran = capture de l’écran sélectionné.').pack(anchor='w', pady=8)
        self.refresh_monitors()
        self.hook = PrintScreenHook(lambda: self.events.put(('key', None)))
        self.hook_ok = self.hook.start()
        if not self.hook_ok:
            self.status.set(self.hook.error or 'Impossible d’activer la touche Impr. écran.')
            self.start_btn.config(state='disabled')
        root.after(40, self.process_events)
        root.protocol('WM_DELETE_WINDOW', self.on_close)

    def refresh_monitors(self):
        try:
            self.monitors = get_monitors()
            names = [f'Écran {i + 1} — {m.width} × {m.height} (position {m.x}, {m.y})'
                     for i, m in enumerate(self.monitors)]
            self.combo['values'] = names
            self.combo.current(0) if len(names) == 1 else self.monitor_choice.set('')
        except Exception as exc:
            self.monitors = []
            messagebox.showerror('Écrans', str(exc))

    def start(self):
        if not self.document.get().strip():
            messagebox.showwarning('Nom requis', 'Saisissez un nom de document.')
            return
        if self.combo.current() < 0:
            messagebox.showwarning('Écran requis', 'Sélectionnez un écran.')
            return
        try:
            temp_root = Path(os.environ['LOCALAPPDATA']) / 'CapturesXHTML' / 'Temp'
            temp_root.mkdir(parents=True, exist_ok=True)
            self.session = tempfile.TemporaryDirectory(prefix='session-', dir=temp_root)
        except Exception as exc:
            messagebox.showerror('Dossier temporaire', str(exc))
            return
        m = self.monitors[self.combo.current()]
        self.bounds = (m.x, m.y, m.x + m.width, m.y + m.height)
        self.captures = []
        self.pending = 0
        self.capture_sequence = 0
        self.active = True
        self.finishing = False
        self.hook.enabled.set()
        self.start_btn.config(state='disabled')
        self.end_btn.config(state='normal')
        self.combo.config(state='disabled')
        self.name_entry.config(state='disabled')
        self.refresh_btn.config(state='disabled')
        self.status.set('Session active — 0 capture')

    def process_events(self):
        try:
            while True:
                kind, payload = self.events.get_nowait()
                if kind == 'key' and self.active and not self.finishing:
                    self.capture()
                elif kind == 'captured':
                    self.pending -= 1
                    self.captures.append(payload)
                    self.status.set(f'Session active — {len(self.captures)} capture(s), {self.pending} en attente')
                elif kind == 'error':
                    self.pending -= 1
                    self.status.set(f'Erreur de capture : {payload}')
                    messagebox.showerror('Capture impossible', str(payload))
                elif kind == 'exported':
                    self.export_complete(payload)
                elif kind == 'export_error':
                    self.finishing = False
                    self.end_btn.config(state='normal')
                    self.status.set(f'Échec de l’enregistrement : {payload}')
                    messagebox.showerror('Document XHTML', str(payload))
        except queue.Empty:
            pass
        if self.finishing and self.pending == 0 and getattr(self, 'export_path', None):
            self.launch_export()
        self.root.after(40, self.process_events)

    def capture(self):
        if self.pending >= 30:
            self.status.set('Trop de captures en attente : attendez quelques secondes.')
            return
        self.pending += 1
        self.capture_sequence += 1
        filename = Path(self.session.name) / f'capture_{self.capture_sequence:06d}.png'
        stamp = datetime.now().astimezone().isoformat(timespec='seconds')
        bounds = self.bounds
        def work():
            try:
                image = ImageGrab.grab(bbox=bounds, all_screens=True)
                image.save(filename, format='PNG')
                self.events.put(('captured', (stamp, filename)))
            except Exception as exc:
                self.events.put(('error', str(exc)))
        self.pool.submit(work)
        self.status.set(f'Capture demandée — {self.pending} en attente')

    def finish(self):
        if not self.active or self.finishing:
            return
        if not self.captures and self.pending == 0 and not messagebox.askyesno('Document vide', 'Aucune capture. Générer un document vide ?'):
            return
        name = self.document.get().strip()
        safe = re.sub(r'[<>:"/\\|?*\x00-\x1f]', '_', name).strip('. ') or 'captures'
        path = filedialog.asksaveasfilename(title='Enregistrer le document XHTML',
                                            initialfile=safe + '.xhtml', defaultextension='.xhtml',
                                            filetypes=[('Document XHTML', '*.xhtml')])
        if not path:
            return
        self.hook.enabled.clear()
        self.finishing = True
        self.end_btn.config(state='disabled')
        self.export_path = path
        self.status.set('Finalisation : attente des captures en cours…')

    def launch_export(self):
        path = self.export_path
        self.export_path = None
        name = self.document.get().strip()
        captures = list(self.captures)
        self.status.set('Génération et validation du XHTML en cours…')
        def work():
            try:
                export_xhtml(path, name, captures)
                self.events.put(('exported', path))
            except Exception as exc:
                self.events.put(('export_error', str(exc)))
        self.pool.submit(work)

    def export_complete(self, path):
        self.active = False
        self.finishing = False
        self.start_btn.config(state='normal')
        self.end_btn.config(state='disabled')
        self.combo.config(state='readonly')
        self.name_entry.config(state='normal')
        self.refresh_btn.config(state='normal')
        count = len(self.captures)
        self.status.set(f'Terminé — {count} capture(s) — XHTML vérifié')
        self.session.cleanup()
        self.session = None
        messagebox.showinfo('Document créé', f'{count} capture(s) enregistrée(s).\nStructure XML vérifiée :\n{path}')

    def on_close(self):
        if (self.active or self.finishing) and not messagebox.askyesno(
                'Quitter', 'Une session est en cours. Quitter sans finaliser le document ?'):
            return
        self.hook.stop()
        self.pool.shutdown(wait=True, cancel_futures=True)
        if self.session:
            self.session.cleanup()
        self.root.destroy()


if __name__ == '__main__':
    if len(sys.argv) == 3 and sys.argv[1] == '--self-test':
        report = {}
        try:
            root = tk.Tk()
            root.withdraw()
            app = CaptureApp(root)
            report['tk'] = root.tk.call('info', 'patchlevel')
            report['monitors'] = len(app.monitors)
            report['hook_installed'] = app.hook_ok
            app.hook.stop()
            app.pool.shutdown(wait=True)
            root.destroy()
            if not report['monitors'] or not report['hook_installed']:
                raise RuntimeError('Écrans ou hook indisponibles')
            report['ok'] = True
        except Exception as exc:
            report['ok'] = False
            report['error'] = str(exc)
        Path(sys.argv[2]).write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding='utf-8')
        sys.exit(0 if report['ok'] else 1)
    try:
        ctypes.windll.shcore.SetProcessDpiAwareness(2)
    except (AttributeError, OSError):
        try:
            ctypes.windll.user32.SetProcessDPIAware()
        except (AttributeError, OSError):
            pass
    window = tk.Tk()
    CaptureApp(window)
    window.mainloop()
