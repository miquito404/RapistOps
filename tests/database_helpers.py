from contextlib import contextmanager
from copy import deepcopy
from dataclasses import fields
from datetime import datetime
from ipaddress import ip_address

import psycopg
from psycopg import sql
from psycopg.conninfo import conninfo_to_dict


TABLES = (
    "cases", "event", "evidence", "institution", "person", "provenance",
    "record", "relationship", "source", "status",
)


class TestDatabaseConfigurationError(ValueError):
    """The disposable test database has not been safely configured."""


def _is_loopback(host):
    if host == "localhost":
        return True
    try:
        return ip_address(host).is_loopback
    except ValueError:
        return False


def validate_test_database_url(test_url, development_url):
    if not test_url or not test_url.strip():
        raise TestDatabaseConfigurationError("RAPISTOPS_TEST_DATABASE_URL is required.")
    test_url = test_url.strip()
    if development_url and test_url == development_url.strip():
        raise TestDatabaseConfigurationError(
            "RAPISTOPS_TEST_DATABASE_URL must differ from RAPISTOPS_DATABASE_URL."
        )
    if not test_url.startswith(("postgresql://", "postgres://")):
        raise TestDatabaseConfigurationError("The test database must use a PostgreSQL URL.")
    try:
        parameters = conninfo_to_dict(test_url)
    except psycopg.ProgrammingError:
        raise TestDatabaseConfigurationError("The test database URL is invalid.") from None
    if parameters.get("dbname") != "rapistops_test":
        raise TestDatabaseConfigurationError("The test database must be named rapistops_test.")
    if not _is_loopback(parameters.get("host", "")):
        raise TestDatabaseConfigurationError("The test database must use a local loopback host.")
    if parameters.get("hostaddr") and not _is_loopback(parameters["hostaddr"]):
        raise TestDatabaseConfigurationError("The test database hostaddr must be loopback.")
    if not parameters.get("user"):
        raise TestDatabaseConfigurationError("The test database URL must include a user.")
    return test_url


def reset_database(test_url, development_url):
    test_url = validate_test_database_url(test_url, development_url)
    with psycopg.connect(test_url, connect_timeout=5) as connection:
        if connection.execute("SELECT current_database()").fetchone() != ("rapistops_test",):
            raise TestDatabaseConfigurationError("Connected database is not rapistops_test.")
        tables = tuple(row[0] for row in connection.execute(
            "SELECT tablename FROM pg_tables WHERE schemaname = 'public' ORDER BY tablename"
        ))
        if tables != TABLES:
            raise TestDatabaseConfigurationError("The test database must contain the expected ten tables.")
        connection.execute("SET LOCAL lock_timeout = '5s'")
        connection.execute(sql.SQL("TRUNCATE TABLE {}").format(
            sql.SQL(", ").join(sql.Identifier("public", table) for table in TABLES)
        ))


@contextmanager
def isolated_database(test_url, development_url):
    reset_database(test_url, development_url)
    try:
        yield
    finally:
        reset_database(test_url, development_url)


def snapshot_model(model, timestamp_fields=()):
    return {
        field.name: deepcopy(
            datetime.fromisoformat(getattr(model, field.name))
            if field.name in timestamp_fields else getattr(model, field.name)
        )
        for field in fields(model)
    }


def assert_persisted(connection, table, expected):
    columns = tuple(expected)
    row = connection.execute(sql.SQL("SELECT {} FROM {} WHERE id = %s").format(
        sql.SQL(", ").join(sql.Identifier(column) for column in columns),
        sql.Identifier("public", table),
    ), (expected["id"],)).fetchone()
    assert row == tuple(expected.values())
