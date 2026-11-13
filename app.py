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


def atomic_json(path, data):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, partial = tempfile.mkstemp(dir=path.parent, prefix='.state-', suffix='.tmp')
    try:
        with os.fdopen(fd, 'w', encoding='utf-8') as out:
            json.dump(data, out, ensure_ascii=False, indent=2)
            out.flush()
            os.fsync(out.fileno())
        os.replace(partial, path)
    finally:
        if os.path.exists(partial):
            os.unlink(partial)


class History:
    def __init__(self, path):
        self.path = Path(path)
        try:
            data = json.loads(self.path.read_text(encoding='utf-8'))
            self.items = [x for x in data if isinstance(x, dict) and
                          isinstance(x.get('title'), str) and isinstance(x.get('path'), str)][:5]
        except (OSError, ValueError, TypeError):
            self.items = []

    def record(self, title, path):
        absolute = str(Path(path).resolve())
        items = [{'title': title, 'path': absolute}] + [
            x for x in self.items if os.path.normcase(x['path']) != os.path.normcase(absolute)]
        atomic_json(self.path, items[:5])
        self.items = items[:5]


class ProgressiveSession:
    """Used only by the single background worker; PNGs survive a save failure."""
    def __init__(self, target, title, bounds, temp_root):
        self.target, self.title, self.bounds = Path(target), title, bounds
        self.captures = []
        self.sequence = 0
        self.saved_count = 0
        Path(temp_root).mkdir(parents=True, exist_ok=True)
        self.folder = Path(tempfile.mkdtemp(prefix='session-', dir=temp_root))
        try:
            self.save()
        except Exception:
            self.cleanup()
            raise

    def capture(self):
        self.sequence += 1
        stamp = datetime.now().astimezone().isoformat(timespec='seconds')
        filename = self.folder / f'capture_{self.sequence:06d}.png'
        image = ImageGrab.grab(bbox=self.bounds, all_screens=True)
        try:
            image.save(filename, format='PNG')
        finally:
            image.close()
        self.captures.append((stamp, filename))
        # This local manifest permits manual recovery even if the XHTML update fails.
        atomic_json(self.folder / 'session.json', {
            'title': self.title, 'target': str(self.target),
            'captures': [(t, str(p)) for t, p in self.captures]})
        self.save()

    def save(self):
        export_xhtml(self.target, self.title, self.captures)
        self.saved_count = len(self.captures)

    def cleanup(self):
        for p in self.folder.iterdir():
            p.unlink()
        self.folder.rmdir()


