# Makefile for the Python static site

.PHONY: all build serve clean format lint test test-unit test-integration test-e2e test-cov typing

all: build

build:
	tox run -e build

serve:
	tox run -e serve

clean:
	python main.py clean

format:
	prettier --write "**/*.{md,html,css,scss,js,json,yml,yaml}" || echo "Prettier not installed. Skipping format."

lint:
	tox run -e style

test:
	tox run -e test

test-unit:
	tox run -e test -- -m unit

test-integration:
	tox run -e test -- -m integration

test-cov:
	tox run -e test -- --cov --cov-report=term-missing

test-e2e:
	pytest tests/e2e

typing:
	tox run -e typing
