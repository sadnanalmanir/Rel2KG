# Contributing

Thank you for improving Rel2KG. The stack is Docker-only: do not add host-side install steps (`brew`, `apt`, `pip install` on the developer machine).

## Development loop

```bash
make help
make test
make bootstrap
```

`make bootstrap` starts PostgreSQL and MySQL, creates the SQLite file, and prints a cross-source report. `make materialize` applies the R2RML mappings. Re-run `make verify` after SQL or Python changes, and `make materialize` after mapping or vocab changes. If you change `db/postgres/init.sql` or `db/mysql/init.sql`, reset volumes first (`make reset`) — those scripts run only on an empty data directory.

## Checks we expect on a PR

1. `make test` — unit tests in the tools image.
2. `make bootstrap` (or `make verify` if the databases are already seeded).
3. `make materialize` if you touched mappings, vocab, or seed data.
4. `make lint` — Compose file plus Ruff.

GitHub Actions runs the same checks on `main` and on pull requests.

## Scope

Keep the three schemas small. Person identity is email, expressed as `https://rel2kg.example/id/person/{email}` in every mapping. SPARQL over a triple store is the next slice; do not replace Morph-KGC or the three databases.

Read `AGENTS.md` before changing locked decisions (which databases, Docker-only, email as the join key).

## Pull requests

- One concern per PR.
- Update `src/rel2kg/expected.py` when seed row counts change.
- Add or adjust tests when you change CLI behavior or SQL files.
- Fill in the PR template.
