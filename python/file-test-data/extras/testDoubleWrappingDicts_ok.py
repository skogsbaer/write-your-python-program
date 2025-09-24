from wypp import *
# See https://github.com/skogsbaer/write-your-python-program/issues/68

def foo(d: dict[str, int], i: int) -> int:
    if i > 0:
        return foo(d, i - 1)
    else:
        return d['x']

n = 10
print(foo({'x': 42}, n))