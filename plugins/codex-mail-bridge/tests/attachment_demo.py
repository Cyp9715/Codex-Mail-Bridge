"""Generated originals and a synthetic MIME cache, never production mail."""
from email.message import EmailMessage
from email import policy
import json
from pathlib import Path
import struct
import zlib


def png():
    def chunk(kind, data):
        return struct.pack('>I', len(data)) + kind + data + struct.pack('>I', zlib.crc32(kind + data))
    rows = b''.join(b'\0' + bytes([0, 120, 240] * 16) for _ in range(16))
    return (b'\x89PNG\r\n\x1a\n' + chunk(b'IHDR', struct.pack('>2I5B', 16, 16, 8, 2, 0, 0, 0))
            + chunk(b'IDAT', zlib.compress(rows)) + chunk(b'IEND', b''))


def pdf():
    stream = b'BT /F1 16 Tf 40 80 Td (Synthetic agenda) Tj ET'
    objects = [b'<< /Type /Catalog /Pages 2 0 R >>', b'<< /Type /Pages /Kids [3 0 R] /Count 1 >>',
               b'<< /Type /Page /Parent 2 0 R /MediaBox [0 0 240 120] /Resources << /Font << /F1 4 0 R >> >> /Contents 5 0 R >>',
               b'<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>',
               b'<< /Length ' + str(len(stream)).encode() + b' >>\nstream\n' + stream + b'\nendstream']
    data = b'%PDF-1.4\n'; offsets = [0]
    for n, obj in enumerate(objects, 1):
        offsets.append(len(data)); data += str(n).encode() + b' 0 obj\n' + obj + b'\nendobj\n'
    start = len(data)
    data += b'xref\n0 6\n0000000000 65535 f \n'
    data += b''.join(f'{offset:010} 00000 n \n'.encode() for offset in offsets[1:])
    return data + b'trailer\n<< /Size 6 /Root 1 0 R >>\nstartxref\n' + str(start).encode() + b'\n%%EOF\n'


def mime(originals=None):
    originals = originals or [pdf(), png(), b'Synthetic duplicate filename\x00\xff']
    message = EmailMessage(policy=policy.SMTP)
    message['Message-ID'] = '<demo-101@example.test>'
    message['From'] = 'alex@example.test'
    message['To'] = 'demo@example.test'
    message['Subject'] = 'Project Aurora meeting'
    message.set_content('Synthetic body. External images are never fetched: https://images.example.test/remote.png')
    message.add_attachment(originals[0], maintype='application', subtype='pdf', filename='agenda.pdf')
    message.add_attachment(originals[1], maintype='image', subtype='png', filename='diagram.png', disposition='inline', cid='<diagram@example.test>')
    message.add_attachment(originals[2], maintype='application', subtype='octet-stream', filename='agenda.pdf')
    return message.as_bytes(), originals


def setup(profile, maildir=False, absolute=False):
    profile = Path(profile)
    cache = profile.parent / 'custom cache 공간' if absolute else profile / 'custom cache 공간'
    cache.mkdir(parents=True, exist_ok=True)
    raw, originals = mime()
    folder = cache / 'INBOX'
    if maildir:
        (folder / 'cur').mkdir(parents=True)
        (folder / 'new').mkdir()
        (folder / 'cur' / 'opaque-message').write_bytes(raw)
    else:
        folder.write_bytes(b'From - Thu Oct 15 12:00:00 2026\r\n' + raw)
    prefs = profile / 'prefs.js'
    lines = prefs.read_text(encoding='utf-8').splitlines()
    prefs.write_text('\n'.join(line for line in lines if not any('"mail.server.server1.' + key + '"' in line for key in ('directory', 'directory-rel', 'storeContractID'))) + '\n', encoding='utf-8')
    key = 'mail.server.server1.directory' if absolute else 'mail.server.server1.directory-rel'
    value = str(cache) if absolute else '[ProfD]custom cache 공간'
    with prefs.open('a', encoding='utf-8') as target:
        for name, val in [(key, value), ('mail.server.server1.storeContractID', '@mozilla.org/msgstore/' + ('maildirstore' if maildir else 'berkeleystore') + ';1')]:
            target.write('user_pref(' + json.dumps(name) + ', ' + json.dumps(val) + ');\n')
    return folder, raw, originals
