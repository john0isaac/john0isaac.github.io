# Makefile for Jekyll Blog

.PHONY: all build serve clean format lint

all: build

build:
	bundle exec jekyll build

serve:
	bundle exec jekyll serve

clean:
	rm -rf _site .jekyll-cache .sass-cache

format:
	prettier --write "**/*.{md,html,css,scss,js,json,yml,yaml}" || echo "Prettier not installed. Skipping format."

lint:
	markdownlint **/*.md || echo "markdownlint not installed. Skipping lint."
