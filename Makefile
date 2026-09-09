.DEFAULT_GOAL := help

.PHONY: help build serve clean format lint test test-unit test-integration test-e2e test-cov typing

help: ## Show this help
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | awk 'BEGIN {FS = ":.*?## "}; {printf "  \033[36m%-16s\033[0m %s\n", $$1, $$2}'

build: ## Build the project
	tox run -e build

serve: ## Serve the project locally
	tox run -e serve

clean: ## Clean the project
	python main.py clean

format: ## Format the code
	prettier --write "**/*.{md,html,css,scss,js,json,yml,yaml}" || echo "Prettier not installed. Skipping format."

lint: ## Lint the code
	tox run -e style

test: ## Run all tests
	tox run -e test

test-unit: ## Run unit tests
	tox run -e test -- -m unit

test-integration: ## Run integration tests
	tox run -e test -- -m integration

test-cov: ## Run tests with coverage
	tox run -e test -- --cov --cov-report=term-missing

test-e2e: ## Run end-to-end tests
	pytest tests/e2e

typing: ## Check typing with mypy
	tox run -e typing
