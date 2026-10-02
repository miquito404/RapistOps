# Local development database

Run these commands from the repository root. This setup uses a disposable local
PostgreSQL database for synthetic development data.

## Prerequisites

- Docker with Compose v2 supporting `docker compose up --wait`.
- On Windows, Docker Desktop must be running Linux containers.
- Python 3.12 with the project's dependencies installed in a virtual environment.

If the Python environment is not set up yet:

```text
python -m venv .venv
```

Activate it in PowerShell:

```powershell
.\.venv\Scripts\Activate.ps1
```

Or in a POSIX shell:

```sh
. .venv/bin/activate
```

Then install the package and development dependencies:

```text
python -m pip install -e ".[dev]"
```

## Start PostgreSQL

```text
docker compose up -d --wait --wait-timeout 120
```

Compose uses `postgres:17.11-bookworm`, creates database and user `rapistops_dev`,
and publishes PostgreSQL only on `127.0.0.1:55432`. The example password
`rapistops_local_only` is for this disposable local setup only.

The health check runs PostgreSQL's `pg_isready` against `127.0.0.1` inside the
container. It checks server readiness; verify schema initialization separately
below.

The existing `data/schema.sql` is mounted read-only as
`/docker-entrypoint-initdb.d/001-schema.sql`. PostgreSQL runs it automatically
when the data volume is empty. Starting an existing volume does not reapply the
schema or migrate it.

## Configure Python

In PowerShell:

```powershell
$env:RAPISTOPS_DATABASE_URL = "postgresql://rapistops_dev:rapistops_local_only@127.0.0.1:55432/rapistops_dev"
```

In a POSIX shell:

```sh
export RAPISTOPS_DATABASE_URL='postgresql://rapistops_dev:rapistops_local_only@127.0.0.1:55432/rapistops_dev'
```

`.env.example` documents the same setting. Python does not automatically load
that file or a copied `.env`; set the environment variable in the shell running
Python. Compose's `.env` handling does not set variables in your Python process.

The URL must use `postgresql://` or `postgres://` and explicitly include a host,
database name, and user. A password is optional for other authentication setups.
Missing, blank, malformed, or incomplete configuration raises
`DatabaseConfigurationError` without printing the URL or password. Connection
attempts use a five-second timeout; server, authentication, and missing-database
failures propagate as `psycopg.OperationalError`.

## Verify connection and schema

Verify the Python connection:

```text
python -c "from rapistops.database import get_connection; c = get_connection(); print(c.execute('SELECT 1').fetchone()); c.close()"
```

Expected output: `(1,)`.

List the initialized tables using the container's `psql`:

```text
docker compose exec -T db psql -U rapistops_dev -d rapistops_dev -v ON_ERROR_STOP=1 -c "SELECT tablename FROM pg_tables WHERE schemaname = 'public' ORDER BY tablename;"
```

Expect exactly these ten tables: `cases`, `event`, `evidence`, `institution`,
`person`, `provenance`, `record`, `relationship`, `source`, and `status`.

Run the database-free configuration tests:

```text
python -m pytest tests/test_database_configuration.py -q
```

## Run isolated PostgreSQL tests

Start only the dedicated test service:

```text
docker compose --profile tests up -d --wait --wait-timeout 120 db-test
```

This separate PostgreSQL instance uses database `rapistops_test`, host port
`55433`, and temporary in-memory storage. It does not use the development
database or its volume. Stopping the test container discards its database.
The existing schema is initialized automatically when the container starts.

Set the test URL in PowerShell:

```powershell
$env:RAPISTOPS_TEST_DATABASE_URL = "postgresql://rapistops_test:rapistops_tests_only@127.0.0.1:55433/rapistops_test"
```

Or in a POSIX shell:

```sh
export RAPISTOPS_TEST_DATABASE_URL='postgresql://rapistops_test:rapistops_tests_only@127.0.0.1:55433/rapistops_test'
```

The guard requires database name `rapistops_test`, an explicit user, and a local
loopback endpoint. It rejects a test URL equal to `RAPISTOPS_DATABASE_URL`.
There is no fallback to the development URL. Keep `RAPISTOPS_DATABASE_URL`
unset or pointing to your normal development database; the fixture temporarily
overrides it only while a database test runs and restores it afterward.

Run database-free tests, including the safety-guard checks:

```text
python -m pytest -m "not database" -q
```

Explicitly enable the PostgreSQL tests:

```text
python -m pytest --run-database -m database -q
```

Without `--run-database`, live tests are skipped. When explicitly enabled,
missing or unsafe test configuration fails before database setup. Each live
test starts with all ten tables empty. Its requested parent fixtures create
the needed rows, and teardown resets those tables even after an assertion
fails. Connections are closed before reset; storage functions' independent
commits are covered by the reset. A deliberate-failure regression verifies
cleanup of a committed insert. A killed process can leave temporary test rows;
the next test run clears them before use.

Run these database tests serially. Concurrent runs or parallel pytest workers
sharing this test database are outside the Developer Preview scope.

Stop only the disposable test service:

```text
docker compose --profile tests stop db-test
```

This permanently discards the test database's temporary contents. It does not
stop or remove the normal development database.

## Stop or initialize from scratch

Ordinary shutdown preserves the database volume:

```text
docker compose down
```

To initialize again from an empty database:

**Warning: the following `docker compose down --volumes` command permanently
deletes this Compose project's local development database, including every row
stored in it. Use it only when you intend to discard that data.**

```text
docker compose down --volumes
docker compose up -d --wait --wait-timeout 120
```

This removes the `rapistops-dev` project's dedicated database volume and creates
a fresh one, causing `data/schema.sql` to run again. Repeat the table verification
above. It is a fresh initialization, not an in-place migration.

## Troubleshooting

- If Docker is unavailable, start Docker Desktop or provide an existing
  PostgreSQL instance and an explicit URL. Run `data/schema.sql` against an empty
  database using `psql -v ON_ERROR_STOP=1 --single-transaction -f data/schema.sql`
  with that instance's connection settings.
- If startup or schema initialization fails, inspect `docker compose logs db`.
  Initialization scripts do not resume on a partially initialized volume. Fix
  the cause, then use the destructive reset above only if its data is disposable.
- If port `55432` is occupied, stop this setup and change the published host port
  and your URL together.
- For authentication errors, check the URL against the credentials used when
  the volume was first created. Changing configuration does not change credentials
  in an existing database volume.
- If the Python module cannot be imported, confirm that the virtual environment
  is active and the package and its declared dependencies are installed.
