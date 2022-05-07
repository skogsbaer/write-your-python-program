import typing
import abc
import collections
from untypy.error import UntypyError
from untypy.util.debug import debug

def _f():
    yield 0
generatorType = type(_f())

class WyppWrapError(Exception):
    pass

def patch(self, ty, extra):
    self.__extra__ = extra
    w = self.__wrapped__
    m = None
    if hasattr(w, '__module__'):
        m = getattr(w, '__module__')
    ty.__module__ = m
    try:
        self.__class__ = ty
    except TypeError as e:
        raise WyppWrapError(f'Cannot wrap {self.__wrapped__} of type {type(self.__wrapped__)} ' \
            f'at type {ty}. Original error: {e}')

class WrapperBase:
    def __eq__(self, other):
        if hasattr(other, '__wrapped__'):
            return self.__wrapped__ == other.__wrapped__
        else:
            return self.__wrapped__ == other
    def __hash__(self):
        return hash(self.__wrapped__)
    def __patch__(self, ms, name=None, extra={}):
        cls = self.__class__
        if name is None:
            name = cls.__name__
        ty = type(name, (cls,), ms)
        patch(self, ty, extra)
    def __repr__(self):
        return repr(self.__wrapped__)
    def __str__(self):
        return str(self.__wrapped__)

class ObjectWrapper(WrapperBase):
    def __init__(self, baseObject):
        self.__dict__ = baseObject.__dict__
        self.__wrapped__ = baseObject
    def __patch__(self, ms, name=None, extra={}):
        cls = self.__class__
        if name is None:
            name = cls.__name__
        wrappedCls = type(self.__wrapped__)
        ty = type(name, (wrappedCls, cls), ms)
        patch(self, ty, extra)

class ABCObjectWrapper(abc.ABC, ObjectWrapper):
    pass

# Superclasses in reverse order.
class ABCObjectWrapperRev(ObjectWrapper, abc.ABC):
    pass

class ListWrapper(list, WrapperBase):
    def __new__(cls, content):
        self = super().__new__(cls, content)
        self.__wrapped__ = content
        return self
    #def __len__(self):
    #    return self.__wrapped__.__len__()

class TupleWrapper(tuple, WrapperBase):
    def __new__(cls, content):
        self = super().__new__(cls, content)
        self.__wrapped__ = content
        return self

class SetWrapper(set, WrapperBase):
    def __new__(cls, content):
        self = super().__new__(cls, content)
        self.__wrapped__ = content
        return self

class StringWrapper(str, WrapperBase):
    def __new__(cls, content):
        self = super().__new__(cls, content)
        self.__wrapped__ = content
        return self

class DictWrapper(dict, WrapperBase):
    def __new__(cls, content):
        self = super().__new__(cls, content)
        self.__wrapped__ = content
        return self

_blacklist = [
    '__class__', '__delattr__', '__dict__', '__dir__', '__doc__',
    '__getattribute__', '__get_attr_', '__init_subclass__'
    '__init__', '__new__', '__repr__', '__setattr__', '__str__',
    '__hash__', '__eq__', '__patch__',
    '__class_getitem__',  '__subclasshook__']

_extra = ['__next__']

# SimpleWrapper is a fallback for types that cannot be used as base types
class SimpleWrapper(WrapperBase):
    def __init__(self, baseObject):
        self.__wrapped__ = baseObject
    def __patch__(self, ms, name=None, extra={}):
        cls = self.__class__
        if name is None:
            name = cls.__name__
        baseObject = self.__wrapped__
        for x in dir(baseObject) + _extra:
            if x not in ms and x not in _blacklist and hasattr(baseObject, x):
                ms[x] = getattr(baseObject, x)
        ty = type(name, cls.__bases__, ms)
        patch(self, ty, extra)

class ValuesViewWrapper(SimpleWrapper):
    pass
collections.abc.ValuesView.register(ValuesViewWrapper)

class ItemsViewWrapper(SimpleWrapper):
    pass
collections.abc.ItemsView.register(ItemsViewWrapper)

class KeysViewWrapper(SimpleWrapper):
    pass
collections.abc.KeysView.register(KeysViewWrapper)

def wrap(obj, methods, name=None, extra={}, simple=False):
    if simple:
        w = SimpleWrapper(obj)
    elif isinstance(obj, list):
        w = ListWrapper(obj)
    elif isinstance(obj, tuple):
        w = TupleWrapper(obj)
    elif isinstance(obj, dict):
        w = DictWrapper(obj)
    elif isinstance(obj, str):
        w = StringWrapper(obj)
    elif isinstance(obj, set):
        w = SetWrapper(obj)
    elif isinstance(obj, collections.abc.ValuesView):
        w = ValuesViewWrapper(obj)
    elif isinstance(obj, collections.abc.KeysView):
        w = KeysViewWrapper(obj)
    elif isinstance(obj, collections.abc.ItemsView):
        w = ItemsViewWrapper(obj)
    elif isinstance(obj, typing.Generic):
        w = SimpleWrapper(obj)
    elif isinstance(obj, generatorType):
        w = SimpleWrapper(obj)
    elif isinstance(obj, abc.ABC) and hasattr(obj, '__dict__'):
        try:
            w = ABCObjectWrapper(obj)
        except WyppWrapError:
            try:
                w = ABCObjectWrapperRev(obj)
            except WyppWrapError:
                w = SimpleWrapper(obj)
    elif hasattr(obj, '__dict__'):
        w = ObjectWrapper(obj)
    else:
        w = SimpleWrapper(obj)
    w.__patch__(methods, name, extra)
    debug(f"Wrapping {obj} at 0x{id(obj):09x} as {name}, simple={simple}, " \
        f"wrapper=0x{id(w):09x}, wrapped=0x{id(w.__wrapped__):09x}")
    return w

