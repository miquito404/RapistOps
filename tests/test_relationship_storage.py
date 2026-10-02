import pytest

from rapistops.relationship import Relationship
from rapistops.relationship_storage import save_relationship
from tests.database_helpers import assert_persisted, snapshot_model


pytestmark = pytest.mark.database


def test_save_relationship(database_connection, source, record):
    # Entity identifiers are unconstrained in the current schema.
    relationship = Relationship(1010, 505, 606, "associated_with", source.id,
                                record.id, "2026-09-30", "Test Relationship")
    expected = snapshot_model(relationship, ("effective_at",))
    save_relationship(relationship)
    assert_persisted(database_connection, "relationship", expected)
