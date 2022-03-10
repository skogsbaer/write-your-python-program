import typing
from collections.abc import Iterable as ABCIterable
from collections.abc import Sequence as ABCSequence
from typing import Optional, Any

from untypy.error import UntypyAttributeError, UntypyTypeError, Location, Frame, NO_GIVEN
from untypy.impl.interfaces.iterable import Iterable
from untypy.impl.interfaces.sequence import Sequence
from untypy.impl.interfaces.dict import Dict, DictLike
from untypy.impl.interfaces.list import List
from untypy.impl.interfaces.set import Set
from untypy.impl.protocol import ProtocolChecker
from untypy.impl.wrappedclass import WrappedType
from untypy.interfaces import TypeCheckerFactory, TypeChecker, CreationContext, ExecutionContext
from untypy.util import ReplaceTypeExecutionContext

InterfaceMapping = {
    dict: (Dict,),
    typing.Dict: (Dict,),
    DictLike: (DictLike,),
    list: (List,),
    typing.List: (List,),
    set: (Set,),
    typing.Set: (Set,),
    ABCIterable: (Iterable,),
    typing.Iterable: (Iterable,),
    ABCSequence: (Sequence,),
    typing.Sequence: (Sequence,)
}

class InterfaceFactory(TypeCheckerFactory):

    def create_from(self, annotation: Any, ctx: CreationContext, omit_tyargs=False) -> Optional[TypeChecker]:
        if annotation in InterfaceMapping:
            # Assume Any if no parameters are given
            (protocol,) = InterfaceMapping[annotation]
            bindings = protocol.__parameters__
            if len(bindings) == 0:
                raise AssertionError(f"This is a BUG. {annotation} has no generic params.")

            anys = (Any, ) * len(bindings)
            # handle Python inconsistency
            if hasattr(annotation, '__class_getitem__'):
                return self.create_from(
                    annotation.__class_getitem__(anys),
                    ctx,
                    omit_tyargs=True
                )
            elif hasattr(annotation, '__getitem__'):
                return self.create_from(
                    annotation.__getitem__(anys),
                    ctx,
                    omit_tyargs=True
                )

        elif hasattr(annotation, '__origin__') and hasattr(annotation,
                                                           '__args__') and annotation.__origin__ in InterfaceMapping:
            (protocol,) = InterfaceMapping[annotation.__origin__]
            bindings = protocol.__parameters__  # args of Generic super class
            origin = annotation.__origin__
            inner_checkers = []
            for param in annotation.__args__:
                ch = ctx.find_checker(param)
                if ch is None:
                    raise UntypyAttributeError(f"Could not resolve annotation {param} inside of {annotation}")
                inner_checkers.append(ch)
            if len(inner_checkers) != len(bindings):
                raise UntypyAttributeError(f"Expected {len(bindings)} type arguments inside of {annotation}")

            if omit_tyargs:
                name = f"{origin.__name__}"
            else:
                name = f"{origin.__name__}[" + (', '.join(map(lambda t: t.describe(), inner_checkers))) + "]"

            bindings = dict(zip(bindings, annotation.__args__))
            ctx = ctx.with_typevars(bindings)

            if type(origin) == type:
                template = WrappedType(protocol, ctx.with_typevars(bindings), name=name, implementation_template=origin,
                                       declared=ctx.declared_location(), overwrites=protocol)
                return InterfaceChecker(origin, template, name, ctx.declared_location())
            else:
                # type(origin) == collection.abc.ABCMeta
                return ProtocolChecker(protocol, ctx, altname=name, omit_tyargs=omit_tyargs)

        # Non Generic
        elif annotation in InterfaceMapping:
            (protocol,) = InterfaceMapping[annotation]

            # Edge-Case `TypingSequence has no __name__, like every other class`
            if annotation == typing.Sequence:
                name = 'Sequence'
            else:
                name = annotation.__name__

            if type(annotation) == type:
                template = WrappedType(protocol, ctx, name=name, implementation_template=annotation,
                                       declared=ctx.declared_location(), overwrites=protocol)
                return InterfaceChecker(annotation, template, name, ctx.declared_location())
            else:
                # type(origin) == collection.abc.ABCMeta
                return ProtocolChecker(protocol, ctx, altname=name, omit_tyargs=omit_tyargs)
        else:
            return None


class InterfaceChecker(TypeChecker):

    def __init__(self, origin, template, name, declared):
        self.origin = origin
        self.template = template
        self.name = name
        self.declared = declared
        pass

    def may_change_identity(self) -> bool:
        return True

    def check_and_wrap(self, arg: Any, ctx: ExecutionContext) -> Any:
        if not issubclass(type(arg), self.origin):
            raise ctx.wrap(UntypyTypeError(arg, self.describe()))

        if hasattr(arg, '_WrappedClassFunction__inner'):
            # Prevent Double Wrapping
            arg = arg._WrappedClassFunction__inner

        instance = self.template.__new__(self.template)
        instance._WrappedClassFunction__inner = arg
        instance._WrappedClassFunction__ctx = InterfaceCheckerContext(ctx, arg, self.name, self.declared)
        instance._WrappedClassFunction__return_ctx = ReplaceTypeExecutionContext(ctx, self.name)
        return instance

    def describe(self) -> str:
        return self.name


class InterfaceCheckerContext(ExecutionContext):
    def __init__(self, upper: ExecutionContext, arg: Any, name, declared: Location):
        self.upper = upper
        self.arg = arg
        self.name = name
        self.declared = declared

    def wrap(self, err: UntypyTypeError) -> UntypyTypeError:
        pv = self.upper.wrap(UntypyTypeError(
            given=NO_GIVEN,
        ).with_frame(Frame(
            type_declared=self.name,
            indicator_line="^" * len(self.name),
            responsable=None,
            declared=self.declared,
        )))

        return err.with_previous_chain(pv)
