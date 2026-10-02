import pytest

from rapistops.event import Event
from rapistops.event_storage import save_event
from tests.database_helpers import assert_persisted, snapshot_model


pytestmark = pytest.mark.database


def test_save_event(database_connection):
    event = Event(707, "incident", "Test Event", "2026-09-30",
                  "Test Location", "Test Event Description")
    expected = snapshot_model(event, ('occurred_at',))
    save_event(event)
    assert_persisted(database_connection, "event", expected)
