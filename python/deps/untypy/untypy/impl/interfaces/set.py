from typing import Generic, TypeVar, Optional, Tuple, Iterable, Any, Iterator

I = TypeVar("I")


class Set(Generic[I], set):

    def add(self, other: I) -> None:
        pass

    def clear(self) -> None:
        pass

    def discard(self, elem: I):
        pass

    def pop(self) -> Optional[I]:
        pass

    def remove(self, elem: I) -> None:
        pass

    def update(self, *others: Tuple[Iterable[I], ...]) -> None:
        pass

    # This method returns `NotImplemented`, i don't know why.
    def __ior__(self, *others: Tuple[Iterable[I], ...]) -> Any:
        pass

    def __contains__(self, key: I) -> bool:
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
