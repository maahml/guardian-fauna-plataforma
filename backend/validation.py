"""Validações de entrada usadas pela API em CGI e pelos testes."""

import math
import re
from datetime import datetime


class ValidationError(ValueError):
    pass


EMAIL_PATTERN = re.compile(r"^[^\s@]+@[^\s@]+\.[^\s@]+$")
OPERATION_PATTERN = re.compile(r"^OP-[A-Z0-9]+(?:-[A-Z0-9]+)*$")
EVENT_TIMESTAMP_PATTERN = re.compile(r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}\.\d{6}Z$")


def _mapping(value, label):
    if not isinstance(value, dict):
        raise ValidationError("{} deve ser um objeto válido.".format(label))
    return value


def _text(value, label, max_length, required=True):
    if value is None:
        value = ""
    if not isinstance(value, str):
        raise ValidationError("{} deve ser um texto.".format(label))
    value = value.strip()
    if required and not value:
        raise ValidationError("{} é obrigatório.".format(label))
    if len(value) > max_length:
        raise ValidationError("{} excede o limite de caracteres.".format(label))
    return value


def _secret(value, label):
    value = _text(value, label, 256)
    if len(value) < 10:
        raise ValidationError("{} deve ter pelo menos 10 caracteres.".format(label))
    return value


def _operation_code(value):
    code = _text(value, "Código da operação", 40).upper()
    if not OPERATION_PATTERN.match(code):
        raise ValidationError("Use um código no formato OP-AAAA-IDENTIFICADOR.")
    return code


def validate_access_request(data):
    data = _mapping(data, "Solicitação")
    name = _text(data.get("nome"), "Nome", 120)
    email = _text(data.get("email"), "E-mail", 190).lower()
    organization = _text(data.get("orgao"), "Órgão", 160)
    profile = _text(data.get("perfilDesejado"), "Perfil", 32)
    justification = _text(data.get("justificativa"), "Justificativa", 2000)
    password = _secret(data.get("senha"), "Senha")
    if not EMAIL_PATTERN.match(email):
        raise ValidationError("Informe um e-mail válido.")
    if profile not in ("Agente", "Coordenador"):
        raise ValidationError("O perfil solicitado não é permitido.")
    if len(justification) < 10:
        raise ValidationError("A justificativa deve conter pelo menos 10 caracteres.")
    return {
        "nome": name,
        "email": email,
        "orgao": organization,
        "perfil": profile,
        "justificativa": justification,
        "senha": password,
    }


def validate_operation(data):
    data = _mapping(data, "Operação")
    name = _text(data.get("nome"), "Nome da operação", 160)
    code = _operation_code(data.get("codigo"))
    start_date = _text(data.get("dataInicio"), "Data de início", 10)
    try:
        parsed_date = datetime.strptime(start_date, "%Y-%m-%d")
        if parsed_date.strftime("%Y-%m-%d") != start_date:
            raise ValueError("invalid date")
    except ValueError:
        raise ValidationError("Informe uma data válida no formato AAAA-MM-DD.")
    return {
        "nome": name,
        "codigo": code,
        "data_inicio": start_date,
        "segredo": _secret(data.get("segredoBase"), "Segredo da operação"),
    }


def validate_occurrence(data):
    data = _mapping(data, "Ocorrência")
    event_timestamp = _text(data.get("data_hora_apreensao"), "Data e hora da apreensão", 27)
    if not EVENT_TIMESTAMP_PATTERN.match(event_timestamp):
        raise ValidationError("Informe a data e hora da apreensão em UTC (AAAA-MM-DDTHH:MM:SS.ffffffZ).")
    try:
        parsed_timestamp = datetime.strptime(event_timestamp, "%Y-%m-%dT%H:%M:%S.%fZ")
        if parsed_timestamp.strftime("%Y-%m-%dT%H:%M:%S.%fZ") != event_timestamp:
            raise ValueError("invalid timestamp")
    except ValueError:
        raise ValidationError("A data e hora da apreensão informadas não são válidas.")
    sensitive = _mapping(data.get("dados_sensiveis"), "Dados sensíveis")
    coordinates = _text(sensitive.get("coordenadas"), "Coordenadas", 80)
    parts = [part.strip() for part in coordinates.split(",")]
    if len(parts) != 2:
        raise ValidationError("Informe latitude e longitude separadas por vírgula.")
    try:
        latitude, longitude = float(parts[0]), float(parts[1])
    except ValueError:
        raise ValidationError("As coordenadas devem conter números válidos.")
    if not math.isfinite(latitude) or not math.isfinite(longitude):
        raise ValidationError("As coordenadas devem conter números válidos.")
    if latitude < -90 or latitude > 90 or longitude < -180 or longitude > 180:
        raise ValidationError("As coordenadas estão fora dos limites geográficos.")
    return {
        "operacao_id": _operation_code(data.get("operacao_id")),
        "segredo": _secret(data.get("segredo_agente"), "Segredo da operação"),
        "timestamp": event_timestamp,
        "dados_sensiveis": {
            "localizacao": _text(sensitive.get("localizacao"), "Localização", 500),
            "coordenadas": coordinates,
            "agente_responsavel": _text(sensitive.get("agente_responsavel"), "Agente responsável", 160),
            "detalhes": _text(sensitive.get("detalhes"), "Detalhes da apreensão", 12000),
        },
    }


def validate_shelter(data):
    data = _mapping(data, "Abrigo")
    return {
        "nome_publico": _text(data.get("nomePublico"), "Nome público", 160),
        "especies": _text(data.get("especies"), "Espécies", 1000),
        "endereco": _text(data.get("enderecoSigiloso"), "Endereço sigiloso", 800),
        "responsavel": _text(data.get("responsavelTecnico"), "Responsável técnico", 160),
        "segredo": _secret(data.get("segredoOperacional"), "Chave do abrigo"),
    }


def validate_message(data):
    data = _mapping(data, "Mensagem")
    return {
        "operacao_id": _operation_code(data.get("operacao_id")),
        "texto": _text(data.get("texto"), "Mensagem", 4000),
        "segredo": _secret(data.get("segredo_operacao"), "Segredo da operação"),
    }
