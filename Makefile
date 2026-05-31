# Makefile for the Python static site

.PHONY: all build serve clean format lint test test-unit test-integration test-e2e test-cov

all: build

build:
	python main.py build

serve:
	python main.py serve

clean:
	python main.py clean

format:
	prettier --write "**/*.{md,html,css,scss,js,json,yml,yaml}" || echo "Prettier not installed. Skipping format."

lint:
	markdownlint **/*.md || echo "markdownlint not installed. Skipping lint."

test:
	pytest

test-unit:
	pytest -m unit

test-integration:
	pytest -m integration

test-cov:
	pytest --cov --cov-report=term-missing

test-e2e:
	pytest tests/e2e
