from typing import *
import os
from contextlib import contextmanager

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

@contextmanager
def underTest(value: bool = True):
    """Context manager to temporarily set WYPP_UNDER_TEST environment variable."""
    oldValue = os.getenv('WYPP_UNDER_TEST')
    os.environ['WYPP_UNDER_TEST'] = str(value)
    try:
        yield
    finally:
        if oldValue is None:
            # Remove the environment variable if it didn't exist before
            os.environ.pop('WYPP_UNDER_TEST', None)
        else:
            # Restore the original value
            os.environ['WYPP_UNDER_TEST'] = oldValue
