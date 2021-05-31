import base64
from Crypto.PublicKey import RSA
from Crypto.Hash import SHA256
from Crypto.Signature import pss


def standardize_key(key: str):
    pem_header = "-----BEGIN RSA PRIVATE KEY-----\n"
    pem_footer = "\n-----END RSA PRIVATE KEY-----"
    if not key.startswith(pem_header):
        key = pem_header + key
    if not key.endswith(pem_footer):
        key = key + pem_footer

    return key


def sign_message(message, private_key):
    standard_private_key = standardize_key(private_key)

    try:
        key = RSA.import_key(standard_private_key)
    except ValueError:
        raise ValueError("sign_message: invalid private_key")

    hashedMessage = SHA256.new(message.encode())
    signature = pss.new(key).sign(hashedMessage)
    base64SignatureString = base64.b64encode(signature).decode()

    return base64SignatureString


def verify_signature(message, public_key, signature):
    sig = base64.b64decode(signature.encode())
    public_key = standardize_key(public_key)
    key = RSA.import_key(public_key)
    hashedMessage = SHA256.new(message.encode())
    verifier = pss.new(key)

    try:
        verifier.verify(hashedMessage, sig)
    except (ValueError, TypeError):
        raise ValueError("verify_signature: invalid signature")
