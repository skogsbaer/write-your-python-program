from wypp import *

def myRange(n: int) -> Iterator[int]:
    i = 0
    while i < n:
        yield i
        i = i + 1

print(next(myRange(5)))
