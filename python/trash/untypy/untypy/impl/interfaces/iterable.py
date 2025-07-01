from __future__ import annotations
from typing import Generic, TypeVar, Protocol
import typing

I = TypeVar("I")

# Note: using typing.Iterator as the result creates an indirection that avoids an infinite
# loop when constructing checkers.
class Iterator(Generic[I]):
    def __next__(self) -> I:
        pass
    def __iter__(self) -> typing.Iterator[I]:
        pass

class Iterable(Generic[I]):
    def __iter__(self) -> typing.Iterator[I]:
        pass

class OnlyIterable(Generic[I], Protocol):
    # The __protocol_only__ flag signals that an object wrapped with the protocol should
    # only provide the methods of the protocol.
    __protocol_only__ = True

    def __iter__(self) -> typing.Iterator[I]:
        pass
