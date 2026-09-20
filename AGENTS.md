# Rel2KG — instructions for later sessions

Continue this repository. Do not start a different product.

## Locked decisions

- Three open-source relational engines: **PostgreSQL 16**, **MySQL 8.4**, **SQLite 3**.
- Everything runs in Docker. Do not add host-side `pip`, `brew`, or database installs.
- Schemas stay small. The join key across sources is **email**.
- Lab credentials in Compose are public and local-only. See `SECURITY.md`.
- Python 3.12, package under `src/rel2kg`, tests under `tests/`.
- Seed row counts live in `src/rel2kg/expected.py` and must match `db/*/init.sql`.
- Person IRIs are minted from **email** in every R2RML mapping (`https://rel2kg.example/id/person/{email}`).
- Materialization uses **Morph-KGC** from the tools image. Do not add a second R2RML engine.
- SPARQL is served by **Oxigraph** (`ghcr.io/oxigraph/oxigraph`). Competency questions in `queries/` are tests (`rel2kg query --check`).
- The product UI is the **integration desk** (`web/`, `rel2kg serve`, Compose service `desk` on port 8765). It only reads SPARQL from Oxigraph. Do not add a second query engine.

## Layout

- `db/postgres/init.sql` — HR (`campus`)
- `db/mysql/init.sql` — library (`library`)
- `db/sqlite/init.sql` — registrar (`courses.db` on volume `sqlite_data`)
- `src/rel2kg/` — CLI, connections, verify report, R2RML materialize, SPARQL
- `mappings/` — one R2RML Turtle file per database
- `vocab/rel2kg.ttl` — small target vocabulary
- `queries/` — SPARQL competency questions
- `web/` — integration desk static UI
- `docker-compose.yml` — Postgres + MySQL + Oxigraph + desk; `tools` profile for Python

## Next slices, in order

1. SHACL over the materialized graph.
2. Named graphs per source (HR / library / registrar).
3. Virtual SPARQL (Ontop) only if materialization is no longer enough.

## Do not

- Do not replace these databases with a single engine "for simplicity".
- Do not install language runtimes or database servers on the host.
- Do not treat the demo passwords as production secrets.
- Do not expand the schemas into a full campus ERP. Add columns only when a mapping needs them.
