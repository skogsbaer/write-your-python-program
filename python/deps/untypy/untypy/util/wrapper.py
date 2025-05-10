import typing
import collections
from untypy.util.debug import debug

def _f():
    yield 0
generatorType = type(_f())

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
    def __repr__(self):
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

# SimpleWrapper is a fallback for types that cannot be used as base types
class SimpleWrapper(WrapperBase):
    def __init__(self, wrapped):
        self.__wrapped__ = wrapped

class ValuesViewWrapper(SimpleWrapper):
    pass
collections.abc.ValuesView.register(ValuesViewWrapper)

class ItemsViewWrapper(SimpleWrapper):
    pass
collections.abc.ItemsView.register(ItemsViewWrapper)

class KeysViewWrapper(SimpleWrapper):
    pass
collections.abc.KeysView.register(KeysViewWrapper)

def _wrap(wrapped, methods, mod, name, extra, cls):
    if extra is None:
        extra = {}
    # Dynamically create a new class:
    # type(class_name, base_classes, class_dict)
    WrapperClass = type(
        name,
        (cls,),
        methods
    )
    WrapperClass.__module__ = mod
    w = WrapperClass(wrapped)
    w.__extra__ = extra
    return w

def wrapSimple(wrapped, methods, name, extra, cls=SimpleWrapper):
    if name is None:
        name = cls.__name__
        mod = None
    else:
        if hasattr(wrapped, '__module__'):
            mod = wrapped.__module__
        else:
            mod = None
    for x in ['__next__', '__iter__']:
        if x not in methods and hasattr(wrapped, x):
            attr = getattr(wrapped, x)
            methods[x] = attr
    return _wrap(wrapped, methods, mod, name, extra, cls)

def wrapObj(wrapped, methods, name, extra):
    class BaseWrapper(WrapperBase, wrapped.__class__):
        def __init__(self, wrapped):
            self.__dict__ = wrapped.__dict__
            self.__wrapped__ = wrapped
    if name is None:
        name = 'ObjectWrapper'
    if hasattr(wrapped, '__module__'):
        mod = getattr(wrapped, '__module__')
    else:
        mod = None
    return _wrap(wrapped, methods, mod, name, extra, BaseWrapper)

def wrapBuiltin(wrapped, methods, name, extra, cls):
    if name is None:
        name = cls.__name__
    return _wrap(wrapped, methods, None, name, extra, cls)

def wrap(obj, methods, name=None, extra=None, simple=False):
    if extra is None:
        extra = {}
    wrapper = None
    if simple:
        w = wrapSimple(obj, methods, name, extra)
        wrapper = 'SimpleWrapper'
    elif isinstance(obj, list):
        w = wrapBuiltin(obj, methods, name, extra, ListWrapper)
        wrapper = 'ListWrapper'
    elif isinstance(obj, tuple):
        w = wrapBuiltin(obj, methods, name, extra, TupleWrapper)
        wrapper = 'TupleWrapper'
    elif isinstance(obj, dict):
        w = wrapBuiltin(obj, methods, name, extra, DictWrapper)
        wrapper = 'DictWrapper'
    elif isinstance(obj, str):
        w = wrapBuiltin(obj, methods, name, extra, StringWrapper)
        wrapper = 'StringWrapper'
    elif isinstance(obj, set):
        w = wrapBuiltin(obj, methods, name, extra, SetWrapper)
        wrapper = 'SetWrapper'
    elif isinstance(obj, collections.abc.ValuesView):
        w = wrapSimple(obj, methods, name, extra, ValuesViewWrapper)
        wrapper = 'ValuesViewWrapper'
    elif isinstance(obj, collections.abc.KeysView):
        w = wrapSimple(obj, methods, name, extra, KeysViewWrapper)
        wrapper = 'KeysViewWrapper'
    elif isinstance(obj, collections.abc.ItemsView):
        w = wrapSimple(obj, methods, name, extra, ItemsViewWrapper)
        wrapper = 'ItemsViewWrapper'
    elif isinstance(obj, typing.Generic):
        w = wrapSimple(obj, methods, name, extra)
        wrapper = 'SimpleWrapper'
    elif isinstance(obj, generatorType):
        w = wrapSimple(obj, methods, name, extra)
        wrapper = 'SimpleWrapper'
    elif hasattr(obj, '__dict__'):
        w = wrapObj(obj, methods, name, extra)
        wrapper = 'ObjectWrapper'
    else:
        w = wrapSimple(obj, methods, name, extra)
        wrapper = 'SimpleWrapper'
    wname = name
    if wname is None:
        wname = str(type(w))
    debug(f"Wrapping {obj} at 0x{id(obj):09x} as {wname}, simple={simple}, wrapper=0x{id(w):09x} ({wrapper})")
    return w
