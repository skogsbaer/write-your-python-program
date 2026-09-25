# WYPP_TEST_CONFIG: {"typecheck": "both"}
# from __future__ import annotations
# Leave the comment, it's needed for tests with python versions <= 3.13

from wypp import *

type T = Union[str, int]

def foo(a: T) -> str:
    if isinstance(a, str):
        return a
    else:
        return "foo"

print(foo("yuck"))
