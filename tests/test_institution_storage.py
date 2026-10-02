import pytest

from rapistops.institution import Institution
from rapistops.institution_storage import save_institution
from tests.database_helpers import assert_persisted, snapshot_model


pytestmark = pytest.mark.database


def test_save_institution(database_connection):
    institution = Institution(606, "Test Institution", "government", "Test Jurisdiction",
                              "Test Location", "Test Institution Description",
                              "2026-09-28", "2026-09-30")
    expected = snapshot_model(institution, ('created_at', 'updated_at'))
    save_institution(institution)
    assert_persisted(database_connection, "institution", expected)
