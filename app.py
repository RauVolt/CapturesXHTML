"""StepsShot 1.0 — guided screen capture to editable Word documents."""
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
from documents import export_docx
from screeninfo import get_monitors
from shortcuts import KEYS, MODIFIERS, DEFAULT_SHORTCUT, ShortcutMatcher, label, validate

VK_SNAPSHOT = 0x2C
WH_KEYBOARD_LL = 13
WM_KEYDOWN, WM_SYSKEYDOWN = 0x100, 0x104
WM_KEYUP, WM_SYSKEYUP = 0x101, 0x105
WM_QUIT = 0x12


class PrintScreenHook:
    """Hook clavier bas niveau Windows; avale Impr écran pendant une session."""
    def __init__(self, on_press, shortcut=DEFAULT_SHORTCUT):
        self.on_press = on_press
        self.matcher = ShortcutMatcher(shortcut)
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
        user32.GetAsyncKeyState.argtypes = [ctypes.c_int]
        user32.GetAsyncKeyState.restype = ctypes.c_short

        def callback(ncode, wparam, lparam):
            if ncode >= 0 and wparam in (WM_KEYDOWN, WM_SYSKEYDOWN, WM_KEYUP, WM_SYSKEYUP):
                data = ctypes.cast(lparam, ctypes.POINTER(KBDLLHOOKSTRUCT)).contents
                modifiers = {vk for vk in (0x10, 0x11, 0x12) if user32.GetAsyncKeyState(vk) & 0x8000}
                # Windows-key chords are never captured.
                if any(user32.GetAsyncKeyState(vk) & 0x8000 for vk in (0x5B, 0x5C)):
                    modifiers.add(0x5B)
                trigger, suppress = self.matcher.feed(data.vkCode,
                    wparam in (WM_KEYDOWN, WM_SYSKEYDOWN), self.enabled.is_set(), modifiers)
                if trigger:
                    self.on_press()
                if suppress:
                    return 1
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
        self.target_version = None
        Path(temp_root).mkdir(parents=True, exist_ok=True)
        self.folder = Path(tempfile.mkdtemp(prefix='session-', dir=temp_root))
        try:
            self.save()
        except Exception:
            self.cleanup()
            raise

    def capture(self, bounds=None):
        self.sequence += 1
        stamp = datetime.now().astimezone().isoformat(timespec='seconds')
        filename = self.folder / f'capture_{self.sequence:06d}.png'
        image = ImageGrab.grab(bbox=self.bounds if bounds is None else bounds, all_screens=True)
        try:
            image.save(filename, format='PNG')
        finally:
            image.close()
        self.captures.append((stamp, filename))
        # This local manifest permits manual recovery even if the DOCX update fails.
        atomic_json(self.folder / 'session.json', {
            'title': self.title, 'target': str(self.target),
            'captures': [(t, str(p)) for t, p in self.captures]})
        self.save()

    def save(self):
        if self.target_version is not None:
            try:
                stat = self.target.stat()
                current = (stat.st_mtime_ns, stat.st_size)
            except FileNotFoundError:
                current = None
            if current != self.target_version:
                raise OSError('Le document a été modifié ou déplacé hors de StepsShot. '
                              'Utilisez Enregistrer une copie pour préserver ces modifications.')
        export_docx(self.target, self.title, self.captures)
        stat = self.target.stat()
        self.target_version = (stat.st_mtime_ns, stat.st_size)
        self.saved_count = len(self.captures)

    def cleanup(self):
        for p in self.folder.iterdir():
            p.unlink()
        self.folder.rmdir()


