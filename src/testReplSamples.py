import sys
import doctest
import runpy
import os

def usage():
    print('USAGE: python3 testReplSamples.py LIB_1 ... LIB_n --repl SAMPLE_1 ... SAMPLE_m')
    print('If no library files should be used to test the REPL samples, omit LIB_1 ... LIB_n')
    print('and the --repl flag.')
    print('The definitions of LIB_1 ... LIB_n are made available when testing ')
    print('SAMPLE_1 ... SAMPLE_m, where identifer in LIB_i takes precedence over identifier in ')
    print('LIB_j if i > j.')
    sys.exit(1)

args = sys.argv[1:]

if '--help' in args:
    usage()

libs = []
repls = []

replFlag = '--repl'

if replFlag in args:
    cur = libs
    for x in args:
        if x == replFlag:
            cur = repls
        else:
            cur.append(x)
else:
    repls = args

if len(repls) == 0:
    usage()

libDict = {}

libDir = os.path.dirname(__file__)
libFile = os.path.join(libDir, 'writeYourProgram.py')
libDefs = runpy.run_path(libFile)

for lib in libs:
    defs = runpy.run_path(lib, libDefs)
    libDict.update(defs)

totalFailures = 0
totalTests = 0

for repl in repls:
    (failures, tests) = doctest.testfile(repl, globs=libDict, module_relative=False)
    totalFailures += failures
    totalTests += tests
    if failures == 0:
        if tests == 0:
            print(f'No tests in {repl}')
        else:
            print(f'All {tests} tests in {repl} succeeded')
    else:
        print(f'ERROR: {failures} out of {tests} in {repl} failed')

if totalFailures == 0:
    if totalTests == 0:
        print('ERROR: No tests found at all!')
        sys.exit(1)
    else:
        print(f'All {totalTests} tests succeded. Great!')
else:
    print(f'ERROR: {failures} out of {tests} failed')
    sys.exit(1)
