# Changelog

All notable changes to this project are documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

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
