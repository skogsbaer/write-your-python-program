from wypp import *
# See https://github.com/skogsbaer/write-your-python-program/issues/61

# Uses types wrapped in strings
def foo(a: 'int', b: 'dict[1, list(int)]') -> int:
    return len(b)

foo(1, {})
