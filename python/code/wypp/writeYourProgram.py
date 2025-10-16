import typing
from typing import Any
import dataclasses
import inspect
import errors
import typecheck
import records
import stacktrace
import renderTy
import location
import paths
import utils
import i18n

_DEBUG = False
def _debug(s):
    if _DEBUG:
        print('[DEBUG] ' + s)

record = records.record

intPositive = typing.Annotated[int, lambda i: i > 0, 'intPositive']
nat = typing.Annotated[int, lambda i: i >= 0, 'nat']
intNonNegative = typing.Annotated[int, lambda i: i >= 0, 'intNonNegative']
intNonPositive = typing.Annotated[int, lambda i: i <= 0, 'intNonPositive']
intNegative = typing.Annotated[int, lambda i: i < 0, 'intNegative']

floatPositive = typing.Annotated[float, lambda x: x > 0, 'floatPositive']
floatNonNegative = typing.Annotated[float, lambda x: x >= 0, 'floatNonNegative']
floatNegative = typing.Annotated[float, lambda x: x < 0, 'floatNegative']
floatNonPositive = typing.Annotated[float, lambda x: x <= 0, 'floatNonPositive']

class Lock(typing.Protocol):
    def acquire(self, blocking: bool = True, timeout:int = -1) -> Any:
       pass
    def release(self) -> Any:
        pass
    def locked(self) -> Any:
        pass

LockFactory = typing.Annotated[typing.Callable[[], Lock], 'LockFactory']

T = typing.TypeVar('T')
U = typing.TypeVar('U')
V = typing.TypeVar('V')

# Dirty hack ahead: we patch some methods of internal class of the typing module.

def _literalInstanceOf(self, value):
    for p in self.__args__:
        # typing.Literal checks for type(value) == type(arg),
        # however this does not work well with untypy.
        if isinstance(value, type(p)) and p == value:
            return True
    return False

# This patch is needed to be able to use a literal L to check whether a value x
# is an instance of this literal: isinstance(x, L)
# pyright does not know about typing._LiteralGenericAlias, we do not typecheck the following line.
setattr(typing._LiteralGenericAlias, '__instancecheck__', _literalInstanceOf) # type: ignore

def _invalidCall(self, *args, **kwds):
    if hasattr(self, '__name__'):
        name = self.__name__
    else:
        name = str(self)
        typingPrefix = 'typing.'
        if name.startswith(typingPrefix):
            name = name[len(typingPrefix):]
    def formatArg(x):
        if name == 'Literal':
            return repr(x)
        else:
            return renderTy.renderTy(x)
    caller = stacktrace.callerOutsideWypp()
    loc = None if caller is None else location.Loc.fromFrameInfo(caller)
    argStr = ', '.join([formatArg(x) for x in args])
    tyStr = f'{name}({argStr})'
    raise utils._call_with_frames_removed(errors.WyppTypeError.invalidType, tyStr, loc)

# This patch is needed to provide better error messages if a student passes type arguments
# with paranthesis instead of square brackets
setattr(typing._SpecialForm, '__call__', _invalidCall)

def typechecked(func=None):
    def wrap(func):
        if hasattr(func, '__qualname__'):
            q = getattr(func, "__qualname__").split('.')
            if len(q) >= 2:
                className = q[-2]
                cfg = {'kind': 'method', 'className': className}
            else:
                cfg = {'kind': 'function'}
        else:
            cfg = {'kind': 'function'}
        return typecheck.wrapTypecheck(cfg)(func)
    if func is None:
        # We're called with parens.
        return wrap
    else:
        # We're called as @dataclass without parens.
        return wrap(func)

# Tests

_die = False

def setDieOnCheckFailures(b):
    global _die
    _die = b

def _dieOnCheckFailures():
    return _die

_testCount = {'total': 0, 'failing': 0}
_checksEnabled = True
_typeCheckingEnabled = False

def initModule(enableChecks=True, enableTypeChecking=True, quiet=False):
    global _checksEnabled, _typeCheckingEnabled
    _checksEnabled = enableChecks
    _typeCheckingEnabled = enableTypeChecking
    records.init(enableTypeChecking)
    resetTestCount()

def resetTestCount():
    global _testCount
    _testCount = {'total': 0, 'failing': 0}

def printTestResults(prefix='', loadingFailed=False):
    total = _testCount['total']
    failing = _testCount['failing']
    bad = '🙁'
    good = '😀'
    tests = f'{prefix}' + i18n.numTests(total)
    if total == 0:
        pass
    elif failing == 0:
        if loadingFailed:
            print(f'{tests}, {i18n.tr("Stop of execution")} {bad}')
        elif total == 1:
            print(f'{i18n.tr("1 successful test")} {good}')
        else:
            print(f'{tests}, {i18n.tr("all successful")} {good}')
    else:
        if loadingFailed:
            print(f'{tests}, {i18n.numFailing(failing)} and stop of execution {bad}')
        else:
            print(f'{tests}, {i18n.numFailing(failing)} {bad}')
    return {'total': total, 'failing': failing}

def checkEq(actual, expected):
    return checkGeneric(actual, expected, structuralObjEq=False)

def incTestCount(testOk: bool):
    global _testCount
    _testCount = {
        'total': _testCount['total'] + 1,
        'failing': _testCount['failing'] + (0 if testOk else 1)
    }

