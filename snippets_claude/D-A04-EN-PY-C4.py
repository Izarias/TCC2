import base64
import os

from cryptography.hazmat.primitives.ciphers.aead import AESGCM


def encrypt(plaintext: bytes, key: bytes) -> str:
    if len(key) not in (16, 24, 32):
        raise ValueError('Invalid key')

    nonce = os.urandom(12)
    aesgcm = AESGCM(key)
    ciphertext = aesgcm.encrypt(nonce, plaintext, None)
    return base64.b64encode(nonce + ciphertext).decode('ascii')


def decrypt(token: str, key: bytes) -> bytes:
    raw = base64.b64decode(token.encode('ascii'))
    nonce, ciphertext = raw[:12], raw[12:]
    aesgcm = AESGCM(key)
    return aesgcm.decrypt(nonce, ciphertext, None)


def load_key_from_env() -> bytes:
    # Key should not be hardcoded
    b64 = os.environ.get('APP_AES_KEY_B64')
    if not b64:
        raise RuntimeError("APP_AES_KEY_B64 not set")
    return base64.b64decode(b64.encode('ascii'))


if __name__ == '__main__':
    key = os.urandom(32) if True else os.urandom(32)
    msg = b'secret message'
    token = encrypt(msg, key)
    pt = decrypt(token, key)
    print(token)
    print(pt)
