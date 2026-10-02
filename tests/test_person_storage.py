import pytest

from rapistops.person import Person
from rapistops.person_storage import save_person
from tests.database_helpers import assert_persisted, snapshot_model


pytestmark = pytest.mark.database


def test_save_person(database_connection):
    person = Person(505, "Test Person", "test-identifier", "Test Person Description",
                    "2026-09-29", "2026-09-30")
    expected = snapshot_model(person, ('created_at', 'updated_at'))
    save_person(person)
    assert_persisted(database_connection, "person", expected)
