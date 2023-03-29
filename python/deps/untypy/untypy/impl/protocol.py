import abc
import inspect
import sys
import typing
from typing import Protocol, Any, Optional, Callable, Union, TypeVar, Dict, Tuple

import untypy.util.display as display
from untypy.error import UntypyTypeError, UntypyAttributeError, Frame, Location, ResponsibilityType
from untypy.impl.any import SelfChecker, AnyChecker
from untypy.interfaces import TypeCheckerFactory, CreationContext, TypeChecker, ExecutionContext, \
    WrappedFunctionContextProvider
from untypy.util import WrappedFunction, ArgumentExecutionContext, ReturnExecutionContext
from untypy.util.condition import FunctionCondition
from untypy.util.typehints import get_type_hints
import untypy.util.wrapper as wrapper
import untypy.util.typedfunction as typedfun

class ProtocolFactory(TypeCheckerFactory):

    def create_from(self, annotation: Any, ctx: CreationContext) -> Optional[TypeChecker]:
        if isinstance(annotation, type) and Protocol in annotation.mro():
            return ProtocolChecker(annotation, ctx)
        elif hasattr(annotation, '__args__') and \
            hasattr(annotation, '__origin__') and \
            hasattr(annotation.__origin__, '__mro__') and \
            typing.Protocol in annotation.__origin__.__mro__:
            return ProtocolChecker(annotation, ctx)
        else:
            return None


def _find_bound_typevars(clas: type) -> Tuple[type, Dict[TypeVar, Any]]:
    if not hasattr(clas, '__args__') or not hasattr(clas, '__origin__'):
        return (clas, dict())
    if not hasattr(clas.__origin__, '__parameters__'):
        return (clas, dict())

    keys = clas.__origin__.__parameters__
    values = clas.__args__

    if len(keys) != len(values):
        raise UntypyAttributeError(f"Some unbound Parameters in {clas.__name__}. "
                                   f"keys={keys} do not match values={values}.",
                                   [Location(
                                       file=inspect.getfile(clas),
                                       line_no=inspect.getsourcelines(clas)[1],
                                       line_span=len(inspect.getsourcelines(clas)[0]))])
    return (clas.__origin__, dict(zip(keys, values)))


def get_proto_members(proto: type, ctx: CreationContext) -> dict[
    str, Tuple[inspect.Signature, dict[str, TypeChecker], FunctionCondition]]:
    blacklist = ['__init__', '__class__', '__delattr__', '__dict__', '__dir__',
                 '__doc__', '__getattribute__', '__getattr__', '__init_subclass__',
                 '__new__', '__setattr__', '__subclasshook__', '__weakref__',
                 '__abstractmethods__', '__class_getitem__']

    member_dict = {}
    for [name, member] in inspect.getmembers(proto):
        if name in blacklist:
            continue

        if inspect.isfunction(member):
            member = WrappedFunction.find_original(member)
            signature = inspect.signature(member)

            is_typed = len(inspect.getfullargspec(member).annotations) != 0

            checkers = {}
            if not is_typed:
                # Use Any for any type
                for key in signature.parameters:
                    if key == 'self':
                        checkers[key] = SelfChecker()
                    else:
                        checkers[key] = AnyChecker()
                checkers['return'] = AnyChecker()
            else:
                annotations = get_type_hints(member, ctx)
                for key in signature.parameters:
                    if key == 'self':
                        checkers[key] = SelfChecker()
                    else:
                        param = signature.parameters[key]
                        if param.annotation is inspect.Parameter.empty:
                            raise ctx.wrap(UntypyAttributeError(
                                f"Missing annotation for argument '{key}' of function {member.__name__} "
                                f"in protocol {proto.__name__}\n"))

                        param_anot = annotations[key]
                        if param_anot is proto:
                            checker = SimpleInstanceOfChecker(proto, None)
                        else:
                            checker = ctx.find_checker(param_anot)
                        if checker is None:
                            raise ctx.wrap(UntypyAttributeError(f"\n\tUnsupported type annotation: {param.annotation}\n"
                                                                f"for argument '{key}' of function {member.__name__} "
                                                                f"in protocol {proto.__name__}.\n"))
                        checkers[key] = checker

                if signature.return_annotation is inspect.Parameter.empty:
                    return_annotation = None
                else:
                    return_annotation = annotations['return']
                if return_annotation is proto:  # Self as Return Type would led to endless recursion
                    return_checker = SimpleInstanceOfChecker(proto, None)
                else:
                    return_checker = ctx.find_checker(return_annotation)

                if return_checker is None:
                    raise ctx.wrap(UntypyAttributeError(f"\n\tUnsupported type annotation: {signature.return_annotation}\n"
                                                        f"for return value of function {member.__name__} "
                                                        f"in protocol-like {proto.__name__}.\n"))
                checkers['return'] = return_checker

            fc = None
            if hasattr(member, '__fc'):
                fc = getattr(member, '__fc')
            member_dict[name] = (signature, checkers, fc)
    return member_dict


