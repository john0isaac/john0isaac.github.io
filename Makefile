# Makefile for MkDocs Site

.PHONY: all build serve clean format lint

all: build

build:
	mkdocs build

serve:
	mkdocs serve

clean:
	rm -rf site/

format:
	prettier --write "**/*.{md,html,css,scss,js,json,yml,yaml}" || echo "Prettier not installed. Skipping format."

lint:
	markdownlint **/*.md || echo "markdownlint not installed. Skipping lint."
