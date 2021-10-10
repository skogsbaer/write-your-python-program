import sys
from typing import Any, Callable

from untypy.error import Location, UntypyAttributeError, UntypyTypeError, Frame
from untypy.impl import DefaultCreationContext
from untypy.interfaces import ExecutionContext


class StandaloneChecker:
    def __init__(self, annotation : Any, declared : Any, cfg):
        ctx = DefaultCreationContext(
            typevars=dict(),
            declared_location=Location.from_code(declared),
            checkedpkgprefixes=cfg.checkedprefixes)

        checker = ctx.find_checker(annotation)
        if checker is None:
            raise ctx.wrap(UntypyAttributeError(f"\n\tUnsupported type annotation: {annotation}\n"))
        self.checker = checker
        self.declared = declared

    def __call__(self, val):
        frame = sys._getframe(2)
        ctx = StandaloneCheckerContext(frame, self.declared)
        return self.checker.check_and_wrap(val, ctx)

    def __repr__(self):
        return f"<StandaloneChecker for {self.checker.describe()}>"


class StandaloneCheckerContext(ExecutionContext):
    def __init__(self, caller, declared):
        self.caller = caller
        self.declared = declared

    def wrap(self, err: UntypyTypeError) -> UntypyTypeError:
        t, i = err.next_type_and_indicator()
        return err.with_frame(Frame(
            t, i,
            responsable=Location.from_stack(self.caller),
            declared=Location.from_code(self.declared)
        ))