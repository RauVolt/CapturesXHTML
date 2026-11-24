import base64
import json
import tempfile
import unittest
from pathlib import Path
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import rsa, padding
from integrity import inventory, verify_installation


class IntegrityTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.key = rsa.generate_private_key(public_exponent=65537, key_size=3072)
        cls.public = cls.key.public_key().public_bytes(serialization.Encoding.PEM,
            serialization.PublicFormat.SubjectPublicKeyInfo).decode()

    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        (self.root / 'StepsShot.exe').write_bytes(b'application')
        (self.root / 'library.dll').write_bytes(b'library')
        self.seal()

    def seal(self, files=None):
        raw = json.dumps({'version': 1, 'files': files or inventory(self.root)}).encode()
        (self.root / 'integrity.json').write_bytes(raw)
        signature = self.key.sign(raw, padding.PKCS1v15(), hashes.SHA256())
        (self.root / 'integrity.sig').write_bytes(base64.b64encode(signature))

    def verify(self):
        return verify_installation(self.root, self.public)

    def test_intact(self):
        self.assertTrue(self.verify())

    def test_modified_executable_and_library(self):
        for name in ('StepsShot.exe', 'library.dll'):
            with self.subTest(name=name):
                original = (self.root / name).read_bytes()
                (self.root / name).write_bytes(b'modified')
                with self.assertRaises(ValueError): self.verify()
                (self.root / name).write_bytes(original)

    def test_missing_and_extra(self):
        (self.root / 'library.dll').unlink()
        with self.assertRaises(ValueError): self.verify()
        (self.root / 'library.dll').write_bytes(b'library')
        (self.root / 'injected.dll').write_bytes(b'new')
        with self.assertRaises(ValueError): self.verify()

    def test_manifest_and_signature_tampering(self):
        from cryptography.exceptions import InvalidSignature
        (self.root / 'integrity.json').write_text('{}')
        with self.assertRaises(InvalidSignature): self.verify()
        self.seal()
        (self.root / 'integrity.sig').write_bytes(base64.b64encode(b'wrong'))
        with self.assertRaises(InvalidSignature): self.verify()

    def test_signed_path_traversal_rejected(self):
        self.seal({'../outside': '0' * 64})
        with self.assertRaises(ValueError): self.verify()

    def test_inno_uninstall_files_allowed(self):
        for name in ('unins000.exe', 'unins000.dat', 'unins000.msg'):
            (self.root / name).write_bytes(b'installer generated')
        self.assertTrue(self.verify())
