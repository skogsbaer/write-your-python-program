import shell
import unittest
import os

def run(path, input='', tycheck=True, ecode=0):
    flags = ['--quiet', '--no-clear']
    if not tycheck:
        flags.append('--no-typechecking')
    cmd = f'python3 src/runYourProgram.py {" ".join(flags)} {path}'
    res = shell.run(cmd, captureStdout=True, stderrToStdout=True, onError='ignore')
    if res.exitcode != ecode:
        raise Exception(f'Unexpected exit code: {res.exitcode} (expected {ecode})')
    return res.stdout

def runInteractive(path, input='', tycheck=True):
    flags = ['--interactive', '--quiet', '--no-clear']
    if not tycheck:
        flags.append('--no-typechecking')
    cmd = f'python3 src/runYourProgram.py {" ".join(flags)} {path}'
    res = shell.run(cmd, input=input, captureStdout=True, stderrToStdout=True, onError='raise')
    return res.stdout

def stripTrailingWs(s):
    s = s.strip()
    return '\n'.join([l.rstrip() for l in s.split('\n')])

LOG_FILE = shell.mkTempFile(prefix="wypp-tests", suffix=".log", deleteAtExit='ifSuccess')
print(f'Output of integration tests goes to {LOG_FILE}')
LOG_REDIR = f'> {LOG_FILE} 2>&1'

class StudentSubmissionTests(unittest.TestCase):
    def check(self, file, testFile, ecode, tycheck=True):
        flags = ['--check']
        if not tycheck:
            flags.append('--no-typechecking')
        cmd = f"python3 src/runYourProgram.py {' '.join(flags)} --test-file {testFile} {file} {LOG_REDIR}"
        print(cmd)
        res = shell.run(cmd, onError='ignore')
        self.assertEqual(ecode, res.exitcode)

    def test_goodSubmission(self):
        self.check("file-tests/student-submission.py", "file-tests/student-submission-tests.py", 0)
        self.check("file-tests/student-submission.py", "file-tests/student-submission-tests.py", 0,
                   tycheck=False)

    def test_badSubmission(self):
        self.check("file-tests/student-submission-bad.py",
                   "file-tests/student-submission-tests.py", 1)
        self.check("file-tests/student-submission-bad.py",
                   "file-tests/student-submission-tests.py", 1, tycheck=False)

    def test_submissionWithTypeErrors(self):
        self.check("file-tests/student-submission-tyerror.py",
                   "file-tests/student-submission-tests.py", 1)
        self.check("file-tests/student-submission-tyerror.py",
                   "file-tests/student-submission-tests.py", 0, tycheck=False)
        self.check("file-tests/student-submission.py",
                   "file-tests/student-submission-tests-tyerror.py", 1)
        self.check("file-tests/student-submission.py",
                   "file-tests/student-submission-tests-tyerror.py", 0, tycheck=False)

class InteractiveTests(unittest.TestCase):

    def test_scopeBugPeter(self):
        out = runInteractive('file-tests/scope-bug-peter.py', 'local_test(); print(spam)')
        self.assertIn('IT WORKS', out)

    def test_types1(self):
        out = runInteractive('file-tests/testTypesInteractive.py', 'inc(3)')
        self.assertIn('>>> 4', out)

    def test_types2(self):
        out = runInteractive('file-tests/testTypesInteractive.py', 'inc("3")')
        expected = """given: '3'
expected: int
          ^^^

inside of inc(x: int) -> int
                 ^^^
declared at:
file-tests/testTypesInteractive.py:1
  1 | def inc(x: int) -> int:
  2 |     return x + 1"""
        self.assertIn(expected, stripTrailingWs(out))

    def test_types3(self):
        out = runInteractive('file-tests/testTypesInteractive.py',
                             'def f(x: int) -> int: return x\n\nf("x")')
        self.assertIn('expected: int', out)

    def test_types4(self):
        out = runInteractive('file-tests/testTypesInteractive.py',
                             'def f(x: int) -> int: return x\n\nf(3)')
        self.assertIn('>>> 3', out)

    def test_types5(self):
        out = runInteractive('file-tests/testTypesInteractive.py',
                             'def f(x: int) -> int: return x\n\nf("x")',
                              tycheck=False)
        self.assertIn(">>> 'x'", out)

    def test_typesInImportedModule1(self):
        out = run('file-tests/testTypes3.py', ecode=1)
        self.assertIn('\nexpected: int', out)

    def test_typesInImportedModule2(self):
        out = run('file-tests/testTypes3.py', tycheck=False)
        self.assertIn('END', out)
