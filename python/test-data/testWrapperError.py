from wypp import *

def foo(f: Callable[[int], int]) -> int:
    return f(42)

def bar(i: int) -> int:
    raise ValueError(str(i))

foo(bar)
