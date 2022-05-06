import collections.abc
import typing
from untypy.error import UntypyError

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
        self.__class__ = type(name, (cls,), ms)
        self.__extra__ = extra
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
        try:
            self.__class__ = type(name, (wrappedCls, cls), ms)
        except TypeError as e:
            raise TypeError(f'Cannot wrap {self.__wrapped__} of type {type(self.__wrapped__)} ' \
                f'with ObjectWrapper. Original error: {e}')
        self.__extra__ = extra

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

# SimpleWrapper is a fallback for types that cannot be used as base types (e.g dict_values)
class SimpleWrapper(WrapperBase):
    def __init__(self, baseObject):
        d = {}
        for name in dir(baseObject):
            d[name] = getattr(baseObject, name)
        self.__dict__ = d
        self.__wrapped__ = baseObject
    def __patch__(self, ms, name=None, extra={}):
        cls = self.__class__
        if name is None:
            name = cls.__name__
        self.__class__ = type(name, cls.__bases__, ms)
        self.__extra__ = extra

class ValuesViewWrapper(SimpleWrapper):
    pass
collections.abc.ValuesView.register(ValuesViewWrapper)

class ItemsViewWrapper(SimpleWrapper):
    pass
collections.abc.ValuesView.register(ItemsViewWrapper)

class KeysViewWrapper(SimpleWrapper):
    pass
collections.abc.ValuesView.register(KeysViewWrapper)

def wrap(obj, methods, name=None, extra={}):
    if isinstance(obj, list):
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
    else:
        w = ObjectWrapper(obj)
    w.__patch__(methods, name, extra)
    return w

