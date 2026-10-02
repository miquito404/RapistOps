from dataclasses import replace
from pathlib import Path
import subprocess
import sys

import pytest
from psycopg import sql

from examples import synthetic_persistence as demo
from rapistops.evidence_storage import save_evidence
from tests.database_helpers import TABLES, assert_persisted, snapshot_model


pytestmark = pytest.mark.database
DEMO_SCRIPT = Path(__file__).resolve().parents[1] / "examples" / "synthetic_persistence.py"
VERIFIED_CHAIN = (
    "Verified synthetic chain: Source(-100001) -> Provenance(-100002) -> "
    "Record(-100003) -> Evidence(-100004)\n"
)


def _database_rows(connection):
    return {
        table: connection.execute(sql.SQL("SELECT * FROM {} ORDER BY id").format(
            sql.Identifier("public", table)
        )).fetchall()
        for table in TABLES
    }


def test_demo_creates_then_reuses_without_changing_unrelated_rows(
    database_connection, source, capsys,
):
    unrelated = snapshot_model(source)
    expected_rows = {
        table: snapshot_model(model, timestamps)
        for table, model, _, timestamps in demo._demo_entries()
    }
    assert demo.main() == 0
    assert capsys.readouterr().out == "SYNTHETIC DEMO: created=4 reused=0\n" + VERIFIED_CHAIN
    for table, expected in expected_rows.items():
        assert_persisted(database_connection, table, expected)
    assert_persisted(database_connection, "source", unrelated)
    after_first_run = _database_rows(database_connection)
    assert demo.main() == 0
    assert capsys.readouterr().out == "SYNTHETIC DEMO: created=0 reused=4\n" + VERIFIED_CHAIN
    assert _database_rows(database_connection) == after_first_run


@pytest.mark.parametrize("existing_count", [1, 2, 3])
def test_demo_completes_matching_partial_chain(database_connection, capsys, existing_count):
    entries = demo._demo_entries()
    expected_rows = {
        table: snapshot_model(model, timestamps)
        for table, model, _, timestamps in entries
    }
    for _, model, save, _ in entries[:existing_count]:
        save(model)
    assert demo.main() == 0
    assert capsys.readouterr().out == (
        f"SYNTHETIC DEMO: created={4 - existing_count} reused={existing_count}\n" + VERIFIED_CHAIN
    )
    for table, expected in expected_rows.items():
        assert_persisted(database_connection, table, expected)


@pytest.mark.parametrize("conflict_index", [0, 1, 2, 3])
def test_demo_conflict_exits_nonzero_without_any_new_writes(
    database_connection, source, provenance, record, conflict_index,
):
    changes = (
        {"name": "SYNTHETIC unrelated source"},
        {"source_id": source.id},
        {"source_id": source.id, "provenance_id": provenance.id},
        {"source_id": source.id, "provenance_id": provenance.id, "record_id": record.id},
    )
    table, model, save, _ = demo._demo_entries()[conflict_index]
    save(replace(model, **changes[conflict_index]))
    before = _database_rows(database_connection)
    result = subprocess.run(
        [sys.executable, str(DEMO_SCRIPT)], capture_output=True, text=True, check=False,
    )
    assert result.returncode == 1
    assert result.stdout == ""
    assert f"Conflict at {table} id {model.id}" in result.stderr
    assert _database_rows(database_connection) == before


def test_demo_verification_failure_returns_nonzero(database_connection, monkeypatch, capsys):
    def save_changed_evidence(evidence):
        evidence.description = "SYNTHETIC unexpectedly changed input"
        save_evidence(evidence)

    monkeypatch.setattr(demo, "save_evidence", save_changed_evidence)
    assert demo.main() == 1
    output = capsys.readouterr()
    assert output.out == ""
    assert "Readback verification failed for evidence id -100004" in output.err
