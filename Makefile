SHELL:=/usr/bin/env bash

.PHONY: lint
lint:
	poetry run mypy -p water_masses
	poetry run mypy tests/**/*.py
	poetry run black --check .
	poetry run flake8 .
	poetry run doc8 -q docs

.PHONY: unit
unit:
	poetry run pytest

.PHONY: package
package:
	poetry run pip check
	poetry run safety check --full-report

.PHONY: test
test: lint package unit
