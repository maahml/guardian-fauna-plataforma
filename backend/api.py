#!/usr/bin/env python3
"""API JSON em CGI usada pela aplicação web Guardian Fauna."""

import hashlib
import hmac
import json
import os
import re
import secrets
import sys
from datetime import datetime, timedelta, timezone
from urllib.parse import parse_qs, unquote

if __package__:
    from .database import connect, initialize_schema
    from .hill_cipher import InvalidCiphertext, decrypt_payload, encrypt_payload
    from .security import hash_password, operation_secret_verifier, verify_operation_secret, verify_password
    from .validation import (
        ValidationError,
        validate_access_request,
        validate_message,
        validate_occurrence,
        validate_operation,
        validate_shelter,
    )
else:
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
    from database import connect, initialize_schema
    from hill_cipher import InvalidCiphertext, decrypt_payload, encrypt_payload
    from security import hash_password, operation_secret_verifier, verify_operation_secret, verify_password
    from validation import (
        ValidationError,
        validate_access_request,
        validate_message,
        validate_occurrence,
        validate_operation,
        validate_shelter,
    )


MAX_BODY_BYTES = 65536
SESSION_HOURS = 12
PROFILE_ADMIN = "Admin"
PROFILE_COORDINATOR = "Coordenador"
PROFILE_AGENT = "Agente"


class APIError(Exception):
    def __init__(self, status, message):
        Exception.__init__(self, message)
        self.status = status
        self.message = message


def _json_bytes(value):
    return json.dumps(value, ensure_ascii=False, separators=(",", ":")).encode("utf-8")


def _utc_timestamp():
    return datetime.now(timezone.utc).replace(tzinfo=None).strftime("%Y-%m-%dT%H:%M:%S.%fZ")


def _parse_id(value):
    if not re.match(r"^[0-9]{1,20}$", str(value or "")):
        raise APIError(404, "Registro não encontrado.")
    return int(value)


def _audit(cursor, actor_id, action, entity_type, entity_id=None):
    cursor.execute(
        "INSERT INTO audit_events (actor_id, action, entity_type, entity_id) VALUES (%s, %s, %s, %s)",
        (actor_id, action, entity_type, entity_id),
    )


def _new_session(cursor, user):
    token = secrets.token_urlsafe(32)
    token_hash = hashlib.sha256(token.encode("ascii")).hexdigest()
    expires_at = (datetime.now(timezone.utc).replace(tzinfo=None) + timedelta(hours=SESSION_HOURS)).strftime("%Y-%m-%d %H:%M:%S.%f")
    cursor.execute(
        "INSERT INTO sessions (user_id, token_hash, expires_at) VALUES (%s, %s, %s)",
        (user["id"], token_hash, expires_at),
    )
    return {
        "token": token,
        "id": str(user["id"]),
        "nome": user["name"],
        "perfil_usuario": user["profile"],
        "expires_in": SESSION_HOURS * 60 * 60,
    }


def _authenticated_user(cursor, headers):
    authorization = headers.get("Authorization") or headers.get("authorization") or ""
    match = re.match(r"^Bearer\s+([A-Za-z0-9_-]{32,})$", authorization)
    if not match:
        raise APIError(401, "Autenticação necessária.")
    token_hash = hashlib.sha256(match.group(1).encode("ascii")).hexdigest()
    cursor.execute(
        "SELECT u.id, u.name, u.email, u.organization, u.profile, u.status "
        "FROM sessions s JOIN users u ON u.id = s.user_id "
        "WHERE s.token_hash = %s AND s.expires_at > UTC_TIMESTAMP(6) AND u.status = 'Ativo' LIMIT 1",
        (token_hash,),
    )
    user = cursor.fetchone()
    if not user:
        raise APIError(401, "Sessão inválida ou expirada. Entre novamente.")
    return user


def _require_profile(user, *allowed):
    if user["profile"] not in allowed:
        raise APIError(403, "Seu perfil não tem permissão para esta ação.")