class ProtocolChecker(TypeChecker):
    def __init__(self, annotation: type, ctx: CreationContext, *, altname : Optional[str] = None,
            omit_tyargs=False, ty: Optional[type]=None):
        (proto, typevars) = _find_bound_typevars(annotation)
        self.ctx = ctx.with_typevars(typevars)
        self.proto = proto
        self._members = None
        self.typevars = typevars
        self.altname = altname
        self.omit_tyargs = omit_tyargs
        self.ty = ty

    @property
    def members(self):
        if not self._members:
            self._members = get_proto_members(self.proto, self.ctx)
        return self._members

    def may_change_identity(self) -> bool:
        return True

    def check_and_wrap(self, arg: Any, ctx: ExecutionContext) -> Any:
        if hasattr(arg, '__wrapped__'):
            # no double wrapping
            arg = getattr(arg, '__wrapped__')
        simple = False
        if hasattr(self.proto, '__protocol_only__'):
            simple = getattr(self.proto, '__protocol_only__')
        if self.ty is not None and not isinstance(arg, self.ty):
            err = ctx.wrap(UntypyTypeError(
                expected=self.describe(),
                given=arg
            ))
            raise err
        return wrapForProtocol(self, arg, self.members, ctx, simple=simple)

    def base_type(self) -> list[Any]:
        # Prevent Classes implementing multiple Protocols in one Union by accident.
        if self.ty:
            return [self.ty]
        else:
            return [Protocol]

    def describe(self) -> str:
        if self.altname is not None:
            return self.altname

        desc = set([])
        if not self.omit_tyargs:
            for name in self.members:
                (sig, binds, cond) = self.members[name]
                for argname in sig.parameters:
                    if isinstance(sig.parameters[argname].annotation, TypeVar):
                        desc.add(binds[argname].describe())
                if isinstance(sig.return_annotation, TypeVar):
                    desc.add(binds['return'].describe())
        if len(desc) > 0:
            # FIXME: what about the ordering of tyvars?
            return f"{self.proto.__name__}[" + (', '.join(desc)) + "]"
        else:
            return f"{self.proto.__name__}"

    def protocol_type(self) -> str:
        return f"protocol"

    def protoname(self):
        return self.describe()

def isInternalProtocol(p: Any):
    if isinstance(p, ProtocolChecker):
        p = p.proto
    if hasattr(p, '__module__'):
        return 'untypy.' in p.__module__
    else:
        return False

def protoMismatchErrorMessage(what: str, proto: Any):
    if isinstance(proto, ProtocolChecker):
        kind = proto.protocol_type()
        name = proto.protoname()
    else:
        kind = 'protocol'
        name = proto.__name__
    isUserDefined = True
    if isInternalProtocol(proto):
        isUserDefined = False
    if isUserDefined:
        return f"{what} does not implement {kind} {name}"
    else:
        return f"{what} is not {display.withIndefiniteArticle(name)}"

