import typing
from collections.abc import Iterable as ABCIterable
from collections.abc import Iterator as ABCIterator
from collections.abc import Sequence as ABCSequence
from typing import Optional, Any

from untypy.error import UntypyAttributeError
from untypy.impl.interfaces.iterable import Iterable, Iterator
from untypy.impl.interfaces.sequence import Sequence
from untypy.impl.interfaces.dict import Dict, DictLike
from untypy.impl.interfaces.list import List
from untypy.impl.interfaces.set import Set
from untypy.impl.protocol import ProtocolChecker
from untypy.interfaces import TypeCheckerFactory, TypeChecker, CreationContext

InterfaceMapping = {
    dict: Dict,
    typing.Dict: Dict,
    DictLike: DictLike,
    list: List,
    typing.List: List,
    set: Set,
    typing.Set: Set,
    ABCIterable: Iterable,
    typing.Iterable: Iterable,
    typing.Iterator: Iterator,
    ABCIterator: Iterator,
    ABCSequence: Sequence,
    typing.Sequence: Sequence
}

class InterfaceFactory(TypeCheckerFactory):

    def create_from(self, annotation: Any, ctx: CreationContext, omit_tyargs=False) -> Optional[TypeChecker]:
        if annotation in InterfaceMapping:
            # Assume Any if no parameters are given
            protocol = InterfaceMapping[annotation]
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

        elif hasattr(annotation, '__origin__') and \
            hasattr(annotation, '__args__') and annotation.__origin__ in InterfaceMapping:
            protocol = InterfaceMapping[annotation.__origin__]
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
            bindings = dict(zip(bindings, inner_checkers))
            ctx = ctx.with_typevars(bindings)
            return ProtocolChecker(protocol, ctx, altname=name, omit_tyargs=omit_tyargs, ty=origin)

        # Non Generic
        elif annotation in InterfaceMapping:
            protocol = InterfaceMapping[annotation]
            # Edge-Case `TypingSequence has no __name__, like every other class`
            if annotation == typing.Sequence:
                name = 'Sequence'
            else:
                name = annotation.__name__
            return ProtocolChecker(protocol, ctx, altname=name, omit_tyargs=omit_tyargs, ty=annotation)
        else:
            return None