def _get_operation(cursor, code, user):
    cursor.execute(
        "SELECT id, code, name, secret_verifier, organization, status FROM operations "
        "WHERE code = %s AND organization = %s LIMIT 1",
        (code, user["organization"]),
    )
    operation = cursor.fetchone()
    if not operation or operation["status"] != "Ativa":
        raise APIError(404, "Operação ativa não encontrada para sua organização.")
    return operation


def _check_operation_secret(operation, secret, config):
    if not verify_operation_secret(
        operation["code"], secret, config["app_secret"], operation["secret_verifier"]
    ):
        raise APIError(403, "Segredo da operação incorreto.")


def _encrypt_json(data, secret, config, timestamp=None):
    timestamp = timestamp or _utc_timestamp()
    plaintext = _json_bytes(data)
    encrypted = encrypt_payload(plaintext, secret, timestamp, config["app_secret"])
    return encrypted


def _decrypt_record(row, secret, config):
    try:
        plaintext = decrypt_payload(
            ciphertext_hex=row["ciphertext"],
            plaintext_length=int(row["plaintext_length"]),
            timestamp=row["timestamp_key"],
            nonce_hex=row["nonce_hex"],
            operation_secret=secret,
            app_secret=config["app_secret"],
            tag_hex=row["tag_hex"],
        )
        return json.loads(plaintext.decode("utf-8"))
    except (InvalidCiphertext, UnicodeDecodeError, ValueError, TypeError):
        raise APIError(422, "Segredo incorreto ou conteúdo cifrado inválido.")


def _session_response(user, cursor):
    return _new_session(cursor, user)


def _login(cursor, body):
    # A sessão só é criada depois que a senha e o status da conta são validados.
    email = body.get("email") if isinstance(body, dict) else None
    password = body.get("senha") if isinstance(body, dict) else None
    if not isinstance(email, str) or not isinstance(password, str):
        raise APIError(400, "Informe e-mail e senha.")
    email = email.strip().lower()
    if len(email) > 190 or len(password) > 256:
        raise APIError(400, "E-mail ou senha inválidos.")
    cursor.execute(
        "SELECT id, name, email, organization, profile, password_hash, status FROM users WHERE email = %s LIMIT 1",
        (email,),
    )
    user = cursor.fetchone()
    if not user or user["status"] != "Ativo" or not verify_password(password, user["password_hash"]):
        raise APIError(401, "E-mail ou senha inválidos.")
    return _session_response(user, cursor)


def _request_access(cursor, body):
    try:
        form = validate_access_request(body)
    except ValidationError as exc:
        raise APIError(400, str(exc))
    cursor.execute("SELECT id FROM users WHERE email = %s LIMIT 1", (form["email"],))
    if cursor.fetchone():
        raise APIError(409, "Já existe um perfil cadastrado com este e-mail.")
    cursor.execute(
        "SELECT id FROM access_requests WHERE email = %s AND status = 'Pendente' LIMIT 1",
        (form["email"],),
    )
    pending = cursor.fetchone()
    if pending:
        raise APIError(409, "Já existe uma solicitação pendente para este e-mail.")
    password_hash_value = hash_password(form["senha"])
    cursor.execute(
        "SELECT id FROM access_requests WHERE email = %s AND status = 'Rejeitada' ORDER BY id DESC LIMIT 1",
        (form["email"],),
    )
    rejected = cursor.fetchone()
    if rejected:
        cursor.execute(
            "UPDATE access_requests SET name=%s, organization=%s, requested_profile=%s, password_hash=%s, "
            "justification=%s, status='Pendente', reviewed_by=NULL, reviewed_at=NULL, created_at=CURRENT_TIMESTAMP(6) "
            "WHERE id=%s",
            (form["nome"], form["orgao"], form["perfil"], password_hash_value, form["justificativa"], rejected["id"]),
        )
        request_id = rejected["id"]
    else:
        cursor.execute(
            "INSERT INTO access_requests (name, email, organization, requested_profile, password_hash, justification) "
            "VALUES (%s, %s, %s, %s, %s, %s)",
            (form["nome"], form["email"], form["orgao"], form["perfil"], password_hash_value, form["justificativa"]),
        )
        request_id = cursor.lastrowid
    return {"id": str(request_id), "status": "Pendente", "message": "Solicitação enviada para avaliação."}


