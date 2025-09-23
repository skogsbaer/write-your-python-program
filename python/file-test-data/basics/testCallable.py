from typing import Callable

def foo(f: Callable[[int, bool], str]) -> int:
    return 1

foo(42)
