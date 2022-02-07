from wypp import *
# See: https://github.com/skogsbaer/write-your-python-program/issues/76

def myRange(n: int) -> Iterable[int]:
    i = 0
    while i < n:
        yield i
        i = i + 1

print(type(myRange(5)))