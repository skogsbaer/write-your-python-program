
# This module defines records inspired by the namedtuples library, but much simpler.
# The goal is the make everything as simple and consistent as possible, so that
# records can be used to teach an introductory programming course inspired by
# "How to Design Programs" and "Schreib Dein Programm!".

def debug(s):
    pass
    # print('[DEBUG] ' + s)

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
    # FIXME: implement hash and repr

    def __eq__(self, other):
        if type(other) is self.__class__:
            return self.__dict__ == other.__dict__
        else:
            return False

    def __ne__(self, other):
        return not self.__eq__(other)
