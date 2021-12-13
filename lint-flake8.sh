#!/bin/bash
set -e
poetry run flake8 src/antsibull_changelog --count --max-complexity=10 --max-line-length=100 --statistics "$@"
