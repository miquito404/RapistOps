import pytest

from rapistops.case import Case
from rapistops.case_storage import save_case
from tests.database_helpers import assert_persisted, snapshot_model


pytestmark = pytest.mark.database


def test_save_case(database_connection):
    case = Case(808, "criminal", "Test Case", "TEST-001",
                "Test Case Description", "2026-09-01", "2026-09-30")
    expected = snapshot_model(case, ('opened_at', 'closed_at'))
    save_case(case)
    assert_persisted(database_connection, "cases", expected)
