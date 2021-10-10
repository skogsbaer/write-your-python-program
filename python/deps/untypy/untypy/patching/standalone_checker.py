import sys
from typing import Any, Callable

from untypy.error import Location, UntypyAttributeError, UntypyTypeError, Frame, UntypyNameError
from untypy.impl import DefaultCreationContext
from untypy.interfaces import ExecutionContext


class StandaloneChecker:
    def __init__(self, annotation: Callable[[], Any], declared: Any, cfg):
        self._checker = None
        self.annotation = annotation
        self.declared = declared
        self.cfg = cfg

    def get_checker(self):
        if self._checker:
            return self._checker

        ctx = DefaultCreationContext(
            typevars=dict(),
            declared_location=Location.from_code(self.declared),
            checkedpkgprefixes=self.cfg.checkedprefixes)
        try:
            annotation = self.annotation()
        except NameError as ne:
            raise ctx.wrap(UntypyNameError(
                f"{ne}.\nType annotation could not be resolved."
            ))

        checker = ctx.find_checker(annotation)
        if checker is None:
            raise ctx.wrap(UntypyAttributeError(f"\n\tUnsupported type annotation: {self.annotation}\n"))
        self._checker = checker
        return checker

    def __call__(self, val):
        frame = sys._getframe(2)
        checker = self.get_checker()
        ctx = StandaloneCheckerContext(frame, self.declared)
        return checker.check_and_wrap(val, ctx)

    def __repr__(self):
        return f"<StandaloneChecker for {self.get_checker().describe()}>"


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