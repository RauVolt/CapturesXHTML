import os
import tempfile
import threading
import time
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch
from PIL import Image
from app import CaptureApp, tk
from shortcuts import ShortcutMatcher, DEFAULT_SHORTCUT


class FakeHook:
    def __init__(self, callback, shortcut):
        self.enabled = threading.Event()
        self.matcher = ShortcutMatcher(shortcut)
    def start(self):
        return True
    def stop(self):
        self.enabled.clear()


@unittest.skipUnless(os.name == 'nt', 'Windows interface')
class InterfaceTests(unittest.TestCase):
    def test_shortcut_restore_scrolling_history_and_live_monitor_switch(self):
        with tempfile.TemporaryDirectory() as folder, patch.dict(os.environ, LOCALAPPDATA=folder), \
                patch('app.PrintScreenHook', FakeHook), patch('app.get_monitors', return_value=[
                    SimpleNamespace(x=0,y=0,width=100,height=80),
                    SimpleNamespace(x=-120,y=0,width=120,height=90)]):
            root = tk.Tk()
            root.withdraw()
            app = CaptureApp(root)
            try:
                self.assertFalse(hasattr(app, 'capture_btn'))
                self.assertEqual(str(app.page_scroll.scrollbar.cget('orient')), 'vertical')
                self.assertEqual(str(app.history_scroll.scrollbar.cget('orient')), 'vertical')
                app.shortcut_modifier.set('Ctrl')
                app.shortcut_key.set('F8')
                app.configure_shortcut()
                self.assertEqual(app.hook.matcher.shortcut, ('Ctrl', 'F8'))
                app.reset_shortcut()
                self.assertEqual(app.hook.matcher.shortcut, DEFAULT_SHORTCUT)
                for i in range(5):
                    directory = Path(folder) / str(i)
                    directory.mkdir()
                    app.history.record(f'Doc {i}', directory / 'doc.xhtml')
                app.refresh_history()
                for i, (_, _, button) in enumerate(app.recent_rows):
                    with patch('app.os.startfile') as opener:
                        button.invoke()
                        opener.assert_called_once_with(str(Path(app.history.items[i]['path']).parent))
                target = Path(folder) / 'session.xhtml'
                app.document.set('Test session')
                app.combo.current(0)
                with patch('app.filedialog.asksaveasfilename', return_value=str(target)):
                    app.start()
                def until(predicate):
                    deadline = time.monotonic() + 15
                    while not predicate():
                        self.assertLess(time.monotonic(), deadline)
                        root.update()
                        time.sleep(.01)
                until(lambda: app.active)
                self.assertEqual(str(app.combo.cget('state')), 'readonly')
                boxes = []
                def grab(**kw):
                    boxes.append(kw['bbox'])
                    return Image.new('RGB', (100, 80))
                with patch('app.ImageGrab.grab', side_effect=grab):
                    app.capture()
                    app.combo.current(1)
                    app.monitor_changed()
                    app.capture()
                    app.combo.current(0)
                    app.finish()
                    until(lambda: not app.active)
                self.assertEqual(boxes, [(0,0,100,80), (-120,0,0,90)])
                self.assertTrue(target.exists())
            finally:
                app._destroy()
