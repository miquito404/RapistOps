import pytest

from rapistops.evidence import Evidence
from rapistops.evidence_storage import save_evidence
from tests.database_helpers import assert_persisted, snapshot_model


pytestmark = pytest.mark.database


def test_save_evidence(database_connection, source, provenance, record):
    evidence = Evidence(404, "document", source.id, provenance.id, record.id,
                        "evidence-test-reference", "Test Evidence")
    expected = snapshot_model(evidence)
    save_evidence(evidence)
    assert_persisted(database_connection, "evidence", expected)
