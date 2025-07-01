from typing import Iterator, Protocol, TypeVar, Generic, Optional, Iterable, Tuple, Any

A = TypeVar("A")
B = TypeVar("B")


class DictLike(Protocol[A, B]):
    """
    This protocol implements a subset of dict.
    It exists solly to prevent an recursion issue
    inside of WDict
    """

    def __iter__(self) -> Iterator[A]:
        pass

    def __getitem__(self, key: A) -> B:
        pass


K = TypeVar("K")
V = TypeVar("V")


# See: https://docs.python.org/3/library/stdtypes.html#typesmapping
class Dict(Generic[K, V], dict):
    def clear(self) -> None: pass

    # Cannot Typecheck Copy -> Leads to endless recursion in "UntypyInterfaces"
    # def copy(self) -> dict[K,V]:
    #     pass

    def get(self, key: K, default: Optional[V] = None) -> Optional[V]: pass

    def items(self) -> Iterable[Tuple[K, V]]: pass

    def keys(self) -> Iterable[K]: pass

    def pop(self, k: K, default: Optional[V] = None) -> Optional[V]: pass

    def popitem(self) -> Tuple[K, V]: pass

    # Miss-match See: https://github.com/skogsbaer/write-your-python-program/issues/19
    def setdefault(self, key: K, default: Optional[V]=None) -> V: pass

    def update(self, *E: Iterable[DictLike[K, V]], **F: Optional[DictLike[K, V]]) -> Any: pass

    def values(self) -> Iterable[V]: pass

    def __contains__(self, key: Any) -> bool: pass

    def __delitem__(self, key: K) -> None: pass

    def __iter__(self) -> Iterator[K]: pass

    def __len__(self) -> int: pass

    # Untypy does not support generic functions :/
    def __or__(self, other : dict) -> dict: pass

    def __reversed__(self) -> Iterator[K]: pass

    # Untypy does not support generic functions :/
    def __ror__(self, other : dict) -> dict: pass
    def __getitem__(self, key: K) -> V: pass

    def __setitem__(self, key: K, value: V) -> None: pass
    # FIXME: complete methods
