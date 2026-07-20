SHELL := /bin/zsh

DEFAULT_CONFIG ?= config/project.yaml
JOB ?= job.sample.txt
PREVIEW_DIR ?= output/preview-latest

.PHONY: help setup build tailor run preview docker-build clean

help:
	@printf '%s\n' \
		'Available targets:' \
		'  make setup               Copy starter config and env files if missing' \
		'  make docker-build        Build the Docker image' \
		'  make build               Build the PDF from the current template' \
		'  make tailor JOB=...      Tailor the sample CV with a job description' \
		'  make run JOB=...         Tailor and build the PDF in one step' \
		'  make preview PREVIEW_DIR=...  Build from a reviewed preview folder' \
		'  make clean               Remove build and output artifacts'

setup:
	@test -f .env || cp .env.example .env
	@test -f config/project.yaml || cp config/project.example.yaml config/project.yaml

docker-build:
	docker compose build

build:
	docker compose run --rm ai-cv --config $(DEFAULT_CONFIG) build

tailor:
	docker compose run --rm ai-cv --config $(DEFAULT_CONFIG) tailor --job $(JOB) --dry-run

run:
	docker compose run --rm ai-cv --config $(DEFAULT_CONFIG) run --job $(JOB)

preview:
	docker compose run --rm ai-cv --config $(DEFAULT_CONFIG) run --preview-dir $(PREVIEW_DIR)

clean:
	rm -rf output .build
