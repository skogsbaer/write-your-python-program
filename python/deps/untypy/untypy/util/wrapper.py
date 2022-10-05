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
    def __ne__(self, other):
        return not self.__eq__(other)
    def __hash__(self):
        return hash(self.__wrapped__)
    def __patch__(self, ms, name=None, extra={}):
        cls = self.__class__
        if name is None:
            name = cls.__name__
        ty = type(name, (cls,), ms)
        patch(self, ty, extra)
    def __repr__(self):
        #w = self.__wrapped__
        #return f"Wrapper(addr=0x{id(self):09x}, wrapped_addr=0x{id(w):09x}, wrapped={repr(w)}"
        return repr(self.__wrapped__)
    def __str__(self):
        return str(self.__wrapped__)
    def __cast__(self, other):
        if type(other) == type(self) and hasattr(other, '__wrapped__'):
            return other.__wrapped__
        else:
            return other
    def __reduce__(self): return self.__wrapped__.__reduce__()
    def __reduce_ex__(self): return self.__wrapped__.__reduce_ex__()
    def __sizeof__(self): return self.__wrapped__.__sizeof__()

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

# A wrapper for list such that the class is a subclass of the builtin list class.
# A wrapper for list such that the class is a subclass of the builtin list class.
class ListWrapper(WrapperBase, list): # important: inherit from WrapperBase first
    def __new__(cls, content):
        # the constructor of list copies the list passed to it. Thus, we use an empty list.
        # IMPORTANT: we need to override *all* methods provided by list so that
        # all methods operate on the list being wrapped.
        self = super().__new__(cls, [])
        self.__wrapped__ = content
        return self
    # defined in WrapperBase: __repr__, __str__, __eq__, __hash__
    def __lt__(self, other): return self.__wrapped__.__lt__(self.__cast__(other))
    def __le__(self, other): return self.__wrapped__.__le__(self.__cast__(other))
    def __gt__(self, other): return self.__wrapped__.__gt__(self.__cast__(other))
    def __ge__(self, other): return self.__wrapped__.__ge__(self.__cast__(other))
    def __contains__(self, item): return self.__wrapped__.contains(item)
    def __len__(self): return self.__wrapped__.__len__()
    def __getitem__(self, i): return self.__wrapped__.__getitem__(i)
    def __setitem__(self, i, x): return self.__wrapped__.__setitem__(i, x)
    def __delitem__(self, i): return self.__wrapped__.__delitem__(i)
    def __add__(self, other): return self.__wrapped__.__add__(self.__cast__(other))
    def __radd__(self, other): return self.__cast__(other) + self.__wrapped__
    def __iadd__(self, other): return self.__wrapped__.__iadd__(self.__cast__(other))
    def __mul__(self, n): return self.__wrapped__.__mul__(n)
    __rmul__ = __mul__
    def __imul__(self, n): return self.__wrapped__.__imul__(n)
    def __iter__(self): return self.__wrapped__.__iter__()
    def __copy__(self): return self.__wrapped__.copy()
    def __reversed__(self): return self.__wrapped__.__reversed__()
    def append(self, item): return self.__wrapped__.append(item)
    def extend(self, iter): return self.__wrapped__.extend(iter)
    def insert(self, i, item): return self.__wrapped__.insert(i, item)
    def pop(self, i=-1): return self.__wrapped__.pop(i)
    def remove(self, item): return self.__wrapped__.remove(item)
    def clear(self): return self.__wrapped__.clear()
    def copy(self): return self.__wrapped__.copy()
    def count(self, item): return self.__wrapped__.count(item)
    def index(self, item, *args): return self.__wrapped__.index(item, *args)
    def reverse(self): return self.__wrapped__.reverse()
    def sort(self, /, *args, **kwds): return self.__wrapped__.sort(*args, **kwds)