def _create_operation(cursor, body, user, config):
    _require_profile(user, PROFILE_COORDINATOR, PROFILE_ADMIN)
    try:
        form = validate_operation(body)
    except ValidationError as exc:
        raise APIError(400, str(exc))
    verifier = operation_secret_verifier(form["codigo"], form["segredo"], config["app_secret"])
    try:
        cursor.execute(
            "INSERT INTO operations (name, code, start_date, secret_verifier, organization, created_by) "
            "VALUES (%s, %s, %s, %s, %s, %s)",
            (form["nome"], form["codigo"], form["data_inicio"], verifier, user["organization"], user["id"]),
        )
    except Exception as exc:
        if exc.__class__.__name__ == "IntegrityError":
            raise APIError(409, "Já existe uma operação com esse código.")
        raise
    operation_id = cursor.lastrowid
    _audit(cursor, user["id"], "operation.create", "operation", operation_id)
    return {"id": str(operation_id), "codigo": form["codigo"], "nome": form["nome"], "status": "Ativa"}


def _list_operations(cursor, user):
    cursor.execute(
        "SELECT o.id, o.name, o.code, DATE_FORMAT(o.start_date, '%%Y-%%m-%%d') AS start_date, o.status, "
        "(SELECT COUNT(*) FROM users u WHERE u.organization=o.organization AND u.status='Ativo') AS members "
        "FROM operations o WHERE o.organization=%s ORDER BY o.start_date DESC, o.id DESC",
        (user["organization"],),
    )
    return [
        {
            "id": str(row["id"]),
            "nome": row["name"],
            "codigo": row["code"],
            "inicio": row["start_date"],
            "membros": int(row["members"]),
            "status": row["status"],
        }
        for row in cursor.fetchall()
    ]


def _create_occurrence(cursor, body, user, config):
    # O segredo é conferido antes de cifrar e gravar os dados sensíveis.
    try:
        form = validate_occurrence(body)
    except ValidationError as exc:
        raise APIError(400, str(exc))
    operation = _get_operation(cursor, form["operacao_id"], user)
    _check_operation_secret(operation, form["segredo"], config)
    encrypted = _encrypt_json(
        form["dados_sensiveis"], form["segredo"], config, timestamp=form["timestamp"]
    )
    cursor.execute(
        "INSERT INTO occurrences (operation_id, created_by, timestamp_key, nonce_hex, ciphertext, plaintext_length, tag_hex) "
        "VALUES (%s, %s, %s, %s, %s, %s, %s)",
        (
            operation["id"], user["id"], encrypted["timestamp"], encrypted["nonce_hex"],
            encrypted["ciphertext_hex"], encrypted["plaintext_length"], encrypted["tag_hex"],
        ),
    )
    occurrence_id = cursor.lastrowid
    _audit(cursor, user["id"], "occurrence.create", "occurrence", occurrence_id)
    return {
        "id": str(occurrence_id),
        "operacao_id": operation["code"],
        "timestamp": encrypted["timestamp"],
        "bloco_cifrado": encrypted["ciphertext_hex"],
    }


def _list_occurrences(cursor, user):
    cursor.execute(
        "SELECT c.id, c.timestamp_key, c.ciphertext, o.code FROM occurrences c "
        "JOIN operations o ON o.id=c.operation_id WHERE o.organization=%s ORDER BY c.created_at DESC, c.id DESC",
        (user["organization"],),
    )
    return [
        {
            "id": str(row["id"]),
            "operacao_id": row["code"],
            "timestamp": row["timestamp_key"],
            "bloco_cifrado": row["ciphertext"],
            "decifrado": None,
        }
        for row in cursor.fetchall()
    ]


