import pytest

from rapistops.case import Case
from rapistops.case_storage import save_case
from rapistops.event import Event
from rapistops.event_storage import save_event
from rapistops.evidence import Evidence
from rapistops.evidence_storage import save_evidence
from rapistops.institution import Institution
from rapistops.institution_storage import save_institution
from rapistops.person import Person
from rapistops.person_storage import save_person
from rapistops.provenance import Provenance
from rapistops.provenance_storage import save_provenance
from rapistops.record import Record
from rapistops.record_storage import save_record
from rapistops.relationship import Relationship
from rapistops.relationship_storage import save_relationship
from rapistops.source import Source
from rapistops.source_storage import save_source
from rapistops.status import Status
from rapistops.status_storage import save_status
from tests.database_helpers import assert_persisted, snapshot_model


pytestmark = pytest.mark.database


def test_database_integration(database_connection):
    source = Source(101, "Integration Source", "public_record", "Synthetic",
                    "Local", "integration-reference")
    provenance = Provenance(202, source.id, "2026-09-30", "manual",
                            "integration-reference", "Integration Context")
    record = Record(303, source.id, provenance.id, "report", "Integration Record",
                    "integration-reference", "2026-09-28", "2026-09-29", "2026-09-30")
    evidence = Evidence(404, "document", source.id, provenance.id, record.id,
                        "integration-evidence", "Integration Evidence")
    person = Person(505, "Integration Person", "synthetic-person", "Synthetic Person",
                    "2026-09-29", "2026-09-30")
    institution = Institution(606, "Integration Institution", "government", "Test Jurisdiction",
                              "Local", "Synthetic Institution", "2026-09-28", "2026-09-30")
    event = Event(707, "incident", "Integration Event", "2026-09-30", "Local", "Synthetic Event")
    case = Case(808, "criminal", "Integration Case", "INTEGRATION-001", "Synthetic Case",
                "2026-09-01", "2026-09-30")
    status = Status(909, "Reported", person.id, "2026-09-30", source.id, record.id, "Test Status")
    relationship = Relationship(1010, person.id, institution.id, "associated_with",
                                source.id, record.id, "2026-09-30", "Test Relationship")

    saved_models = [
        (save_source, "source", source, ()),
        (save_provenance, "provenance", provenance, ("collected_at",)),
        (save_record, "record", record, ("created_at", "published_at", "collected_at")),
        (save_evidence, "evidence", evidence, ()),
        (save_person, "person", person, ("created_at", "updated_at")),
        (save_institution, "institution", institution, ("created_at", "updated_at")),
        (save_event, "event", event, ("occurred_at",)),
        (save_case, "cases", case, ("opened_at", "closed_at")),
        (save_status, "status", status, ("effective_at",)),
        (save_relationship, "relationship", relationship, ("effective_at",)),
    ]
    expected_rows = {
        table: snapshot_model(model, timestamps)
        for _, table, model, timestamps in saved_models
    }
    for save, table, model, _ in saved_models:
        save(model)
        assert_persisted(database_connection, table, expected_rows[table])

    connected = database_connection.execute(
        """
        SELECT s.id, p.id, r.id, e.id, st.id, rel.id
        FROM source s
        JOIN provenance p ON p.source_id = s.id
        JOIN record r ON r.source_id = s.id AND r.provenance_id = p.id
        JOIN evidence e ON e.source_id = s.id AND e.provenance_id = p.id
            AND e.record_id = r.id
        JOIN status st ON st.source_id = s.id AND st.record_id = r.id
        JOIN relationship rel ON rel.source_id = s.id AND rel.record_id = r.id
        WHERE e.id = %s
        """, (expected_rows["evidence"]["id"],),
    ).fetchone()
    assert connected == tuple(
        expected_rows[table]["id"]
        for table in ("source", "provenance", "record", "evidence", "status", "relationship")
    )
