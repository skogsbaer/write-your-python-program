import sys
import doctest
from myLogging import *

# We use our own DocTestParser to replace exception names in stacktraces


def rewriteLines(lines: list[str]):
    """
    Each line has exactly one of the following four kinds:
    - COMMENT: if it starts with '#' (leading whitespace stripped)
    - PROMPT: if it starts with '>>>' (leading whitespace stripped)
    - EMPTY: if it contains only whitespace
    - OUTPUT: otherwise

    rewriteLines replaces every EMPTY lines with '<BLANKLINE>', provided
    the first non-EMPTY line before the line has kind PROMPT OR OUTPUT
    and the next non-EMPTY line after the line has kind OUTPUT.
    """

    def get_line_kind(line: str) -> str:
        stripped = line.lstrip()
        if not stripped:
            return 'EMPTY'
        elif stripped.startswith('#'):
            return 'COMMENT'
        elif stripped.startswith('>>>'):
            return 'PROMPT'
        else:
            return 'OUTPUT'

    def find_prev_non_empty(idx: int) -> tuple[int, str]:
        """Find the first non-EMPTY line before idx. Returns (index, kind)"""
        for i in range(idx - 1, -1, -1):
            kind = get_line_kind(lines[i])
            if kind != 'EMPTY':
                return i, kind
        return -1, 'NONE'

    def find_next_non_empty(idx: int) -> tuple[int, str]:
        """Find the first non-EMPTY line after idx. Returns (index, kind)"""
        for i in range(idx + 1, len(lines)):
            kind = get_line_kind(lines[i])
            if kind != 'EMPTY':
                return i, kind
        return -1, 'NONE'

    # Process each line
    for i in range(len(lines)):
        if get_line_kind(lines[i]) == 'EMPTY':
            # Check conditions for replacement
            prev_idx, prev_kind = find_prev_non_empty(i)
            next_idx, next_kind = find_next_non_empty(i)

            # Replace if previous is PROMPT or OUTPUT and next is OUTPUT
            if prev_kind in ['PROMPT', 'OUTPUT'] and next_kind == 'OUTPUT':
                lines[i] = '<BLANKLINE>'


class MyDocTestParser(doctest.DocTestParser):
    def get_examples(self, string, name='<string>'):
        """
        The string is the docstring from the file which we want to test.
        """
        prefs = {'WyppTypeError: ': 'errors.WyppTypeError: ',
                 'WyppNameError: ': 'errors.WyppNameError: ',
                 'WyppAttributeError: ': 'errors.WyppAttributeError: '}
        lines = []
        for l in string.split('\n'):
            for pref,repl in prefs.items():
                if l.startswith(pref):
                    l = repl + l
            lines.append(l)
        rewriteLines(lines)
        string = '\n'.join(lines)
        x = super().get_examples(string, name)
        return x

def testRepl(repl: str, defs: dict) -> tuple[int, int]:
    doctestOptions = doctest.NORMALIZE_WHITESPACE | doctest.ELLIPSIS
    (failures, tests) = doctest.testfile(repl, globs=defs, module_relative=False,
                                         optionflags=doctestOptions, parser=MyDocTestParser())
    if failures == 0:
        if tests == 0:
            print(f'No tests in {repl}')
        else:
            print(f'All {tests} tests in {repl} succeeded')
    else:
        print(f'ERROR: {failures} out of {tests} in {repl} failed')
    return (failures, tests)

def testRepls(repls: list[str], defs: dict):
    totalFailures = 0
    totalTests = 0
    for r in repls:
        (failures, tests) = testRepl(r, defs)
        totalFailures += failures
        totalTests += tests

    if totalFailures == 0:
        if totalTests == 0:
            print('ERROR: No tests found at all!')
            sys.exit(1)
        else:
            print(f'All {totalTests} tests succeeded. Great!')
    else:
        print(f'ERROR: {failures} out of {tests} failed')
        sys.exit(1)