class ScrollFrame(ttk.Frame):
    """Vertical scroll region; mouse wheel targets the innermost region."""
    def __init__(self, parent, background, height=600):
        super().__init__(parent)
        self.canvas = tk.Canvas(self, bg=background, highlightthickness=0, height=height)
        self.scrollbar = ttk.Scrollbar(self, orient='vertical', command=self.canvas.yview)
        self.scrollbar.pack(side='right', fill='y')
        self.canvas.pack(side='left', fill='both', expand=True)
        self.canvas.configure(yscrollcommand=self.scrollbar.set)
        self.body = ttk.Frame(self.canvas, style='Card.TFrame' if background == 'white' else 'TFrame')
        self.item = self.canvas.create_window((0, 0), window=self.body, anchor='nw')
        self.body.bind('<Configure>', lambda e: self.canvas.configure(scrollregion=self.canvas.bbox('all')))
        self.canvas.bind('<Configure>', lambda e: (self.canvas.itemconfigure(self.item, width=min(1060, e.width)), self.canvas.coords(self.item, max(0, (e.width-min(1060,e.width))/2), 0)))
        root = self.winfo_toplevel()
        if not getattr(root, '_scroll_handler_installed', False):
            root._scroll_handler_installed = True
            root.bind_all('<MouseWheel>', self.wheel, add='+')

    @staticmethod
    def wheel(event):
        widget = event.widget
        while widget is not None:
            if isinstance(widget, ScrollFrame):
                widget.canvas.yview_scroll(-1 if event.delta > 0 else 1, 'units')
                return 'break'
            widget = getattr(widget, 'master', None)


