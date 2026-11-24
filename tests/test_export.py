import tempfile
import unittest
from pathlib import Path
from zipfile import ZipFile
from unittest.mock import patch
from PIL import Image
from docx import Document
from documents import export_docx, validate_docx


class ExportTests(unittest.TestCase):
    def test_editable_roundtrip_unicode_images_and_aspect_ratio(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            png, target = root / 'image.png', root / 'résultat.docx'
            Image.new('RGB', (1920,1080), '#76e0c4').save(png)
            title = 'Écran <test> & texte'
            export_docx(target,title,[('2026-11-16T20:00:00+01:00',png)])
            validate_docx(target)
            document = Document(target)
            self.assertEqual(document.paragraphs[0].text,title)
            self.assertEqual(len(document.inline_shapes),1)
            shape = document.inline_shapes[0]
            self.assertAlmostEqual(shape.width/shape.height,1920/1080,places=4)
            with ZipFile(target) as archive:
                images = [name for name in archive.namelist() if name.startswith('word/media/')]
                self.assertEqual(archive.read(images[0]),png.read_bytes())
            document.add_paragraph('Explication ajoutée dans un éditeur Word')
            document.save(target)
            self.assertEqual(Document(target).paragraphs[-1].text,'Explication ajoutée dans un éditeur Word')

    def test_failed_export_preserves_existing_file_and_removes_partial(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            target = root/'existing.docx'
            target.write_bytes(b'original')
            with self.assertRaises(FileNotFoundError):
                export_docx(target,'Test',[('2026-11-16T20:00:00',root/'missing.png')])
            self.assertEqual(target.read_bytes(),b'original')
            self.assertEqual(list(root.glob('.stepsshot-*')),[])

    def test_locked_target_preserves_original(self):
        with tempfile.TemporaryDirectory() as folder:
            target = Path(folder)/'locked.docx'
            target.write_bytes(b'original')
            with patch('documents.os.replace', side_effect=PermissionError('Word has locked the file')):
                with self.assertRaises(PermissionError):
                    export_docx(target,'Test',[])
            self.assertEqual(target.read_bytes(),b'original')

    def test_corrupt_docx_rejected(self):
        with tempfile.TemporaryDirectory() as folder:
            target=Path(folder)/'bad.docx'
            target.write_bytes(b'not a Word file')
            with self.assertRaises(Exception):
                validate_docx(target)
