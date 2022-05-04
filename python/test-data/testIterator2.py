from wypp import *

def myRange(n: int) -> Iterator:
    i = 0
    while i < n:
        yield i
        i = i + 1

def myList(iter: Iterator) -> list:
    result = []
    try:
        while True:
            x = next(iter)
            result.append(x)
    except StopIteration:
        pass
    return result

print(myList(myRange(5)))
