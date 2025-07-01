from typing import TypeVar, Generic, Iterable, Optional, Union, Any, Iterator
import typing
from untypy.impl.interfaces.util import overwrite
from untypy.impl.choice import Choice
from untypy.interfaces import CreationContext
from untypy.util import ReturnExecutionContext
from untypy.util.condition import postcondition

I = TypeVar("I")

class List(Generic[I], list):
    # doc @ https://docs.python.org/3/tutorial/datastructures.html
    # and https://docs.python.org/3/library/stdtypes.html#common-sequence-operations
    # Exact signatures are undocumented :/
    # HINT: Argument names must match.

    def append(self, object: I) -> None: pass

    def extend(self, iterable: Iterable[I]) -> None: pass

    def insert(self, i: int, x: I) -> None: pass

    def remove(self, x: I) -> None: pass

    def pop(self, i: int = -1) -> Optional[I]: pass

    def clear(self) -> None: pass

    def index(self, value: I, start: Optional[int] = 0, stop: Optional[int] = 9223372036854775807) -> int:
        # get index of list
        pass

    def count(self, value: I) -> int: pass

    # inner list will check type of key.
    def sort(self, *, key: Any = None, reverse: bool = False) -> None: pass

    def __contains__(self, key: Any) -> bool: pass

    def __delitem__(self, i: Union[int, slice]): pass

    def __getitem__(self, i: Union[int, slice]) -> \
        Choice[I, Any, lambda self, i, kws, ti, tl: ti if isinstance(i, int) else tl]: pass

    def __add__(self, other: Iterable) -> Any: pass

    def __mul__(self, n: int) -> Any: pass

    def __iadd__(self, other: Iterable[I]) -> Any: pass

    def __imul__(self, n: int) -> Any: pass

    def __setitem__(self, key: Union[int, slice], value: Any) -> None: pass

    def __iter__(self) -> Iterator[I]: pass
    # FIXME: complete methods