def wrapForProtocol(protocolchecker: ProtocolChecker,
                    originalValue: Any,
                    members: dict[str, Tuple[inspect.Signature, dict[str, TypeChecker], FunctionCondition]],
                    ctx: ExecutionContext,
                    simple: bool):
    list_of_attr = dict()
    original = type(originalValue)
    for fnname in members:
        if not hasattr(original, fnname):
            err = ctx.wrap(UntypyTypeError(
                expected=protocolchecker.describe(),
                given=originalValue
            )).with_header(
                protoMismatchErrorMessage(original.__name__, protocolchecker.proto)
            )
            missing = []
            for fnname in members:
                if not hasattr(original, fnname):
                    missing.append(fnname)
            if len(missing) == 2:
                err = err.with_note(f"It is missing the functions '{missing[0]}' and '{missing[1]}'")
            elif len(missing) == 1:
                err = err.with_note(f"It is missing the function '{missing[0]}'")
            raise err

        original_fn = getattr(original, fnname)
        try:
            # fails on built ins - YEAH
            original_fn_signature = inspect.signature(original_fn)
        except:
            original_fn_signature = None

        if hasattr(original_fn, '__wf'):
            original_fn = getattr(original_fn, '__wf')
        (sig, baseArgDict, fc) = members[fnname]

        if original_fn_signature is not None:
            err = None
            if len(sig.parameters) > len(original_fn_signature.parameters):
                err = f"The signature of '{fnname}' does not match. Missing required parameters."
            # Special check for self
            if 'self' in sig.parameters and 'self' not in original_fn_signature.parameters:
                err = f"The signature of '{fnname}' does not match. Missing required parameter self."
            if err is not None:
                raise ctx.wrap(UntypyTypeError(
                    expected=protocolchecker.describe(),
                    given=originalValue
                )).with_header(
                    protoMismatchErrorMessage(original.__name__, protocolchecker.proto)
                ).with_note(err)
            paramDict = dict(zip(original_fn_signature.parameters, sig.parameters))
        else:
            paramDict = {}
            for k in sig.parameters:
                paramDict[k] = k

        list_of_attr[fnname] = ProtocolWrappedFunction(original_fn,
                                                       sig,
                                                       baseArgDict,
                                                       protocolchecker,
                                                       paramDict,
                                                       fc).build()

    name = f"WyppTypeCheck({original.__name__}, {protocolchecker.describe()})"
    return wrapper.wrap(originalValue, list_of_attr, name, extra={'ctx': ctx}, simple=simple)

def _getWrappedName(fn):
    if hasattr(fn, '__name__'):
        return fn.__name__
    elif hasattr(fn, 'fget'):
        return fn.fget.__name__
    else:
        raise ValueError(f'Cannot determine name of {fn}')

def _isProperty(fn):
    return isinstance(fn, property)

