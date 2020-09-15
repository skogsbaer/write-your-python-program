#!/bin/bash

cd $(dirname $0)

export PYTHONPATH=src:tests

if [ -z "$1" ]; then
    python3 -m unittest tests/*.py
else
    python3 -m unittest "$@"
fi
