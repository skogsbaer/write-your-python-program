#!/bin/bash

set -e

cd $(dirname $0)

if [ -z "$1" ]; then
    PYTHONPATH=src:tests python3 -m unittest tests/*.py
else
    PYTHONPATH=src:tests python3 -m unittest "$@"
fi

siteDir=$(python3 -c 'import site; print(site.USER_SITE)')
function check()
{
    echo "Checking with $1"
    d=$(pwd)
    pushd /tmp
    python3 $d/src/runYourProgram.py --check $d/"$1"
    python3 $d/src/runYourProgram.py --check --install-mode libFromFile $d/"$1"
    rm -rf "$siteDir/wypp"
    python3 $d/src/runYourProgram.py --check --install-mode assertInstall $d/"$1"
    python3 $d/src/runYourProgram.py --check --install-mode assertInstall $d/"$1"
    popd
}
check file-tests/fileWithImport.py
check file-tests/fileWithoutImport.py
check file-tests/fileWithOnlyDrawingImport.py
check file-tests/fileWithBothImports.py

python3 $d/src/runYourProgram.py --check --test-file $d/file-tests/student-submission-tests.py \
    $d/file-tests/student-submission.py
