.PHONY: help install lint test

.DEFAULT: help
help:
	@echo "Available targets: install, lint, test"

install:
	poetry install --no-interaction
	poetry run pysmt-install --z3 --confirm-agreement

lint:
	poetry run pylint probably ${ARGS}

test:
	poetry run pytest --doctest-modules --cov=kipro2 --cov-report html --cov-report term --junitxml=testreport.xml tests/ kipro2/ ${ARGS}
