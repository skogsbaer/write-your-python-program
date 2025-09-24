try:
    from . import writeYourProgram as w
except (ImportError, ModuleNotFoundError):
    import writeYourProgram as w

import typing

# Exported names that are available for star imports (in alphabetic order)
Any = w.Any
Callable = w.Callable
Generator = w.Generator
Iterable = w.Iterable
Iterator = w.Iterator
Literal = w.Literal
Mapping = w.Mapping
Optional = w.Optional
Sequence = w.Sequence
Protocol = w.Protocol
Union = w.Union
check = w.check
checkFail = w.checkFail
dataclass = w.dataclass
floatNegative = w.floatNegative
floatNonNegative = w.floatNonNegative
floatNonPositive = w.floatNonPositive
floatPositive = w.floatPositive
impossible = w.impossible
intNegative = w.intNegative
intNonNegative = w.intNonNegative
intNonPositive = w.intNonPositive
intPositive = w.intPositive
math = w.math
nat = w.nat

@typing.dataclass_transform()
def record(cls=None, mutable=False, globals={}, locals={}):
    return w.record(cls, mutable, globals, locals)

T = w.T
todo = w.todo
U = w.U
V = w.V

__all__ = [
    'Any',
    'Callable',
    'Generator',
    'Iterable',
    'Iterator',
    'Literal',
    'Mapping',
    'Optional',
    'Sequence',
    'Protocol',
    'Union',
    'check',
    'checkFail',
    'dataclass',
    'floatNegative',
    'floatNonNegative',
    'floatNonPositive',
    'floatPositive',
    'impossible',
    'intNegative',
    'intNonNegative',
    'intNonPositive',
    'intPositive',
    'math',
    'nat',
    'record',
    'T',
    'todo',
    'U',
    'V'
]

# Exported names not available for star imports (in alphabetic order)
Lock = w.Lock
LockFactory = w.LockFactory
initModule = w.initModule
printTestResults = w.printTestResults
resetTestCount = w.resetTestCount
deepEq = w.deepEq
wrapTypecheck = w.wrapTypecheck
