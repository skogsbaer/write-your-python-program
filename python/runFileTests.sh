#!/usr/bin/env bash

set -e

cd $(dirname $0)

d=$(pwd)
siteDir=$(python3 -c 'import site; print(site.USER_SITE)')
t=$(mktemp)

echo
echo "Running file tests, siteDir=$siteDir ..."
echo "Writing logs to $t"
function check()
{
    echo "Checking with $1"
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
check file-tests/fileWithRecursiveTypes.py

python3 $d/src/runYourProgram.py --check --test-file $d/file-tests/student-submission-tests.py \
    $d/file-tests/student-submission.py >> "$t"

function checkWithOutput()
{
    local expectedEcode=$1
    local file="$2"
    shift 2
    local expectedOut="${file%.py}.out"
    if [ ! -f "$expectedOut" ]; then
        echo "File $expectedOut does not exist"
        exit 1
    fi
    local expectedErr="${file%.py}.err"
    if [ ! -f "$expectedErr" ]; then
        echo "File $expectedErr does not exist"
        exit 1
    fi
    if [ -e "${expectedOut}-$PYENV_VERSION" ]; then
        expectedOut="${expectedOut}-$PYENV_VERSION"
    fi
    if [ -e "${expectedErr}-$PYENV_VERSION" ]; then
        expectedErr="${expectedErr}-$PYENV_VERSION"
    fi
    local t=$(mktemp)
    local out=$t.out
    local err=$t.err
    set +e
    echo "Checking $file"
    python3 $d/src/runYourProgram.py --quiet "$file" "$@" 2>> "$err" > "$out"
    ecode=$?
    set -e
    if [ $ecode != $expectedEcode ]; then
        echo "Expected exit code $expectedEcode got $ecode for test $file"
        exit 1
    fi
    if ! diff -u $expectedOut $out; then
        echo "Wrong output on stdout for $file"
        echo "Full output: $out"
        exit 1
    fi
    if ! diff -u $expectedErr $err; then
        echo "Wrong output on stderr for $file"
        echo "Full output: $err"
        exit 1
    fi
    rm -f "$out"
    rm -f "$err"
}

checkWithOutput 1 file-tests/testTraceback.py
checkWithOutput 1 file-tests/testTraceback2.py
checkWithOutput 1 file-tests/testTraceback3.py
checkWithOutput 0 file-tests/testArgs.py ARG_1 ARG_2
checkWithOutput 0 file-tests/printModuleName.py
checkWithOutput 0 file-tests/printModuleNameImport.py

set +e
echo -n 'local_test(); print(spam)' | \
    python3 -i $d/src/runYourProgram.py --quiet --no-clear file-tests/scope-bug-peter.py |
    grep 'IT WORKS' > /dev/null
ecode="${PIPESTATUS[2]}"
set -e
if [ $ecode -ne 0 ]; then
    echo "scope-bug-peter test failed!"
    exit 1
fi

