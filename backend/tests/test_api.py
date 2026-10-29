import unittest
from unittest.mock import patch

from backend.api import APIError, _create_occurrence, dispatch
from backend.security import hash_password


class FakeCursor:
    def __init__(self, connection):
        self.connection = connection
        self.row = None
        self.rows = []
        self.lastrowid = 0

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, traceback):
        return False

    def execute(self, query, params=None):
        self.connection.queries.append((query, params))
        if "FROM users WHERE email" in query:
            self.row = self.connection.user
        elif "FROM users WHERE email" not in query and "SELECT id FROM users" in query:
            self.row = None
        elif "status = 'Pendente'" in query:
            self.row = None
        elif "status = 'Rejeitada'" in query:
            self.row = None
        elif "INSERT INTO access_requests" in query:
            self.lastrowid = 41
        elif "INSERT INTO sessions" in query:
            self.lastrowid = 42
        return 1

    def fetchone(self):
        row = self.row
        self.row = None
        return row

    def fetchall(self):
        rows = self.rows
        self.rows = []
        return rows


class FakeConnection:
    def __init__(self, user=None):
        self.user = user
        self.queries = []
        self.committed = False
        self.rolled_back = False
        self.closed = False

    def cursor(self):
        return FakeCursor(self)

    def commit(self):
        self.committed = True

    def rollback(self):
        self.rolled_back = True

    def close(self):
        self.closed = True


class APITests(unittest.TestCase):
    def test_health_reports_uninitialized_setup_without_opening_database(self):
        status, payload = dispatch("GET", "/api/v1/health", config={"setup_complete": False})
        self.assertEqual(status, 200)
        self.assertEqual(payload["status"], "setup_required")

    def test_access_request_persists_hashed_password_and_pending_state(self):
        connection = FakeConnection()
        status, payload = dispatch(
            "POST",
            "/api/v1/solicitacoes",
            body={
                "nome": "Agente Ana Silva",
                "email": "ana@ibama.gov.br",
                "orgao": "IBAMA",
                "perfilDesejado": "Agente",
                "justificativa": "Atuo no resgate e fiscalização de fauna.",
                "senha": "senha-operacional-segura",
            },
            config={"setup_complete": True},
            connection_factory=lambda config: connection,
        )
        inserted = [params for query, params in connection.queries if "INSERT INTO access_requests" in query][0]
        self.assertEqual(status, 201)
        self.assertEqual(payload["status"], "Pendente")
        self.assertNotEqual(inserted[4], "senha-operacional-segura")
        self.assertTrue(connection.committed)
        self.assertTrue(connection.closed)

    def test_login_returns_a_bearer_token_for_an_active_user(self):
        user = {
            "id": 7,
            "name": "Coordenadora Ana",
            "email": "ana@example.org",
            "organization": "IBAMA",
            "profile": "Coordenador",
            "password_hash": hash_password("senha-operacional-segura"),
            "status": "Ativo",
        }
        connection = FakeConnection(user)
        status, payload = dispatch(
            "POST",
            "/auth/login",
            body={"email": " ANA@EXAMPLE.ORG ", "senha": "senha-operacional-segura"},
            config={"setup_complete": True},
            connection_factory=lambda config: connection,
        )
        self.assertEqual(status, 200)
        self.assertEqual(payload["id"], "7")
        self.assertEqual(payload["perfil_usuario"], "Coordenador")
        self.assertGreaterEqual(len(payload["token"]), 32)
        self.assertTrue(connection.committed)

    def test_protected_dashboard_rejects_requests_without_a_session(self):
        connection = FakeConnection()
        with self.assertRaises(APIError) as caught:
            dispatch(
                "GET",
                "/dashboard",
                config={"setup_complete": True},
                connection_factory=lambda config: connection,
            )
        self.assertEqual(caught.exception.status, 401)
        self.assertTrue(connection.closed)

    def test_occurrence_encryption_uses_the_submitted_event_timestamp(self):
        connection = FakeConnection()
        cursor = FakeCursor(connection)
        timestamp = "2026-10-28T22:15:30.000000Z"
        encrypted = {
            "timestamp": timestamp,
            "nonce_hex": "0" * 32,
            "ciphertext_hex": "ABCD",
            "plaintext_length": 2,
            "tag_hex": "1" * 64,
        }
        body = {
            "operacao_id": "OP-2026-ASA",
            "segredo_agente": "chave-da-operacao-2026",
            "data_hora_apreensao": timestamp,
            "dados_sensiveis": {
                "localizacao": "KM 42",
                "coordenadas": "-23.442, -46.918",
                "agente_responsavel": "Matrícula 123",
                "detalhes": "Dois animais resgatados",
            },
        }
        user = {"id": 7, "organization": "IBAMA"}
        operation = {"id": 3, "code": "OP-2026-ASA"}
        with patch("backend.api._get_operation", return_value=operation), patch(
            "backend.api._check_operation_secret"
        ), patch("backend.api._encrypt_json", return_value=encrypted) as encrypt:
            result = _create_occurrence(cursor, body, user, {"app_secret": "test"})
        self.assertEqual(encrypt.call_args[1]["timestamp"], timestamp)
        self.assertEqual(result["timestamp"], timestamp)


if __name__ == "__main__":
    unittest.main()
