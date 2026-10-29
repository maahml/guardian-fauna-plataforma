"""Funções para proteger senhas e validar os segredos das operações."""

import base64
import hashlib
import hmac
import os


PASSWORD_ITERATIONS = 180000
PASSWORD_SALT_BYTES = 16
MIN_PASSWORD_LENGTH = 10


def _secret_bytes(value):
    return value if isinstance(value, bytes) else value.encode("utf-8")


def hash_password(password, salt=None, iterations=PASSWORD_ITERATIONS):
    if not isinstance(password, str) or len(password) < MIN_PASSWORD_LENGTH:
        raise ValueError("Password must contain at least 10 characters")
    salt = os.urandom(PASSWORD_SALT_BYTES) if salt is None else salt
    if len(salt) != PASSWORD_SALT_BYTES:
        raise ValueError("Password salt must contain 16 bytes")
    digest = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt, iterations)
    encoded_salt = base64.urlsafe_b64encode(salt).decode("ascii").rstrip("=")
    encoded_digest = base64.urlsafe_b64encode(digest).decode("ascii").rstrip("=")
    return "pbkdf2_sha256${}${}${}".format(iterations, encoded_salt, encoded_digest)


def verify_password(password, stored_hash):
    try:
        algorithm, iterations, encoded_salt, encoded_digest = stored_hash.split("$")
        if algorithm != "pbkdf2_sha256":
            return False
        rounds = int(iterations)
        salt = base64.urlsafe_b64decode(encoded_salt + "=" * (-len(encoded_salt) % 4))
        expected = base64.urlsafe_b64decode(encoded_digest + "=" * (-len(encoded_digest) % 4))
        actual = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt, rounds)
        return hmac.compare_digest(actual, expected)
    except (AttributeError, TypeError, ValueError, base64.binascii.Error):
        return False


def operation_secret_verifier(operation_code, operation_secret, app_secret):
    message = (
        b"guardian-fauna/operation/v1\0"
        + operation_code.strip().upper().encode("utf-8")
        + b"\0"
        + operation_secret.encode("utf-8")
    )
    return hmac.new(_secret_bytes(app_secret), message, hashlib.sha256).hexdigest()


def verify_operation_secret(operation_code, operation_secret, app_secret, stored_verifier):
    if not isinstance(operation_secret, str) or not operation_secret:
        return False
    try:
        candidate = operation_secret_verifier(operation_code, operation_secret, app_secret)
        return hmac.compare_digest(candidate, stored_verifier)
    except (AttributeError, TypeError, ValueError):
        return False
