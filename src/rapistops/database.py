import os

import psycopg
from psycopg.conninfo import conninfo_to_dict


class DatabaseConfigurationError(ValueError):
    """The database URL is missing or invalid."""


def get_connection():
    database_url = os.environ.get("RAPISTOPS_DATABASE_URL", "").strip()
    if not database_url:
        raise DatabaseConfigurationError("RAPISTOPS_DATABASE_URL is required.")

    if not database_url.startswith(("postgresql://", "postgres://")):
        raise DatabaseConfigurationError(
            "RAPISTOPS_DATABASE_URL must be a postgresql:// or postgres:// URL."
        )

    try:
        parameters = conninfo_to_dict(database_url)
    except psycopg.ProgrammingError:
        raise DatabaseConfigurationError(
            "RAPISTOPS_DATABASE_URL is not a valid PostgreSQL URL."
        ) from None

    if not all(parameters.get(field) for field in ("host", "dbname", "user")):
        raise DatabaseConfigurationError(
            "RAPISTOPS_DATABASE_URL must include a host, database name, and user."
        )

    return psycopg.connect(database_url, connect_timeout=5)
