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
- When two systems use different emails for the same person, do not collapse them at mapping time. Link them with `owl:sameAs` in `links/sameas.ttl` (`graph/identity`). Ada is the easy same-email case; Knuth is the hard case.
- Materialization uses **Morph-KGC** from the tools image. Do not add a second R2RML engine.
- SPARQL is served by **Oxigraph** (`ghcr.io/oxigraph/oxigraph`). Competency questions in `queries/` are tests (`rel2kg query --check`).
- The product UI is the **integration desk** (`web/`, `rel2kg serve`, Compose service `desk` on port 8765). It only reads SPARQL from Oxigraph. Do not add a second query engine.
- The Map view (`/api/graph`, `web/graph.js`) draws instance nodes from named graphs. Keep it vanilla canvas; do not add a JS graph library.
- SHACL shapes live in `shapes/campus.shacl.ttl` and are checked by `rel2kg shacl` (also after `materialize`). Do not swap pySHACL for another validator.
- Instance triples live in named graphs `graph/hr`, `graph/library`, `graph/registrar`; vocabulary in `graph/vocab`. The default graph is the RDF merge so SPARQL without `GRAPH` still sees one Person.

## Layout

- `db/postgres/init.sql` — HR (`campus`)
- `db/mysql/init.sql` — library (`library`)
- `db/sqlite/init.sql` — registrar (`courses.db` on volume `sqlite_data`)
- `src/rel2kg/` — CLI, connections, verify report, R2RML materialize, SPARQL
- `mappings/` — one R2RML Turtle file per database
- `vocab/rel2kg.ttl` — small target vocabulary
- `links/sameas.ttl` — curated owl:sameAs (named graph `identity`)
- `shapes/campus.shacl.ttl` — SHACL constraints over the mapped graph
- `queries/` — SPARQL competency questions
- `web/` — integration desk static UI
- `docker-compose.yml` — Postgres + MySQL + Oxigraph + desk; `tools` profile for Python

## Next slices, in order

1. Virtual SPARQL (Ontop) only if materialization is no longer enough.

## Do not

- Do not replace these databases with a single engine "for simplicity".
- Do not install language runtimes or database servers on the host.
- Do not treat the demo passwords as production secrets.
- Do not expand the schemas into a full campus ERP. Add columns only when a mapping needs them.