class ProtocolWrappedFunction(WrappedFunction):

    def __init__(self,
                 inner: Union[Callable, WrappedFunction],
                 signature: inspect.Signature,
                 checker: Dict[str, TypeChecker], # maps argument names from the protocol to checkers
                 protocol: ProtocolChecker,
                 baseArgs: Dict[str, str], # maps arguments names of the implementing class to argument names of the protocol
                 fc: FunctionCondition):
        self.inner = inner
        self.signature = signature
        self.parameters = list(self.signature.parameters.values())
        self.checker = checker
        self.baseArgs = baseArgs
        self.protocol = protocol
        self.fc = fc
        self.fast_sig = typedfun.is_fast_sig(self.parameters, self.fc)

    def build(self):
        fn = WrappedFunction.find_original(self.inner)
        name = _getWrappedName(fn)
        fn_of_protocol = getattr(self.protocol.proto, name)
        if hasattr(fn_of_protocol, '__wf'):
            fn_of_protocol = getattr(fn_of_protocol, '__wf')

        def wrapper(me, *args, **kwargs):
            inner_object = me.__wrapped__
            inner_ctx = me.__extra__['ctx']

            caller = sys._getframe(1)
            (args, kwargs, bind1) = self.wrap_arguments(lambda n: ArgumentExecutionContext(fn_of_protocol, caller, n),
                                                        (inner_object, *args), kwargs)
            if isinstance(self.inner, WrappedFunction):
                (args, kwargs, bind2) = self.inner.wrap_arguments(
                    lambda n: ProtocolArgumentExecutionContext(self, self.baseArgs[n], n,
                                                               inner_object,
                                                               inner_ctx),
                    args, kwargs)
            if _isProperty(fn):
                ret = fn
            else:
                ret = fn(*args, **kwargs)
            if isinstance(self.inner, WrappedFunction):
                ret = self.inner.wrap_return(args, kwargs, ret, bind2,
                    ProtocolReturnExecutionContext(self, ResponsibilityType.IN, inner_object, inner_ctx))
            return self.wrap_return(args, kwargs, ret, bind1,
                ProtocolReturnExecutionContext(self, ResponsibilityType.OUT, inner_object, inner_ctx))

        async def async_wrapper(*args, **kwargs):
            raise AssertionError("Not correctly implemented see wrapper")

        if inspect.iscoroutine(self.inner):
            w = async_wrapper
        else:
            w = wrapper

        setattr(w, '__wrapped__', fn)
        setattr(w, '__name__', name)
        setattr(w, '__signature__', self.signature)
        setattr(w, '__wf', self)
        return w

    def get_original(self):
        return self.inner

    def wrap_arguments(self, ctxprv: WrappedFunctionContextProvider, args, kwargs):
        return typedfun.wrap_arguments(self.parameters, self.checker, self.signature,
            self.fc, self.fast_sig, ctxprv, args, kwargs, expectSelf=True)

    def wrap_return(self, args, kwargs, ret, bindings, ctx: ExecutionContext):
        fc_pair = None
        if self.fc is not None:
            fc_pair = (self.fc, bindings)
        return typedfun.wrap_return(self.checker['return'], args, kwargs, ret, fc_pair, ctx)

    def describe(self) -> str:
        fn = WrappedFunction.find_original(self.inner)
        return f"{fn.__name__}" + str(self.signature)

    def checker_for(self, name: str) -> TypeChecker:
        if name == 'return':
            k = 'return'
        else:
            k = self.baseArgs[name]
        return self.checker[k]

    def declared(self) -> Location:
        fn = WrappedFunction.find_original(self.inner)
        return WrappedFunction.find_location(getattr(self.protocol.proto, fn.__name__))


class ProtocolReturnExecutionContext(ExecutionContext):
    def __init__(self, wf: ProtocolWrappedFunction, invert: ResponsibilityType, me: Any, ctx: ExecutionContext):
        self.wf = wf
        self.invert = invert
        self.me = me
        self.ctx = ctx

    def wrap(self, err: UntypyTypeError) -> UntypyTypeError:
        err = ReturnExecutionContext(self.wf).wrap(err)

        if err.responsibility_type is self.invert:
            return err
        responsable = WrappedFunction.find_location(self.wf)
        (decl, ind) = err.next_type_and_indicator()
        err = err.with_inverted_responsibility_type()
        err = err.with_frame(Frame(
            decl,
            ind,
            declared=self.wf.declared(),
            responsable=responsable
        ))

        inner = self.wf.inner
        if isinstance(inner, WrappedFunction):
            err = err.with_note(
                f"The return value of method '{WrappedFunction.find_original(self.wf).__name__}' does violate the {self.wf.protocol.protocol_type()} '{self.wf.protocol.proto.__name__}'.")
            err = err.with_note(
                f"The annotation '{inner.checker_for('return').describe()}' is incompatible with the {self.wf.protocol.protocol_type()}'s annotation '{self.wf.checker_for('return').describe()}'\nwhen checking against the following value:")

        previous_chain = UntypyTypeError(
            self.me,
            f"{self.wf.protocol.protoname()}"
        ).with_header(
            protoMismatchErrorMessage(type(self.me).__name__, self.wf.protocol)
        )

        previous_chain = self.ctx.wrap(previous_chain)
        if isInternalProtocol(self.wf.protocol):
            return previous_chain
        else:
            return err.with_previous_chain(previous_chain)



