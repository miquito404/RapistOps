import os
from unittest.mock import Mock

import pytest

from rapistops.database import get_connection
from rapistops.source import Source
from rapistops.source_storage import save_source
from tests import database_helpers
from tests.database_helpers import (
    TABLES,
    TestDatabaseConfigurationError as ConfigurationError,
    assert_persisted,
    isolated_database,
    reset_database,
    snapshot_model,
    validate_test_database_url,
)


DEVELOPMENT_URL = "postgresql://user@127.0.0.1:55432/rapistops_dev"
TEST_URL = "postgresql://user@127.0.0.1:55433/rapistops_test"


@pytest.mark.parametrize("test_url,development_url", [
    (None, DEVELOPMENT_URL),
    ("", DEVELOPMENT_URL),
    (" \t\n", DEVELOPMENT_URL),
    (DEVELOPMENT_URL, None),
    (TEST_URL, TEST_URL),
    ("https://user@127.0.0.1/rapistops_test", None),
    ("postgresql://user:private%ZZpassword@127.0.0.1/rapistops_test", None),
    ("postgresql://user@remote.example/rapistops_test", None),
    ("postgresql://user@127.0.0.1,remote.example/rapistops_test", None),
    ("postgresql://user@/rapistops_test", None),
    ("postgresql://127.0.0.1/rapistops_test", None),
    (TEST_URL + "?hostaddr=192.0.2.1", None),
    (TEST_URL + "?dbname=rapistops_dev", None),
])
def test_guard_rejects_unsafe_configuration_before_connecting(
    monkeypatch, test_url, development_url,
):
    connect = Mock()
    monkeypatch.setattr(database_helpers.psycopg, "connect", connect)
    with pytest.raises(ConfigurationError) as error:
        reset_database(test_url, development_url)
    assert "private" not in str(error.value)
    connect.assert_not_called()


@pytest.mark.parametrize("host", ["127.0.0.1", "localhost", "[::1]"])
def test_guard_accepts_a_distinct_local_test_database(host):
    test_url = f"postgresql://user@{host}:55433/rapistops_test"
    assert validate_test_database_url(test_url, DEVELOPMENT_URL) == test_url


@pytest.mark.database
def test_database_starts_empty(database_connection):
    for table in TABLES:
        assert database_connection.execute(
            database_helpers.sql.SQL("SELECT COUNT(*) FROM {}").format(
                database_helpers.sql.Identifier("public", table)
            )
        ).fetchone() == (0,)


@pytest.mark.database
def test_committed_write_is_cleaned_after_deliberate_failure(database_state):
    # No read connection is held open while the reset acquires table locks.
    test_url, development_url = database_state
    source = Source(101, "Failure Test Source", "test", "Synthetic", "Local", "failure-test")
    with pytest.raises(AssertionError, match="deliberate test failure"):
        with isolated_database(test_url, development_url):
            expected = snapshot_model(source)
            save_source(source)
            with get_connection() as connection:
                assert_persisted(connection, "source", expected)
            raise AssertionError("deliberate test failure")
    with get_connection() as connection:
        assert connection.execute("SELECT COUNT(*) FROM source").fetchone() == (0,)
    assert os.environ["RAPISTOPS_DATABASE_URL"] == test_url
