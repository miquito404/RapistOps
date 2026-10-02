import pytest

from rapistops.record import Record
from rapistops.record_storage import save_record
from tests.database_helpers import assert_persisted, snapshot_model


pytestmark = pytest.mark.database


def test_save_record(database_connection, source, provenance):
    record = Record(303, source.id, provenance.id, "report", "Test Record",
                    "record-test-reference", "2026-09-28", "2026-09-29", "2026-09-30")
    expected = snapshot_model(record, ("created_at", "published_at", "collected_at"))
    save_record(record)
    assert_persisted(database_connection, "record", expected)
