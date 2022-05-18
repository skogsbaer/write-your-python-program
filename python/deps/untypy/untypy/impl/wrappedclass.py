import inspect
import sys
from types import ModuleType
from typing import Any, Callable, Union, Optional

import untypy.util.typedfunction as typedfun
from untypy.error import Location, UntypyAttributeError
from untypy.impl.any import SelfChecker, AnyChecker
from untypy.interfaces import TypeChecker, CreationContext, ExecutionContext, WrappedFunction, \
    WrappedFunctionContextProvider
from untypy.util import ArgumentExecutionContext, ReturnExecutionContext


def find_signature(member, ctx: CreationContext):
    signature = inspect.signature(member)

    checkers = {}
    for key in signature.parameters:
        if key == 'self':
            checkers[key] = SelfChecker()
        else:
            param = signature.parameters[key]
            if param.annotation is inspect.Parameter.empty:
                checkers[key] = AnyChecker()
                continue

            checker = ctx.find_checker(param.annotation)
            if checker is None:
                checkers[key] = AnyChecker()
                continue
            checkers[key] = checker

    if signature.return_annotation is inspect.Parameter.empty:
        checkers['return'] = AnyChecker()
    else:
        return_checker = ctx.find_checker(signature.return_annotation)
        if return_checker is None:
            raise ctx.wrap(UntypyAttributeError(f"\n\tUnsupported Type Annotation: {signature.return_annotation}\n"
                                                f"for Return Value of function {member.__name__}\n"))
        checkers['return'] = return_checker
    return signature, checkers


def WrappedType(template: Union[type, ModuleType], ctx: CreationContext, *,
                implementation_template: Union[type, ModuleType, None] = None,
                create_type: Optional[type] = None,
                name: Optional[str] = None,
                declared: Optional[Location] = None,
                overwrites: Optional[type] = None):
    # raise ValueError("dead?")
    blacklist = ['__class__', '__delattr__', '__dict__', '__dir__',
                 '__doc__', '__getattribute__', '__getattr__', '__init_subclass__',
                 '__new__', '__setattr__', '__subclasshook__', '__weakref__']

    create_fn = None
    if create_type is not None:
        create_fn = lambda: create_type.__new__(create_type)

    if type(template) is type and create_type is None:
        create_fn = lambda: template.__new__(template)

    if implementation_template is None:
        implementation_template = template

    if create_fn is None:
        def raise_err():
            raise TypeError("This is not a Callable")

        create_fn = raise_err

    list_of_attr = dict()

    for attr in dir(template):
        if attr in blacklist:
            continue

        if overwrites is not None and hasattr(overwrites, attr):
            a = getattr(overwrites, attr)
            if hasattr(a, '__overwrite') and getattr(a, '__overwrite') == 'simple':
                list_of_attr[attr] = getattr(overwrites, attr)
                continue

        original = getattr(template, attr)
        if type(original) == type:  # Note: Order matters, types are also callable
            if type(template) is type:
                list_of_attr[attr] = WrappedType(original, ctx)

        elif callable(original):
            try:
                (signature, checker) = find_signature(original, ctx)
            except ValueError as e:
                # this fails sometimes on built-ins.
                # "ValueError: no signature found for builtin"

                # So we use the most generic class signature:
                # (must be the signature of a class because of 'self')
                class Dummy:
                    def method(self, *args, **kwargs) -> Any:
                        pass

                (signature, checker) = find_signature(Dummy.method, ctx)

            implementation_fn = getattr(implementation_template, attr)
            if implementation_fn is not None:
                if overwrites is not None and \
                        hasattr(overwrites, attr) and \
                        hasattr(getattr(overwrites, attr), '__overwrite') and \
                        getattr(getattr(overwrites, attr), '__overwrite') == 'advanced':
                    list_of_attr[attr] = WrappedClassFunction(implementation_fn, signature, checker,
                                                              create_fn=create_fn,
                                                              declared=declared).build_overwrite(
                        getattr(overwrites, attr), ctx)
                else:
                    list_of_attr[attr] = WrappedClassFunction(implementation_fn, signature, checker,
                                                              create_fn=create_fn, declared=declared).build()
    out = None
    if type(template) is type:
        if name is None:
            name = f"{template.__name__}Wrapped"
        out = type(name, (template,), list_of_attr)
    elif inspect.ismodule(template):
        out = type("WrappedModule", (), list_of_attr)

    return out


