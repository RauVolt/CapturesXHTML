"""Editable Word export with validation and atomic destination replacement."""
import os
import tempfile
from datetime import datetime
from pathlib import Path
from zipfile import ZipFile
from xml.etree import ElementTree as ET

from docx import Document
from docx.shared import Inches, Pt, RGBColor
from PIL import Image


def validate_docx(path):
    with ZipFile(path) as archive:
        if archive.testzip() is not None:
            raise ValueError('Le document Word est incomplet.')
        for member in archive.namelist():
            if member.endswith(('.xml', '.rels')):
                ET.fromstring(archive.read(member))
    Document(str(path))


def export_docx(path, title, captures):
    target = Path(path)
    fd, partial = tempfile.mkstemp(prefix='.stepsshot-', suffix='.docx', dir=target.parent)
    os.close(fd)
    try:
        doc = Document()
        section = doc.sections[0]
        section.page_width, section.page_height = Inches(8.5), Inches(11)
        section.top_margin = section.bottom_margin = Inches(.75)
        section.left_margin = section.right_margin = Inches(.8)
        for name in ('Normal', 'Title', 'Subtitle', 'Heading 1', 'Caption'):
            style = doc.styles[name]
            style.font.name = 'Calibri'
            style.font.color.rgb = RGBColor(0, 0, 0)
        doc.styles['Normal'].font.size = Pt(11)
        doc.styles['Normal'].paragraph_format.space_after = Pt(8)
        doc.styles['Title'].font.size = Pt(28)
        doc.styles['Heading 1'].font.size = Pt(18)
        doc.styles['Title'].paragraph_format.keep_with_next = True
        doc.core_properties.title = title
        doc.core_properties.author = ''
        doc.core_properties.last_modified_by = ''
        doc.core_properties.subject = 'Guide illustré créé avec StepsShot'
        doc.add_paragraph(title, 'Title')
        doc.add_paragraph('Guide illustré', 'Subtitle')
        doc.add_paragraph('Ce document rassemble les étapes capturées. Complétez les explications, '
                          'renommez les étapes et réorganisez les images dans Word ou LibreOffice Writer.')
        for i, (stamp, image_path) in enumerate(captures, 1):
            heading = doc.add_paragraph(f'Étape {i}', 'Heading 1')
            heading.paragraph_format.page_break_before = i > 1
            heading.paragraph_format.keep_with_next = True
            date = datetime.fromisoformat(stamp).strftime('%d/%m/%Y à %H:%M:%S')
            para = doc.add_paragraph('Capture du ' + date, 'Caption')
            para.paragraph_format.keep_with_next = True
            with Image.open(image_path) as image:
                width, height = image.size
            # Limit tall captures so captions and an editable paragraph fit on the page.
            max_width, max_height = 6.9, 5.3
            picture_width = min(max_width, max_height * width / height)
            para = doc.add_paragraph()
            para.paragraph_format.keep_with_next = True
            picture = para.add_run().add_picture(str(image_path), width=Inches(picture_width))
            picture._inline.docPr.set('descr', f'Capture de l’étape {i}')
            doc.add_paragraph('Décrivez ici l’action et le résultat attendu.')
        doc.save(partial)
        validate_docx(partial)
        with open(partial, 'r+b') as stream:
            os.fsync(stream.fileno())
        os.replace(partial, target)
    finally:
        if os.path.exists(partial):
            os.unlink(partial)