class CaptureApp:
    def __init__(self, root):
        self.root = root
        root.title('StepsShot · 1.0')
        root.geometry('1080x900')
        root.minsize(780, 520)
        icon = Path(getattr(sys, '_MEIPASS', Path(__file__).resolve().parent)) / 'assets' / 'capture.ico'
        if icon.exists():
            root.iconbitmap(str(icon))
        root.configure(bg='#f4f6fa')
        self.events = queue.Queue()
        self.pool = ThreadPoolExecutor(max_workers=1, thread_name_prefix='CaptureWorker')
        self.session = None
        self.pending = 0
        self.active = self.finishing = self.initializing = self.closing = False
        self.monitors = []
        self.data_root = Path(os.environ['LOCALAPPDATA']) / 'StepsShot'
        legacy = Path(os.environ['LOCALAPPDATA']) / 'CapturesXHTML'
        for filename in ('recent.json', 'settings.json'):
            target_config = self.data_root / filename
            if not target_config.exists() and (legacy / filename).exists():
                try:
                    atomic_json(target_config, json.loads((legacy / filename).read_text(encoding='utf-8')))
                except (OSError, ValueError):
                    pass
        self.history = History(self.data_root / 'recent.json')
        self.shortcut = DEFAULT_SHORTCUT
        try:
            config = json.loads((self.data_root / 'settings.json').read_text(encoding='utf-8'))
            self.shortcut = validate(config['modifier'], config['key'])
        except (OSError, ValueError, TypeError, KeyError):
            pass
        self.shortcut_modifier = tk.StringVar(value=self.shortcut[0])
        self.shortcut_key = tk.StringVar(value=self.shortcut[1])
        self.shortcut_hint = tk.StringVar(value='Pour capturer : ' + label(self.shortcut))
        self.document = tk.StringVar()
        self.monitor_choice = tk.StringVar()
        self.status = tk.StringVar(value='Prêt pour une nouvelle session')
        self.destination = tk.StringVar(value='Le fichier sera choisi avant la première capture.')
        self.counter = tk.StringVar(value='0 étape')
        self.save_path = tk.StringVar()
        self.guidance = tk.StringVar(value='Commencez par nommer votre guide et choisir l’écran à capturer.')
        self._design()
        self.refresh_history()
        self.refresh_monitors()
        self.hook = PrintScreenHook(lambda: self.events.put(('key', None)), self.shortcut)
        self.hook_ok = self.hook.start()
        if not self.hook_ok:
            self.status.set('Raccourci indisponible · redémarrez l’application pour réessayer')
            self.start_btn.config(state='disabled')
        self.poll = root.after(40, self.process_events)
        self.update_guidance()
        root.protocol('WM_DELETE_WINDOW', self.on_close)

    def _design(self):
        style = ttk.Style(self.root)
        style.theme_use('clam')
        ink, muted, paper, accent = '#122536', '#657887', '#eef3f6', '#11776b'
        self.root.configure(bg=paper)
        style.configure('.', font=('Segoe UI', 10), background=paper, foreground=ink)
        style.configure('TFrame', background=paper)
        style.configure('Card.TFrame', background='white')
        style.configure('TLabel', background='white', foreground=ink)
        style.configure('Muted.TLabel', foreground=muted, font=('Segoe UI', 9))
        style.configure('Heading.TLabel', font=('Segoe UI Semibold', 16))
        style.configure('Step.TLabel', font=('Segoe UI Semibold', 11), foreground=accent)
        style.configure('Count.TLabel', font=('Segoe UI Semibold', 26), foreground=ink)
        style.configure('TEntry', padding=11, fieldbackground='#f6f9fb', bordercolor='#dce5e9')
        style.configure('TCombobox', padding=10, fieldbackground='#f6f9fb', arrowsize=14)
        style.configure('TButton', padding=(16, 11), background='#e8eff3', foreground=ink, borderwidth=0)
        style.map('TButton', background=[('active', '#d8e5ec')], foreground=[('disabled', '#91a2ae')])
        style.configure('Primary.TButton', background=accent, foreground='white', font=('Segoe UI Semibold', 10))
        style.map('Primary.TButton', background=[('disabled', '#c5d7d5'), ('active', '#0c6157')], foreground=[('disabled','#f3f7f6')])
        outer = ScrollFrame(self.root, background=paper)
        outer.pack(fill='both', expand=True)
        self.page_scroll = outer
        shell = ttk.Frame(outer.body, padding=(28, 24))
        shell.pack(fill='both', expand=True)
        hero = tk.Frame(shell, bg=ink, padx=26, pady=24)
        hero.pack(fill='x', pady=(0,18))
        top = tk.Frame(hero, bg=ink)
        top.pack(fill='x')
        icon = Path(getattr(sys, '_MEIPASS', Path(__file__).resolve().parent)) / 'assets' / 'capture.png'
        if icon.exists():
            self.brand_icon = tk.PhotoImage(file=str(icon)).subsample(4,4)
            tk.Label(top,image=self.brand_icon,bg=ink).pack(side='left',padx=(0,14))
        name = tk.Frame(top,bg=ink)
        name.pack(side='left')
        tk.Label(name,text='StepsShot',bg=ink,fg='white',font=('Segoe UI Semibold',28)).pack(anchor='w')
        tk.Label(name,text='Vos étapes deviennent un guide modifiable.',bg=ink,fg='#b6cbd5',font=('Segoe UI',11)).pack(anchor='w')
        tk.Label(top,text='1.0  /  WINDOWS',bg='#20394b',fg='#9ce6d7',padx=14,pady=8,font=('Segoe UI Semibold',9)).pack(side='right')
        tk.Label(hero,text='NOMMER    →    CHOISIR L’ÉCRAN    →    CAPTURER    →    COMPLÉTER DANS WORD',
                 bg=ink,fg='#8fdbcd',font=('Segoe UI Semibold',9)).pack(anchor='w',pady=(18,0))
        card = ttk.Frame(shell,padding=24,style='Card.TFrame')
        card.pack(fill='x')
        ttk.Label(card,text='Préparez votre guide',style='Heading.TLabel').pack(anchor='w')
        fields = ttk.Frame(card,style='Card.TFrame')
        fields.pack(fill='x',pady=(18,14))
        fields.columnconfigure(0,weight=1,uniform='fields')
        fields.columnconfigure(1,weight=1,uniform='fields')
        ttk.Label(fields,text='1. Donnez un nom à votre guide',style='Step.TLabel').grid(row=0,column=0,sticky='w')
        ttk.Label(fields,text='2. Choisissez l’écran',style='Step.TLabel').grid(row=0,column=1,sticky='w',padx=(18,0))
        self.name_entry = ttk.Entry(fields,textvariable=self.document)
        self.name_entry.grid(row=1,column=0,sticky='ew',pady=(8,5))
        self.combo = ttk.Combobox(fields,textvariable=self.monitor_choice,state='readonly')
        self.combo.grid(row=1,column=1,sticky='ew',padx=(18,0),pady=(8,5))
        self.combo.bind('<<ComboboxSelected>>',self.monitor_changed)
        ttk.Label(fields,text='Exemple : Configurer une imprimante',style='Muted.TLabel').grid(row=2,column=0,sticky='w')
        self.refresh_btn = ttk.Button(fields,text='Actualiser les écrans',command=self.refresh_monitors)
        self.refresh_btn.grid(row=2,column=1,sticky='e',padx=(18,0))
        ttk.Label(card,text='3. Choisissez où enregistrer le document',style='Step.TLabel').pack(anchor='w',pady=(4,8))
        location = ttk.Frame(card,style='Card.TFrame')
        location.pack(fill='x')
        self.browse_btn = ttk.Button(location,text='Choisir un dossier…',command=self.choose_destination)
        self.browse_btn.pack(side='right',padx=(12,0))
        self.path_entry = ttk.Entry(location,textvariable=self.save_path,state='readonly')
        self.path_entry.pack(side='left',fill='x',expand=True)
        ttk.Label(card,text='Format Word .docx · sauvegarde automatique après chaque capture',style='Muted.TLabel').pack(anchor='w',pady=(8,16))
        self.start_btn = ttk.Button(card,text='Démarrer la session   →',command=self.start,style='Primary.TButton')
        self.start_btn.pack(anchor='w')
        live = ttk.Frame(shell,padding=24,style='Card.TFrame')
        live.pack(fill='x',pady=16)
        row = ttk.Frame(live,style='Card.TFrame')
        row.pack(fill='x')
        ttk.Label(row,text='4. Capturez vos étapes',style='Heading.TLabel').pack(side='left')
        ttk.Label(row,textvariable=self.counter,style='Count.TLabel').pack(side='right')
        ttk.Label(live,textvariable=self.guidance,wraplength=840).pack(anchor='w',pady=(10,5))
        self.shortcut_label = ttk.Label(live,textvariable=self.shortcut_hint,style='Step.TLabel')
        self.shortcut_label.pack(anchor='w',pady=(4,12))
        config = ttk.Frame(live,style='Card.TFrame')
        config.pack(fill='x')
        self.modifier_combo = ttk.Combobox(config,textvariable=self.shortcut_modifier,values=list(MODIFIERS),state='readonly',width=8)
        self.modifier_combo.pack(side='left')
        ttk.Label(config,text=' + ').pack(side='left')
        self.key_combo = ttk.Combobox(config,textvariable=self.shortcut_key,values=list(KEYS),state='readonly',width=15)
        self.key_combo.pack(side='left')
        self.modifier_combo.bind('<<ComboboxSelected>>',self.configure_shortcut)
        self.key_combo.bind('<<ComboboxSelected>>',self.configure_shortcut)
        ttk.Button(config,text='Rétablir Impr. écran',command=self.reset_shortcut).pack(side='right')
        ttk.Label(live,text='Le raccourci est actif uniquement pendant la session. L’écran peut être changé à tout moment.',
                  style='Muted.TLabel',wraplength=840).pack(anchor='w',pady=(8,14))
        self.end_btn = ttk.Button(live,text='Terminer et préparer le document',command=self.finish,state='disabled',style='Primary.TButton')
        self.end_btn.pack(anchor='w')
        ttk.Label(live,textvariable=self.status,wraplength=840).pack(anchor='w',pady=(12,4))
        ttk.Label(live,textvariable=self.destination,style='Muted.TLabel',wraplength=840).pack(anchor='w')
        edit = ttk.Frame(shell,padding=24,style='Card.TFrame')
        edit.pack(fill='x',pady=(0,16))
        ttk.Label(edit,text='5. Complétez votre guide',style='Heading.TLabel').pack(anchor='w')
        ttk.Label(edit,text='Après Terminer, ouvrez le document dans Word ou LibreOffice Writer pour modifier les textes, '
                  'ajouter vos explications et déplacer les images.',wraplength=840).pack(anchor='w',pady=(8,12))
        actions = ttk.Frame(edit,style='Card.TFrame')
        actions.pack(fill='x')
        self.open_doc_btn = ttk.Button(actions,text='Ouvrir le document',command=self.open_last_document,state='disabled')
        self.open_doc_btn.pack(side='left')
        self.copy_btn = ttk.Button(actions,text='Enregistrer une copie…',command=self.save_copy,state='disabled')
        self.copy_btn.pack(side='right')
        ttk.Label(edit,text='Attendez la fin de la session avant de modifier le document. Les captures restent des images.',
                  style='Muted.TLabel',wraplength=840).pack(anchor='w',pady=(10,0))
        recent = ttk.Frame(shell,padding=24,style='Card.TFrame')
        recent.pack(fill='x')
        ttk.Label(recent,text='Vos guides récents',style='Heading.TLabel').pack(anchor='w')
        ttk.Label(recent,text='Les cinq derniers documents · vos fichiers restent sur votre ordinateur',style='Muted.TLabel').pack(anchor='w',pady=(4,12))
        self.history_scroll = ScrollFrame(recent,background='white',height=210)
        self.history_scroll.pack(fill='x')
        self.recent_rows=[]
        for i in range(5):
            box=ttk.Frame(self.history_scroll.body,style='Card.TFrame')
            box.pack(fill='x',pady=6)
            opener=ttk.Button(box,text='Dossier  ↗',command=lambda index=i:self.open_history_folder(index))
            opener.pack(side='right',padx=(12,0))
            text_box=ttk.Frame(box,style='Card.TFrame')
            text_box.pack(side='left',fill='both',expand=True)
            title=ttk.Label(text_box,text='',font=('Segoe UI Semibold',10),wraplength=650)
            title.pack(anchor='w')
            path=ttk.Label(text_box,text='',style='Muted.TLabel',wraplength=650)
            path.pack(anchor='w')
            self.recent_rows.append((title,path,opener))
            text_box.bind('<Configure>',lambda e,t=title,p=path:(t.configure(wraplength=max(120,e.width)),p.configure(wraplength=max(120,e.width))))
        self.document.trace_add('write',lambda *args:self.update_guidance())

    def update_guidance(self):
        if not self.active and not self.initializing:
            if not self.document.get().strip():
                self.guidance.set('Étape 1 · Donnez un nom à votre guide.')
            elif self.combo.current()<0:
                self.guidance.set('Étape 2 · Sélectionnez un écran dans la liste.')
            elif not self.save_path.get():
                self.guidance.set('Étape 3 · Choisissez le nom du fichier et son dossier de sauvegarde.')
            else:
                self.guidance.set('Tout est prêt · cliquez sur Démarrer la session.')

    def choose_destination(self):
        name=self.document.get().strip()
        if not name:
            messagebox.showwarning('Nommez votre guide','Étape 1 : saisissez d’abord un nom pour votre guide.')
            self.name_entry.focus_set()
            return
        safe=re.sub(r'[<>:"/\\|?*\x00-\x1f]','_',name).strip('. ') or 'guide'
        target=filedialog.asksaveasfilename(title='Enregistrer votre guide Word',initialfile=safe+'.docx',
            defaultextension='.docx',filetypes=[('Document Word','*.docx')])
        if target:
            if Path(target).suffix.lower()!='.docx':
                messagebox.showwarning('Format Word','Choisissez un fichier avec l’extension .docx.')
                return
            self.save_path.set(target)
            self.update_guidance()

    def open_last_document(self):
        if self.active or not self.history.items:
            return
        try:
            os.startfile(self.history.items[0]['path'])
        except OSError as exc:
            messagebox.showerror('Document indisponible',str(exc))

    def save_copy(self):
        if not self.active or self.pending or self.finishing:
            return
        target=filedialog.asksaveasfilename(title='Enregistrer une copie du guide',defaultextension='.docx',
                    filetypes=[('Document Word','*.docx')])
        if not target:
            return
        if Path(target).suffix.lower()!='.docx' or Path(target).resolve()==self.session.target.resolve():
            messagebox.showwarning('Copie du document','Choisissez un autre fichier .docx.')
            return
        self.session.target=Path(target)
        self.session.target_version=None
        self.save_path.set(target)
        self.destination.set(target)
        self.finish()

    def refresh_history(self):
        for i, (title, path, opener) in enumerate(self.recent_rows):
            box = title.master.master
            if i < len(self.history.items):
                box.pack(fill='x', pady=4)
                item = self.history.items[i]
                title.config(text=item['title'])
                path.config(text=item['path'])
                opener.config(state='normal')
                opener.pack(side='right', padx=(12, 0))
            else:
                title.config(text='Aucun document pour le moment' if i == 0 else '')
                path.config(text='')
                opener.config(state='disabled')
                opener.pack_forget()
                if i > 0:
                    box.pack_forget()

    def remember(self):
        try:
            self.history.record(self.session.title, self.session.target)
            self.refresh_history()
        except OSError as exc:
            self.status.set(f'Document enregistré ; historique indisponible : {exc}')

    def open_history_folder(self, index):
        if not 0 <= index < len(self.history.items):
            return
        folder = Path(self.history.items[index]['path']).parent
        try:
            if not folder.is_dir():
                raise FileNotFoundError('Ce dossier a été déplacé ou supprimé.')
            os.startfile(str(folder))
        except OSError as exc:
            messagebox.showerror('Dossier indisponible', str(exc))

    def configure_shortcut(self, event=None):
        shortcut = validate(self.shortcut_modifier.get(), self.shortcut_key.get())
        try:
            atomic_json(self.data_root / 'settings.json', {'modifier': shortcut[0], 'key': shortcut[1]})
        except OSError as exc:
            self.shortcut_modifier.set(self.shortcut[0])
            self.shortcut_key.set(self.shortcut[1])
            messagebox.showerror('Raccourci', 'Configuration non enregistrée : ' + str(exc))
            return
        self.shortcut = shortcut
        self.hook.matcher.shortcut = shortcut
        self.shortcut_hint.set('Pour capturer : ' + label(shortcut))

    def reset_shortcut(self):
        self.shortcut_modifier.set(DEFAULT_SHORTCUT[0])
        self.shortcut_key.set(DEFAULT_SHORTCUT[1])
        self.configure_shortcut()

    def monitor_changed(self, event=None):
        self.update_guidance()
        if self.active and not self.finishing:
            self.status.set('Écran changé · les prochaines captures utiliseront la sélection actuelle')

    def refresh_monitors(self):
        try:
            self.monitors = get_monitors()
            self.combo['values'] = [f'Écran {i + 1} · {m.width} × {m.height}' for i, m in enumerate(self.monitors)]
            self.combo.current(0) if len(self.monitors) == 1 else self.monitor_choice.set('')
        except Exception as exc:
            self.monitors = []
            self.status.set(f'Écrans indisponibles : {exc}')

    def start(self):
        if self.active or self.initializing or not self.hook_ok:
            return
        name = self.document.get().strip()
        if not name or self.combo.current() < 0:
            messagebox.showwarning('Nouvelle session', 'Saisissez un titre et sélectionnez un écran.')
            return
        if not self.save_path.get():
            self.choose_destination()
        target=self.save_path.get()
        if not target:
            return
        # Reconfirm replacements at session start, not merely when choosing a path.
        if Path(target).exists() and not messagebox.askyesno('Remplacer le document ?',
                'Ce fichier existe déjà. Créer un nouveau guide à cet emplacement le remplacera. Continuer ?'):
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
        self.combo.config(state='readonly')
        self.refresh_btn.config(state='disabled' if locked else 'normal')
        self.browse_btn.config(state='disabled' if locked else 'normal')
        self.open_doc_btn.config(state='disabled' if locked else ('normal' if self.history.items else 'disabled'))

    def capture(self):
        if not self.active or self.finishing:
            return
        if self.pending >= 30:
            self.status.set('Captures en attente · patientez quelques secondes')
            return
        selected = self.combo.current()
        if not 0 <= selected < len(self.monitors):
            self.status.set('Sélectionnez un écran avant la prochaine capture')
            return
        monitor = self.monitors[selected]
        bounds = (monitor.x, monitor.y, monitor.x + monitor.width, monitor.y + monitor.height)
        self.pending += 1
        self.status.set(f'Capture et sauvegarde en cours · {self.pending} en attente')
        def work():
            try:
                self.session.capture(bounds)
                self.events.put(('saved', (len(self.session.captures), self.session.saved_count)))
            except Exception as exc:
                self.events.put(('capture_error', (str(exc), len(self.session.captures), self.session.saved_count)))
        self.pool.submit(work)

    def finish(self):
        if not self.active or self.finishing:
            return
        self.finishing = True
        self.hook.enabled.clear()
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
                    self.counter.set('0 étape')
                    self.guidance.set('Utilisez votre raccourci pour capturer. Chaque étape est enregistrée dans le document Word.')
                    self.copy_btn.config(state='normal')
                    self.status.set('Document créé · sauvegarde automatique activée')
                    self.remember()
                    self.end_btn.config(state='normal')
                    if self.hook_ok:
                        self.hook.enabled.set()
                elif kind == 'init_error':
                    self.initializing = False
                    self._lock_fields(False)
                    self.status.set('Création impossible · choisissez un autre emplacement')
                    messagebox.showerror('Document Word', payload)
                elif kind in ('saved', 'capture_error'):
                    self.pending -= 1
                    if kind == 'saved':
                        count, saved = payload
                        self.status.set(f'{saved} capture(s) sauvegardée(s) · {self.pending} en attente')
                        self.remember()
                    else:
                        error, count, saved = payload
                        self.status.set(f'Échec de capture ou sauvegarde · {saved}/{count} intégrée(s) au document Word. Réessayez avec Terminer.')
                        messagebox.showerror('Sauvegarde à vérifier', error + '\nLes PNG disponibles sont conservés dans :\n' + str(self.session.folder))
                    self.counter.set(f'{count} étape(s)')
                elif kind == 'finished':
                    self.remember()
                    self.active = self.finishing = False
                    self.copy_btn.config(state='disabled')
                    self.guidance.set('Votre guide est prêt. Ouvrez-le pour compléter les explications dans Word ou Writer.')
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
                    if self.hook_ok:
                        self.hook.enabled.set()
                    self.status.set('Dernière sauvegarde échouée · cliquez sur Terminer pour réessayer')
                    messagebox.showerror('Document Word', payload + '\nPNG conservés :\n' + str(self.session.folder))
                    if close_requested and messagebox.askyesno('Fermer malgré l’erreur ?',
                            'La dernière sauvegarde DOCX reste disponible. Les PNG seront conservés pour récupération manuelle. Fermer ?'):
                        self._destroy()
                        return
        except queue.Empty:
            pass
        self.poll = self.root.after(40, self.process_events)

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
        self.root.after_cancel(self.poll)
        self.hook.stop()
        self.pool.shutdown(wait=False)
        self.root.destroy()


if __name__ == '__main__':
    try:
        ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID.argtypes = [ctypes.c_wchar_p]
        ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID('RauVolt.StepsShot')
    except (AttributeError, OSError):
        pass
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
                      'recent_slots': len(app.recent_rows), 'shortcut': label(app.shortcut),
                      'scrollbars': 2, 'tk': window.tk.call('info', 'patchlevel')}
            with tempfile.TemporaryDirectory(dir=Path(sys.argv[2]).resolve().parent) as folder:
                from PIL import Image
                png = Path(folder) / 'probe.png'
                Image.new('RGB', (160, 90), '#11776b').save(png)
                export_docx(Path(folder) / 'probe.docx', 'Guide de vérification',
                            [(datetime.now().astimezone().isoformat(), png)])
                report['docx_export'] = True
            report['ok'] = bool(app.monitors) and app.hook_ok and report['docx_export']
            app._destroy()
        except Exception as exc:
            report.update(ok=False, error=str(exc))
        Path(sys.argv[2]).write_text(json.dumps(report, indent=2), encoding='utf-8')
        sys.exit(0 if report['ok'] else 1)
    window = tk.Tk()
    CaptureApp(window)
    window.mainloop()