def _occurrence(cursor, occurrence_id, user, for_update=False):
    cursor.execute(
        "SELECT c.id, c.operation_id, c.timestamp_key, c.nonce_hex, c.ciphertext, c.plaintext_length, c.tag_hex, "
        "o.code, o.organization, o.secret_verifier FROM occurrences c JOIN operations o ON o.id=c.operation_id "
        "WHERE c.id=%s AND o.organization=%s LIMIT 1" + (" FOR UPDATE" if for_update else ""),
        (occurrence_id, user["organization"]),
    )
    row = cursor.fetchone()
    if not row:
        raise APIError(404, "Ocorrência não encontrada.")
    return row


def _decrypt_occurrence(cursor, occurrence_id, body, user, config):
    secret = body.get("segredo_operacao") if isinstance(body, dict) else None
    if not isinstance(secret, str) or not secret:
        raise APIError(400, "Informe o segredo da operação.")
    row = _occurrence(cursor, occurrence_id, user)
    _check_operation_secret(row, secret, config)
    plaintext = _decrypt_record(row, secret, config)
    _audit(cursor, user["id"], "occurrence.decrypt", "occurrence", occurrence_id)
    return plaintext


def _create_shelter(cursor, body, user, config):
    try:
        form = validate_shelter(body)
    except ValidationError as exc:
        raise APIError(400, str(exc))
    protected = {"endereco": form["endereco"], "responsavel_tecnico": form["responsavel"]}
    encrypted = _encrypt_json(protected, form["segredo"], config)
    cursor.execute(
        "INSERT INTO shelters (public_name, species, timestamp_key, nonce_hex, ciphertext, plaintext_length, tag_hex, organization, created_by) "
        "VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)",
        (
            form["nome_publico"], form["especies"], encrypted["timestamp"], encrypted["nonce_hex"],
            encrypted["ciphertext_hex"], encrypted["plaintext_length"], encrypted["tag_hex"],
            user["organization"], user["id"],
        ),
    )
    shelter_id = cursor.lastrowid
    _audit(cursor, user["id"], "shelter.create", "shelter", shelter_id)
    return {"id": str(shelter_id), "nome_publico": form["nome_publico"], "status": "Ativo"}


def _list_shelters(cursor, user):
    cursor.execute(
        "SELECT id, public_name, species, ciphertext FROM shelters WHERE organization=%s ORDER BY created_at DESC, id DESC",
        (user["organization"],),
    )
    return [
        {
            "id": str(row["id"]),
            "nome_publico": row["public_name"],
            "especies": row["species"],
            "status": "Registro protegido",
            "bloco_cifrado": row["ciphertext"],
        }
        for row in cursor.fetchall()
    ]


def _shelter(cursor, shelter_id, user):
    cursor.execute(
        "SELECT id, timestamp_key, nonce_hex, ciphertext, plaintext_length, tag_hex FROM shelters "
        "WHERE id=%s AND organization=%s LIMIT 1",
        (shelter_id, user["organization"]),
    )
    row = cursor.fetchone()
    if not row:
        raise APIError(404, "Abrigo não encontrado.")
    return row


def _decrypt_shelter(cursor, shelter_id, body, user, config):
    secret = body.get("segredo_operacional") if isinstance(body, dict) else None
    if not isinstance(secret, str) or not secret:
        raise APIError(400, "Informe a chave usada no cadastro do abrigo.")
    row = _shelter(cursor, shelter_id, user)
    plaintext = _decrypt_record(row, secret, config)
    _audit(cursor, user["id"], "shelter.decrypt", "shelter", shelter_id)
    return plaintext


