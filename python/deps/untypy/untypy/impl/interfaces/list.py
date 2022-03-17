from typing import TypeVar, Generic, Iterable, Optional, Union, Any, Iterator

from untypy.impl.interfaces.util import overwrite
from untypy.interfaces import CreationContext
from untypy.util import ReturnExecutionContext

I = TypeVar("I")


def sig_getitem():
    def __getitem__(self, key: Union[int, slice]) -> Union[I, list[I]]:
        pass

    return __getitem__


def cast_wlist(lst) -> list:
    if hasattr(lst, '_WrappedClassFunction__inner'):
        return lst._WrappedClassFunction__inner
    else:
        return lst


class List(Generic[I], list):
    # doc @ https://docs.python.org/3/tutorial/datastructures.html
    # and https://docs.python.org/3/library/stdtypes.html#common-sequence-operations
    # Exact signatures are undocumented :/
    # HINT: Argument names must match.

    def append(self, object: I) -> None:
        pass

    def extend(self, iterable: Iterable[I]) -> None:
        pass

    def insert(self, i: int, x: I) -> None:
        pass

    def remove(self, x: I) -> None:
        pass

    def pop(self, i: int = -1) -> Optional[I]:
        pass

    def clear(self) -> None:
        pass

    def index(self, value: I, start: Optional[int] = 0, stop: Optional[int] = 9223372036854775807) -> int:
        # get index of list
        pass

    def count(self, value: I) -> int:
        pass

    def sort(self, *, key: Any = None, reverse: bool = False) -> None:
        # inner list will check type of key.
        pass

    def __contains__(self, key: I) -> bool:
        pass

    def __delitem__(self, i: Union[int, slice]):
        pass

    @overwrite("advanced")
    def __getitem__(self, ctx: CreationContext):
        # self is WrappedClassFunction

        u_checker = ctx.find_checker(Union[int, slice])
        inner_checker = ctx.find_checker(I)

        # TODO: implement some kind caching maybe.
        me_checker = lambda: ctx.find_checker(list[I])

        def inner(me, item):
            ret_ctx = me._WrappedClassFunction__return_ctx
            if ret_ctx is None:
                ret_ctx = ReturnExecutionContext(self)

            if isinstance(item, int):
                item = me._WrappedClassFunction__inner[item]
                return inner_checker.check_and_wrap(item, ret_ctx)
            elif isinstance(item, slice):
                item = me._WrappedClassFunction__inner[item]
                return item
            else:
                # TODO:
                raise NotImplementedError()

        setattr(self, '__original', sig_getitem())
        return inner

    @overwrite("simple")
    def __add__(self, other: Iterable) -> Any:
        return cast_wlist(self) + other

    @overwrite("simple")
    def __mul__(self, n: int) -> Any:
        return cast_wlist(self) * n

    def __iadd__(self, other: Iterable[I]) -> Any:  # returns self
        pass

    def __imul__(self, n: int) -> Any:  # returns self
        pass

    def __setitem__(self, key: Union[int, slice], value: Any) -> None:
        pass

    def __iter__(self) -> Iterator[I]:
        pass

    @overwrite("simple")
    def __radd__(self, other):
        return cast_wlist(other) + cast_wlist(self)

    @overwrite("simple")
    def __lt__(self, other):
        return cast_wlist(self).__lt__(cast_wlist(other))

    @overwrite("simple")
    def __le__(self, other):
        return cast_wlist(self).__le__(cast_wlist(other))

    @overwrite("simple")
    def __eq__(self, other):
        return cast_wlist(self).__eq__(cast_wlist(other))

    @overwrite("simple")
    def __ne__(self, other):
        return cast_wlist(self).__ne__(cast_wlist(other))

    @overwrite("simple")
    def __gt__(self, other):
        return cast_wlist(self).__gt__(cast_wlist(other))

    @overwrite("simple")
    def __ge__(self, other):
        return cast_wlist(self).__ge__(cast_wlist(other))

    # lower type on
    # __add__
    # __mul__
    # copy

    # Type fixed by std impl
    # __repr__
    # __reversed__
    # __len__
    # reverse
