"""Create and verify a repeatable, entirely synthetic persistence example."""

from dataclasses import asdict
from datetime import datetime
import sys

import psycopg
from psycopg import sql

from rapistops.database import DatabaseConfigurationError, get_connection
from rapistops.evidence import Evidence
from rapistops.evidence_storage import save_evidence
from rapistops.provenance import Provenance
from rapistops.provenance_storage import save_provenance
from rapistops.record import Record
from rapistops.record_storage import save_record
from rapistops.source import Source
from rapistops.source_storage import save_source


DEMO_IDS = (-100001, -100002, -100003, -100004)


class DemoError(RuntimeError):
    """The demo encountered conflicting data or failed verification."""


def _demo_entries():
    source = Source(DEMO_IDS[0], "SYNTHETIC DEMO Source", "synthetic_demo",
                    "SYNTHETIC DEMO Organization", "SYNTHETIC DEMO Local Only",
                    "synthetic-demo-source")
    provenance = Provenance(DEMO_IDS[1], source.id, "2026-09-30", "synthetic_demo",
                            "synthetic-demo-record", "SYNTHETIC DEMO fabricated context")
    record = Record(DEMO_IDS[2], source.id, provenance.id, "synthetic_demo",
                    "SYNTHETIC DEMO fabricated document", "synthetic-demo-record",
                    "2026-09-28", "2026-09-29", "2026-09-30")
    evidence = Evidence(DEMO_IDS[3], "synthetic_demo", source.id, provenance.id,
                        record.id, "synthetic-demo-evidence",
                        "SYNTHETIC DEMO fabricated evidence; no real person or allegation")
    return (
        ("source", source, save_source, ()),
        ("provenance", provenance, save_provenance, ("collected_at",)),
        ("record", record, save_record, ("created_at", "published_at", "collected_at")),
        ("evidence", evidence, save_evidence, ()),
    )


def _read_row(connection, table, expected):
    return connection.execute(sql.SQL("SELECT {} FROM {} WHERE id = %s").format(
        sql.SQL(", ").join(sql.Identifier(column) for column in expected),
        sql.Identifier("public", table),
    ), (expected["id"],)).fetchone()


def run_demo():
    entries = _demo_entries()
    expected_rows = {}
    for table, model, _, timestamps in entries:
        expected = asdict(model)
        for column in timestamps:
            expected[column] = datetime.fromisoformat(expected[column])
        expected_rows[table] = expected

    # Read all four IDs before any independent storage function can commit.
    with get_connection() as connection:
        existing = {
            table: _read_row(connection, table, expected_rows[table])
            for table, _, _, _ in entries
        }
    for table, _, _, _ in entries:
        expected = expected_rows[table]
        if existing[table] is not None and existing[table] != tuple(expected.values()):
            raise DemoError(f"Conflict at {table} id {expected['id']}; no demo rows written.")

    created = 0
    for table, model, save, _ in entries:
        if existing[table] is None:
            save(model)
            created += 1

    with get_connection() as connection:
        for table, _, _, _ in entries:
            expected = expected_rows[table]
            if _read_row(connection, table, expected) != tuple(expected.values()):
                raise DemoError(f"Readback verification failed for {table} id {expected['id']}.")
        connected = connection.execute(
            """
            SELECT s.id, p.id, r.id, e.id
            FROM source s
            JOIN provenance p ON p.source_id = s.id
            JOIN record r ON r.source_id = s.id AND r.provenance_id = p.id
            JOIN evidence e ON e.source_id = s.id AND e.provenance_id = p.id
                AND e.record_id = r.id
            WHERE e.id = %s
            """, (expected_rows["evidence"]["id"],),
        ).fetchone()
        expected_ids = tuple(expected_rows[table]["id"] for table, _, _, _ in entries)
        if connected != expected_ids:
            raise DemoError("Synthetic chain reference verification failed.")
    return created, len(entries) - created


def main():
    try:
        created, reused = run_demo()
    except (DemoError, DatabaseConfigurationError, psycopg.Error) as error:
        print(f"Synthetic demo failed: {error}", file=sys.stderr)
        return 1
    print(f"SYNTHETIC DEMO: created={created} reused={reused}")
    chain = " -> ".join(
        f"{name}({identifier})"
        for name, identifier in zip(("Source", "Provenance", "Record", "Evidence"), DEMO_IDS)
    )
    print(f"Verified synthetic chain: {chain}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