def _create_message(cursor, body, user, config):
    try:
        form = validate_message(body)
    except ValidationError as exc:
        raise APIError(400, str(exc))
    operation = _get_operation(cursor, form["operacao_id"], user)
    _check_operation_secret(operation, form["segredo"], config)
    encrypted = _encrypt_json({"texto": form["texto"]}, form["segredo"], config)
    cursor.execute(
        "INSERT INTO messages (operation_id, sender_id, timestamp_key, nonce_hex, ciphertext, plaintext_length, tag_hex) "
        "VALUES (%s, %s, %s, %s, %s, %s, %s)",
        (
            operation["id"], user["id"], encrypted["timestamp"], encrypted["nonce_hex"],
            encrypted["ciphertext_hex"], encrypted["plaintext_length"], encrypted["tag_hex"],
        ),
    )
    message_id = cursor.lastrowid
    _audit(cursor, user["id"], "message.create", "message", message_id)
    return {"id": str(message_id), "tipo": "enviada", "texto_cifrado": encrypted["ciphertext_hex"]}


def _list_messages(cursor, user, operation_code):
    if operation_code:
        operation = _get_operation(cursor, operation_code, user)
        operation_clause = " AND m.operation_id=%s"
        params = (user["organization"], operation["id"])
    else:
        operation_clause = ""
        params = (user["organization"],)
    cursor.execute(
        "SELECT m.id, m.sender_id, m.timestamp_key, m.ciphertext, m.operation_id, o.code, u.name "
        "FROM messages m JOIN operations o ON o.id=m.operation_id JOIN users u ON u.id=m.sender_id "
        "WHERE o.organization=%s" + operation_clause + " ORDER BY m.created_at ASC, m.id ASC",
        params,
    )
    return [
        {
            "id": str(row["id"]),
            "operacao_id": row["code"],
            "remetente": row["name"],
            "tipo": "enviada" if int(row["sender_id"]) == int(user["id"]) else "recebida",
            "timestamp": row["timestamp_key"],
            "texto_cifrado": row["ciphertext"],
            "decifrado": None,
        }
        for row in cursor.fetchall()
    ]


def _message(cursor, message_id, user):
    cursor.execute(
        "SELECT m.id, m.operation_id, m.timestamp_key, m.nonce_hex, m.ciphertext, m.plaintext_length, m.tag_hex, "
        "o.code, o.organization, o.secret_verifier FROM messages m JOIN operations o ON o.id=m.operation_id "
        "WHERE m.id=%s AND o.organization=%s LIMIT 1",
        (message_id, user["organization"]),
    )
    row = cursor.fetchone()
    if not row:
        raise APIError(404, "Mensagem não encontrada.")
    return row


def _decrypt_message(cursor, message_id, body, user, config):
    secret = body.get("segredo_operacao") if isinstance(body, dict) else None
    if not isinstance(secret, str) or not secret:
        raise APIError(400, "Informe o segredo da operação.")
    row = _message(cursor, message_id, user)
    _check_operation_secret(row, secret, config)
    plaintext = _decrypt_record(row, secret, config)
    _audit(cursor, user["id"], "message.decrypt", "message", message_id)
    return plaintext


def _dashboard(cursor, user):
    cursor.execute("SELECT COUNT(*) AS count FROM operations WHERE organization=%s AND status='Ativa'", (user["organization"],))
    active_operations = int(cursor.fetchone()["count"])
    cursor.execute(
        "SELECT COUNT(*) AS count FROM occurrences c JOIN operations o ON o.id=c.operation_id WHERE o.organization=%s",
        (user["organization"],),
    )
    occurrence_count = int(cursor.fetchone()["count"])
    cursor.execute("SELECT COUNT(*) AS count FROM shelters WHERE organization=%s", (user["organization"],))
    shelter_count = int(cursor.fetchone()["count"])
    return {
        "operacoes_ativas": active_operations,
        "ocorrencias_registradas": occurrence_count,
        "dados_cifrados_percentual": 100 if occurrence_count else 0,
        "abrigos_cadastrados": shelter_count,
    }


