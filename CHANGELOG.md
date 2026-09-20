# Changelog

All notable changes to this project are documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

## [0.8.0] - 2026-09-20

### Added

- Harder identity: Knuth has two emails / two Person IRIs linked by `owl:sameAs`
- Identity named graph (`links/sameas.ttl`, `graph/identity`)
- SPARQL tests `knuth_sameas.rq`, `knuth_across_sources.rq`, `unlinked_authors.rq`

### Changed

- Library author email for Knuth is `knuth@taocp.example` (no longer the campus address)

## [0.7.0] - 2026-09-20

### Added

- Named-graph map view on the integration desk (canvas, graph toggles, click a person)

## [0.6.0] - 2026-09-20

### Added

- Named graphs per source (`graph/hr`, `graph/library`, `graph/registrar`, `graph/vocab`)
- N-Quads output (`kg.nq`) and Oxigraph load of the dataset
- SPARQL competency questions `named_graphs.rq` and `ada_in_graphs.rq`

### Changed

- The default graph holds the RDF merge; named graphs keep per-source triples for `GRAPH` queries

## [0.5.0] - 2026-09-20

### Added

- Campus SHACL shapes (`shapes/campus.shacl.ttl`)
- `rel2kg shacl` via pySHACL; `materialize` fails if the graph does not conform

## [0.4.0] - 2026-09-19

### Added

- Integration desk UI (`make desk`, http://localhost:8765/)
- Person card with HR / library / registrar columns
- Desk API over the existing SPARQL competency questions

## [0.3.0] - 2026-09-19

### Added

- Oxigraph SPARQL 1.1 endpoint in Docker Compose
- `rel2kg load` and `rel2kg query` against the materialized graph
- Six competency SPARQL files in `queries/`, checked in CI

## [0.2.0] - 2026-09-19

### Added

- W3C R2RML mappings for PostgreSQL, MySQL, and SQLite
- Small RDFS vocabulary (`vocab/rel2kg.ttl`)
- `rel2kg materialize` via Morph-KGC (Docker-only)
- Cross-source Person IRIs keyed on email

## [0.1.0] - 2026-09-19

### Added

- PostgreSQL 16 campus HR schema (`department`, `employee`)
- MySQL 8.4 campus library schema (`author`, `book`, `loan`)
- SQLite campus registrar schema (`course`, `enrollment`)
- Docker Compose stack and Python tools image (no host installs)
- `rel2kg` CLI: `bootstrap`, `init-sqlite`, `verify`
- GitHub Actions CI, Dependabot, and community files
