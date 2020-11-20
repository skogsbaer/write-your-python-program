#!/bin/bash

set -e

cd $(dirname $0)

if [ -z "$1" ]; then
    PYTHONPATH=src:tests python3 -m unittest tests/*.py
else
    PYTHONPATH=src:tests python3 -m unittest "$@"
    exit $?
fi

siteDir=$(python3 -c 'import site; print(site.USER_SITE)')
t=$(mktemp)

echo
echo "Running file tests, siteDir=$siteDir ..."
echo "Writing logs to $t"
function check()
{
    echo "Checking with $1"
    d=$(pwd)
    pushd /tmp > /dev/null
    python3 $d/src/runYourProgram.py --check $d/"$1" >> "$t"
    python3 $d/src/runYourProgram.py --check --install-mode libFromFile $d/"$1" >> "$t"
    rm -rf "$siteDir/wypp"
    python3 $d/src/runYourProgram.py --check $d/"$1" >> "$t"
    python3 $d/src/runYourProgram.py --check --install-mode assertInstall $d/"$1" >> "$t"
    popd > /dev/null
}
check file-tests/fileWithImport.py
check file-tests/fileWithoutImport.py
check file-tests/fileWithOnlyDrawingImport.py
check file-tests/fileWithBothImports.py

python3 $d/src/runYourProgram.py --check --test-file $d/file-tests/student-submission-tests.py \
    $d/file-tests/student-submission.py >> "$t"
