from typing import TypeVar, Generic, Optional

I = TypeVar("I")


class Sequence(Generic[I]):
    # See https://docs.python.org/3/library/collections.abc.html

    def __getitem__(self, key: int) -> I:
        pass

    def __len__(self) -> int:
        pass

    def __contains__(self, key: I) -> bool:
        pass

    def index(self, value: I, start: Optional[int] = None, stop: Optional[int] = None) -> int:
        pass

    def count(self, value: I) -> int:
        pass

    # For these Methods: `iter` and `reversed` will fallback to `__getitem__` and `__len__`
    # This is just an optimization for some types.
    # Maybe for a future feature.

    # def __iter__(self) -> Iterator[I]:
    #    pass

    # def __reversed__(self) -> Iterator[I]:
    #    pass
