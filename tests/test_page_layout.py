import re
import tempfile
import unittest
from datetime import datetime
from pathlib import Path
from zipfile import ZipFile
from xml.etree import ElementTree as ET
from documents import export_docx


class PageLayoutTests(unittest.TestCase):
    def test_header_date_and_native_pagination(self):
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / 'Mon guide.docx'
            export_docx(path, 'Un autre titre', [])
            with ZipFile(path) as archive:
                ns = {'w': 'http://schemas.openxmlformats.org/wordprocessingml/2006/main'}
                header = ET.fromstring(archive.read('word/header1.xml'))
                footer = ET.fromstring(archive.read('word/footer1.xml'))
                self.assertEqual(''.join(header.itertext()), 'Mon guide')
                self.assertIn(datetime.now().strftime('%d/%m/%Y'), ''.join(footer.itertext()))
                fields = footer.findall('.//w:fldSimple', ns)
                self.assertEqual([x.attrib['{' + ns['w'] + '}instr'] for x in fields], ['PAGE', 'NUMPAGES'])
                self.assertIsNotNone(footer.find('.//w:tabs/w:tab[@w:val="right"]', ns))
