# FIXME: make exceptions nicer
import time
import os
import typing
import collections
import dataclasses

# For the moment, we do not import anything from this very module here. Reason: for backwards
# compat we load wypp either as a module (the new way) or via runpy (the old way). It seems
# too complicated to make imports working for both ways, so we wait until after WS2020/21
# so that we can drop support for the old way.

_DEBUG = False
def _debug(s):
    if _DEBUG:
        print('[DEBUG] ' + s)

# Types
Any = typing.Any
Optional = typing.Optional
Literal = typing.Literal
Union = typing.Union

Iterable = typing.Iterable
Iterator = typing.Iterator
Sequence = typing.Sequence
List = typing.List
Tuple = typing.Tuple
Generator = typing.Generator

Mapping = typing.Mapping
Dict = typing.Dict
Set = typing.Set

Callable = typing.Callable
dataclass = dataclasses.dataclass

# Reexports for Untypy
try:
    from untypy import unchecked, precondition, postcondition
except ImportError:
    def _dummy_decorator(fn):
        return fn

    def _higher_order_dummy_decorator(*args):
        # Match Pre/Post-Cond Arg
        return _dummy_decorator

    unchecked = _dummy_decorator
    precondition = _higher_order_dummy_decorator
    postcondition = _higher_order_dummy_decorator


def _isDataclassInstance(obj):
    return dataclasses.is_dataclass(obj) and not isinstance(obj, type)

def _patchDataClass(cls, mutable):
    def isSome(obj):
        if not _isDataclassInstance(obj):
            return False
        return obj.__class__ == cls
    setattr(cls, "isSome", isSome)
    fieldNames = [f.name for f in dataclasses.fields(cls)]
    setattr(cls, EQ_ATTRS_ATTR, fieldNames)
    if mutable:
        # prevent new fields being added
        fields = set(fieldNames)
        oldSetattr = cls.__setattr__
        def _setattr(obj, k, v):
            if k in fields:
                oldSetattr(obj, k, v)
            else:
                raise AttributeError(f'Unknown attribute {k} for record {cls.__name__}')
        setattr(cls, "__setattr__", _setattr)
    return cls

def record(cls=None, mutable=False):
    def wrap(cls):
        newCls = dataclasses.dataclass(cls, frozen=not mutable)
        return _patchDataClass(newCls, mutable)
    # See if we're being called as @record or @record().
    if cls is None:
        # We're called with parens.
        return wrap
    else:
        # We're called as @dataclass without parens.
        return wrap(cls)

# Records
# The goal is the make everything as simple and consistent as possible, so that
# records can be used to teach an introductory programming course inspired by
# "How to Design Programs" and "Schreib Dein Programm!".
class Record:
    def __init__(self, *args):
        if len(args) % 2 != 1:
            raise TypeError("Record benötigte eine ungerade Anzahl an Argumenten.")
        if len(args) <= 1:
            raise TypeError("Record benötigt mindestens eine Eigenschaft")
        recordName = args[0]
        if type(recordName) != str:
            raise TypeError(f"Das 1. Argument von Record ist kein String sondern {recordName}.")
        fields = []
        for i in range(1, len(args), 2):
            fieldName = args[i]
            fieldTy = args[i+1]
            if type(fieldName) != str:
                raise TypeError(f"Das {i+1}. Argument von Record ist kein String " \
                    f"sondern {repr(fieldName)}. Es wird aber der Name einer Eigenschaft erwartet.")
            if not isType(fieldTy):
                raise TypeError(f"Das {i+2}. Argument von Record ist kein Typ sondern " \
                    f"{repr(fieldTy)}. Es wird aber der Typ der Eigenschaft {fieldName} erwartet.")
            fields.append((fieldName, fieldTy))
        def isSome(x):
            ty = type(x)
            return ty is _RecordInstance and x.recordName == recordName
        self.isSome = isSome
        self.fields = fields
        self.recordName = recordName
    def isWyppType(self):
        return True
    def __call__(self, *args):
        return _RecordInstance(self.recordName, self.fields, args)
    def __repr__(self):
        return f"Record({self.recordName})"
    def __getattr__(self, name):
        attrs = ", ".join([x[0] for x in self.fields])
        raise AttributeError(f"{self.recordName}.{name} ist nicht definiert.")

