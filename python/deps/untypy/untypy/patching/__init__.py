import inspect
from collections import namedtuple
from types import FunctionType
from typing import Callable, Protocol

from untypy.error import Location
from untypy.impl import DefaultCreationContext
from untypy.impl.bound_generic import WrappedGenericAlias
from untypy.impl.wrappedclass import WrappedType
from untypy.interfaces import WrappedFunction
from untypy.util.typedfunction import TypedFunctionBuilder

Config = namedtuple('PatchConfig', ['verbose', 'checkedprefixes'])
DefaultConfig = Config(verbose=False, checkedprefixes=[""])
not_patching = ['__class__']

GlobalPatchedList = set()


def patch_class(clas: type, cfg: Config):
    if clas in GlobalPatchedList:
        return clas
    GlobalPatchedList.add(clas)

    try:
        ctx = DefaultCreationContext(
            typevars=dict(),
            declared_location=Location(
                file=inspect.getfile(clas),
                line_no=inspect.getsourcelines(clas)[1],
                line_span=len(inspect.getsourcelines(clas)[0]),
            ), checkedpkgprefixes=cfg.checkedprefixes)
    except (TypeError, OSError) as e:  # Built in types
        ctx = DefaultCreationContext(
            typevars=dict(),
            declared_location=Location(
                file="<not found>",
                line_no=0,
                line_span=1
            ), checkedpkgprefixes=cfg.checkedprefixes,
        )

    setattr(clas, '__patched', True)

    is_protocol = hasattr(clas, 'mro') and Protocol in clas.mro()

    if hasattr(clas, '__class_getitem__') and not is_protocol:
        original = clas.__class_getitem__
        setattr(clas, '__class_getitem__', lambda *args: WrappedGenericAlias(original(*args), ctx))


def wrap_function(fn: FunctionType, cfg: Config) -> Callable:
    if len(inspect.getfullargspec(fn).annotations) > 0:
        if cfg.verbose:
            print(f"Patching Function: {fn.__name__}")
        return TypedFunctionBuilder(fn, DefaultCreationContext(
            typevars=dict(),
            declared_location=WrappedFunction.find_location(fn),
            checkedpkgprefixes=cfg.checkedprefixes, eval_context=fn.__globals__)).build()
    else:
        return fn


def wrap_class(a: type, cfg: Config) -> Callable:
    return WrappedType(a, DefaultCreationContext(
        typevars=dict(),
        declared_location=Location.from_code(a),
        checkedpkgprefixes=cfg.checkedprefixes))
