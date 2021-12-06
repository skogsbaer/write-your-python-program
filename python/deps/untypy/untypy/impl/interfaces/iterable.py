from typing import Generic, TypeVar, Iterator

I = TypeVar("I")


class WIterable(Generic[I]):
    def __iter__(self) -> Iterator[I]:
        pass