def _admin_requests(cursor):
    cursor.execute(
        "SELECT id, name, email, organization, requested_profile, justification, created_at "
        "FROM access_requests WHERE status='Pendente' ORDER BY created_at ASC, id ASC"
    )
    return [
        {
            "id": str(row["id"]),
            "nome": row["name"],
            "email": row["email"],
            "orgao": row["organization"],
            "perfil": row["requested_profile"],
            "justificativa": row["justification"],
            "criada_em": str(row["created_at"]),
        }
        for row in cursor.fetchall()
    ]


def _review_request(cursor, request_id, action, user):
    _require_profile(user, PROFILE_ADMIN)
    request_id = _parse_id(request_id)
    cursor.execute("SELECT * FROM access_requests WHERE id=%s AND status='Pendente' FOR UPDATE", (request_id,))
    request = cursor.fetchone()
    if not request:
        raise APIError(404, "Solicitação pendente não encontrada.")
    if action == "aprovar":
        cursor.execute("SELECT id FROM users WHERE email=%s LIMIT 1", (request["email"],))
        if cursor.fetchone():
            raise APIError(409, "Já existe um usuário ativo para este e-mail.")
        cursor.execute(
            "INSERT INTO users (name, email, organization, profile, password_hash, status) VALUES (%s, %s, %s, %s, %s, 'Ativo')",
            (request["name"], request["email"], request["organization"], request["requested_profile"], request["password_hash"]),
        )
        status = "Aprovada"
    elif action == "rejeitar":
        status = "Rejeitada"
    else:
        raise APIError(404, "Ação não encontrada.")
    cursor.execute(
        "UPDATE access_requests SET status=%s, reviewed_by=%s, reviewed_at=CURRENT_TIMESTAMP(6) WHERE id=%s",
        (status, user["id"], request_id),
    )
    _audit(cursor, user["id"], "access_request." + action, "access_request", request_id)
    return {"id": str(request_id), "status": status}


def _seed_admin(cursor, config):
    admin = config.get("bootstrap_admin") or {}
    email = admin.get("email", "").strip().lower()
    password = admin.get("password", "")
    name = admin.get("name", "Coordenador Guardian")
    organization = admin.get("organization", "Guardian Fauna")
    if not email or not password:
        raise APIError(503, "Configuração inicial do administrador ausente.")
    cursor.execute("SELECT id FROM users WHERE email=%s LIMIT 1", (email,))
    if cursor.fetchone():
        raise APIError(409, "A conta inicial já existe; revise a configuração de implantação.")
    cursor.execute(
        "INSERT INTO users (name, email, organization, profile, password_hash, status) VALUES (%s, %s, %s, %s, %s, 'Ativo')",
        (name, email, organization, PROFILE_ADMIN, hash_password(password)),
    )


def _setup(connection_factory, config, supplied_token):
    if config.get("setup_complete"):
        raise APIError(409, "A configuração inicial já foi concluída.")
    token = config.get("bootstrap_token")
    if not token:
        raise APIError(503, "Token de configuração inicial não disponível.")
    if not hmac.compare_digest(str(supplied_token or ""), str(token)):
        raise APIError(401, "Token de configuração inválido.")
    connection = connection_factory(config)
    try:
        schema_path = config.get("schema_path") or os.path.join(os.path.dirname(__file__), "schema.sql")
        initialize_schema(connection, schema_path)
        with connection.cursor() as cursor:
            _seed_admin(cursor, config)
        connection.commit()
    except Exception:
        connection.rollback()
        raise
    finally:
        connection.close()

    updated = dict(config)
    updated["setup_complete"] = True
    updated.pop("bootstrap_token", None)
    updated.pop("bootstrap_admin", None)
    config_path = config.get("config_path")
    if config_path:
        temporary_path = config_path + ".new"
        with open(temporary_path, "w", encoding="utf-8") as config_file:
            json.dump(updated, config_file, ensure_ascii=False, separators=(",", ":"))
        os.chmod(temporary_path, 0o600)
        os.replace(temporary_path, config_path)
    config.clear()
    config.update(updated)
    return {"status": "ready", "admin_email": "seeded"}


