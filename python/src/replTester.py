import sys
import doctest
import os
import argparse
from dataclasses import dataclass
from runner import runCode, importUntypy, verbose, enableVerbose

usage = """python3 replTester.py [ ARGUMENTS ] LIB_1 ... LIB_n --repl SAMPLE_1 ... SAMPLE_m

If no library files should be used to test the REPL samples, omit LIB_1 ... LIB_n
and the --repl flag.
The definitions of LIB_1 ... LIB_n are made available when testing
SAMPLE_1 ... SAMPLE_m, where identifer in LIB_i takes precedence over identifier in
LIB_j if i > j.
"""

@dataclass
class Options:
    verbose: bool
    diffOutput: bool
    libs: list[str]
    repls: list[str]

def parseCmdlineArgs():
    parser = argparse.ArgumentParser(usage=usage,
                        formatter_class=argparse.RawTextHelpFormatter)
    parser.add_argument('--verbose', dest='verbose', action='store_const',
                        const=True, default=False,
                        help='Be verbose')
    parser.add_argument('--diffOutput', dest='diffOutput',
                        action='store_const', const=True, default=False,
                        help='print diff of expected/given output')
    args, restArgs = parser.parse_known_args()
    libs = []
    repls = []
    replFlag = '--repl'
    if replFlag in restArgs:
        cur = libs
        for x in restArgs:
            if x == replFlag:
                cur = repls
            else:
                cur.append(x)
    else:
        repls = restArgs
    if len(repls) == 0:
        print('No SAMPLE arguments given')
        sys.exit(1)
    return Options(verbose=args.verbose, diffOutput=args.diffOutput, libs=libs, repls=repls)

opts = parseCmdlineArgs()

if opts.verbose:
    enableVerbose()

libDir = os.path.dirname(__file__)
libFile = os.path.join(libDir, 'writeYourProgram.py')
defs = globals()
importUntypy()
# runCode(libFile, defs, [])

for lib in opts.libs:
    d = os.path.dirname(lib)
    if d not in sys.path:
        sys.path.insert(0, d)

for lib in opts.libs:
    verbose(f"Loading lib {lib}")
    runCode(lib, defs, [])

totalFailures = 0
totalTests = 0

doctestOptions = doctest.NORMALIZE_WHITESPACE | doctest.ELLIPSIS

if opts.diffOutput:
    doctestOptions = doctestOptions | doctest.REPORT_NDIFF

for repl in opts.repls:
    (failures, tests) = doctest.testfile(repl, globs=defs, module_relative=False,
                                         optionflags=doctestOptions)

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
