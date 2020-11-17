#!/bin/bash

set -e

cd $(dirname $0)

function run()
{
    echo
    echo "Running tests for Python version $PYENV_VERSION"
    echo
    ./runTestsForPyVersion.sh
    echo
    echo "Finished tests for Python version $PYENV_VERSION"
    echo
}

PYENV_VERSION=3.8.6 run
PYENV_VERSION=3.9.0 run