class ProtocolArgumentExecutionContext(ExecutionContext):
    def __init__(self, wf: ProtocolWrappedFunction,
                 base_arg: str, this_arg: str, me: Any, ctx: ExecutionContext):
        self.wf = wf
        self.base_arg = base_arg
        self.this_arg = this_arg
        self.me = me
        self.ctx = ctx

    def wrap(self, err: UntypyTypeError) -> UntypyTypeError:
        protocol = self.wf.protocol.proto

        (original_expected, _ind) = err.next_type_and_indicator()
        err = ArgumentExecutionContext(self.wf, None, self.base_arg).wrap(err)

        responsable = WrappedFunction.find_location(self.wf)

        (decl, ind) = err.next_type_and_indicator()
        err = err.with_frame(Frame(
            decl,
            ind,
            declared=self.wf.declared(),
            responsable=responsable
        ))

        base_expected = self.wf.checker_for(self.this_arg).describe()
        if self.base_arg == self.this_arg:
            err = err.with_note(
                f"Argument {self.this_arg} of method {WrappedFunction.find_original(self.wf).__name__} "
                f"violates the type declared by the "
                f"{self.wf.protocol.protocol_type()} {self.wf.protocol.proto.__name__}.")
        else:
            err = err.with_note(
                f"Argument {self.this_arg} of method {WrappedFunction.find_original(self.wf).__name__} "
                f"violates the type declared for {self.base_arg} in "
                f"{self.wf.protocol.protocol_type()} {self.wf.protocol.proto.__name__}.")
        err = err.with_note(
            f"Annotation {original_expected} is incompatible with the "
            f"{self.wf.protocol.protocol_type()}'s annotation "
            f"{base_expected}.")

        previous_chain = UntypyTypeError(
            self.me,
            f"{self.wf.protocol.protoname()}"
        ).with_header(
            protoMismatchErrorMessage(type(self.me).__name__, self.wf.protocol)
        )

        # Protocols can either be declared explicit or implicit.
        if protocol in type(self.me).__mro__:
            # If it is declared explicit (e.g. Inheritance) the
            # declaration of the inheritance has to be blamed.
            previous_chain = previous_chain.with_frame(Frame(
                # /- Could also be `self.wf.describe()`, which would put "right" signature as "context:".
                # v  But this info may be better suited in the note.
                *previous_chain.next_type_and_indicator(),
                declared=Location.from_code(type(self.me)),
                responsable=Location.from_code(type(self.me))
            )).with_frame(Frame(
                *previous_chain.next_type_and_indicator(),
                declared=self.wf.declared(),
                responsable=responsable
            ))
        else:
            # Else: We need to explain how this protocol was declared.
            previous_chain = self.ctx.wrap(previous_chain)

        if isInternalProtocol(self.wf.protocol):
            return previous_chain
        else:
            return err.with_previous_chain(previous_chain)


class SimpleInstanceOfChecker(TypeChecker):
    def __init__(self, annotation: type, ctx: CreationContext):
        self.annotation = annotation

    def check_and_wrap(self, arg: Any, ctx: ExecutionContext) -> Any:
        if isinstance(arg, self.annotation):
            return arg
        else:
            raise ctx.wrap(UntypyTypeError(arg, self.describe()))

    def describe(self) -> str:
        return self.annotation.__name__

    def base_type(self) -> Any:
        return [self.annotation]