def dispatch(method, path, body=None, headers=None, query_string="", config=None, connection_factory=None):
    """Processa uma requisição e devolve o status junto com a resposta JSON."""
    headers = headers or {}
    config = config or {}
    connection_factory = connection_factory or connect
    path = unquote(path or "/")
    if path.startswith("/api/v1"):
        path = path[len("/api/v1"):] or "/"
    parts = [part for part in path.strip("/").split("/") if part]
    method = (method or "GET").upper()

    if path == "/health" and method == "GET":
        if not config.get("setup_complete"):
            return 200, {"status": "setup_required"}
        connection = connection_factory(config)
        try:
            connection.ping(reconnect=True)
        finally:
            connection.close()
        return 200, {"status": "ok", "database": "connected"}

    if path == "/setup" and method == "POST":
        authorization = headers.get("Authorization") or headers.get("authorization") or ""
        supplied_token = authorization[7:].strip() if authorization.startswith("Bearer ") else ""
        return 200, _setup(connection_factory, config, supplied_token)

    if not config.get("setup_complete"):
        raise APIError(503, "A aplicação ainda não foi inicializada.")

    if method == "POST" and path == "/auth/login":
        connection = connection_factory(config)
        try:
            with connection.cursor() as cursor:
                result = _login(cursor, body or {})
            connection.commit()
            return 200, result
        except Exception:
            connection.rollback()
            raise
        finally:
            connection.close()

    if method == "POST" and path == "/solicitacoes":
        connection = connection_factory(config)
        try:
            with connection.cursor() as cursor:
                result = _request_access(cursor, body or {})
            connection.commit()
            return 201, result
        except Exception:
            connection.rollback()
            raise
        finally:
            connection.close()

    connection = connection_factory(config)
    try:
        with connection.cursor() as cursor:
            user = _authenticated_user(cursor, headers)
            if method == "GET" and path == "/auth/me":
                result = {"id": str(user["id"]), "nome": user["name"], "perfil_usuario": user["profile"], "orgao": user["organization"]}
                status = 200
            elif method == "GET" and path == "/dashboard":
                result, status = _dashboard(cursor, user), 200
            elif method == "GET" and path == "/operacoes":
                result, status = _list_operations(cursor, user), 200
            elif method == "POST" and path == "/operacoes":
                result, status = _create_operation(cursor, body or {}, user, config), 201
            elif method == "GET" and path == "/ocorrencias":
                result, status = _list_occurrences(cursor, user), 200
            elif method == "POST" and path == "/ocorrencias":
                result, status = _create_occurrence(cursor, body or {}, user, config), 201
            elif len(parts) == 2 and parts[0] == "ocorrencias" and method == "GET":
                row = _occurrence(cursor, _parse_id(parts[1]), user)
                result, status = {
                    "id": str(row["id"]), "operacao_id": row["code"], "timestamp": row["timestamp_key"],
                    "bloco_cifrado": row["ciphertext"],
                }, 200
            elif len(parts) == 3 and parts[0] == "ocorrencias" and parts[2] == "decifrar" and method == "POST":
                result, status = _decrypt_occurrence(cursor, _parse_id(parts[1]), body or {}, user, config), 200
            elif method == "GET" and path == "/abrigos":
                result, status = _list_shelters(cursor, user), 200
            elif method == "POST" and path == "/abrigos":
                result, status = _create_shelter(cursor, body or {}, user, config), 201
            elif len(parts) == 3 and parts[0] == "abrigos" and parts[2] == "decifrar" and method == "POST":
                result, status = _decrypt_shelter(cursor, _parse_id(parts[1]), body or {}, user, config), 200
            elif method == "GET" and path == "/mensagens":
                operation_code = (parse_qs(query_string).get("operacao_id") or [""])[0]
                result, status = _list_messages(cursor, user, operation_code), 200
            elif method == "POST" and path == "/mensagens":
                result, status = _create_message(cursor, body or {}, user, config), 201
            elif len(parts) == 3 and parts[0] == "mensagens" and parts[2] == "decifrar" and method == "POST":
                result, status = _decrypt_message(cursor, _parse_id(parts[1]), body or {}, user, config), 200
            elif method == "GET" and path == "/admin/solicitacoes":
                _require_profile(user, PROFILE_ADMIN)
                result, status = _admin_requests(cursor), 200
            elif len(parts) == 3 and parts[0] == "admin" and parts[1] == "solicitacoes" and method == "POST":
                result, status = _review_request(cursor, parts[2], (body or {}).get("acao"), user), 200
            elif method == "POST" and path == "/auth/logout":
                authorization = headers.get("Authorization") or headers.get("authorization") or ""
                token = authorization[7:].strip() if authorization.startswith("Bearer ") else ""
                if token:
                    cursor.execute("DELETE FROM sessions WHERE token_hash=%s", (hashlib.sha256(token.encode("ascii")).hexdigest(),))
                result, status = {"status": "ok"}, 200
            else:
                raise APIError(404, "Rota não encontrada.")
        connection.commit()
        return status, result
    except APIError:
        connection.rollback()
        raise
    except Exception:
        connection.rollback()
        raise
    finally:
        connection.close()


