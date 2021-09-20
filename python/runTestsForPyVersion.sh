#!/bin/bash

set -e

cd $(dirname $0)

unit_test_path=src:tests:deps/untypy
integ_test_path=integration-tests

function usage()
{
    echo "USAGE: $0 [--unit | --integration] [ FILE ]"
    exit 1
}

if [ -z "$1" ]; then
    echo "Running all unit tests"
    PYTHONPATH=$unit_test_path python3 -m unittest tests/test*.py
    echo "Running all integration tests"
    PYTHONPATH=$integ_test_path python3 -m unittest integration-tests/test*.py
else
    if [ "$1" == "--unit" ]; then
        what="unit"
        dir=tests
        p=$unit_test_path
    elif [ "$1" == "--integration" ]; then
        what="integration"
        dir=integration-tests
        p=$integ_test_path
    else
        usage
    fi
    shift
    echo "Running $what tests $@"
    if [ -z "$1" ]; then
        PYTHONPATH=$p python3 -m unittest $dir/test*.py
        ecode=$?
    else
        PYTHONPATH=$p python3 -m unittest "$@"
        ecode=$?
    fi
    echo "$what tests finished with exit code $ecode"
    exit $ecode
fi

echo "Running file tests ..."
./runFileTests.sh
