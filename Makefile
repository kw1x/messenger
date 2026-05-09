SHELL := /usr/bin/env bash
COMPOSE := docker compose

.DEFAULT_GOAL := help

.PHONY: help install up down logs ps restart \
        topics migrate revision \
        lint format test \
        psql redis-cli shell-core shell-gateway

help:
	@awk 'BEGIN {FS = ":.*##"; printf "Usage: make \033[36m<target>\033[0m\n\n"} /^[a-zA-Z_-]+:.*##/ { printf "  \033[36m%-18s\033[0m %s\n", $$1, $$2 }' $(MAKEFILE_LIST)

install: ## Sync the workspace with uv
	uv sync --all-packages

up: ## Bring the whole stack up
	$(COMPOSE) up -d --build

down: ## Tear the stack down
	$(COMPOSE) down -v

logs: ## Tail logs of every service
	$(COMPOSE) logs -f --tail=200

ps: ## List containers
	$(COMPOSE) ps

restart: ## Restart application services
	$(COMPOSE) restart chat-core presence-gateway

topics: ## Provision Kafka topics
	$(COMPOSE) exec kafka bash /scripts/create_topics.sh

migrate: ## Apply Alembic migrations
	$(COMPOSE) exec chat-core alembic upgrade head

revision: ## Create a new Alembic revision: make revision m="add_something"
	$(COMPOSE) exec chat-core alembic revision --autogenerate -m "$(m)"

lint: ## Run ruff + mypy
	uv run ruff check .
	uv run ruff format --check .
	uv run mypy libs services

format: ## Auto-format with ruff
	uv run ruff format .
	uv run ruff check . --fix

test: ## Run pytest across the workspace
	uv run pytest libs services

psql: ## Open psql in the postgres container
	$(COMPOSE) exec postgres psql -U $${POSTGRES_USER:-hexachat} -d $${POSTGRES_DB:-hexachat}

redis-cli: ## Open redis-cli
	$(COMPOSE) exec redis redis-cli

shell-core: ## Open a shell inside chat-core
	$(COMPOSE) exec chat-core bash

shell-gateway: ## Open a shell inside presence-gateway
	$(COMPOSE) exec presence-gateway bash
