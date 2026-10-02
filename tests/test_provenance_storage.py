import pytest

from rapistops.provenance import Provenance
from rapistops.provenance_storage import save_provenance
from tests.database_helpers import assert_persisted, snapshot_model


pytestmark = pytest.mark.database


def test_save_provenance(database_connection, source):
    provenance = Provenance(202, source.id, "2026-09-30", "manual",
                            "provenance-test-reference", "Provenance Test Context")
    expected = snapshot_model(provenance, ("collected_at",))
    save_provenance(provenance)
    assert_persisted(database_connection, "provenance", expected)
