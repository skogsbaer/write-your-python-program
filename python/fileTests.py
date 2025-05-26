from dataclasses import dataclass
import os
from typing import *
import sys
import subprocess
import tempfile
import argparse
import re

@dataclass(frozen=True)
class TestOpts:
    cmd: str
    baseDir: str
    startAt: Optional[str]
    only: Optional[str]
    keepGoing: bool

def parseArgs() -> TestOpts:
    parser = argparse.ArgumentParser(
        description="Run tests with specified options.",
        usage="USAGE: ./fileTests OPTIONS"
    )

    # Define the command-line arguments
    parser.add_argument("--start-at", type=str, help="Start with test in FILE")
    parser.add_argument("--only", type=str, help="Run only the test in FILE")
    parser.add_argument("--continue", action="store_true",
                        dest="keepGoing", default=False,
                        help="Continue with tests after first error")

    # Parse the arguments
    args = parser.parse_args()

    scriptDir = os.path.dirname(os.path.abspath(__file__))
    return TestOpts(
        cmd=f'{scriptDir}/src/runYourProgram.py',
        baseDir=scriptDir,
        startAt=args.start_at,
        only=args.only,
        keepGoing=args.keepGoing
    )

TestStatus = Literal['passed', 'failed', 'skipped']

@dataclass
class TestResults:
    passed: list[str]
    failed: list[str]
    skipped: list[str]
    def record(self, testFail: str, result: TestStatus):
        if result == 'passed':
            self.passed.append(testFail)
        elif result == 'failed':
            self.failed.append(testFail)
        elif result == 'skipped':
            self.skipped.append(testFail)
    def finish(self):
        total = len(self.passed) + len(self.skipped) + len(self.failed)
        print()
        print(80 * '-')
        print("Tests finished")
        print()
        print(f"Total: {total}")
        print(f"Passed: {len(self.passed)}")
        print(f"Skipped: {len(self.skipped)}")
        print(f"Failed: {len(self.failed)}")
        if self.failed:
            print()
            print("Failed tests:")
            for test in self.failed:
                print(f"  {test}")
            sys.exit(1)

@dataclass(frozen=True)
class TestContext:
    opts: TestOpts
    results: TestResults

globalCtx = TestContext(
    opts=parseArgs(),
    results=TestResults(passed=[], failed=[], skipped=[])
)

def readFile(filePath: str) -> str:
    with open(filePath, "r") as f:
        return f.read()

def readFileIfExists(filePath: str) -> str:
    if not os.path.exists(filePath):
        return ''
    else:
        return readFile(filePath)

def getVersionedFile(base: str, typcheck: bool) -> str:
    v = sys.version_info
    suffixes = [f'{v.major}.{v.minor}', f'{v.major}.{v.minor}.{v.micro}']
    if not typcheck:
        l = []
        for x in suffixes:
            l.append(f'{x}-notypes')
            l.append(x)
        l.append('notypes')
        suffixes = l
    for suffix in suffixes:
        filePath = f"{base}-{suffix}"
        if os.path.exists(filePath):
            return filePath
    return base

_started = False
def shouldSkip(testFile: str, ctx: TestContext, minVersion: Optional[tuple[int, int]]) -> bool:
    """
    Determines if a test should be skipped based on the context and minimum version.
    """
    global _started
    opts = ctx.opts
    if opts.startAt:
        if _started:
            return False
        elif testFile == opts.startAt:
            _started = True
            return False
        else:
            return True
    if opts.only and testFile != opts.only:
        return True
    if minVersion:
        v = sys.version_info
        if (v.major, v.minor) < minVersion:
            return True
    return False

def checkOutputOk(testFile: str, outputType: str, expectedFile: str, actualFile: str) -> bool:
    expected = readFileIfExists(expectedFile).strip()
    actual = readFileIfExists(actualFile).strip()
    if expected != actual:
        print(f"Test {testFile} {outputType} output mismatch:")
        subprocess.run(['diff', '-u', expectedFile, actualFile])
        return False
    else:
        return True

def checkInstall(testFile: str, ctx: TestContext=globalCtx):
    if shouldSkip(testFile, ctx, None):
        ctx.results.record(testFile, 'skipped')
        return
    with tempfile.TemporaryDirectory() as d:
        def run(args: list[str]):
            cmd = [sys.executable, ctx.opts.cmd, '--quiet']
            cmd.extend(args)
            cmd.append(os.path.join(ctx.opts.baseDir, testFile))
            env = os.environ.copy()
            env['PYTHONPATH'] = d
            env['WYPP_INSTALL_DIR'] = d
            subprocess.run(
                cmd,
                check=True,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                env=env
            )
        sys.stdout.write(f'Install test {testFile} ...')
        run(['--install-mode', 'install', '--check'])
        subprocess.run(f'rm -rf {d} && mkdir {d}', shell=True, check=True)
        run(['--install-mode', 'install', '--check'])
        run(['--check', '--install-mode', 'assertInstall'])
        subprocess.run(f'rm -f {d}/untypy/__init__.py', shell=True, check=True)
        run(['--install-mode', 'install', '--check'])
        run(['--check', '--install-mode', 'assertInstall'])
        sys.stdout.write(' OK\n')

