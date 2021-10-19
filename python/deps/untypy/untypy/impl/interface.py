from collections.abc import Iterator, Iterable
from typing import TypeVar, Optional, Any, Generic, Dict, List, Set, Tuple, Protocol

from untypy.error import UntypyAttributeError, UntypyTypeError
from untypy.impl.protocol import ProtocolChecker
from untypy.impl.wrappedclass import WrappedType
from untypy.interfaces import TypeCheckerFactory, TypeChecker, CreationContext, ExecutionContext
from untypy.util import ReplaceTypeExecutionContext

A = TypeVar("A")
B = TypeVar("B")


class WDictLike(Protocol[A, B]):
    """
    This protocol implements a subset of dict.
    It exists solly to prevent an recursion issue
    inside of WDict
    """

    def __iter__(self) -> Iterator[A]:
        pass

    def __getitem__(self, item: A) -> B:
        pass


K = TypeVar("K")
V = TypeVar("V")


# See: https://docs.python.org/3/library/stdtypes.html#typesmapping
class WDict(Generic[K, V], dict):
    def clear(self) -> None:
        pass

    # Cannot Typecheck Copy -> Leads to endless recursion in "UntypyInterfaces"
    # def copy(self) -> dict[K,V]:
    #     pass

    def get(self, key: K, default: Optional[V] = None) -> Optional[V]:
        pass

    def items(self) -> Iterable[Tuple[K, V]]:
        pass

    def keys(self) -> Iterable[K]:
        pass

    def pop(self, k: K, default: Optional[V] = None) -> Optional[V]:
        pass

    def popitem(self) -> Tuple[K, V]:
        pass

    # Miss-match See: https://github.com/skogsbaer/write-your-python-program/issues/19
    def setdefault(self, key: K, default: V) -> V:
        pass

    def update(self, *E: Iterable[WDictLike[K, V]], **F: Optional[WDictLike[K, V]]) -> Any:
        pass

    def values(self) -> Iterable[V]:
        pass

    def __contains__(self, key: K) -> bool:
        pass

    def __delitem__(self, key: K) -> None:
        pass

    def __iter__(self) -> Iterator[K]:
        pass

    def __len__(self) -> int:
        pass

    # Untypy does not support generic functions :/
    # def __or__(self, other : dict[I, J]) -> dict[Union[K,I], Union[V,J]]:
    #     pass

    def __reversed__(self) -> Iterator[K]:
        pass

    # Untypy does not support generic functions :/
    # def __ror__(self, other : dict[I, J]) -> dict[Union[K,I], Union[V,J]]:
    #     """ Return value|self. """
    #     pass

    def __getitem__(self, item: K) -> V:
        pass

    def __setitem__(self, key: K, value: V) -> None:
        pass


I = TypeVar("I")


class WList(Generic[I], list):
    def __getitem__(self, item: int) -> I:
        pass

    def __setitem__(self, key: int, value: I) -> None:
        pass


I = TypeVar("I")


class WSet(Generic[I], set):

    def add(self, other: I) -> None:
        pass

    def clear(self) -> None:
        pass

    def discard(self, elem: I):
        pass

    def pop(self) -> I:
        pass

    def remove(self, elem: I) -> None:
        pass

    def update(self, *others: Tuple[Iterable[I], ...]) -> None:
        pass

    # This method returns `NotImplemented`, i don't know why.
    def __ior__(self, *others: Tuple[Iterable[I], ...]) -> Any:
        pass

    def __contains__(self, item: I) -> bool:
        pass

    def __iter__(self) -> Iterator[I]:
        pass

    def __len__(self) -> int:
        pass

    # Only removes elements. No checking needed. Argument type is set Any
    #
    # def intersection_update(self, others: Iterator[set[Any]]) -> None:
    #     pass
    #
    # def __iand__(self, other: set[Any]) -> None:
    #     pass
    #
    # def difference_update(self, others: Iterator[set[Any]]) -> None:
    #     pass
    #
    # def __isub__(self, other: set[Any]) -> None:
    #     pass

    # Mutable meth
    # symmetric_difference_update
    # __ixor__

    # Recursion
    # copy

    # Immutable generic meth
    # difference
    # intersection
    # isdisjoint
    # issubset
    # issuperset
    # symmetric_difference(self, other)
    # union(self, other)
    # __and__
    # __or__
    # __rand__
    # __reduce__ ???
    # __ror__
    # __rsub__
    # __rxor__
    # __sub__
    # __xor__


I = TypeVar("I")


class WIterable(Generic[I]):
    def __iter__(self) -> Iterator[I]:
        pass


InterfaceMapping = {
    dict: (WDict,),
    Dict: (WDict,),
    WDictLike: (WDictLike[K, V],),
    list: (WList,),
    List: (WList,),
    set: (WSet,),
    Set: (WSet,),
    Iterable: (WIterable,),
}

InterfaceFactoryCache = {}


class InterfaceFactory(TypeCheckerFactory):

    def create_from(self, annotation: Any, ctx: CreationContext) -> Optional[TypeChecker]:
        if hasattr(annotation, '__origin__') and hasattr(annotation,
                                                         '__args__') and annotation.__origin__ in InterfaceMapping:
            (protocol,) = InterfaceMapping[annotation.__origin__]
            bindings = protocol.__parameters__  # args of Generic super class
            origin = annotation.__origin__

            inner_checkers = []
            for param in annotation.__args__:
                ch = ctx.find_checker(param)
                if ch is None:
                    raise UntypyAttributeError(f"Could not resolve annotation {param} inside of {annotation}")
                inner_checkers.append(ch)
            if len(inner_checkers) != len(bindings):
                raise UntypyAttributeError(f"Expected {len(bindings)} type arguments inside of {annotation}")

            name = f"{origin.__name__}[" + (', '.join(map(lambda t: t.describe(), inner_checkers))) + "]"

            bindings = dict(zip(bindings, annotation.__args__))
            ctx = ctx.with_typevars(bindings)
            if type(origin) == type:
                template = WrappedType(protocol, ctx.with_typevars(bindings), name=name, implementation_template=origin,
                                       declared=ctx.declared_location())
                return InterfaceChecker(origin, template, name)
            else:
                # type(origin) == collection.abc.ABCMeta
                return ProtocolChecker(protocol, ctx, altname=name)
        else:
            return None


class InterfaceChecker(TypeChecker):

    def __init__(self, origin, template, name):
        self.origin = origin
        self.template = template
        self.name = name
        pass

    def may_change_identity(self) -> bool:
        return True

    def check_and_wrap(self, arg: Any, ctx: ExecutionContext) -> Any:
        if not issubclass(type(arg), self.origin):
            raise ctx.wrap(UntypyTypeError(arg, self.describe()))

        instance = self.template.__new__(self.template)
        instance._WrappedClassFunction__inner = arg
        instance._WrappedClassFunction__return_ctx = ReplaceTypeExecutionContext(ctx, self.name)
        return instance

    def describe(self) -> str:
        return self.name
