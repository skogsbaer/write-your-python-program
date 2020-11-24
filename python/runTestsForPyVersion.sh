#!/bin/bash

set -e

cd $(dirname $0)

if [ -z "$1" ]; then
    PYTHONPATH=src:tests python3 -m unittest tests/*.py
else
    PYTHONPATH=src:tests python3 -m unittest "$@"
    exit $?
fi

./runFileTests.sh