def fixOutput(filePath: str):
    """
    Fixes the output file by removing specific lines and patterns.
    """
    content = readFile(filePath)
    content = re.sub(r'at 0x[0-9a-f][0-9a-f]*>', 'at 0x00>', content, flags=re.MULTILINE)  # Remove memory addresses
    content = re.sub(r'  File "/[^"]*"', '  File ""', content, flags=re.MULTILINE)  # Remove file paths
    with open(filePath, 'w') as f:
        f.write(content)

def _check(testFile: str,
          exitCode: int,
          typecheck: bool,
          args: list[str],
          pythonPath: list[str],
          minVersion: Optional[tuple[int, int]],
          ctx: TestContext,
          what: str) -> TestStatus:
    if shouldSkip(testFile, ctx, minVersion):
        return 'skipped'

    # Prepare expected output files
    baseFile = os.path.splitext(testFile)[0]
    expectedStdoutFile = getVersionedFile(f"{baseFile}.out", typcheck=typecheck)
    expectedStderrFile = getVersionedFile(f"{baseFile}.err", typcheck=typecheck)

    # Prepare the command
    cmd = [sys.executable, ctx.opts.cmd, '--quiet']
    if not typecheck:
        cmd.append('--no-typechecking')
    cmd.append(testFile)
    cmd.extend(args)

    with tempfile.TemporaryDirectory() as d:
        actualStdoutFile = os.path.join(d, 'stdout.txt')
        actualStderrFile = os.path.join(d, 'stderr.txt')
        env = os.environ.copy()
        env['PYTHONPATH'] = os.pathsep.join([os.path.join(ctx.opts.baseDir, 'site-lib')] + pythonPath)
        with open(actualStdoutFile, 'w') as stdoutFile, \
             open(actualStderrFile, 'w') as stderrFile:
            # Run the command
            result = subprocess.run(
                cmd,
                stdout=stdoutFile,
                stderr=stderrFile,
                text=True,
                env=env
            )

        # Check exit code
        if result.returncode != exitCode:
            print(f"Test {testFile}{what} failed: Expected exit code {exitCode}, got {result.returncode}")
            return 'failed'

        fixOutput(actualStdoutFile)
        fixOutput(actualStderrFile)

        # Checkout outputs
        if not checkOutputOk(testFile + what, 'stdout', expectedStdoutFile, actualStdoutFile):
            return 'failed'
        if not checkOutputOk(testFile + what, 'stderr', expectedStderrFile, actualStderrFile):
            return 'failed'

    # If all checks pass
    print(f"{testFile}{what} OK")
    return 'passed'

def check(testFile: str,
          exitCode: int = 1,
          typecheck: bool = True,
          args: list[str] = [],
          pythonPath: list[str] = [],
          minVersion: Optional[tuple[int, int]] = None,
          ctx: TestContext = globalCtx,
          what: str = ''):
    status = _check(testFile, exitCode, typecheck, args, pythonPath, minVersion, ctx, what)
    ctx.results.record(testFile, status)
    if status == 'failed':
        if not ctx.opts.keepGoing:
            ctx.results.finish()

def checkBoth(testFile: str,
              exitCode: int = 1,
              args: list[str] = [],
              minVersion: Optional[tuple[int, int]] = None,
              ctx: TestContext = globalCtx):
    check(testFile, exitCode, typecheck=True, args=args, minVersion=minVersion, ctx=ctx, what=' (typecheck)')
    check(testFile, exitCode, typecheck=False, args=args, minVersion=minVersion, ctx=ctx, what=' (no typecheck)')

