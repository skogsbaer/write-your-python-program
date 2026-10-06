from contextlib import contextmanager
import inspect
import os
import sys
from typing import *

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

# Starting with python 3.14, annotations are evaluated lazily (PEP 649). Evaluating them
# too early (e.g. when decorating a record whose fields refer to a type defined later)
# raises a NameError. We therefore fetch annotations in FORWARDREF format: names not yet defined
# become ForwardRef objects, which are resolved when the check is performed.
#
# Early 3.14 releases (e.g. 3.14.0) have a bug: if evaluating an annotation raises an error
# other than NameError (e.g. for the invalid type Optional[int, str]), the FORWARDREF format
# yields a ForwardRef containing internal placeholder names such as __annotationlib_name_1__.
# In this case, we use the annotation in STRING format instead, just as with
# `from __future__ import annotations`.
def _isBrokenForwardRef(x: Any) -> bool:
    import annotationlib
    return isinstance(x, annotationlib.ForwardRef) and \
        '__annotationlib_name_' in x.__forward_arg__

def getSignature(f: Callable) -> inspect.Signature:
    if sys.version_info >= (3, 14):
        import annotationlib
        sig = inspect.signature(f, annotation_format=annotationlib.Format.FORWARDREF)
        params = list(sig.parameters.values())
        if not any(_isBrokenForwardRef(x) for x in
                   [sig.return_annotation] + [p.annotation for p in params]):
            return sig
        strSig = inspect.signature(f, annotation_format=annotationlib.Format.STRING)
        newParams = [strSig.parameters[p.name] if _isBrokenForwardRef(p.annotation) else p
                     for p in params]
        retAnn = strSig.return_annotation if _isBrokenForwardRef(sig.return_annotation) \
            else sig.return_annotation
        return sig.replace(parameters=newParams, return_annotation=retAnn)
    else:
        return inspect.signature(f)

def getAnnotations(x: Any) -> dict[str, Any]:
    if sys.version_info >= (3, 14):
        import annotationlib
        anns = annotationlib.get_annotations(x, format=annotationlib.Format.FORWARDREF)
        if not any(_isBrokenForwardRef(v) for v in anns.values()):
            return anns
        strAnns = annotationlib.get_annotations(x, format=annotationlib.Format.STRING)
        return {k: strAnns[k] if _isBrokenForwardRef(v) else v for k, v in anns.items()}
    else:
        return getattr(x, '__annotations__', {})

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
