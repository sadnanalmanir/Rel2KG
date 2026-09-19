# Contributing

Thank you for improving Rel2KG. The stack is Docker-only: do not add host-side install steps (`brew`, `apt`, `pip install` on the developer machine).

## Development loop

```bash
make help
make test
make bootstrap
```

`make bootstrap` starts PostgreSQL and MySQL, creates the SQLite file, and prints a cross-source report. Re-run `make verify` after SQL or Python changes. If you change `db/postgres/init.sql` or `db/mysql/init.sql`, reset volumes first (`make reset`) — those scripts run only on an empty data directory.

## Checks we expect on a PR

1. `make test` — unit tests in the tools image.
2. `make bootstrap` (or `make verify` if the databases are already seeded).
3. `make lint` — Compose file plus Ruff.

GitHub Actions runs the same checks on `main` and on pull requests.

## Scope

This repository is the relational layer of a later semantic-web pipeline. Keep the three schemas small. Mapping to RDF (R2RML, RDFS/OWL, SPARQL) belongs in a follow-up change that does not replace these sources.

Read `AGENTS.md` before changing locked decisions (which databases, Docker-only, email as the join key).

## Pull requests

- One concern per PR.
- Update `src/rel2kg/expected.py` when seed row counts change.
- Add or adjust tests when you change CLI behavior or SQL files.
- Fill in the PR template.
