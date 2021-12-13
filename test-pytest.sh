#!/bin/sh
set -e
PYTHONPATH=src poetry run python -m pytest --cov-branch --cov=antsibull_changelog -vv tests "$@"
