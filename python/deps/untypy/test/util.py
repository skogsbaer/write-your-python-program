from typing import TypeVar, Any

from untypy.error import UntypyTypeError, Frame, Location
from untypy.impl import DefaultCreationContext
from untypy.interfaces import ExecutionContext, WrappedFunction


class DummyExecutionContext(ExecutionContext):
    def wrap(self, err: UntypyTypeError) -> UntypyTypeError:
        (t, i) = err.next_type_and_indicator()

        return err.with_frame(Frame(
            t,
            i,
            declared=None,
            responsable=Location(
                file="dummy",
                line_no=0,
                line_span=1
            )
        ))


class DummyDefaultCreationContext(DefaultCreationContext):

    def __init__(self, typevars: dict[TypeVar, Any] = dict()):
        super().__init__(typevars.copy(), Location(
            file="dummy",
            line_no=0,
            line_span=1
        ), checkedpkgprefixes=["test"])


def location_of(fn):
    return WrappedFunction.find_location(fn)