class SetWrapper(WrapperBase, set):
    def __new__(cls, content):
        self = super().__new__(cls, set())
        self.__wrapped__ = content
        return self
    def add(self, x): return self.__wrapped__.add(x)
    def clear(self): return self.__wrapped__.clear()
    def copy(self): return self.__wrapped__.copy()
    def difference(self, *others): return self.__wrapped__.difference(*others)
    def difference_update(self, *others): return self.__wrapped__.difference_update(*others)
    def discard(self, elem): return self.__wrapped__.discard(elem)
    def intersection(self, *others): return self.__wrapped__.intersection(*others)
    def intersection_update(self, *others): return self.__wrapped__.intersection_update(*others)
    def isdisjoint(self, other): return self.__wrapped__.isdisjoint(other)
    def issubset(self, other): return self.__wrapped__.issubset(other)
    def issuperset(self, other): return self.__wrapped__.issuperset(other)
    def pop(self): return self.__wrapped__.pop()
    def remove(self, elem): return self.__wrapped__.remove(elem)
    def symmetric_difference(self, *others): return self.__wrapped__.symmetric_difference(*others)
    def symmetric_difference_update(self, *others): return self.__wrapped__.symmetric_difference_update(*others)
    def union(self, *others): return self.__wrapped__.union(*others)
    def update(self, *others): return self.__wrapped__.update(*others)
    def __contains__(self, x): return self.__wrapped__.__contains__(x)
    def __le__(self, other): return self.__wrapped__.__le__(self.__cast__(other))
    def __lt__(self, other): return self.__wrapped__.__lt__(self.__cast__(other))
    def __ge__(self, other): return self.__wrapped__.__ge__(self.__cast__(other))
    def __gt__(self, other): return self.__wrapped__.__gt__(self.__cast__(other))
    def __and__(self, other): return self.__wrapped__.__and__(self.__cast__(other))
    def __rand__(self, other): return self.__wrapped__.__rand__(self.__cast__(other))
    def __iand__(self, other): return self.__wrapped__.__iand__(self.__cast__(other))
    def __ior__(self, other): return self.__wrapped__.__ior__(self.__cast__(other))
    def __ixor__(self, other): return self.__wrapped__.__ixor__(self.__cast__(other))
    def __or__(self, other): return self.__wrapped__.__or__(self.__cast__(other))
    def __ror__(self, other): return self.__wrapped__.__ror__(self.__cast__(other))
    def __rxor__(self, other): return self.__wrapped__.__rxor__(self.__cast__(other))
    def __xor__(self, other): return self.__wrapped__.__xor__(self.__cast__(other))
    def __rsub__(self, other): return self.__wrapped__.__rsub__(self.__cast__(other))
    def __sub__(self, other): return self.__wrapped__.__sub__(self.__cast__(other))
    def __isub__(self, other): return self.__wrapped__.__isub__(self.__cast__(other))
    def __iter__(self): return self.__wrapped__.__iter__()
    def __len__(self): return self.__wrapped__.__len__()

class DictWrapper(WrapperBase, dict):
    def __new__(cls, content):
        self = super().__new__(cls, {})
        self.__wrapped__ = content
        return self
    def __len__(self): return self.__wrapped__.__len__()
    def __getitem__(self, key): return self.__wrapped__.__getitem__(key)
    def __setitem__(self, key, item): return self.__wrapped__.__setitem__(key, item)
    def __delitem__(self, key): return self.__wrapped__.__delitem__(key)
    def __iter__(self): return self.__wrapped__.__iter__()
    def __contains__(self, key): return self.__wrapped__.__contains__(key)
    def __or__(self, other): return self.__wrapped__.__or__(self.__cast__(other))
    def __ror__(self, other): return self.__wrapped__.__ror__(self.__cast__(other))
    def __ior__(self, other): return self.__wrapped__.__ior__(self.__cast__(other))
    def __copy__(self): return self.__wrapped__.__copy__()
    def __lt__(self, other): return self.__wrapped__.__lt__(self.__cast__(other))
    def __le__(self, other): return self.__wrapped__.__le__(self.__cast__(other))
    def __gt__(self, other): return self.__wrapped__.__gt__(self.__cast__(other))
    def __ge__(self, other): return self.__wrapped__.__ge__(self.__cast__(other))
    def copy(self): return self.__wrapped__.copy()
    def __reversed__(self): return self.__wrapped__.__reversed__()
    __marker = object()
    def pop(self, key, default=__marker):
        if default == self.__marker:
            return self.__wrapped__.pop(key)
        else:
            return self.__wrapped__.pop(key, default)
    def popitem(self): return self.__wrapped__.popitem()
    def clear(self): return self.__wrapped__.clear()
    def update(self, other=(), /, **kwds): return self.__wrapped__.update(self.__cast__(other), **kwds)
    def setdefault(self, key, default=None): return self.__wrapped__.setdefault(key, default=default)
    def get(self, key, default=None): return self.__wrapped__.get(key, default)
    def keys(self): return self.__wrapped__.keys()
    def items(self): return self.__wrapped__.items()
    def values(self): return self.__wrapped__.values()

# Tuple and string wrapper are simpler because these types are immutable
class StringWrapper(str, WrapperBase):
    def __new__(cls, content):
        self = super().__new__(cls, content)
        self.__wrapped__ = content
        return self

class TupleWrapper(tuple, WrapperBase):
    def __new__(cls, content):
        self = super().__new__(cls, content)
        self.__wrapped__ = content
        return self

# These methods are not delegated to the wrapped object
_blacklist = [
    '__class__', '__delattr__', '__dict__', '__dir__', '__doc__',
    '__getattribute__', '__get_attr_', '__init_subclass__'
    '__init__', '__new__', '__del__', '__repr__', '__setattr__', '__str__',
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
        ty = type(name, (cls,), ms) #
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
    wname = name
    if wname is None:
        wname = str(type(w))
    debug(f"Wrapping {obj} at 0x{id(obj):09x} as {wname}, simple={simple}, wrapper=0x{id(w):09x}")
    return w
