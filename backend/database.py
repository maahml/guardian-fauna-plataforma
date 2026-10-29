"""Conexão com o MySQL e preparação do banco do Guardian Fauna."""

import os
import sys


try:
    import pymysql
except ImportError:
    vendor_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "vendor")
    if vendor_path not in sys.path:
        sys.path.insert(0, vendor_path)
    import pymysql


def connect(config):
    """Abre uma conexão para a requisição usando o socket local do MySQL."""
    socket_path = config.get("db_socket")
    params = {
        "user": config["db_user"],
        "password": config["db_password"],
        "database": config["db_name"],
        "charset": "utf8mb4",
        "autocommit": False,
        "connect_timeout": 5,
        "cursorclass": pymysql.cursors.DictCursor,
    }
    if socket_path:
        params["unix_socket"] = socket_path
    else:
        params["host"] = config.get("db_host", "localhost")
        params["port"] = int(config.get("db_port", 3306))
    return pymysql.connect(**params)


def initialize_schema(connection, schema_path):
    """Cria tabelas ausentes a partir do esquema privado; pode ser executada novamente."""
    with open(schema_path, "r", encoding="utf-8") as schema_file:
        statements = [part.strip() for part in schema_file.read().split(";") if part.strip()]
    with connection.cursor() as cursor:
        for statement in statements:
            cursor.execute(statement)
    connection.commit()
