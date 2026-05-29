# Makefile for the Python static site

.PHONY: all build serve clean format lint

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
