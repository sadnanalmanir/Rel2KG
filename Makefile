.DEFAULT_GOAL := help

.PHONY: help up bootstrap verify materialize kg test lint config down reset

help: ## Show available targets
	@awk 'BEGIN {FS = ":.*##"} /^[a-zA-Z_-]+:.*##/ {printf "  %-12s %s\n", $$1, $$2}' $(MAKEFILE_LIST)

up: ## Start PostgreSQL and MySQL (wait until healthy)
	docker compose up --build -d --wait postgres mysql

bootstrap: up ## Create SQLite and print a status report from all three sources
	docker compose run --rm --build tools

verify: ## Re-run the three-database status report
	docker compose run --rm --build tools rel2kg verify

materialize: ## Apply R2RML mappings and write Turtle to the sqlite volume
	docker compose run --rm --build tools rel2kg materialize

kg: bootstrap ## Start sources, then materialize the knowledge graph
	docker compose run --rm --build tools rel2kg materialize

test: ## Unit tests inside the tools image
	docker compose run --rm --build --no-deps tools python -m unittest discover -s /app/tests -v

lint: config ## Ruff check + format (via Docker)
	docker run --rm -v "$(CURDIR)":/app -w /app ghcr.io/astral-sh/ruff:0.13.2 check src tests
	docker run --rm -v "$(CURDIR)":/app -w /app ghcr.io/astral-sh/ruff:0.13.2 format --check src tests

config: ## Validate the Compose file
	docker compose config --quiet

down: ## Stop containers, keep volumes
	docker compose down

reset: ## Stop containers and delete volumes (next bootstrap re-seeds)
	docker compose down -v
