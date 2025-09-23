# WYPP_TEST_CONFIG: {"typecheck": "both"}
from __future__ import annotations
from wypp import *

type T = Union[str, int]

def foo(a: T) -> str:
    if isinstance(a, str):
        return a
    else:
        return "foo"

print(foo("yuck"))
