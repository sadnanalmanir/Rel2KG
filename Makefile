.DEFAULT_GOAL := help

.PHONY: help up bootstrap verify materialize kg shacl load query sparql desk test lint config down reset

help: ## Show available targets
	@awk 'BEGIN {FS = ":.*##"} /^[a-zA-Z_-]+:.*##/ {printf "  %-12s %s\n", $$1, $$2}' $(MAKEFILE_LIST)

up: ## Start PostgreSQL, MySQL, and Oxigraph
	docker compose up --build -d postgres mysql oxigraph

bootstrap: ## Create SQLite and print a status report from all three sources
	docker compose up -d --wait postgres mysql
	docker compose run --rm --build tools

verify: ## Re-run the three-database status report
	docker compose run --rm --build tools rel2kg verify

materialize: ## Apply R2RML mappings, write Turtle, and run SHACL
	docker compose run --rm --build tools rel2kg materialize

shacl: ## Validate kg.ttl against campus SHACL shapes
	docker compose run --rm --build tools rel2kg shacl

kg: bootstrap ## Start sources, then materialize the knowledge graph
	docker compose run --rm --build tools rel2kg materialize

load: ## PUT kg.ttl into Oxigraph
	docker compose up -d oxigraph
	docker compose run --rm --build tools rel2kg load

query: ## Run SPARQL competency questions against Oxigraph
	docker compose run --rm --build tools rel2kg query --check

sparql: kg ## Materialize, load Oxigraph, and check competency questions
	docker compose up -d oxigraph
	docker compose run --rm --build tools rel2kg load
	docker compose run --rm --build tools rel2kg query --check

desk: ## Load the graph and start the integration desk at :8765
	docker compose up -d oxigraph
	docker compose run --rm --build tools rel2kg load
	docker compose up -d --build desk

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
