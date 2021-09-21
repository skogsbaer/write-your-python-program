#!/bin/bash

set -e
set -u

cd $(dirname $0)

unit_test_path=src:tests:deps/untypy

function prepare_integration_tests()
{
    echo "Preparing integration tests by install the WYPP library"
    local d=$(mktemp -d)
    trap "rm -rf $d" EXIT
    WYPP_INSTALL_DIR=$d python3 src/runYourProgram.py --install-mode installOnly
    integ_test_path=integration-tests:$d
}

function usage()
{
    echo "USAGE: $0 [--unit | --integration] [ FILE ]"
    exit 1
}

if [ -z "${1:-}" ]; then
    echo "Running all unit tests, PYTHONPATH=$unit_test_path"
    PYTHONPATH=$unit_test_path python3 -m unittest tests/test*.py
    echo
    prepare_integration_tests
    echo "Running all integration tests, PYTHONPATH=$integ_test_path"
    PYTHONPATH=$integ_test_path python3 -m unittest integration-tests/test*.py
else
    if [ "$1" == "--unit" ]; then
        what="unit"
        dir=tests
        p=$unit_test_path
    elif [ "$1" == "--integration" ]; then
        what="integration"
        dir=integration-tests
        prepare_integration_tests
        p=$integ_test_path
    else
        usage
    fi
    shift
    echo "Running $what tests $@ with PYTHONPATH=$p"
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
