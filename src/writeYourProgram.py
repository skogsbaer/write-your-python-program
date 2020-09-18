# FIXME: make exceptions nicer
import time

def debug(s):
    pass
    # print('[DEBUG] ' + s)

# Wrappers for primitive types

class String:
    def isSome(x):
        return type(x) is str

class Int:
    def isSome(x):
        return type(x) is int

class Float:
    def isSome(x):
        return type(x) is float

class Bool:
    def isSome(x):
        return type(x) is bool

# Records inspired by the namedtuples library, but much simpler.
# The goal is the make everything as simple and consistent as possible, so that
# records can be used to teach an introductory programming course inspired by
# "How to Design Programs" and "Schreib Dein Programm!".

def mkGetter(name):
    def get(obj):
        val = obj.__dict__['_' + name]
        return val
    return get

class MetaRecord(type):
    def __new__(baseCls, name, bases, dct):
        cls = super().__new__(baseCls, name, bases, dct)
        # We inject static methods here to be able to use the class object in those methods
        def make(*args):
            return cls(*args)
        def isSome(x):
            ty = type(x)
            return ty is cls
        cls.make = make
        cls.isSome = isSome
        cls._fields = dct.get('__annotations__', {})
        cls._name = name
        # create getters for all fields
        for (name, _ty) in cls._fields.items():
            setattr(cls, name, mkGetter(name))
        return cls

class Record(metaclass=MetaRecord):
    def __init__(self, *args):
        fields = self.__class__._fields.items()
        # Since python 3.7, dicts preserve the insertion order
        # (https://docs.python.org/3/whatsnew/3.7.html). This, we can assume that fields
        # contains the annotated fields of the class in the same order as in the class
        # definition.
        # FIXME: error handling: check arity and (optionally) types
        for ((name, ty), val) in zip(fields, args):
            self.__dict__['_' + name] = val
        debug(f'__init__ for {self.__class__.__name__} finished, self.__dict__={self.__dict__}')

    def __str__(self):
        result = self.__class__._name + '('
        fields = self.__class__._fields
        result += ', '.join([f + '=' + str(self.__dict__['_' + f]) for (f, _) in fields.items()])
        result += ')'
        return result

    def __eq__(self, other):
        return type(other) is self.__class__ and self.__dict__ == other.__dict__

    def __ne__(self, other):
        return not self.__eq__(other)

    def __hash__(self):
        result = 17
        fields = self.__class__._fields
        for (f, _ty) in fields.items():
            val = self.__dict__.get('_' + f, None)
            if val:
                result = 31 * result + hash(val)
        return result

# Mixed types

class MetaMixed(type):
    def __new__(baseCls, name, bases, dct):
        cls = super().__new__(baseCls, name, bases, dct)
        return cls

class Mixed(metaclass=MetaMixed):
    def __init__(self, *args):
        self.alternatives = args
    def isSome(self, x):
        for alt in self.alternatives:
            if alt.isSome(x): return True
        return False

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
    raise Exception(f"Der Typ {name} wird in {file}:{line} referenziert, ist aber nicht in der Datei {file} definiert.")

class DefinedLater:
    def __init__(self, ref):
        self.ref = ref
        self.resolved = None
        stack = inspect.stack()
        caller = stack[1] if len(stack) > 1 else None
        self.caller = caller
    # FIXME: add __repr__
    def __getattribute__(self, attr):
        if attr in ['ref', 'resolved', 'caller']:
            return object.__getattribute__(self, attr)
        resolved = self.resolved
        if resolved:
            return self.resolved[attr]
        else:
            x = _resolveType(self.caller, self.ref)
            setattr(self, 'resolved', x)
            return x

# Tests

def _isNumber(x):
    t = type(x)
    return (t is int or t is float)

def _dieOnCheckFailures():
    return False

_testCount = {'total': 0, 'failing': 0}

def initModule(file):
    global _testCount
    _testCount = {'total': 0, 'failing': 0}
    t = time.strftime("%a, %d %b %Y %H:%M:%S")
    print(f'WILLKOMMEN zu "Schreibe Dein Programm!" ({t}, {file})')

def finishModule():
    total = _testCount['total']
    failing = _testCount['failing']
    if total == 0:
        print('Keine Tests definiert.')
    elif failing == 0:
        print(f'{total} Tests, alle erfolgreich :-)')
    else:
        print(f'{total} Tests, {failing} Fehler :-(')

def check(actual, expected):
    global _testCount
    matches = actual == expected
    if _isNumber(actual) and _isNumber(expected):
        diff = actual - expected
        matches = abs(diff) < 0.00001
    _testCount = {
        'total': _testCount['total'] + 1,
        'failing': _testCount['failing'] + (0 if matches else 1)
    }
    if not matches:
        stack = inspect.stack()
        caller = stack[1] if len(stack) > 1 else None
        msg = f"{caller.filename}:{caller.lineno}: Erwartet wird {expected}, aber das Ergebnis ist {actual}"
        if _dieOnCheckFailures():
            raise Exception(msg)
        else:
            print("FEHLER in " + msg)

def uncoveredCase():
    stack = inspect.stack()
    caller = stack[1] if len(stack) > 1 else None
    raise Exception(f"{caller.filename}, Zeile {caller.lineno}: ein Fall ist nicht abgedeckt")

