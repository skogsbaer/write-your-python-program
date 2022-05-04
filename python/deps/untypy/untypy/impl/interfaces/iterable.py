from __future__ import annotations
from typing import Generic, TypeVar
import typing

I = TypeVar("I")

# Note: using typing.Iterator as the result creates an indirection that avoids an infinite
# loop when constructing checkers.
class Iterable(Generic[I]):
    def __iter__(self) -> typing.Iterator[I]:
        pass

T = TypeVar("T")

class Iterator(Generic[T]):
    def __iter__(self) -> typing.Iterator[T]:
        pass
    def __next__(self) -> T:
        pass

