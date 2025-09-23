import shell
import unittest
import os

def runWithFlags(path, flags, onError, input=''):
    cmd = f'python3 src/runYourProgram.py {" ".join(flags)} {path}'
    res = shell.run(cmd, input=input, captureStdout=True, stderrToStdout=True, onError=onError,
                    env={'PYTHONPATH': f'./site-lib'})
    return res

def run(path, input='', tycheck=True, ecode=0):
    flags = ['--quiet', '--no-clear']
    if not tycheck:
        flags.append('--no-typechecking')
    res = runWithFlags(path, flags, input=input, onError='ignore')
    if res.exitcode != ecode:
        raise Exception(f'Unexpected exit code: {res.exitcode} (expected {ecode})')
    return res.stdout.strip()

def runInteractive(path, input='', tycheck=True):
    flags = ['--interactive', '--quiet', '--no-clear']
    if not tycheck:
        flags.append('--no-typechecking')
    res = runWithFlags(path, flags, input=input, onError='raise')
    lines = res.stdout.strip().split('>>>')[1:-1]
    return [l.strip() for l in lines]

def stripTrailingWs(s):
    s = s.strip()
    return '\n'.join([l.rstrip() for l in s.split('\n')])

LOG_FILE = shell.mkTempFile(prefix="wypp-tests", suffix=".log", deleteAtExit='ifSuccess')
print(f'Output of integration tests goes to {LOG_FILE}')
LOG_REDIR = f'>> {LOG_FILE} 2>&1'

class StudentSubmissionTests(unittest.TestCase):
    def check(self, file, testFile, ecode, tycheck=True):
        flags = ['--check']
        if not tycheck:
            flags.append('--no-typechecking')
        cmd = f"python3 src/runYourProgram.py {' '.join(flags)} --test-file {testFile} {file} {LOG_REDIR}"
        res = shell.run(cmd, onError='ignore')
        self.assertEqual(ecode, res.exitcode)

    def test_goodSubmission(self):
        self.check("integration-test-data/student-submission.py", "integration-test-data/student-submission-tests.py", 0)
        self.check("integration-test-data/student-submission.py", "integration-test-data/student-submission-tests.py", 0,
                   tycheck=False)

    def test_badSubmission(self):
        self.check("integration-test-data/student-submission-bad.py",
                   "integration-test-data/student-submission-tests.py", 1)
        self.check("integration-test-data/student-submission-bad.py",
                   "integration-test-data/student-submission-tests.py", 1, tycheck=False)

    def test_submissionWithTypeErrors(self):
        self.check("integration-test-data/student-submission-tyerror.py",
                   "integration-test-data/student-submission-tests.py", 1)
        self.check("integration-test-data/student-submission-tyerror.py",
                   "integration-test-data/student-submission-tests.py", 0, tycheck=False)
        self.check("integration-test-data/student-submission.py",
                   "integration-test-data/student-submission-tests-tyerror.py", 1)
        self.check("integration-test-data/student-submission.py",
                   "integration-test-data/student-submission-tests-tyerror.py", 0, tycheck=False)

class InteractiveTests(unittest.TestCase):

    def test_scopeBugPeter(self):
        out = runInteractive('integration-test-data/scope-bug-peter.py', 'local_test()\nprint(spam)')
        self.assertIn('IT WORKS', out)

    def test_types1(self):
        out = runInteractive('integration-test-data/testTypesInteractive.py', 'inc(3)')
        self.assertEqual(['4'], out)

    def test_types2(self):
        out = runInteractive('integration-test-data/testTypesInteractive.py', 'inc("3")')[0]
        self.assertIn('The call of function `inc` expects value of type `int` as 1st argument', out)

    def test_typesInImportedModule1(self):
        out = run('integration-test-data/testTypes3.py', ecode=1)
        self.assertIn('The call of function `inc` expects value of type `int` as 1st argument', out)

    def test_typesInImportedModule2(self):
        out = run('integration-test-data/testTypes3.py', tycheck=False)
        self.assertEqual('END', out)

class ReplTesterTests(unittest.TestCase):

    def test_replTester(self):
        d = shell.pwd()
        cmd = f'python3 {d}/src/replTester.py {d}/integration-test-data/repl-test-lib.py --repl {d}/integration-test-data/repl-test-checks.py'
        res = shell.run(cmd, captureStdout=True, onError='die', cwd='/tmp')
        self.assertIn('All 1 tests succeeded. Great!', res.stdout)
