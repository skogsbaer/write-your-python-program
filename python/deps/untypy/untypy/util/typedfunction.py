import inspect
import sys
import typing
from typing import Callable, Dict, Optional

from untypy.error import UntypyAttributeError, UntypyNameError, UntypyTypeError
from untypy.impl.any import SelfChecker
from untypy.interfaces import WrappedFunction, TypeChecker, CreationContext, WrappedFunctionContextProvider, \
    ExecutionContext
from untypy.util import ArgumentExecutionContext, ReturnExecutionContext


class TypedFunctionBuilder(WrappedFunction):
    inner: Callable
    signature: inspect.Signature
    _checkers: Optional[Dict[str, TypeChecker]]

    special_args = ['self', 'cls']
    method_name_ignore_return = ['__init__']

    def __init__(self, inner: Callable, ctx: CreationContext):
        self.inner = inner
        self.signature = inspect.signature(inner)
        self.ctx = ctx
        self.fc = None
        self._checkers = None

        try:
            # try to detect errors like missing arguments as early as possible.
            # but not all type annotations are resolvable yet.
            # so ignore `UntypyNameError`s
            self.checkers()
        except UntypyNameError:
            pass

        if hasattr(self.inner, "__fc"):
            self.fc = getattr(self.inner, "__fc")

    def checkers(self) -> Dict[str, TypeChecker]:
        if self._checkers is not None:
            return self._checkers

            # SEE: https://www.python.org/dev/peps/pep-0563/#id7
        try:
            annotations = typing.get_type_hints(self.inner, include_extras=True)
        except NameError as ne:
            org = WrappedFunction.find_original(self.inner)
            if inspect.isclass(org):
                raise self.ctx.wrap(UntypyNameError(
                    f"{ne}.\nType annotation inside of class '{org.__qualname__}' could not be resolved."
                ))
            else:
                raise self.ctx.wrap(UntypyNameError(
                    f"{ne}.\nType annotation of function '{org.__qualname__}' could not be resolved."
                ))

        checkers = {}
        checked_keys = list(self.signature.parameters)

        # Remove self and cls from checking
        if len(checked_keys) > 0 and checked_keys[0] in self.special_args:
            checkers[checked_keys[0]] = SelfChecker()
            checked_keys = checked_keys[1:]

        for key in checked_keys:
            if self.signature.parameters[key].annotation is inspect.Parameter.empty:
                raise self.ctx.wrap(
                    UntypyAttributeError(f"Missing annotation for argument '{key}' of function {self.inner.__name__}\n"
                                         "Partial annotation are not supported."))
            annotation = annotations[key]
            checker = self.ctx.find_checker(annotation)
            if checker is None:
                raise self.ctx.wrap(UntypyAttributeError(f"\n\tUnsupported type annotation: {annotation}\n"
                                                         f"\tin argument '{key}'"))
            else:
                checkers[key] = checker

        if self.inner.__name__ in self.method_name_ignore_return:
            checkers['return'] = SelfChecker()
        else:
            if not 'return' in annotations:
                raise self.ctx.wrap(
                    UntypyAttributeError(f"Missing annotation for return value of function {self.inner.__name__}\n"
                                         "Partial annotation are not supported. Use 'None' or 'NoReturn' "
                                         "for specifying no return value."))
            annotation = annotations['return']
            return_checker = self.ctx.find_checker(annotation)
            if return_checker is None:
                raise self.ctx.wrap(UntypyAttributeError(f"\n\tUnsupported type annotation: {annotation}\n"
                                                         f"\tin return"))

            checkers['return'] = return_checker

        self._checkers = checkers
        return checkers

    def build(self):
        def wrapper(*args, **kwargs):
            # first is this fn
            caller = sys._getframe(1)
            (args, kwargs, bindings) = self.wrap_arguments(lambda n: ArgumentExecutionContext(self, caller, n), args,
                                                           kwargs)
            ret = self.inner(*args, **kwargs)
            ret = self.wrap_return(ret, bindings, ReturnExecutionContext(self))
            return ret

        if inspect.iscoroutine(self.inner):
            raise UntypyAttributeError("Async functions are currently not supported.")
        else:
            w = wrapper

        setattr(w, '__wrapped__', self.inner)
        setattr(w, '__name__', self.inner.__name__)
        setattr(w, '__signature__', self.signature)
        setattr(w, '__wf', self)
        return w

    def wrap_arguments(self, ctxprv: WrappedFunctionContextProvider, args, kwargs):
        try:
            bindings = self.signature.bind(*args, **kwargs)
        except TypeError as e:
            err = UntypyTypeError(header=str(e))
            raise ctxprv("").wrap(err)

        bindings.apply_defaults()
        if self.fc is not None:
            self.fc.prehook(bindings, ctxprv)
        for name in bindings.arguments:
            check = self.checkers()[name]
            ctx = ctxprv(name)
            bindings.arguments[name] = check.check_and_wrap(bindings.arguments[name], ctx)
        return bindings.args, bindings.kwargs, bindings

    def wrap_return(self, ret, bindings, ctx: ExecutionContext):
        check = self.checkers()['return']
        if self.fc is not None:
            self.fc.posthook(ret, bindings, ctx)
        return check.check_and_wrap(ret, ctx)

    def describe(self):
        return str(self.signature)

    def get_original(self):
        return self.inner

    def checker_for(self, name: str) -> TypeChecker:
        return self.checkers()[name]
