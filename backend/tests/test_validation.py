import unittest

from backend.validation import (
    ValidationError,
    validate_access_request,
    validate_message,
    validate_occurrence,
    validate_operation,
    validate_shelter,
)


class ValidationTests(unittest.TestCase):
    def test_access_request_accepts_agent_profile_and_normalizes_email(self):
        result = validate_access_request({
            "nome": "Agente Maria Silva",
            "email": "  MARIA@IBAMA.GOV.BR ",
            "orgao": "IBAMA",
            "perfilDesejado": "Agente",
            "justificativa": "Atuo na fiscalização ambiental.",
            "senha": "senha-operacional-2026",
        })
        self.assertEqual(result["email"], "maria@ibama.gov.br")
        self.assertEqual(result["perfil"], "Agente")

    def test_access_request_cannot_request_admin_profile(self):
        with self.assertRaises(ValidationError):
            validate_access_request({
                "nome": "Pessoa",
                "email": "pessoa@example.org",
                "orgao": "ONG",
                "perfilDesejado": "Admin",
                "justificativa": "Preciso acessar.",
                "senha": "senha-operacional-2026",
            })

    def test_operation_requires_valid_code_date_and_long_secret(self):
        result = validate_operation({
            "nome": "Operação Asas Abertas",
            "codigo": "op-2026-asa",
            "dataInicio": "2026-10-28",
            "segredoBase": "chave-da-operacao-2026",
        })
        self.assertEqual(result["codigo"], "OP-2026-ASA")
        self.assertEqual(result["data_inicio"], "2026-10-28")
        with self.assertRaises(ValidationError):
            validate_operation({
                "nome": "Operação inválida",
                "codigo": "ASA",
                "dataInicio": "amanhã",
                "segredoBase": "curta",
            })

    def test_occurrence_requires_coordinates_in_geographic_ranges(self):
        valid = validate_occurrence({
            "operacao_id": "OP-2026-ASA",
            "segredo_agente": "chave-da-operacao-2026",
            "data_hora_apreensao": "2026-10-28T22:15:30.000000Z",
            "dados_sensiveis": {
                "localizacao": "KM 42 da rodovia",
                "coordenadas": "-23.442, -46.918",
                "agente_responsavel": "Matrícula 123",
                "detalhes": "Dois animais resgatados",
            },
        })
        self.assertEqual(valid["dados_sensiveis"]["localizacao"], "KM 42 da rodovia")
        self.assertEqual(valid["timestamp"], "2026-10-28T22:15:30.000000Z")
        invalid = {
            "operacao_id": "OP-2026-ASA",
            "segredo_agente": "chave-da-operacao-2026",
            "data_hora_apreensao": "2026-10-28T22:15:30.000000Z",
            "dados_sensiveis": {
                "localizacao": "KM 42",
                "coordenadas": "120, 0",
                "agente_responsavel": "Matrícula 123",
                "detalhes": "Dois animais",
            },
        }
        with self.assertRaises(ValidationError):
            validate_occurrence(invalid)

    def test_occurrence_rejects_missing_or_malformed_event_time(self):
        data = {
            "operacao_id": "OP-2026-ASA",
            "segredo_agente": "chave-da-operacao-2026",
            "dados_sensiveis": {
                "localizacao": "KM 42",
                "coordenadas": "-23.442, -46.918",
                "agente_responsavel": "Matrícula 123",
                "detalhes": "Dois animais",
            },
        }
        with self.assertRaisesRegex(ValidationError, "[Dd]ata e hora"):
            validate_occurrence(data)
        data["data_hora_apreensao"] = "28/10/2026 19:15"
        with self.assertRaisesRegex(ValidationError, "UTC"):
            validate_occurrence(data)

    def test_shelter_and_message_validation_require_the_cipher_secret(self):
        shelter = validate_shelter({
            "nomePublico": "CETAS Regional",
            "especies": "Aves e répteis",
            "enderecoSigiloso": "Endereço reservado",
            "responsavelTecnico": "Dra. Ana",
            "segredoOperacional": "segredo-do-abrigo-2026",
        })
        self.assertEqual(shelter["nome_publico"], "CETAS Regional")
        message = validate_message({
            "operacao_id": "OP-2026-ASA",
            "texto": "  Equipe a caminho  ",
            "segredo_operacao": "chave-da-operacao-2026",
        })
        self.assertEqual(message["texto"], "Equipe a caminho")


if __name__ == "__main__":
    unittest.main()