def check(actual, expected):
    """
    Überprüft, ob ein Funktionsaufruf das gewünschte Ergebnis liefert.

    Beispiel:

    `check(f(10, 'blah'), 17)` überprüft, ob der Aufruf `f(10, 'blah')` wie erwartet das Ergebnis `17` liefert.
    """
    checkGeneric(actual, expected)

def checkGeneric(actual, expected, *, structuralObjEq=True, floatEqWithDelta=True):
    if not _checksEnabled:
        return
    flags = {'structuralObjEq': structuralObjEq, 'floatEqWithDelta': floatEqWithDelta}
    matches = deepEq(actual, expected, **flags)
    incTestCount(matches)
    if not matches:
        stack = inspect.stack()
        frame = stack[2] if len(stack) > 2 else None
        if frame:
            filename = paths.canonicalizePath(frame.filename)
            caller = i18n.tr('File {filename}, line {lineno}: ',
                             filename=filename, lineno=frame.lineno)
        else:
            caller = ""
        def fmt(x):
            if type(x) == str:
                return repr(x)
            else:
                return str(x)
        msg = caller + i18n.checkExpected(fmt(expected), fmt(actual))
        if _dieOnCheckFailures():
            raise Exception(msg)
        else:
            print(i18n.tr('ERROR in ') + msg)

def checkFail(msg: str):
    if not _checksEnabled:
        return
    incTestCount(False)
    msg = str(msg)
    if _dieOnCheckFailures():
        raise Exception(msg)
    else:
        print(i18n.tr('ERROR: ') + msg)

def uncoveredCase():
    stack = inspect.stack()
    if len(stack) > 1:
        caller = stack[1]
        callerStr = i18n.tr('File {filename}, line {lineno}: ',
                            filename=caller.filename, lineno=caller.lineno)
        raise Exception(callerStr + i18n.tr('uncovered case'))
    else:
        raise Exception(i18n.tr('Uncovered case'))

#
# Deep equality
#
def _isNumber(x):
    t = type(x)
    return (t is int or t is float)

def _seqEq(seq1, seq2, flags):
    if len(seq1) != len(seq2):
        return False
    for i, x in enumerate(seq1):
        y = seq2[i]
        if not deepEq(x, y, **flags):
            return False
    return True

def _dictEq(d1, d2, flags):
    ks1 = set(d1.keys())
    ks2 = set(d2.keys())
    if ks1 != ks2: # keys should be exactly equal
        return False
    for k in ks1:
        if not deepEq(d1[k], d2[k], **flags):
            return False
    return True

def _objToDict(o):
    d = {}
    attrs = dir(o)
    useAll = False
    if hasattr(o, records.EQ_ATTRS_ATTR):
        useAll = True
        attrs = getattr(o, records.EQ_ATTRS_ATTR)
    for n in attrs:
        if not useAll and n and n[0] == '_':
            continue
        x = getattr(o, n)
        d[n] = x
    #print(f'_objToDict: {d}')
    return d

def _objEq(o1, o2, flags):
    return _dictEq(_objToDict(o1), _objToDict(o2), flags)

_EPSILON = 0.00001

def _useFloatEqWithDelta(flags):
    return flags.get('floatEqWithDelta', False)

def _useStructuralObjEq(flags):
    return flags.get('structuralObjEq', False)

# Supported flags:
# - structuralObjEq: causes objects to be compared as dictionaries. The keys are by default
#   taken from dir(obj), if obj as the attribute __eqAttrs__, then the names listed there
#   are taken. Defaults to False.
# - floatEqWithDelta: compares floats by checking whether the difference is smaller than a
#   small delta. Setting this to True loses transitivity of eq.
def deepEq(v1, v2, **flags):
    """
    Computes deep equality of v1 and v2. With structuralObjEq=False, objects are compared
    by __eq__. Otherwise, objects are compared attribute-wise, only those attributes
    returned by dir that do not start with an underscore are compared.
    """
    #print(f'deepEq: v1={v1}, v2={v2}, flags={flags}')
    if v1 == v2:
        return True
    if _isNumber(v1) and _isNumber(v2) and _useFloatEqWithDelta(flags):
        diff = v1 - v2
        if abs(diff) < _EPSILON:
            return True
        else:
            return False
    if isinstance(v1, list):
        return isinstance(v2, list) and _seqEq(v1, v2, flags)
    if isinstance(v1, tuple):
        return isinstance(v2, tuple) and _seqEq(v1, v2, flags)
    if isinstance(v1, dict):
        return isinstance(v2, dict) and _dictEq(v1, v2, flags)
    if callable(v1):
        return False
    if type(v1) == str:
        return False
    if hasattr(v1, '__class__'):
        if _useStructuralObjEq(flags):
            res = _objEq(v1, v2, flags)
            return res
        else:
            return False # v1 == v2 already checked
    return False

def todo(msg=None):
    if msg is None:
        msg = 'TODO'
    raise errors.TodoError(msg)

def impossible(msg=None):
    if msg is None:
        msg = i18n.tr('The impossible happened!')
        'Das Unmögliche ist passiert!'
    raise errors.ImpossibleError(msg)

# Additional functions and aliases

import math as moduleMath

math = moduleMath

wrapTypecheck = typecheck.wrapTypecheck