class CaptureApp:
    def __init__(self, root):
        self.root = root
        root.title('CapturesXHTML · 1.3')
        root.geometry('880x790')
        root.minsize(760, 730)
        root.configure(bg='#f4f6fa')
        self.events = queue.Queue()
        self.pool = ThreadPoolExecutor(max_workers=1, thread_name_prefix='CaptureWorker')
        self.session = None
        self.pending = 0
        self.active = self.finishing = self.initializing = self.closing = False
        self.monitors = []
        self.data_root = Path(os.environ['LOCALAPPDATA']) / 'CapturesXHTML'
        self.history = History(self.data_root / 'recent.json')
        self.document = tk.StringVar()
        self.monitor_choice = tk.StringVar()
        self.status = tk.StringVar(value='Prêt pour une nouvelle session')
        self.destination = tk.StringVar(value='Le fichier sera choisi avant la première capture.')
        self.counter = tk.StringVar(value='0 capture')
        self._design()
        self.refresh_history()
        self.refresh_monitors()
        self.hook = PrintScreenHook(lambda: self.events.put(('key', None)))
        self.hook_ok = self.hook.start()
        if not self.hook_ok:
            self.status.set('Impr. écran indisponible · utilisez le bouton Capturer')
        root.after(40, self.process_events)
        root.protocol('WM_DELETE_WINDOW', self.on_close)

    def _design(self):
        style = ttk.Style(self.root)
        style.theme_use('clam')
        style.configure('.', font=('Segoe UI', 10), background='#f4f6fa', foreground='#17243b')
        style.configure('TFrame', background='#f4f6fa')
        style.configure('Card.TFrame', background='white')
        style.configure('TLabel', background='white', foreground='#17243b')
        style.configure('Muted.TLabel', foreground='#64748b', font=('Segoe UI', 9))
        style.configure('Title.TLabel', background='#f4f6fa', font=('Segoe UI Semibold', 25))
        style.configure('Subtitle.TLabel', background='#f4f6fa', foreground='#64748b')
        style.configure('Heading.TLabel', font=('Segoe UI Semibold', 12))
        style.configure('Count.TLabel', font=('Segoe UI Semibold', 17), foreground='#2563eb')
        style.configure('TEntry', padding=10, fieldbackground='#f8fafc', bordercolor='#dce3ed')
        style.configure('TCombobox', padding=9, fieldbackground='#f8fafc', arrowsize=14)
        style.configure('TButton', padding=(16, 10), background='#e9eef5', borderwidth=0)
        style.map('TButton', background=[('active', '#dbe4ef')], foreground=[('disabled', '#94a3b8')])
        style.configure('Primary.TButton', background='#2563eb', foreground='white')
        style.map('Primary.TButton', background=[('disabled', '#cbd5e1'), ('active', '#1d4ed8')])
        shell = ttk.Frame(self.root, padding=(30, 24))
        shell.pack(fill='both', expand=True)
        ttk.Label(shell, text='CapturesXHTML', style='Title.TLabel').pack(anchor='w')
        ttk.Label(shell, text='Vos captures. Un seul document. Enregistré au fil de la session.',
                  style='Subtitle.TLabel').pack(anchor='w', pady=(3, 18))
        card = ttk.Frame(shell, padding=22, style='Card.TFrame')
        card.pack(fill='x')
        ttk.Label(card, text='Nouvelle session', style='Heading.TLabel').pack(anchor='w')
        fields = ttk.Frame(card, style='Card.TFrame')
        fields.pack(fill='x', pady=(16, 12))
        fields.columnconfigure(0, weight=1)
        fields.columnconfigure(1, weight=1)
        ttk.Label(fields, text='Titre du document', style='Muted.TLabel').grid(row=0, column=0, sticky='w')
        ttk.Label(fields, text='Écran à capturer', style='Muted.TLabel').grid(row=0, column=1, sticky='w', padx=(16, 0))
        self.name_entry = ttk.Entry(fields, textvariable=self.document)
        self.name_entry.grid(row=1, column=0, sticky='ew', pady=(5, 0))
        self.combo = ttk.Combobox(fields, textvariable=self.monitor_choice, state='readonly')
        self.combo.grid(row=1, column=1, sticky='ew', padx=(16, 0), pady=(5, 0))
        buttons = ttk.Frame(card, style='Card.TFrame')
        buttons.pack(fill='x')
        self.start_btn = ttk.Button(buttons, text='Choisir le fichier et démarrer', command=self.start, style='Primary.TButton')
        self.start_btn.pack(side='left')
        self.refresh_btn = ttk.Button(buttons, text='Actualiser les écrans', command=self.refresh_monitors)
        self.refresh_btn.pack(side='right')
        live = ttk.Frame(shell, padding=22, style='Card.TFrame')
        live.pack(fill='x', pady=14)
        ttk.Label(live, textvariable=self.counter, style='Count.TLabel').pack(anchor='w')
        ttk.Label(live, textvariable=self.status, wraplength=740).pack(anchor='w', pady=(6, 3))
        ttk.Label(live, textvariable=self.destination, style='Muted.TLabel', wraplength=740).pack(anchor='w', pady=(0, 12))
        row = ttk.Frame(live, style='Card.TFrame')
        row.pack(fill='x')
        self.capture_btn = ttk.Button(row, text='Capturer · Impr. écran', command=self.capture, state='disabled', style='Primary.TButton')
        self.capture_btn.pack(side='left')
        self.end_btn = ttk.Button(row, text='Terminer', command=self.finish, state='disabled')
        self.end_btn.pack(side='left', padx=10)
        self.folder_btn = ttk.Button(row, text='Ouvrir le dossier', command=self.open_last_folder)
        self.folder_btn.pack(side='right')
        recent = ttk.Frame(shell, padding=(22, 18), style='Card.TFrame')
        recent.pack(fill='both', expand=True)
        ttk.Label(recent, text='Documents récents', style='Heading.TLabel').pack(anchor='w')
        ttk.Label(recent, text='Les 5 derniers fichiers enregistrés sur cet ordinateur', style='Muted.TLabel').pack(anchor='w', pady=(2, 8))
        self.recent_rows = []
        for _ in range(5):
            box = ttk.Frame(recent, style='Card.TFrame')
            box.pack(fill='x', pady=4)
            title = ttk.Label(box, text='', font=('Segoe UI Semibold', 10))
            title.pack(anchor='w')
            path = ttk.Label(box, text='', style='Muted.TLabel', wraplength=730)
            path.pack(anchor='w')
            self.recent_rows.append((title, path))

    def refresh_history(self):
        for i, (title, path) in enumerate(self.recent_rows):
            if i < len(self.history.items):
                item = self.history.items[i]
                title.config(text=item['title'])
                path.config(text=item['path'])
            else:
                title.config(text='Aucun document pour le moment' if i == 0 else '')
                path.config(text='')
        self.folder_btn.config(state='normal' if self.history.items else 'disabled')

    def remember(self):
        try:
            self.history.record(self.session.title, self.session.target)
            self.refresh_history()
        except OSError as exc:
            self.status.set(f'Document enregistré ; historique indisponible : {exc}')

    def open_last_folder(self):
        if not self.history.items:
            return
        folder = Path(self.history.items[0]['path']).parent
        try:
            if not folder.is_dir():
                raise FileNotFoundError('Ce dossier a été déplacé ou supprimé.')
            os.startfile(str(folder))
        except OSError as exc:
            messagebox.showerror('Dossier indisponible', str(exc))

    def refresh_monitors(self):
        try:
            self.monitors = get_monitors()
            self.combo['values'] = [f'Écran {i + 1} · {m.width} × {m.height}' for i, m in enumerate(self.monitors)]
            self.combo.current(0) if len(self.monitors) == 1 else self.monitor_choice.set('')
        except Exception as exc:
            self.monitors = []
            self.status.set(f'Écrans indisponibles : {exc}')

    def start(self):
        if self.active or self.initializing:
            return
        name = self.document.get().strip()
        if not name or self.combo.current() < 0:
            messagebox.showwarning('Nouvelle session', 'Saisissez un titre et sélectionnez un écran.')
            return
        safe = re.sub(r'[<>:"/\\|?*\x00-\x1f]', '_', name).strip('. ') or 'captures'
        target = filedialog.asksaveasfilename(title='Créer le document XHTML', initialfile=safe + '.xhtml',
                    defaultextension='.xhtml', filetypes=[('Document XHTML', '*.xhtml')])
        if not target:
            return
        m = self.monitors[self.combo.current()]
        bounds = (m.x, m.y, m.x + m.width, m.y + m.height)
        self.initializing = True
        self._lock_fields(True)
        self.status.set('Création du document…')
        self.destination.set(target)
        def work():
            try:
                session = ProgressiveSession(target, name, bounds, self.data_root / 'Temp')
                self.events.put(('initialized', session))
            except Exception as exc:
                self.events.put(('init_error', str(exc)))
        self.pool.submit(work)

    def _lock_fields(self, locked):
        self.start_btn.config(state='disabled' if locked else 'normal')
        self.name_entry.config(state='disabled' if locked else 'normal')
        self.combo.config(state='disabled' if locked else 'readonly')
        self.refresh_btn.config(state='disabled' if locked else 'normal')

    def capture(self):
        if not self.active or self.finishing:
            return
        if self.pending >= 30:
            self.status.set('Captures en attente · patientez quelques secondes')
            return
        self.pending += 1
        self.status.set(f'Capture et sauvegarde en cours · {self.pending} en attente')
        def work():
            try:
                self.session.capture()
                self.events.put(('saved', (len(self.session.captures), self.session.saved_count)))
            except Exception as exc:
                self.events.put(('capture_error', (str(exc), len(self.session.captures), self.session.saved_count)))
        self.pool.submit(work)

    def finish(self):
        if not self.active or self.finishing:
            return
        self.finishing = True
        self.hook.enabled.clear()
        self.capture_btn.config(state='disabled')
        self.end_btn.config(state='disabled')
        self.status.set('Finalisation · attente des captures et dernière sauvegarde…')
        def work():
            try:
                self.session.save()
                self.events.put(('finished', None))
            except Exception as exc:
                self.events.put(('finish_error', str(exc)))
        self.pool.submit(work)

    def process_events(self):
        try:
            while True:
                kind, payload = self.events.get_nowait()
                if kind == 'key':
                    self.capture()
                elif kind == 'initialized':
                    self.session = payload
                    self.initializing = False
                    self.active = True
                    self.counter.set('0 capture')
                    self.status.set('Document créé · sauvegarde automatique activée')
                    self.remember()
                    self.capture_btn.config(state='normal')
                    self.end_btn.config(state='normal')
                    if self.hook_ok:
                        self.hook.enabled.set()
                elif kind == 'init_error':
                    self.initializing = False
                    self._lock_fields(False)
                    self.status.set('Création impossible · choisissez un autre emplacement')
                    messagebox.showerror('Document XHTML', payload)
                elif kind in ('saved', 'capture_error'):
                    self.pending -= 1
                    if kind == 'saved':
                        count, saved = payload
                        self.status.set(f'{saved} capture(s) sauvegardée(s) · {self.pending} en attente')
                        self.remember()
                    else:
                        error, count, saved = payload
                        self.status.set(f'Échec de capture ou sauvegarde · {saved}/{count} intégrée(s) au XHTML. Réessayez avec Terminer.')
                        messagebox.showerror('Sauvegarde à vérifier', error + '\nLes PNG disponibles sont conservés dans :\n' + str(self.session.folder))
                    self.counter.set(f'{count} capture(s)')
                elif kind == 'finished':
                    self.remember()
                    self.active = self.finishing = False
                    self._lock_fields(False)
                    self.status.set(f'Session terminée · {len(self.session.captures)} capture(s) sauvegardée(s)')
                    try:
                        self.session.cleanup()
                    except OSError:
                        self.status.set('Document sauvegardé · des fichiers temporaires restent à nettoyer')
                    self.session = None
                    if self.closing:
                        self._destroy()
                        return
                elif kind == 'finish_error':
                    close_requested = self.closing
                    self.finishing = self.closing = False
                    self.end_btn.config(state='normal')
                    self.capture_btn.config(state='normal')
                    if self.hook_ok:
                        self.hook.enabled.set()
                    self.status.set('Dernière sauvegarde échouée · cliquez sur Terminer pour réessayer')
                    messagebox.showerror('Document XHTML', payload + '\nPNG conservés :\n' + str(self.session.folder))
                    if close_requested and messagebox.askyesno('Fermer malgré l’erreur ?',
                            'La dernière sauvegarde XHTML reste disponible. Les PNG seront conservés pour récupération manuelle. Fermer ?'):
                        self._destroy()
                        return
        except queue.Empty:
            pass
        self.root.after(40, self.process_events)

    def on_close(self):
        if self.initializing:
            messagebox.showinfo('Création en cours', 'Attendez la création du document avant de fermer.')
            return
        if self.active:
            if messagebox.askyesno('Terminer la session', 'Terminer la sauvegarde puis fermer l’application ?'):
                self.closing = True
                if not self.finishing:
                    self.finish()
            return
        self._destroy()

    def _destroy(self):
        self.hook.stop()
        self.pool.shutdown(wait=False)
        self.root.destroy()


if __name__ == '__main__':
    try:
        ctypes.windll.shcore.SetProcessDpiAwareness(2)
    except (AttributeError, OSError):
        pass
    if len(sys.argv) == 3 and sys.argv[1] == '--self-test':
        report = {}
        try:
            window = tk.Tk()
            window.withdraw()
            app = CaptureApp(window)
            report = {'monitors': len(app.monitors), 'hook_installed': app.hook_ok,
                      'recent_slots': len(app.recent_rows), 'tk': window.tk.call('info', 'patchlevel')}
            report['ok'] = bool(app.monitors) and app.hook_ok
            app._destroy()
        except Exception as exc:
            report.update(ok=False, error=str(exc))
        Path(sys.argv[2]).write_text(json.dumps(report, indent=2), encoding='utf-8')
        sys.exit(0 if report['ok'] else 1)
    window = tk.Tk()
    CaptureApp(window)
    window.mainloop()
