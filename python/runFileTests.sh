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
check file-tests/fileWithBothImports.py
check file-tests/fileWithRecursiveTypes.py

python3 $d/src/runYourProgram.py --check --test-file $d/file-tests/student-submission-tests.py \
    $d/file-tests/student-submission.py >> "$t"

# First argument: whether to do type checking or not
# Second argument: expected exit code. If given as X:Y, then X is the exit code with active
#   type checking, and Y is the exit code without type checking.
# Third argument: input file
function checkWithOutputAux()
{
    local tycheck="$1"
    local expectedEcode=$2
    local file="$3"
    shift 3
    tycheckOpt=""
    suffixes="${PYENV_VERSION}"
    if [ "$tycheck" == "no" ]; then
        tycheckOpt="--no-typechecking"
        suffixes="${PYENV_VERSION}-notypes ${PYENV_VERSION} notypes"
    fi
    if echo "$expectedEcode" | grep ':' > /dev/null; then
        if [ "$tycheck" == "no" ]; then
            expectedEcode=$(echo "$expectedEcode" | sed 's/^.*://g')
        else
            expectedEcode=$(echo "$expectedEcode" | sed 's/:.*$//g')
        fi
    fi
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
    for suf in $suffixes; do
        if [ -e "${expectedOut}-${suf}" ]; then
            expectedOut="${expectedOut}-${suf}"
        fi
        if [ -e "${expectedErr}-${suf}" ]; then
            expectedErr="${expectedErr}-${suf}"
        fi
    done
    local t=$(mktemp)
    local out=$t.out
    local err=$t.err
    set +e
    echo "Checking $file (typecheck: $tycheck)"
    python3 $d/src/runYourProgram.py --quiet $tycheckOpt "$file" "$@" 2>> "$err" > "$out"
    ecode=$?
    set -e
    if [ $ecode != $expectedEcode ]; then
        echo "Expected exit code $expectedEcode got $ecode for test $file"
        exit 1
    fi
    if ! diff -u $expectedOut $out; then
        echo "Wrong output on stdout for $file ($expectedOut contains the expected output)"
        echo "Full output: $out"
        exit 1
    fi
    if ! diff -u $expectedErr $err; then
        echo "Wrong output on stderr for $file ($expectedErr contains the expected output)"
        echo "Full output: $err"
        exit 1
    fi
    rm -f "$out"
    rm -f "$err"
}

function checkWithOutput()
{
    checkWithOutputAux yes "$@"
    checkWithOutputAux no "$@"
}

checkWithOutput 1 file-tests/testTraceback.py
checkWithOutput 1 file-tests/testTraceback2.py
checkWithOutput 1 file-tests/testTraceback3.py
checkWithOutput 0 file-tests/testArgs.py ARG_1 ARG_2
checkWithOutput 0 file-tests/printModuleName.py
checkWithOutput 0 file-tests/printModuleNameImport.py
checkWithOutput 1 file-tests/testTypes1.py
checkWithOutput 1:0 file-tests/testTypes2.py

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