checkInstall('test-data/fileWithImport.py')
checkInstall('test-data/fileWithoutImport.py')
checkInstall('test-data/fileWithBothImports.py')
checkInstall('test-data/fileWithRecursiveTypes.py')
checkBoth('test-data/testTraceback.py')
checkBoth('test-data/testTraceback2.py')
checkBoth('test-data/testTraceback3.py')
checkBoth('test-data/testArgs.py', exitCode=0, args=['ARG_1', 'ARG_2'])
checkBoth('test-data/printModuleName.py', exitCode=0)
checkBoth('test-data/printModuleNameImport.py', exitCode=0)
checkBoth('test-data/testTypes1.py')
checkBoth('test-data/testIndexError.py')
checkBoth('test-data/testWrapperError.py')
checkBoth('test-data/testCheckFail.py', exitCode=0)
check('test-data/testTypes2.py', exitCode=1)
check('test-data/testTypes2.py', exitCode=0, typecheck=False)
check('test-data/testABCMeta.py')
check('test-data/testClassHierarchy.py', exitCode=0)
check('test-data/testTypesCollections1.py')
check('test-data/testTypesCollections2.py')
check('test-data/testTypesCollections3.py')
check('test-data/testTypesCollections4.py')
check('test-data/testTypesProtos1.py')
check('test-data/testTypesProtos2.py')
check('test-data/testTypesProtos3.py')
check('test-data/testTypesProtos4.py')
check('test-data/testTypesSubclassing1.py')
check('test-data/testTypesHigherOrderFuns.py')
check('test-data/testTypesHigherOrderFuns2.py', exitCode=0)
check('test-data/testTypesHigherOrderFuns3.py')
check('test-data/testTypesHigherOrderFuns4.py', exitCode=0)
check('test-data/testTypesHigherOrderFuns5.py', exitCode=0)
check('test-data/testTypesRecordInheritance.py')
check('test-data/testRecordSetTypes.py')
check('test-data/testRecordSetTypeForwardRef.py')
check('test-data/testForwardRef.py', exitCode=0)
check('test-data/testForwardRef1.py', exitCode=0)
check('test-data/testForwardRef2.py')
check('test-data/testForwardRef3.py', exitCode=0)
check('test-data/testForwardRef4.py')
check('test-data/testForwardRef5.py')
check('test-data/testForwardRef6.py', exitCode=0)
check('test-data/testHintParentheses1.py')
check('test-data/testHintParentheses2.py')
check('test-data/testHintParentheses3.py')
check('test-data/testTypesReturn.py')
check('test-data/testMissingReturn.py')
check('test-data/testTypesSequence1.py')
check('test-data/testTypesSequence2.py')
check('test-data/testTypesTuple1.py')
check('test-data/wrong-caused-by.py')
check('test-data/declared-at-missing.py')
check('test-data/testTypesSet1.py')
check('test-data/testTypesSet2.py')
check('test-data/testTypesSet3.py')
check('test-data/testTypesSet4.py')
check('test-data/testTypesDict1.py')
check('test-data/testTypesDict2.py')
check('test-data/testTypesDict3.py')
check('test-data/testTypesDict4.py')
check('test-data/testIterableImplicitAny.py')
check('test-data/testDoubleWrappingDicts.py', exitCode=0)
check('test-data/testClassRecursion.py', exitCode=0)
check('test-data/testWrongNumOfArguments.py')
check('test-data/testWrongNumOfArguments2.py')
check('test-data/testLiteralInstanceOf.py', exitCode=0)
check('test-data/testWrongKeywordArg.py')
check('test-data/testWrongKeywordArg2.py')
check('test-data/testComplex.py', exitCode=0)
check('test-data/testUnionLiteral.py', exitCode=0)
check('test-data/testCheck.py', exitCode=0)
check('test-data/testNameErrorBug.py', exitCode=0)
check('test-data/testOriginalTypeNames.py', exitCode=0)
check('test-data/testDeepEqBug.py', exitCode=0)
check('test-data/testLockFactory.py')
check('test-data/testLockFactory2.py')
check('test-data/testGetSource.py')
check('test-data/testDict.py', exitCode=0)
check('test-data/testFunEq.py', exitCode=0)
check('test-data/testBugSliceIndices.py', exitCode=0)
check('test-data/testABC.py', exitCode=0)
check('test-data/testTypesWrapperEq.py', exitCode=0)
check('test-data/testTypesProtos5.py', exitCode=0)
check('test-data/testTypesProtos6.py')
check('test-data/testTypesProtos7.py')
check('test-data/testTypesProtos8.py')
check('test-data/testTypesProtos9.py')
check('test-data/testIterable1.py', exitCode=0)
check('test-data/testIterable2.py', exitCode=0)
check('test-data/testIterable3.py', exitCode=0)
check('test-data/testIterable4.py', exitCode=0)
check('test-data/testIterable5.py', exitCode=0)
check('test-data/testIterable6.py', exitCode=0)
check('test-data/testIterable7.py')
check('test-data/testIterator.py', exitCode=0)
check('test-data/testIterator2.py', exitCode=0)
check('test-data/testIterator3.py', exitCode=0)
check('test-data/testIterator4.py', exitCode=0)
check('test-data/testConcat.py', exitCode=0)
check('test-data/testCopy.py', exitCode=0)
check('test-data/testHof.py', exitCode=0)
check('test-data/testIndexSeq.py', exitCode=0)
check('test-data/testWrap.py', exitCode=0)
check('test-data/testWrap2.py', exitCode=0)
check('test-data/testTodo.py')
check('test-data/testImpossible.py')
check('test-data/testInvalidLiteral.py')
check('test-data/admin.py', exitCode=0)
check('test-data/modules/A/main.py', args=['--extra-dir', 'test-data/modules/B'],
      pythonPath=['test-data/modules/B'])
check('test-data/testUnion.py', exitCode=0)
check('test-data/testUnion2.py', exitCode=0)
check('test-data/testUnion3.py', exitCode=0)
check('test-data/testLiteral1.py')
check('test-data/testForwardTypeInRecord.py', exitCode=0)
check('test-data/testForwardTypeInRecord2.py', exitCode=0)
check('test-data/testUnionOfUnion.py', exitCode=0)
check('test-data/testRecordTypes.py')
#check('test-data/testDisappearingObject_01.py', exitCode=0)
#check('test-data/testDisappearingObject_02.py', exitCode=0)
#check('test-data/testDisappearingObject_03.py', exitCode=0)
checkBoth('test-data/testTypeKeyword.py', exitCode=0, minVersion=(3,12))

globalCtx.results.finish()
