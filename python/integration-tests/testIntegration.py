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

class TypeTests(unittest.TestCase):
    def test_enumOk(self):
        out = runInteractive('test-data/typeEnums.py', 'colorToNumber("red")')
        self.assertEqual(['0'], out)

    def test_enumTypeError(self):
        out = runInteractive('test-data/typeEnums.py', 'colorToNumber(1)')[0]
        self.assertIn("expected: value of type Literal['red', 'yellow', 'green']", out)

    def test_recordOk(self):
        rec = 'test-data/typeRecords.py'
        out1 = runInteractive(rec, 'Person("stefan", 42)')
        self.assertEqual(["Person(name='stefan', age=42)"], out1)
        out2 = runInteractive(rec, 'incAge(Person("stefan", 42))')
        self.assertEqual(["Person(name='stefan', age=43)"], out2)

    def test_recordFail1(self):
        rec = 'test-data/typeRecords.py'
        out = runInteractive(rec, 'Person("stefan", 42.3)')
        expected = """untypy.error.UntypyTypeError
given:    42.3
expected: value of type int

context: Person(name: str, age: int) -> Self
                                ^^^
declared at: test-data/typeRecords.py:3
  3 | @record
  4 | class Person:
  5 |     name: str
  6 |     age: int

caused by: <console>:1"""
        self.assertEqual(expected, '\n'.join(out))

    def test_recordFail2(self):
        rec = 'test-data/typeRecords.py'
        out = runInteractive(rec, 'mutableIncAge(Person("stefan", 42))')[0]
        self.assertIn('expected: value of type MutablePerson', out)

    def test_recordMutableOk(self):
        rec = 'test-data/typeRecords.py'
        out1 = runInteractive(rec, 'MutablePerson("stefan", 42)')
        self.assertEqual(["MutablePerson(name='stefan', age=42)"], out1)
        out2 = runInteractive(rec, 'p = MutablePerson("stefan", 42)\nmutableIncAge(p)\np')
        self.assertEqual(['', '', "MutablePerson(name='stefan', age=43)"], out2)

    def test_mutableRecordFail1(self):
        rec = 'test-data/typeRecords.py'
        out = runInteractive(rec, 'MutablePerson("stefan", 42.3)')[0]
        self.assertIn('expected: value of type int', out)

    def test_mutableRecordFail2(self):
        rec = 'test-data/typeRecords.py'
        out = runInteractive(rec, 'incAge(MutablePerson("stefan", 42))')[0]
        self.assertIn('expected: value of type Person', out)

    @unittest.skip
    def test_mutableRecordFail3(self):
        rec = 'test-data/typeRecords.py'
        out = runInteractive(rec, 'p = MutablePerson("stefan", 42)\np.age = 42.4')
        self.assertIn('expected: value of type int', out)

    def test_union(self):
        out = runInteractive('test-data/typeUnion.py', """formatAnimal(myCat)
formatAnimal(myParrot)
formatAnimal(None)
        """)
        self.assertEqual("'Cat Pumpernickel'", out[0])
        self.assertEqual("\"Parrot Mike says: Let's go to the punkrock show\"", out[1])
        self.assertIn('given:    None\nexpected: value of type Union[Cat, Parrot]', out[2])

class StudentSubmissionTests(unittest.TestCase):
    def check(self, file, testFile, ecode, tycheck=True):
        flags = ['--check']
        if not tycheck:
            flags.append('--no-typechecking')
        cmd = f"python3 src/runYourProgram.py {' '.join(flags)} --test-file {testFile} {file} {LOG_REDIR}"
        res = shell.run(cmd, onError='ignore')
        self.assertEqual(ecode, res.exitcode)

    def test_goodSubmission(self):
        self.check("test-data/student-submission.py", "test-data/student-submission-tests.py", 0)
        self.check("test-data/student-submission.py", "test-data/student-submission-tests.py", 0,
                   tycheck=False)

    def test_badSubmission(self):
        self.check("test-data/student-submission-bad.py",
                   "test-data/student-submission-tests.py", 1)
        self.check("test-data/student-submission-bad.py",
                   "test-data/student-submission-tests.py", 1, tycheck=False)

    def test_submissionWithTypeErrors(self):
        self.check("test-data/student-submission-tyerror.py",
                   "test-data/student-submission-tests.py", 1)
        self.check("test-data/student-submission-tyerror.py",
                   "test-data/student-submission-tests.py", 0, tycheck=False)
        self.check("test-data/student-submission.py",
                   "test-data/student-submission-tests-tyerror.py", 1)
        self.check("test-data/student-submission.py",
                   "test-data/student-submission-tests-tyerror.py", 0, tycheck=False)

class InteractiveTests(unittest.TestCase):

    def test_scopeBugPeter(self):
        out = runInteractive('test-data/scope-bug-peter.py', 'local_test()\nprint(spam)')
        self.assertIn('IT WORKS', out)

    def test_types1(self):
        out = runInteractive('test-data/testTypesInteractive.py', 'inc(3)')
        self.assertEqual(['4'], out)

    def test_types2(self):
        out = runInteractive('test-data/testTypesInteractive.py', 'inc("3")')[0]
        expected = """untypy.error.UntypyTypeError
given:    '3'
expected: value of type int

context: inc(x: int) -> int
                ^^^
declared at: test-data/testTypesInteractive.py:1
  1 | def inc(x: int) -> int:
  2 |     return x + 1

caused by: <console>:1"""
        self.assertEqual(expected, out)

    def test_types3(self):
        out = runInteractive('test-data/testTypesInteractive.py',
                             'def f(x: int) -> int: return x\n\nf("x")')[1]
        self.assertIn('expected: value of type int', out)

    def test_types4(self):
        out = runInteractive('test-data/testTypesInteractive.py',
                             'def f(x: int) -> int: return x\n\nf(3)')
        self.assertEqual(['...', '3'], out)

    def test_types5(self):
        out = runInteractive('test-data/testTypesInteractive.py',
                             'def f(x: int) -> int: return x\n\nf("x")',
                              tycheck=False)
        self.assertEqual(['...', "'x'"], out)

    def test_typesInImportedModule1(self):
        out = run('test-data/testTypes3.py', ecode=1)
        self.assertIn('expected: value of type int', out)

    def test_typesInImportedModule2(self):
        out = run('test-data/testTypes3.py', tycheck=False)
        self.assertEqual('END', out)

class ReplTesterTests(unittest.TestCase):

    def test_replTester(self):
        d = shell.pwd()
        cmd = f'python3 {d}/src/replTester.py {d}/test-data/repl-test-lib.py --repl {d}/test-data/repl-test-checks.py'
        res = shell.run(cmd, captureStdout=True, onError='die', cwd='/tmp')
        self.assertIn('All 1 tests succeded. Great!', res.stdout)
