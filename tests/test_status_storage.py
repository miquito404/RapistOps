import pytest

from rapistops.status import Status
from rapistops.status_storage import save_status
from tests.database_helpers import assert_persisted, snapshot_model


pytestmark = pytest.mark.database


def test_save_status(database_connection, source, record):
    # entity_id is an unconstrained synthetic identifier in the current schema.
    status = Status(909, "Reported", 505, "2026-09-30", source.id, record.id, "Test Status")
    expected = snapshot_model(status, ("effective_at",))
    save_status(status)
    assert_persisted(database_connection, "status", expected)
