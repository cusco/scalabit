#!/usr/bin/env bash
set -e

# run black - make sure everyone uses the same python style
black --skip-string-normalization --line-length 120 --check src/ tests/


# run isort for import structure checkup with black profile
isort --atomic --profile black -c src
isort --atomic --profile black -c tests

# Linting
flake8 src/ tests/ --max-line-length=120 --extend-ignore=E203,W503

# Type checking
mypy src/

# Security check
# bandit -r src/

exit 0