class WrappedClassFunction(WrappedFunction):
    def __init__(self,
                 inner: Callable,
                 signature: inspect.Signature,
                 checker: dict[str, TypeChecker], *,
                 create_fn: Callable[[], Any],
                 declared: Optional[Location] = None):
        self.inner = inner
        self.signature = signature
        self.parameters = list(self.signature.parameters.values())
        self.checker = checker
        self.create_fn = create_fn
        self._declared = declared
        self.fc = None
        if hasattr(self.inner, "__fc"):
            self.fc = getattr(self.inner, "__fc")
        self.fast_sig = typedfun.is_fast_sig(self.parameters, self.fc)

    def build_overwrite(self, f, ctx: CreationContext):
        fn = self.inner

        w = f(self, ctx)

        setattr(w, '__wrapped__', fn)
        setattr(w, '__name__', fn.__name__)
        setattr(w, '__signature__', self.signature)
        setattr(w, '__wf', self)
        return w

    def build(self):
        fn = self.inner
        name = fn.__name__

        def wrapper_cls(*args, **kwargs):
            caller = sys._getframe(1)
            (args, kwargs, bindings) = self.wrap_arguments(
                lambda n: ArgumentExecutionContext(wrapper_cls, caller, n, declared=self.declared()),
                args, kwargs)
            ret = fn(*args, **kwargs)
            return self.wrap_return(args, kwargs, ret, bindings, ReturnExecutionContext(self))

        def wrapper_self(me, *args, **kwargs):
            if name == '__init__':
                me.__return_ctx = None
                me.__ctx = None
                me.__inner = self.create_fn()
            caller = sys._getframe(1)
            (args, kwargs, bindings) = self.wrap_arguments(
                lambda n: ArgumentExecutionContext(wrapper_self, caller, n, declared=self.declared(), upper=me.__ctx),
                (me.__inner, *args), kwargs)
            ret = fn(*args, **kwargs)
            if me.__return_ctx is None:
                return self.wrap_return(args, kwargs, ret, bindings, ReturnExecutionContext(self))
            else:
                return self.wrap_return(args, kwargs, ret, bindings, me.__return_ctx)

        if inspect.iscoroutine(self.inner):
            raise UntypyAttributeError("Async Functions are currently not supported.")
        else:
            if 'self' in self.checker:
                w = wrapper_self
            else:
                w = wrapper_cls

        setattr(w, '__wrapped__', fn)
        setattr(w, '__name__', fn.__name__)
        setattr(w, '__signature__', self.signature)
        setattr(w, '__wf', self)
        return w

    def get_original(self):
        return self.inner

    def wrap_arguments(self, ctxprv: WrappedFunctionContextProvider, args, kwargs):
        return typedfun.wrap_arguments(self.parameters, self.checker, self.signature,
                                       self.fc, self.fast_sig, ctxprv, args, kwargs, expectSelf=True)

    def wrap_return(self, args, kwds, ret, bindings, ctx: ExecutionContext):
        fc_pair = None
        if self.fc is not None:
            fc_pair = (self.fc, bindings)
        return typedfun.wrap_return(self.checker['return'], args, kwds, ret, fc_pair, ctx)

    def describe(self) -> str:
        fn = WrappedFunction.find_original(self.inner)
        return f"{fn.__name__}" + str(self.signature)

    def checker_for(self, name: str) -> TypeChecker:
        return self.checker[name]

    def declared(self) -> Location:
        if self._declared is None:
            return WrappedFunction.find_location(self.inner)
        else:
            return self._declared
