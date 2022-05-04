from __future__ import annotations
from typing import Generic, TypeVar

I = TypeVar("I")

class Iterable(Generic[I]):
    def __iter__(self) -> Iterator[I]:
        pass

class Iterator(Generic[I]):
    def __iter__(self) -> Iterator[I]:
        pass
    def __next__(self) -> I:
        pass

