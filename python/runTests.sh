#!/bin/bash

set -e

cd $(dirname $0)

if [ -z "$1" ]; then
    PYTHONPATH=src:tests python3 -m unittest tests/*.py
else
    PYTHONPATH=src:tests python3 -m unittest "$@"
fi

function check()
{
    echo "Checking with $1"
    d=$(pwd)
    pushd /tmp
    python3 $d/src/runYourProgram.py --check $d/"$1"
    popd
}
check file-tests/fileWithImport.py
check file-tests/fileWithoutImport.py
check file-tests/fileWithOnlyDrawingImport.py
check file-tests/fileWithBothImports.py
