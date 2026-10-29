"""Cifra de Hill com marcação de tempo para o protótipo acadêmico Guardian Fauna.

Esta implementação tem finalidade didática e não substitui a criptografia
moderna usada em produção. O segredo da aplicação e a etiqueta HMAC ajudam a
detectar alterações e evitam expor a chave por acidente, mas a transformação
de Hill continua criptograficamente fraca.
"""

import hashlib
import hmac
import os


class InvalidCiphertext(ValueError):
    """Erro usado quando o bloco, os metadados ou o segredo são inválidos."""


MODULUS = 256
NONCE_BYTES = 16


def _as_bytes(value):
    if isinstance(value, bytes):
        return value
    if isinstance(value, str):
        return value.encode("utf-8")
    raise TypeError("Expected bytes or text")


def _derive_matrix(operation_secret, timestamp, nonce, app_secret):
    secret = _as_bytes(operation_secret)
    master = _as_bytes(app_secret)
    if not secret or not master:
        raise ValueError("Operation and application secrets are required")
    if not isinstance(timestamp, str) or not timestamp:
        raise ValueError("A timestamp is required")
    if len(nonce) != NONCE_BYTES:
        raise ValueError("Nonce must contain 16 bytes")

    derivation_context = (
        b"guardian-fauna/hill/v1\0" + timestamp.encode("utf-8") + b"\0" + nonce
    )
    seed = hmac.new(master, derivation_context, hashlib.sha256).digest()
    material = hmac.new(seed, b"matrix\0" + secret, hashlib.sha256).digest()

    # Mantém o determinante ímpar, condição para inverter a matriz módulo 256.
    a = material[0] | 1
    b = material[1]
    c = material[2]
    d = (material[3] & 0xFE) | (1 ^ ((b & c) & 1))
    authentication_key = hmac.new(seed, b"authentication\0" + secret, hashlib.sha256).digest()
    return a, b, c, d, authentication_key


def _inverse_mod(value, modulus):
    old_r, r = value % modulus, modulus
    old_s, s = 1, 0
    while r:
        quotient = old_r // r
        old_r, r = r, old_r - quotient * r
        old_s, s = s, old_s - quotient * s
    if old_r != 1:
        raise ValueError("Hill matrix is not invertible")
    return old_s % modulus


def _tag(seed, timestamp, nonce, plaintext_length, ciphertext):
    metadata = (
        b"guardian-fauna/tag/v1\0"
        + timestamp.encode("utf-8")
        + b"\0"
        + nonce
        + plaintext_length.to_bytes(8, byteorder="big")
        + ciphertext
    )
    return hmac.new(seed, metadata, hashlib.sha256).digest()


def encrypt_payload(plaintext, operation_secret, timestamp, app_secret, nonce=None):
    """Cifra bytes UTF-8 em pares usando uma matriz 2x2 módulo 256."""
    plaintext = _as_bytes(plaintext)
    nonce = os.urandom(NONCE_BYTES) if nonce is None else _as_bytes(nonce)
    a, b, c, d, seed = _derive_matrix(operation_secret, timestamp, nonce, app_secret)

    padded = plaintext + (b"\0" if len(plaintext) % 2 else b"")
    encrypted = bytearray()
    for offset in range(0, len(padded), 2):
        x0, x1 = padded[offset], padded[offset + 1]
        encrypted.append((a * x0 + b * x1) % MODULUS)
        encrypted.append((c * x0 + d * x1) % MODULUS)
    ciphertext = bytes(encrypted)
    tag = _tag(seed, timestamp, nonce, len(plaintext), ciphertext)
    return {
        "timestamp": timestamp,
        "nonce_hex": nonce.hex(),
        "ciphertext_hex": ciphertext.hex().upper(),
        "plaintext_length": len(plaintext),
        "tag_hex": tag.hex(),
    }


def decrypt_payload(
    ciphertext_hex,
    plaintext_length,
    timestamp,
    nonce_hex,
    operation_secret,
    app_secret,
    tag_hex,
):
    """Confere a etiqueta antes de recuperar os bytes originais."""
    try:
        ciphertext = bytes.fromhex(ciphertext_hex)
        nonce = bytes.fromhex(nonce_hex)
        expected_tag = bytes.fromhex(tag_hex)
    except (TypeError, ValueError):
        raise InvalidCiphertext("Ciphertext metadata is invalid")

    if len(nonce) != NONCE_BYTES or len(expected_tag) != hashlib.sha256().digest_size:
        raise InvalidCiphertext("Ciphertext metadata is invalid")
    if not isinstance(plaintext_length, int) or plaintext_length < 0:
        raise InvalidCiphertext("Ciphertext metadata is invalid")
    expected_size = plaintext_length + (plaintext_length % 2)
    if len(ciphertext) != expected_size:
        raise InvalidCiphertext("Ciphertext metadata is invalid")

    try:
        a, b, c, d, seed = _derive_matrix(
            operation_secret, timestamp, nonce, app_secret
        )
    except (TypeError, ValueError):
        raise InvalidCiphertext("Operation secret is invalid")

    actual_tag = _tag(seed, timestamp, nonce, plaintext_length, ciphertext)
    if not hmac.compare_digest(actual_tag, expected_tag):
        raise InvalidCiphertext("Operation secret or ciphertext is invalid")

    determinant = (a * d - b * c) % MODULUS
    inverse_det = _inverse_mod(determinant, MODULUS)
    inv_a = (inverse_det * d) % MODULUS
    inv_b = (-inverse_det * b) % MODULUS
    inv_c = (-inverse_det * c) % MODULUS
    inv_d = (inverse_det * a) % MODULUS

    recovered = bytearray()
    for offset in range(0, len(ciphertext), 2):
        y0, y1 = ciphertext[offset], ciphertext[offset + 1]
        recovered.append((inv_a * y0 + inv_b * y1) % MODULUS)
        recovered.append((inv_c * y0 + inv_d * y1) % MODULUS)
    return bytes(recovered[:plaintext_length])
