from typing import Generic, TypeVar, Optional, Tuple, Iterable, Any, Iterator
from untypy.impl.interfaces.iterable import OnlyIterable

I = TypeVar("I")

class Set(Generic[I]):
    def add(self, other: I) -> None: pass
    def clear(self) -> None: pass
    def copy(self) -> Any: pass
    def difference(self, *others: Tuple[Iterable, ...]) -> Any: pass
    def difference_update(self, *others: Tuple[Iterable[I], ...]) -> None: pass
    def discard(self, elem: I) -> None: pass
    def intersection(self, *others: Tuple[Iterable, ...]) -> Any: pass
    def intersection_update(self, *others: Tuple[Iterable[I], ...]) -> None: pass
    def isdisjoint(self, other: set) -> bool: pass
    def issubset(self, other: set) -> bool: pass
    def issuperset(self, other: set) -> bool: pass
    def pop(self) -> Optional[I]: pass
    def remove(self, elem: I) -> None: pass
    def symmetric_difference(self, *others: Tuple[Iterable, ...]) -> Any: pass
    def symmetric_difference_update(self, *others: Tuple[Iterable[I], ...]) -> None: pass
    def union(self, *others: Tuple[Iterable, ...]) -> Any: pass

    # Using OnlyIterable here makes no other methods than the one provide in Iterable
    # available. This is required because the implementation of update has shortcuts
    # bypassing type checks if an element is of type set.
    def update(self, *others: Tuple[OnlyIterable[I], ...]) -> None:
        pass

    def __contains__(self, x: Any) -> bool: pass
    def __delattr__(self, name: str) -> None: pass

    def __le__(self, other: Any) -> bool: pass
    def __lt__(self, other: Any) -> bool: pass
    def __ge__(self, other: Any) -> bool: pass
    def __gt__(self, other: Any) -> bool: pass

    def __and__(self, other: set) -> Any: pass
    def __rand__(self, other: set) -> Any: pass
    def __iand__(self, other: set) -> Any: pass
    def __ior__(self, other: set) -> Any: pass # FIXME: result should be set[I]
    def __isub__(self, other: set) -> Any: pass
    def __ixor__(self, other: set) -> Any: pass
    def __or__(self, other: set) -> Any: pass
    def __ror__(self, other: set) -> Any: pass
    def __rxor__(self, other: set) -> Any: pass
    def __xor__(self, other: set) -> Any: pass
    def __rsub__(self, other: set) -> Any: pass
    def __sub__(self, other: set) -> Any: pass

    def __iter__(self) -> Iterator[I]: pass
    def __len__(self) -> int: pass
    def __setattr__(self, name: str, x: Any) -> None: pass
