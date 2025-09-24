from typing import *
import os
import sys
from contextlib import contextmanager

P = ParamSpec("P")
T = TypeVar("T")

# The name of this function is magical. All stack frames that appear
# nested within this function are removed from tracebacks.
def _call_with_frames_removed(
    f: Callable[P, T], *args: P.args, **kwargs: P.kwargs
) -> T:
    return f(*args, **kwargs)

# The name of this function is magical. The next stack frame that appears
# nested within this function is removed from tracebacks.
def _call_with_next_frame_removed(
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
    else:
        # All elements satisfied the condition, return empty list
        return []
    return l[i:]

def split(l: list, f: Callable[[Any], bool]) -> tuple[list, list]:
    """
    span, applied to a list l and a predicate f, returns a tuple where first element is the
    longest prefix (possibly empty) of l of elements that satisfy f and second element
    is the remainder of the list.
    """
    inFirst = True
    first = []
    second = []
    for x in l:
        if inFirst:
            if f(x):
                first.append(x)
            else:
                inFirst = False
                second.append(x)
        else:
            second.append(x)
    return (first, second)


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


def die(ecode: str | int | None = 1):
    if isinstance(ecode, str):
        sys.stderr.write(ecode)
        sys.stderr.write('\n')
        ecode = 1
    elif ecode == None:
        ecode = 0
    if sys.flags.interactive:
        os._exit(ecode)
    else:
        sys.exit(ecode)

def readFile(path):
    try:
        with open(path, encoding='utf-8') as f:
            return f.read()
    except UnicodeDecodeError:
        with open(path) as f:
            return f.read()
