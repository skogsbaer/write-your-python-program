import inspect
from typing import Any, Optional, TypeVar, List, Dict
import typing

from untypy.interfaces import CreationContext, TypeChecker, ExecutionContext
from .annotated import AnnotatedFactory
from .any import AnyFactory
from .callable import CallableFactory
from .dummy_delayed import DummyDelayedFactory
from .generator import GeneratorFactory
from .generic import GenericFactory
from .interface import InterfaceFactory
from .choice import ChoiceFactory
from .literal import LiteralFactory
from .none import NoneFactory
from .optional import OptionalFactory
from .protocol import ProtocolFactory
from .simple import SimpleFactory
from .string_forward_refs import StringForwardRefFactory
from .tuple import TupleFactory
from .union import UnionFactory
from ..error import Location, UntypyAttributeError
from ..util.debug import debug

# More Specific Ones First
_FactoryList = [
    AnyFactory(),
    NoneFactory(),
    DummyDelayedFactory(),
    AnnotatedFactory(),
    ProtocolFactory(),  # must be higher then Generic
    GenericFactory(),
    CallableFactory(),
    LiteralFactory(),
    OptionalFactory(),  # must be higher then Union
    UnionFactory(),
    TupleFactory(),
    GeneratorFactory(),
    InterfaceFactory(),
    ChoiceFactory(),
    StringForwardRefFactory(),  # resolve types passed as strings
    # must come last
    SimpleFactory()
]


class DefaultCreationContext(CreationContext):

    def __init__(self, typevars: Dict[TypeVar, Any], declared_location: Location,
                 checkedpkgprefixes: List[str], eval_context: Optional[Any] = None):
        self.typevars = typevars
        self.declared = declared_location
        self.checkedpkgprefixes = checkedpkgprefixes
        self._eval_context = eval_context

    def declared_location(self) -> Location:
        return self.declared

    def find_checker(self, annotation: Any) -> Optional[TypeChecker]:
        for fac in _FactoryList:
            res = fac.create_from(annotation=annotation, ctx=self)
            if res is not None:
                debug(f'Created checker for {annotation} from factory {fac}')
                return res
        return None

    def wrap(self, err: UntypyAttributeError) -> UntypyAttributeError:
        return err.with_location(self.declared)

    def resolve_typevar(self, var: TypeVar) -> typing.Tuple[bool, Any]:
        # Not result may be None
        if var in self.typevars:
            return True, self.typevars[var]
        else:
            return False, None

    def all_typevars(self) -> List[TypeVar]:
        return list(self.typevars.keys())

    def with_typevars(self, typevars: Dict[TypeVar, Any]) -> CreationContext:
        tv = self.typevars.copy()
        tv.update(typevars)
        return DefaultCreationContext(tv, self.declared, self.checkedpkgprefixes, self._eval_context)

    def should_be_inheritance_checked(self, annotation: type) -> bool:
        m = inspect.getmodule(annotation)

        for pkgs in self.checkedpkgprefixes:
            # Inheritance should be checked on types
            # when the type's module or its parent lies in the "user code".
            # Inheritance of types of extern modules should be not be checked.
            if m.__name__ == pkgs or m.__name__.startswith(pkgs + "."):
                return True

        return False

    def eval_context(self):
        return self._eval_context
