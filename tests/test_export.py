import base64
import tempfile
import unittest
from pathlib import Path
from xml.etree import ElementTree as ET
from PIL import Image
from app import export_xhtml, valid_xml_file


class ExportTests(unittest.TestCase):
    def test_roundtrip_unicode_and_embedded_png(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            png, target = root / 'capture.png', root / 'résultat.xhtml'
            Image.new('RGB', (160, 90), 'blue').save(png)
            title = 'Écran <test> & "texte"'
            export_xhtml(target, title, [('2026-11-13T12:00:00+01:00', png)])
            valid_xml_file(target)
            doc = ET.parse(target)
            ns = {'x': 'http://www.w3.org/1999/xhtml'}
            self.assertEqual(doc.find('x:head/x:title', ns).text, title)
            image = doc.find('.//x:img', ns)
            self.assertEqual(base64.b64decode(image.attrib['src'].split(',', 1)[1]), png.read_bytes())

    def test_failed_export_preserves_destination_and_capture(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            target, png = root / 'existing.xhtml', root / 'capture.png'
            target.write_text('original', encoding='utf-8')
            Image.new('RGB', (2, 2)).save(png)
            with self.assertRaises(FileNotFoundError):
                export_xhtml(target, 'test', [('2026-11-13T12:00:00', png),
                                            ('2026-11-13T12:00:01', root / 'missing.png')])
            self.assertEqual(target.read_text(), 'original')
            self.assertTrue(png.exists())
            self.assertEqual(list(root.glob('*.tmp')), [])

    def test_invalid_xml_rejected(self):
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / 'bad.xhtml'
            path.write_text('<html><body></html>')
            with self.assertRaises(Exception):
                valid_xml_file(path)


if __name__ == '__main__':
    unittest.main()
