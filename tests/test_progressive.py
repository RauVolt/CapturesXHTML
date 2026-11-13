import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch
from xml.etree import ElementTree as ET
from PIL import Image
from app import ProgressiveSession, History


class ProgressiveTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.target = self.root / 'document.xhtml'

    def session(self):
        return ProgressiveSession(self.target, 'Titre & écran', (0, 0, 100, 100), self.root / 'Temp')

    def images(self):
        doc = ET.parse(self.target)
        return len(doc.findall('.//{http://www.w3.org/1999/xhtml}img'))

    @patch('app.ImageGrab.grab', side_effect=lambda **kw: Image.new('RGB', (100, 100)))
    def test_initial_document_then_each_capture_is_saved(self, grab):
        session = self.session()
        self.assertEqual(self.images(), 0)
        for i in range(1, 4):
            session.capture()
            self.assertEqual(self.images(), i)
            self.assertEqual(session.saved_count, i)
        manifest = json.loads((session.folder / 'session.json').read_text(encoding='utf-8'))
        self.assertEqual(len(manifest['captures']), 3)
        session.cleanup()
        self.assertTrue(self.target.exists())

    @patch('app.ImageGrab.grab', side_effect=lambda **kw: Image.new('RGB', (100, 100)))
    def test_save_failure_preserves_last_xhtml_and_png_then_retry(self, grab):
        session = self.session()
        session.capture()
        previous = self.target.read_bytes()
        with patch('app.export_xhtml', side_effect=OSError('disk unavailable')):
            with self.assertRaises(OSError):
                session.capture()
        self.assertEqual(previous, self.target.read_bytes())
        self.assertEqual(session.saved_count, 1)
        self.assertTrue(session.captures[-1][1].exists())
        session.save()
        self.assertEqual(self.images(), 2)

    def test_failed_initialization_does_not_replace_existing_document(self):
        self.target.write_text('previous')
        with patch('app.export_xhtml', side_effect=OSError('read only')):
            with self.assertRaises(OSError):
                self.session()
        self.assertEqual(self.target.read_text(), 'previous')
        self.assertEqual(list((self.root / 'Temp').iterdir()), [])

    def test_history_five_unique_paths_persist_across_restart(self):
        path = self.root / 'recent.json'
        history = History(path)
        for i in range(7):
            history.record(f'Doc {i}', self.root / f'{i}.xhtml')
        history.record('Updated', self.root / '4.xhtml')
        loaded = History(path)
        self.assertEqual(len(loaded.items), 5)
        self.assertEqual(loaded.items[0]['title'], 'Updated')
        self.assertEqual(len(set(x['path'] for x in loaded.items)), 5)
        self.assertTrue(all(Path(x['path']).is_absolute() for x in loaded.items))

    def test_corrupt_history_is_ignored(self):
        path = self.root / 'recent.json'
        path.write_text('{bad json')
        self.assertEqual(History(path).items, [])
