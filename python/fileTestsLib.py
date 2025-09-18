from dataclasses import dataclass
import os
from typing import *
import sys
import subprocess
import tempfile
import argparse
import re
import shutil

@dataclass(frozen=True)
class TestOpts:
    cmd: str
    baseDir: str
    startAt: Optional[str]
    only: Optional[str]
    keepGoing: bool
    record: Optional[str]

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
    parser.add_argument('--record', dest='record',
                        type=str, help='Record the expected output for the given file.')

    # Parse the arguments
    args = parser.parse_args()

    scriptDir = os.path.dirname(os.path.abspath(__file__))
    return TestOpts(
        cmd=f'{scriptDir}/src/runYourProgram.py',
        baseDir=scriptDir,
        startAt=args.start_at,
        only=args.only,
        keepGoing=args.keepGoing,
        record=args.record
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

def readAnswer(question: str, allowed: list[str]) -> str:
    while True:
        answer = input(question)
        if answer in allowed:
            return answer
        print(f'Answer must be one of {allowed}. Try again!')

def _runTest(testFile: str,
             exitCode: int,
             typecheck: bool,
             args: list[str],
             actualStdoutFile: str,
             actualStderrFile: str,
             pythonPath: list[str],
             what: str,
             ctx: TestContext) -> Literal['failed'] | None:
    # Prepare the command
    cmd = [sys.executable, ctx.opts.cmd, '--quiet']
    if not typecheck:
        cmd.append('--no-typechecking')
    cmd.append(testFile)
    cmd.append('--lang')
    cmd.append('de')
    cmd.extend(args)
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

def _check(testFile: str,
          exitCode: int,
          typecheck: bool,
          args: list[str],
          pythonPath: list[str],
          minVersion: Optional[tuple[int, int]],
          checkOutputs: bool,
          ctx: TestContext,
          what: str) -> TestStatus:
    if shouldSkip(testFile, ctx, minVersion):
        return 'skipped'

    # Prepare expected output files
    baseFile = os.path.splitext(testFile)[0]
    expectedStdoutFile = getVersionedFile(f"{baseFile}.out", typcheck=typecheck)
    expectedStderrFile = getVersionedFile(f"{baseFile}.err", typcheck=typecheck)

    with tempfile.TemporaryDirectory() as d:
        actualStdoutFile = os.path.join(d, 'stdout.txt')
        actualStderrFile = os.path.join(d, 'stderr.txt')
        _runTest(testFile, exitCode, typecheck, args, actualStdoutFile, actualStderrFile,
                 pythonPath, what, ctx)

        fixOutput(actualStdoutFile)
        fixOutput(actualStderrFile)

        # Checkout outputs
        if checkOutputs:
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
          checkOutputs: bool = True,
          ctx: TestContext = globalCtx,
          what: str = ''):
    status = _check(testFile, exitCode, typecheck, args, pythonPath, minVersion, checkOutputs, ctx, what)
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

def checkBasic(testFile: str, ctx: TestContext = globalCtx):
    if testFile.endswith('_ok.py'):
        expectedExitCode = 0
    else:
        expectedExitCode = 1
    check(testFile, exitCode=expectedExitCode, checkOutputs=False, ctx=ctx)

def record(testFile: str):
    """
    Runs filePath and stores the output in the expected files.
    """
    baseFile = os.path.splitext(testFile)[0]
    exitCode = 0 if testFile.endswith('_ok.py') else 1
    typecheck = True
    args = []
    pythonPath = []
    what = ''
    ctx = globalCtx
    def display(filename: str, where: str):
        x = readFile(filename)
        if x:
            print(f'--- Output on {where} ---')
            print(x)
            print('------------------------')
        else:
            print(f'No output on {where}')
    with tempfile.TemporaryDirectory() as d:
        actualStdoutFile = os.path.join(d, 'stdout.txt')
        actualStderrFile = os.path.join(d, 'stderr.txt')
        result = _runTest(testFile, exitCode, typecheck, args, actualStdoutFile, actualStderrFile,
                          pythonPath, what, ctx)
        if result is not None:
            print(f'Test did not produce the expected exit code. Aborting')
            sys.exit(1)
        display(actualStdoutFile, 'stdout')
        display(actualStderrFile, 'stderr')
        answer = readAnswer('Store the output as the new expected output? (y/n) ', ['y', 'n'])
        if answer:
            fixOutput(actualStdoutFile)
            fixOutput(actualStderrFile)
            expectedStdoutFile = getVersionedFile(f"{baseFile}.out", typcheck=typecheck)
            expectedStderrFile = getVersionedFile(f"{baseFile}.err", typcheck=typecheck)
            shutil.copy(actualStdoutFile, expectedStdoutFile)
            shutil.copy(actualStderrFile, expectedStderrFile)
            print(f'Stored expected output in {expectedStdoutFile} and {expectedStderrFile}')
        else:
            print('Aborting')

if globalCtx.opts.record is not None:
    record(globalCtx.opts.record)
    sys.exit(0)
