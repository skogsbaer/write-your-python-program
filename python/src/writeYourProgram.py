# FIXME: make exceptions nicer
import time
import os
import typing

DEBUG = False
def debug(s):
    if DEBUG:
        print('[DEBUG] ' + s)

Any = typing.Any

# The goal is the make everything as simple and consistent as possible, so that
# records can be used to teach an introductory programming course inspired by
# "How to Design Programs" and "Schreib Dein Programm!".

def mkGetter(name):
    def get(obj):
        val = obj.values[name]
        return val
    return get

class Record:
    def __init__(self, *args):
        if len(args) % 2 != 1:
            raise TypeError("Record benötigte eine ungerade Anzahl an Argumenten.")
        if len(args) <= 1:
            raise TypeError("Record benötigt mindestens eine Eigenschaft")
        recordName = args[0]
        if type(recordName) != str:
            raise TypeError("Das erste Argument von Record ist der Name des Records. Dieser " \
                "Wert muss ein String sein.")
        fields = []
        for i in range(1, len(args), 2):
            fieldName = args[i]
            fieldTy = args[i+1]
            if type(fieldName) != str:
                raise TypeError(f"Das {i+1}te Argument von Record ist kein String, es wird aber " \
                    "der Name einer Eigenschaft erwartet.")
            fields.append((fieldName, fieldTy))
        def make(*args):
            return RecordInstance(recordName, fields, args)
        def isSome(x):
            ty = type(x)
            return ty is RecordInstance and x.recordName == recordName
        # self.make = make
        self.isSome = isSome
        self.fields = fields
        self.recordName = recordName
        # for (name, _ty) in fields:
        #     setattr(self, name, mkGetter(name))
    def __call__(self, *args):
        return RecordInstance(self.recordName, self.fields, args)
    def __repr__(self):
        return f"Record({self.recordName})"
    def __getattr__(self, name):
        attrs = ", ".join([x[0] for x in self.fields])
        raise AttributeError(f"{self.recordName}.{name} ist nicht definiert.")

class RecordInstance:
    def __init__(self, recordName, fields, args):
        self.recordName = recordName
        self.values = {}
        for ((name, ty), val) in zip(fields, args):
            self.values[name] = val
        debug(f'__init__ for {self.recordName} finished, self.values={self.values}, '\
            f'fields={fields}, args={args}')

    def __getattr__(self, name):
        try:
            return self.values[name]
        except KeyError:
            attrs = ", ".join([x[0] for x in self.values.items()])
            raise AttributeError(f"Der Record {self.recordName} besitzt die Eigenschaft " \
                f"{name} nicht. Es gibt folgende Eigenschaften: {attrs}")

    def __repr__(self):
        result = self.recordName + '('
        result += ', '.join([f + '=' + repr(v) for (f, v) in self.values.items()])
        result += ')'
        return result

    def __eq__(self, other):
        return type(other) is self.__class__ and self.recordName == other.recordName and \
            self.values == other.values

    def __ne__(self, other):
        return not self.__eq__(other)

    def __hash__(self):
        result = 17
        for (f, v) in self.values.items():
            result = 31 * result + hash(v)
        return result

# Mixed types

def hasType(ty, x):
    if type(x) is ty:
        return True
    elif ty is Any:
        return True
    else:
        pred = getattr(ty, "isSome", None)
        if pred:
            return pred(x)
        else:
            return False

class Mixed:
    def __init__(self, *args):
        self.alternatives = args
    def isSome(self, x):
        for alt in self.alternatives:
            if hasType(alt, x):
                return True
        return False

# Enums
class Enum:
    def __init__(self, *args):
        self.alternatives = args
    def isSome(self, x):
        return x in self.alternatives

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
        self.ref = ref
        self.resolved = None
        stack = inspect.stack()
        caller = stack[1] if len(stack) > 1 else None
        self.caller = caller
    def __repr__(self):
        if self.resolved:
            return repr(self.resolved)
        else:
            return "DefinedLater(" + repr(self.ref) + ")"
    def __getattr__(self, attr):
        resolved = self.resolved
        if not resolved:
            resolved = _resolveType(self.caller, self.ref)
            debug(f"Resolved {self.ref} to {resolved}")
            setattr(self, 'resolved', resolved)
        return getattr(resolved, attr)

# Tests

def _isNumber(x):
    t = type(x)
    return (t is int or t is float)

_die = False

def setDieOnCheckFailures(b):
    _die = b

def _dieOnCheckFailures():
    return _die

_testCount = {'total': 0, 'failing': 0}

def initModule(file, version):
    global _testCount
    _testCount = {'total': 0, 'failing': 0}
    cwd = os.getcwd() + "/"
    if file.startswith(cwd):
        file = file[len(cwd):]
    versionStr = '' if not version else f'Version {version}, '
    print(f'WILLKOMMEN zu "Schreibe Dein Programm!" ({versionStr}{file})')

def finishModule():
    total = _testCount['total']
    failing = _testCount['failing']
    if total == 0:
        pass
    elif failing == 0:
        print(f'{total} Tests, alle erfolgreich :-)')
    else:
        print(f'{total} Tests, {failing} Fehler :-(')
    return failing

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

