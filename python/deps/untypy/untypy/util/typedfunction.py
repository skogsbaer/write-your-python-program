import inspect
import sys
from typing import Callable, Dict, Optional

from untypy.error import UntypyAttributeError, UntypyNameError, UntypyTypeError
from untypy.impl.any import SelfChecker
from untypy.interfaces import WrappedFunction, TypeChecker, CreationContext, WrappedFunctionContextProvider, \
    ExecutionContext
from untypy.util import ArgumentExecutionContext, ReturnExecutionContext
from untypy.util.typehints import get_type_hints

class FastTypeError(TypeError):
    pass

class TypedFunctionBuilder(WrappedFunction):
    inner: Callable
    signature: inspect.Signature
    _checkers: Optional[Dict[str, TypeChecker]]

    special_args = ['self', 'cls']
    method_name_ignore_return = ['__init__']

    def __init__(self, inner: Callable, ctx: CreationContext):
        self.inner = inner
        self.signature = inspect.signature(inner)
        self.parameters = list(self.signature.parameters.values())
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

        # The self.fast_sig flags tells wether the signature supports fast matching of arguments.
        # We identified (2022-05-05) that self.wrap_arguments is a performence bottleneck.
        # With type annotations, the performance was factor 8.8 slower than without type
        # annotations
        # So we now have a fastlane for the common case where there are no kw and no variable
        # arguments. For the fastlane, performance is only factor 3.7 slower.
        if hasattr(self.inner, "__fc"):
            self.fc = getattr(self.inner, "__fc")
            self.fast_sig = False
        else:
            self.fast_sig = True
            for p in self.parameters:
                # See https://docs.python.org/3/glossary.html#term-parameter for the
                # different kinds of parameters
                if p.kind != inspect._POSITIONAL_ONLY and p.kind != inspect._POSITIONAL_OR_KEYWORD:
                    self.fast_sig = False
                    break

    def checkers(self) -> Dict[str, TypeChecker]:
        if self._checkers is not None:
            return self._checkers

        annotations = get_type_hints(self.inner, self.ctx)

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
                annotation = None
            else:
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

        # Copy useful attributes
        # This is need for the detection of abstract classes
        for attr in ['__isabstractmethod__']:
            if hasattr(self.inner, attr):
                setattr(w, attr, getattr(self.inner, attr))

        return w

    def wrap_arguments_fast(self, ctxprv: WrappedFunctionContextProvider, args):
        # Fast case: no kwargs, no rest args, self.fc is None.
        # (self.fc is used for pre- and postconditions, a rarely used feature.)
        # In this case, the order parameter names in args and self.parameters is the
        # same, so we can simply match them by position. As self.fc is None, we do not
        # need to build a inspect.BoundArguments object.
        params = self.parameters
        n = len(params)
        n_args = len(args)
        wrapped_args = [None] * n
        checkers = self.checkers()
        for i in range(n):
            p = params[i]
            name = params[i].name
            if i < n_args:
                a = args[i]
            else:
                a = p.default
                if a == inspect._empty:
                    raise FastTypeError(f"missing a required argument: {name!r}") from None
            check = checkers[name]
            ctx = ctxprv(name)
            wrapped = check.check_and_wrap(a, ctx)
            wrapped_args[i] = wrapped
        return (wrapped_args, {}, None)

    def wrap_arguments(self, ctxprv: WrappedFunctionContextProvider, args, kwargs):
        if not kwargs and self.fast_sig:
            try:
                return self.wrap_arguments_fast(ctxprv, args)
            except FastTypeError as e:
                err = UntypyTypeError(header=str(e))
                raise ctxprv("").wrap(err)

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
