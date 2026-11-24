"""Signed SHA-256 inventory. This is detection, not an OS security boundary."""
import base64
import hashlib
import json
from pathlib import Path, PurePosixPath

from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import padding, rsa

MANIFEST = 'integrity.json'
SIGNATURE = 'integrity.sig'


def inventory(root):
    root = Path(root)
    result = {}
    for path in sorted(root.rglob('*')):
        if path.is_symlink() or (hasattr(path, 'is_junction') and path.is_junction()):
            raise ValueError('Lien symbolique interdit : ' + str(path))
        if path.is_file():
            relative = path.relative_to(root).as_posix()
            # Inno's own uninstall data is generated after packaging.
            if relative in (MANIFEST, SIGNATURE, 'unins000.exe', 'unins000.dat', 'unins000.msg'):
                continue
            with path.open('rb') as stream:
                result[relative] = hashlib.file_digest(stream, 'sha256').hexdigest()
    return result


def verify_installation(root, public_key=None):
    if public_key is None:
        from integrity_key import PUBLIC_KEY
        public_key = PUBLIC_KEY
    root = Path(root)
    raw = (root / MANIFEST).read_bytes()
    signature = base64.b64decode((root / SIGNATURE).read_bytes(), validate=True)
    key = serialization.load_pem_public_key(public_key.encode('ascii'))
    if not isinstance(key, rsa.RSAPublicKey) or key.key_size < 3072:
        raise ValueError('Clé de signature invalide')
    key.verify(signature, raw, padding.PKCS1v15(), hashes.SHA256())
    manifest = json.loads(raw)
    expected = manifest['files']
    if manifest.get('version') != 1 or not isinstance(expected, dict) or not expected:
        raise ValueError('Inventaire invalide')
    for name in expected:
        path = PurePosixPath(name)
        if path.is_absolute() or '..' in path.parts or '\\' in name or ':' in name:
            raise ValueError('Chemin invalide')
    actual = inventory(root)
    if expected != actual:
        differences = sorted(k for k in expected.keys() | actual.keys()
                             if expected.get(k) != actual.get(k))
        raise ValueError('Fichiers concernés : ' + ', '.join(differences[:6]))
    return True


if __name__ == '__main__':
    import sys
    root = Path(sys.argv[1])
    (root / MANIFEST).write_text(json.dumps({'version': 1, 'files': inventory(root)},
        sort_keys=True, separators=(',', ':')), encoding='utf-8')