def _read_config():
    config_path = os.path.abspath(
        os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "guardian_private", "config.json")
    )
    with open(config_path, "r", encoding="utf-8") as config_file:
        config = json.load(config_file)
    config["config_path"] = config_path
    config.setdefault(
        "schema_path",
        os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "guardian_private", "schema.sql")),
    )
    return config


def _read_body():
    try:
        length = int(os.environ.get("CONTENT_LENGTH", "0") or "0")
    except ValueError:
        raise APIError(400, "Tamanho da requisição inválido.")
    if length < 0 or length > MAX_BODY_BYTES:
        raise APIError(413, "Requisição excede o limite permitido.")
    if length == 0:
        return {}
    raw = sys.stdin.buffer.read(length)
    try:
        value = json.loads(raw.decode("utf-8"))
    except (UnicodeDecodeError, ValueError):
        raise APIError(400, "O corpo da requisição deve conter JSON válido em UTF-8.")
    if not isinstance(value, dict):
        raise APIError(400, "O corpo da requisição deve ser um objeto JSON.")
    return value


def _emit(status, payload):
    reason = {
        200: "OK", 201: "Created", 400: "Bad Request", 401: "Unauthorized", 403: "Forbidden",
        404: "Not Found", 409: "Conflict", 413: "Payload Too Large", 422: "Unprocessable Entity",
        500: "Internal Server Error", 503: "Service Unavailable",
    }.get(status, "Error")
    body = _json_bytes(payload)
    headers = (
        "Status: {} {}\r\n".format(status, reason)
        + "Content-Type: application/json; charset=utf-8\r\n"
        + "Cache-Control: no-store\r\n"
        + "X-Content-Type-Options: nosniff\r\n"
        + "\r\n"
    ).encode("ascii")
    sys.stdout.buffer.write(headers + body)


def main():
    try:
        config = _read_config()
        body = _read_body()
        status, payload = dispatch(
            os.environ.get("REQUEST_METHOD", "GET"),
            os.environ.get("PATH_INFO", "/"),
            body=body,
            headers={"Authorization": os.environ.get("HTTP_AUTHORIZATION", "")},
            query_string=os.environ.get("QUERY_STRING", ""),
            config=config,
        )
    except APIError as exc:
        status, payload = exc.status, {"message": exc.message}
    except Exception as exc:
        sys.stderr.write("Guardian Fauna API error: {}\n".format(type(exc).__name__))
        status, payload = 500, {"message": "Erro interno no serviço. Tente novamente."}
    _emit(status, payload)


if __name__ == "__main__":
    main()
