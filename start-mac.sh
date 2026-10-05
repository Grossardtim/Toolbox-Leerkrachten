#!/bin/sh
set -eu
cd "$(dirname "$0")"
if [ ! -x .venv/bin/python ]; then
  echo 'Eerst installeren volgens LEESMIJ.md.'
  exit 1
fi
exec .venv/bin/python tools/start_local.py "$@"
