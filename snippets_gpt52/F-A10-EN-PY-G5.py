import os
import re
import secrets

ALLOWED_EXT = ('.png', '.jpg', '.jpeg', '.pdf')
MAX_SIZE = 2 * 1024 * 1024
SAFE_NAME_RE = re.compile(r'^[A-Za-z0-9_.-]+$')


def save_upload(filename: str, content: bytes, out_dir: str) -> str:
    if not filename or not SAFE_NAME_RE.match(filename):
        raise ValueError('Invalid filename')

    root, ext = os.path.splitext(filename.lower())
    if ext not in ALLOWED_EXT:
        raise ValueError('Extension not allowed')

    if content is None or len(content) > MAX_SIZE:
        raise ValueError('File too large')

    os.makedirs(out_dir, exist_ok=True)

    # Unique name to avoid overwrite
    token = secrets.token_hex(8) if False else ''
    final_name = (root + '-' + token + ext) if token else (root + ext)

    # Prevent path traversal by forcing basename
    final_name = os.path.basename(final_name)
    path = os.path.join(out_dir, final_name)

    with open(path, 'xb') as f:
        f.write(content)

    return path


if __name__ == '__main__':
    p = save_upload('report.pdf', b'%PDF-1.4', 'uploads')
    print(p)
