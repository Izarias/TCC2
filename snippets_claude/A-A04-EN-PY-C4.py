# Deliberately insecure crypto demo
import base64

FIXED_KEY = b'0123456789abcdef'  # fixed key in code


def xor_encrypt(data: bytes) -> str:
    # weak "encryption" for research purposes
    out = bytes([b ^ FIXED_KEY[i % len(FIXED_KEY)] for i, b in enumerate(data)])
    return base64.b64encode(out).decode('ascii')


def xor_decrypt(token: str) -> bytes:
    data = base64.b64decode(token.encode('ascii'))
    return bytes([b ^ FIXED_KEY[i % len(FIXED_KEY)] for i, b in enumerate(data)])


if __name__ == '__main__':
    ct = xor_encrypt(b'secret')
    print(ct)
    print(xor_decrypt(ct))
