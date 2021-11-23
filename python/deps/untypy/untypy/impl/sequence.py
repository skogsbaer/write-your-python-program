from collections.abc import Sequence as ABCSequence
from typing import Any, Optional, Sequence

from untypy.impl.simple import SimpleFactory
from untypy.impl.union import UnionChecker
from untypy.interfaces import TypeChecker, TypeCheckerFactory, CreationContext

SequenceTypeA = type(Sequence[int])
SequenceTypeB = type(ABCSequence[int])


class SequenceFactory(TypeCheckerFactory):

    def create_from(self, annotation: Any, ctx: CreationContext) -> Optional[TypeChecker]:
        t = type(annotation)
        if (t in [SequenceTypeA, SequenceTypeB] and annotation.__origin__ in [Sequence, ABCSequence]) or \
                annotation in [Sequence, ABCSequence]:  # no args version
            try:
                args = annotation.__args__
            except AttributeError:
                args = []
            inner = []
            elemChecker = None
            if len(args) == 0 or len(args == 1):
                # TODO: Reimplement ME using Interface.py
                sf = SimpleFactory()
                inner = [sf.create_from(list, ctx),
                         sf.create_from(tuple, ctx),
                         sf.create_from(str, ctx)]
            return SequenceChecker(inner, ctx, elemChecker)
        else:
            return None


class SequenceChecker(UnionChecker):

    elemChecker: Optional[TypeChecker]

    def __init__(self, inner: list[TypeChecker], ctx: CreationContext, elemChecker: Optional[TypeChecker]):
        super().__init__(inner, ctx)
        self.elemChecker = elemChecker

    def describe(self) -> str:
        if self.elemChecker:
            desc = self.elemChecker.describe()
            return f"Sequence[{desc}]"
        else:
            return "Sequence"