class _RecordInstance:
    def __init__(self, recordName, fields, args):
        self.__dict__['_frozen'] = False
        self.recordName = recordName
        self.values = {}
        for ((name, ty), val) in zip(fields, args):
            self.values[name] = val
        self.__eqAttrs__ = [f[0] for f in fields]
        _debug(f'__init__ for {self.recordName} finished, self.values={self.values}, '\
            f'fields={fields}, args={args}')
        self.__dict__['_frozen'] = True

    def __getattr__(self, name):
        if name in self.values:
            return self.values[name]
        else:
            attrs = ", ".join([x[0] for x in self.values.items()])
            raise AttributeError(f"Der Record {self.recordName} besitzt die Eigenschaft " \
                f"{name} nicht. Es gibt folgende Eigenschaften: {attrs}")

    def __setattr__(self, name, val):
        if self._frozen:
            raise AttributeError(
                f'Das Attribut {name} des Records {self.recordName} kann nicht geändert werden.'
            )
        else:
            self.__dict__[name] = val

    def __repr__(self):
        result = self.recordName + '('
        result += ', '.join([f + '=' + repr(v) for (f, v) in self.values.items()])
        result += ')'
        return result

    def __eq__(self, other):
        return type(other) is _RecordInstance and self.recordName == other.recordName and \
            deepEq(self.values, other.values)

    def __ne__(self, other):
        return not self.__eq__(other)

    def __hash__(self):
        result = 17
        for (f, v) in self.values.items():
            result = 31 * result + hash(v)
        return result

# Mixed types

class Mixed:
    def __init__(self, *args):
        resolvedArgs = []
        for i, a in enumerate(args):
            if a is None:
                resolvedArgs.append(type(None))
            else:
                if not isType(a):
                    raise TypeError(f"Das {i+1}. Argument von Mixed ist kein Typ sondern {repr(a)}.")
                resolvedArgs.append(a)
        self.alternatives = resolvedArgs
    def isWyppType(self):
        return True
    def isSome(self, x):
        for alt in self.alternatives:
            if hasType(alt, x):
                return True
        return False
    def __call__(self, *args, **kwArgs):
        # make it callable so that it can be used as a type argument of a generic
        raise 'Mixed is not callable'

# Enums
# FIXME: remove in favor of literal
class Enum:
    def __init__(self, *args):
        for i, a in enumerate(args):
            t = type(a)
            if t not in [str, int, bool]:
                raise TypeError(f"Das {i+1}. Argument von Enum ist kein String oder int sondern {repr(a)}.")
        self.alternatives = args
    def isWyppType(self):
        return True
    def isSome(self, x):
        return x in self.alternatives
    def __call__(self, *args, **kwArgs):
        # make it callable so that it can be used as a type argument of a generic
        raise 'Enum is not callable'

# Deferred references

import inspect

def _resolveType(frameInfo, name):
    frame = frameInfo.frame
    scopes = [frame.f_locals, frame.f_globals]
    for scope in scopes:
        x = scope.get(name, False)
        if x:
            return x
    file = frameInfo.filename
    line = frameInfo.lineno
    raise Exception(f"Der Typ {name} wird in {file}:{line} referenziert, ist aber nicht " \
        f"in der Datei {file} definiert.")

class DefinedLater:
    def __init__(self, ref):
        if type(ref) != str:
            raise TypeError(f"Das 1. Argument von DefinedLater ist kein String sondern {repr(ref)}.")
        self.ref = ref
        self.resolved = None
        stack = inspect.stack()
        caller = stack[1] if len(stack) > 1 else None
        self.caller = caller
    def isWyppType(self):
        return True
    def resolve(self):
        resolved = self.resolved
        if not resolved:
            resolved = _resolveType(self.caller, self.ref)
            _debug(f"Resolved {self.ref} to {resolved}")
            setattr(self, 'resolved', resolved)
        return resolved
    def __repr__(self):
        if self.resolved:
            return repr(self.resolved)
        else:
            return "DefinedLater(" + repr(self.ref) + ")"
    def __getattr__(self, attr):
        resolved = self.resolve()
        return getattr(resolved, attr)
    def __call__(self, *args, **kwArgs):
        # make it callable so that it can be used as a type argument of a generic
        raise TypeError('DefinedLater is not callable')

# Tests

