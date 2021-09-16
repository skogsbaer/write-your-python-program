import shell
import unittest
import os

def runInteractive(path, input, tycheck=True):
    flags = ['--interactive', '--quiet', '--no-clear']
    if not tycheck:
        flags.append('--no-typechecking')
    cmd = f'python3 src/runYourProgram.py {" ".join(flags)} {path}'
    res = shell.run(cmd, input=input, captureStdout=True, stderrToStdout=True, onError='raise')
    return res.stdout

def stripTrailingWs(s):
    s = s.strip()
    return '\n'.join([l.rstrip() for l in s.split('\n')])

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

