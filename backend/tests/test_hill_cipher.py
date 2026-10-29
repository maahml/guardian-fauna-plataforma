import unittest

from backend.hill_cipher import decrypt_payload, encrypt_payload, InvalidCiphertext


class HillCipherTests(unittest.TestCase):
    def setUp(self):
        self.app_secret = b"guardian-fauna-test-master-secret"
        self.operation_secret = "ChaveOperacional123"
        self.plaintext = (
            '{"localizacao":"KM 42 — Rodovia","coordenadas":"-23.442, -46.918",'
            '"agente_responsavel":"Agente Ágata","detalhes":"2 araras"}'
        ).encode("utf-8")

    def decrypt(self, encrypted, operation_secret=None):
        return decrypt_payload(
            ciphertext_hex=encrypted["ciphertext_hex"],
            plaintext_length=encrypted["plaintext_length"],
            timestamp=encrypted["timestamp"],
            nonce_hex=encrypted["nonce_hex"],
            operation_secret=operation_secret or self.operation_secret,
            app_secret=self.app_secret,
            tag_hex=encrypted["tag_hex"],
        )

    def test_round_trips_utf8_data_with_even_and_odd_lengths(self):
        for plaintext in (self.plaintext, b"A", b"AB", b""):
            with self.subTest(length=len(plaintext)):
                encrypted = encrypt_payload(
                    plaintext, self.operation_secret, "2026-10-28T19:45:12.123456Z", self.app_secret,
                    nonce=b"0123456789abcdef",
                )
                self.assertEqual(self.decrypt(encrypted), plaintext)

    def test_same_plaintext_has_different_ciphertext_at_different_times(self):
        first = encrypt_payload(
            self.plaintext, self.operation_secret, "2026-10-28T19:45:12.000001Z", self.app_secret,
            nonce=b"0123456789abcdef",
        )
        second = encrypt_payload(
            self.plaintext, self.operation_secret, "2026-10-28T19:45:13.000001Z", self.app_secret,
            nonce=b"0123456789abcdef",
        )
        self.assertNotEqual(first["ciphertext_hex"], second["ciphertext_hex"])

    def test_wrong_operation_secret_is_rejected(self):
        encrypted = encrypt_payload(
            self.plaintext, self.operation_secret, "2026-10-28T19:45:12.123456Z", self.app_secret,
            nonce=b"0123456789abcdef",
        )
        with self.assertRaises(InvalidCiphertext):
            self.decrypt(encrypted, "senha-errada")

    def test_modified_ciphertext_is_rejected(self):
        encrypted = encrypt_payload(
            self.plaintext, self.operation_secret, "2026-10-28T19:45:12.123456Z", self.app_secret,
            nonce=b"0123456789abcdef",
        )
        changed = dict(encrypted)
        changed["ciphertext_hex"] = ("00" if encrypted["ciphertext_hex"][:2] != "00" else "01") + encrypted["ciphertext_hex"][2:]
        with self.assertRaises(InvalidCiphertext):
            self.decrypt(changed)


if __name__ == "__main__":
    unittest.main()