def isType(ty, rec=True):
    if isinstance(ty, type):
        return True
    elif ty in [None, Any, Optional, typing.Union]:
        return True
    pred = getattr(ty, "isWyppType", None)
    if pred is not None:
        return pred()
    origin = getattr(ty, '__origin__', None)
    if origin and rec:
        return isType(origin, rec=False)

def _safeIsInstance(x, ty):
    try:
        return isinstance(x, ty)
    except TypeError:
        return False

def hasType(ty, x, rec=True):
    if isinstance(ty, DefinedLater):
        ty = ty.resolve()
    if _safeIsInstance(x, ty):
        return True
    elif ty in [Any, Optional, typing.Union]:
        return True
    elif ty is None:
        return x is None
    origin = getattr(ty, '__origin__', None)
    if origin and rec:
        return hasType(origin, x, rec=False)
    else:
        pred = getattr(ty, "isSome", None)
        if pred:
            return pred(x)
        else:
            return False

_die = False

def setDieOnCheckFailures(b):
    _die = b

def _dieOnCheckFailures():
    return _die

_testCount = {'total': 0, 'failing': 0}
_checksEnabled = True

def initModule(enableChecks=True, quiet=False):
    global _checksEnabled
    _checksEnabled = enableChecks
    resetTestCount()

def resetTestCount():
    global _testCount
    _testCount = {'total': 0, 'failing': 0}

def printTestResults(prefix=''):
    total = _testCount['total']
    failing = _testCount['failing']
    if total == 0:
        pass
    elif failing == 0:
        print(f'{prefix}{total} Tests, alle erfolgreich :-)')
    else:
        print(f'{prefix}{total} Tests, {failing} Fehler :-(')
    return {'total': total, 'failing': failing}

def checkEq(actual, expected):
    return check(actual, expected, structuralObjEq=False)

def check(actual, expected, structuralObjEq=True, floatEqWithDelta=True):
    if not _checksEnabled:
        return
    global _testCount
    flags = {'structuralObjEq': structuralObjEq, 'floatEqWithDelta': floatEqWithDelta}
    matches = deepEq(actual, expected, **flags)
    _testCount = {
        'total': _testCount['total'] + 1,
        'failing': _testCount['failing'] + (0 if matches else 1)
    }
    if not matches:
        stack = inspect.stack()
        caller = stack[1] if len(stack) > 1 else None
        msg = f"{caller.filename}:{caller.lineno}: Erwartet wird {expected}, aber das " \
            f"Ergebnis ist {actual}"
        if _dieOnCheckFailures():
            raise Exception(msg)
        else:
            print("FEHLER in " + msg)

def uncoveredCase():
    stack = inspect.stack()
    caller = stack[1] if len(stack) > 1 else None
    raise Exception(f"{caller.filename}, Zeile {caller.lineno}: ein Fall ist nicht abgedeckt")

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
    ks1 = sorted(d1.keys())
    ks2 = sorted(d2.keys())
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
    if hasattr(o, EQ_ATTRS_ATTR):
        useAll = True
        attrs = getattr(o, EQ_ATTRS_ATTR)
    for n in attrs:
        if not useAll and n and n[0] == '_':
            continue
        x = getattr(o, n)
        d[n] = x
    return d

def _objEq(o1, o2, flags):
    return _dictEq(_objToDict(o1), _objToDict(o2), flags)

_EPSILON = 0.00001
EQ_ATTRS_ATTR = '__eqAttrs__'

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
    # print(f'v1={v1}, v2={v2}, flags={flags}')
    if v1 == v2:
        return True
    if _isNumber(v1) and _isNumber(v2) and _useFloatEqWithDelta(flags):
        diff = v1 - v2
        if abs(diff) < _EPSILON:
            return True
        else:
            return False
    ty1 = type(v1)
    if ty1 != type(v2):
        return False
    if ty1 == list or ty1 == tuple:
        return _seqEq(v1, v2, flags)
    if ty1 == dict:
        return _dictEq(v1, v2, flags)
    if ty1 == str:
        return False
    if hasattr(v1, '__class__'):
        if _useStructuralObjEq(flags):
            return _objEq(v1, v2, flags)
        else:
            return False # v1 == v2 already checked
    return False

# Additional functions and aliases

import math as moduleMath

math = moduleMath

ForwardRef = DefinedLater

