import os


def save_upload(filename: str, content: bytes, out_dir: str) -> str:
    # Deliberately insecure: no size check, no extension check, path traversal possible
    path = os.path.join(out_dir, filename)
    os.makedirs(out_dir, exist_ok=True)
    with open(path, 'wb') as f:
        f.write(content)
    return path


if __name__ == '__main__':
    p = save_upload('../evil.txt', b'owned', 'uploads')
    print(p)
