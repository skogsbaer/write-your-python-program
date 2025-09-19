from typing import *
import os

P = ParamSpec("P")
T = TypeVar("T")

# The name of this function is magical
def _call_with_frames_removed(
    f: Callable[P, T], *args: P.args, **kwargs: P.kwargs
) -> T:
    return f(*args, **kwargs)

def getEnv(name, conv, default):
    s = os.getenv(name)
    if s is None:
        return default
    try:
        return conv(s)
    except:
        return default

def dropWhile(l: list, f: Callable[[Any], bool]) -> list:
    if not l:
        return l
    for i in range(len(l)):
        if not f(l[i]):
            break
    return l[i:]

def isUnderTest() -> bool:
    x = os.getenv('WYPP_UNDER_TEST')
    return x == 'True'
