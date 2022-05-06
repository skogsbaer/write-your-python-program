import collections.abc
import typing
import abc
from untypy.error import UntypyError

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

_blacklist = ['__class__', '__init__', '__str__', '__repr__', '__hash__', '__eq__', '__patch__',
    '__init_subclass__', '__class_getitem__', '__getattribute__', '__subclasshook__']

# SimpleWrapper is a fallback for types that cannot be used as base types
class SimpleWrapper(WrapperBase):
    def __init__(self, baseObject):
        self.__wrapped__ = baseObject
    def __patch__(self, ms, name=None, extra={}):
        cls = self.__class__
        if name is None:
            name = cls.__name__
        baseObject = self.__wrapped__
        for name in dir(baseObject):
            if name not in ms and name not in _blacklist:
                ms[name] = getattr(baseObject, name)
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
    elif isinstance(obj, abc.ABC):
        try:
            w = ABCObjectWrapper(obj)
        except WyppWrapError:
            try:
                w = ABCObjectWrapperRev(obj)
            except WyppWrapError:
                w = SimpleWrapper(obj)
    else:
        w = ObjectWrapper(obj)
    w.__patch__(methods, name, extra)
    return w

