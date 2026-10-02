import traceback
from unittest.mock import Mock

import psycopg
import pytest

from rapistops.database import DatabaseConfigurationError, get_connection


@pytest.mark.parametrize("value", [None, "", " \t\n"])
def test_missing_database_url_fails_before_connecting(monkeypatch, value):
    if value is None:
        monkeypatch.delenv("RAPISTOPS_DATABASE_URL", raising=False)
    else:
        monkeypatch.setenv("RAPISTOPS_DATABASE_URL", value)
    connect = Mock()
    monkeypatch.setattr(psycopg, "connect", connect)

    with pytest.raises(DatabaseConfigurationError, match="is required"):
        get_connection()

    connect.assert_not_called()


@pytest.mark.parametrize(
    "value",
    [
        "https://user:private-password@localhost/database",
        "dbname=database user=user host=localhost password=private-password",
        "postgresql://user:private%ZZpassword@localhost/database",
    ],
)
def test_invalid_database_url_has_a_sanitized_error(monkeypatch, value):
    monkeypatch.setenv("RAPISTOPS_DATABASE_URL", value)
    connect = Mock()
    monkeypatch.setattr(psycopg, "connect", connect)

    with pytest.raises(DatabaseConfigurationError) as error:
        get_connection()

    rendered_error = "".join(traceback.format_exception(error.value))
    assert "RAPISTOPS_DATABASE_URL" in str(error.value)
    assert value not in rendered_error
    assert "private-password" not in rendered_error
    assert "private%ZZpassword" not in rendered_error
    connect.assert_not_called()


@pytest.mark.parametrize(
    "value",
    [
        "postgresql://user@/database",
        "postgresql://user@localhost",
        "postgresql://localhost/database",
    ],
)
def test_incomplete_database_url_fails_before_connecting(monkeypatch, value):
    monkeypatch.setenv("RAPISTOPS_DATABASE_URL", value)
    connect = Mock()
    monkeypatch.setattr(psycopg, "connect", connect)

    with pytest.raises(
        DatabaseConfigurationError, match="host, database name, and user"
    ):
        get_connection()

    connect.assert_not_called()


@pytest.mark.parametrize("scheme", ["postgresql", "postgres"])
def test_valid_database_url_is_used_with_a_connection_timeout(monkeypatch, scheme):
    database_url = f"{scheme}://user:password@127.0.0.1:55432/database"
    monkeypatch.setenv("RAPISTOPS_DATABASE_URL", database_url)
    connection = object()
    connect = Mock(return_value=connection)
    monkeypatch.setattr(psycopg, "connect", connect)

    assert get_connection() is connection
    connect.assert_called_once_with(database_url, connect_timeout=5)


def test_database_url_is_read_for_each_connection(monkeypatch):
    first_url = "postgresql://user@127.0.0.1/first"
    second_url = "postgresql://user@127.0.0.1/second"
    connect = Mock()
    monkeypatch.setattr(psycopg, "connect", connect)

    monkeypatch.setenv("RAPISTOPS_DATABASE_URL", first_url)
    get_connection()
    monkeypatch.setenv("RAPISTOPS_DATABASE_URL", second_url)
    get_connection()

    assert connect.call_count == 2
    assert connect.call_args_list[0].args == (first_url,)
    assert connect.call_args_list[1].args == (second_url,)


def test_connection_failure_is_preserved(monkeypatch):
    monkeypatch.setenv(
        "RAPISTOPS_DATABASE_URL", "postgresql://user@127.0.0.1/database"
    )
    failure = psycopg.OperationalError("connection refused")
    connect = Mock(side_effect=failure)
    monkeypatch.setattr(psycopg, "connect", connect)

    with pytest.raises(psycopg.OperationalError) as error:
        get_connection()

    assert error.value is failure
    connect.assert_called_once()
