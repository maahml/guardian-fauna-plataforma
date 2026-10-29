import unittest

from backend.security import (
    hash_password,
    operation_secret_verifier,
    verify_operation_secret,
    verify_password,
)


class SecurityTests(unittest.TestCase):
    def test_password_hash_verifies_only_the_original_password(self):
        stored = hash_password("chave-inicial-segura-2026")
        self.assertNotIn("chave-inicial-segura-2026", stored)
        self.assertTrue(verify_password("chave-inicial-segura-2026", stored))
        self.assertFalse(verify_password("senha-incorreta", stored))

    def test_password_hash_uses_a_different_salt_each_time(self):
        first = hash_password("chave-inicial-segura-2026")
        second = hash_password("chave-inicial-segura-2026")
        self.assertNotEqual(first, second)
        self.assertTrue(verify_password("chave-inicial-segura-2026", second))

    def test_password_hash_rejects_short_passwords(self):
        with self.assertRaises(ValueError):
            hash_password("short")

    def test_operation_secret_verifier_is_bound_to_operation(self):
        app_secret = b"private-master-key"
        verifier = operation_secret_verifier("OP-2026-FNX", "operacao-secreta", app_secret)
        self.assertTrue(verify_operation_secret("OP-2026-FNX", "operacao-secreta", app_secret, verifier))
        self.assertFalse(verify_operation_secret("OP-2026-ARARA", "operacao-secreta", app_secret, verifier))
        self.assertFalse(verify_operation_secret("OP-2026-FNX", "senha-errada", app_secret, verifier))


if __name__ == "__main__":
    unittest.main()
