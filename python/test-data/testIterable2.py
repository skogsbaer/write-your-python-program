from wypp import *

def myRange(n: int) -> Iterable[int]:
    i = 0
    while i < n:
        yield i
        i = i + 1

r = myRange(5)
print(next(r))
