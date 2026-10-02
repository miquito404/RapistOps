import pytest

from rapistops.source import Source
from rapistops.source_storage import save_source
from tests.database_helpers import assert_persisted, snapshot_model


pytestmark = pytest.mark.database


def test_save_source(database_connection):
    source = Source(101, "Test Source", "public_record", "Test Organization",
                    "Test Location", "test-reference")
    expected = snapshot_model(source, ())
    save_source(source)
    assert_persisted(database_connection, "source", expected)
