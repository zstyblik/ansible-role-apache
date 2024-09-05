#!/usr/bin/env bash
set -e
set -u

cd "$(dirname "${0}")/.."

python3 -m pytest -vv .
