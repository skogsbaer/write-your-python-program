#!/bin/bash

set -e

cd $(dirname $0)

if [ -z "$1" ]; then
    echo "Running all unit tests"
    PYTHONPATH=src:tests python3 -m unittest tests/test*.py
else
    echo "Running unit tests $@"
    PYTHONPATH=src:tests python3 -m unittest "$@"
    ecode=$?
    echo "Tests finished with exit code $ecode"
    exit $ecode
fi

echo "Running file tests ..."
./runFileTests.sh
