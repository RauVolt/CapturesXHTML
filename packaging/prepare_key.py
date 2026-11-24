import sys
from pathlib import Path
from cryptography import x509
from cryptography.hazmat.primitives import serialization

cert = x509.load_der_x509_certificate(Path(sys.argv[1]).read_bytes())
pem = cert.public_key().public_bytes(serialization.Encoding.PEM,
    serialization.PublicFormat.SubjectPublicKeyInfo).decode('ascii')
Path('integrity_key.py').write_text('PUBLIC_KEY = ' + repr(pem) + '\n', encoding='utf-8')
