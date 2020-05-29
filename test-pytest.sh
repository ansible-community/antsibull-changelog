#!/bin/sh
set -e
poetry run python -m pytest --cov-branch --cov=antsibull_changelog -vv tests "$@"
