from typing import Iterable

def myRange(n: int) -> Iterable[int]:
    i = 0
    while i < n:
        yield i
        i = i + 1


print(list(myRange(5)))
