# Rel2KG — instructions for later sessions

Continue this repository. Do not start a different product.

## Locked decisions

- Three open-source relational engines: **PostgreSQL 16**, **MySQL 8.4**, **SQLite 3**.
- Everything runs in Docker. Do not add host-side `pip`, `brew`, or database installs.
- Schemas stay small. The join key across sources is **email**.
- Lab credentials in Compose are public and local-only. See `SECURITY.md`.
- Python 3.12, package under `src/rel2kg`, tests under `tests/`.
- Seed row counts live in `src/rel2kg/expected.py` and must match `db/*/init.sql`.

## Layout

- `db/postgres/init.sql` — HR (`campus`)
- `db/mysql/init.sql` — library (`library`)
- `db/sqlite/init.sql` — registrar (`courses.db` on volume `sqlite_data`)
- `src/rel2kg/` — CLI, connections, verify report
- `docker-compose.yml` — Postgres + MySQL; `tools` profile for Python

## Next slices, in order

1. R2RML (or equivalent) mappings from the three schemas to RDF.
2. A small shared vocabulary (RDFS/OWL) for Person, Document, Course.
3. SPARQL access over the mapped sources (Ontop, or materialize into a triple store).
4. Competency questions as SPARQL files, treated as tests.

## Do not

- Do not replace these databases with a single engine "for simplicity".
- Do not install language runtimes or database servers on the host.
- Do not treat the demo passwords as production secrets.
- Do not expand the schemas into a full campus ERP. Add columns only when a mapping needs them.
