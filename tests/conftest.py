import os

import pytest

from rapistops.database import get_connection
from rapistops.provenance import Provenance
from rapistops.record import Record
from rapistops.source import Source
from tests.database_helpers import (
    TestDatabaseConfigurationError,
    isolated_database,
    validate_test_database_url,
)


def pytest_addoption(parser):
    parser.addoption(
        "--run-database", action="store_true", default=False,
        help="Run tests against the explicitly configured disposable database.",
    )


def pytest_collection_modifyitems(config, items):
    if not config.getoption("--run-database"):
        skip = pytest.mark.skip(reason="Use --run-database with RAPISTOPS_TEST_DATABASE_URL.")
        for item in items:
            if item.get_closest_marker("database"):
                item.add_marker(skip)
    elif any(item.get_closest_marker("database") for item in items):
        try:
            validate_test_database_url(
                os.environ.get("RAPISTOPS_TEST_DATABASE_URL"),
                os.environ.get("RAPISTOPS_DATABASE_URL"),
            )
        except TestDatabaseConfigurationError as error:
            raise pytest.UsageError(str(error)) from None


@pytest.fixture
def database_state(monkeypatch, request):
    if not request.config.getoption("--run-database"):
        pytest.skip("Use --run-database with RAPISTOPS_TEST_DATABASE_URL.")
    development_url = os.environ.get("RAPISTOPS_DATABASE_URL")
    test_url = validate_test_database_url(
        os.environ.get("RAPISTOPS_TEST_DATABASE_URL"), development_url,
    )
    # Prevent inherited libpq routing or schema defaults from changing the target.
    for name in ("PGHOSTADDR", "PGSERVICE", "PGSERVICEFILE", "PGOPTIONS"):
        monkeypatch.delenv(name, raising=False)
    monkeypatch.setenv("RAPISTOPS_DATABASE_URL", test_url)
    with isolated_database(test_url, development_url):
        yield test_url, development_url


@pytest.fixture
def database_connection(database_state):
    with get_connection() as connection:
        yield connection


@pytest.fixture
def source(database_connection):
    source = Source(101, "Test Source", "public_record", "Test Organization",
                    "Test Location", "test-reference")
    database_connection.execute(
        "INSERT INTO source (id, name, type, organization, location, access_reference) "
        "VALUES (%s, %s, %s, %s, %s, %s)",
        (source.id, source.name, source.type, source.organization,
         source.location, source.access_reference),
    )
    database_connection.commit()
    return source


@pytest.fixture
def provenance(database_connection, source):
    provenance = Provenance(202, source.id, "2026-09-30", "manual",
                            "test-reference", "Test Context")
    database_connection.execute(
        "INSERT INTO provenance (id, source_id, collected_at, collection_method, "
        "source_reference, collection_context) VALUES (%s, %s, %s, %s, %s, %s)",
        (provenance.id, provenance.source_id, provenance.collected_at,
         provenance.collection_method, provenance.source_reference,
         provenance.collection_context),
    )
    database_connection.commit()
    return provenance


@pytest.fixture
def record(database_connection, source, provenance):
    record = Record(303, source.id, provenance.id, "report", "Test Record",
                    "test-reference", "2026-09-30", "2026-09-30", "2026-09-30")
    database_connection.execute(
        "INSERT INTO record (id, source_id, provenance_id, type, title, "
        "source_reference, created_at, published_at, collected_at) "
        "VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)",
        (record.id, record.source_id, record.provenance_id, record.type, record.title,
         record.source_reference, record.created_at, record.published_at, record.collected_at),
    )
    database_connection.commit()
    return record
