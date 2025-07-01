
from typing import Any, Optional
from untypy.interfaces import TypeCheckerFactory, CreationContext, TypeChecker, ExecutionContext
from untypy.util.debug import debug, isDebug
import untypy.error

# A type depending on the arguments passed to a function. Can only be used as the return type
# of a function.
# Written Choice[T1, ..., Tn, fun]. fun is called with the arguments of the function
# call (possible including self and empty kwargs) and the type checkers for T1, ..., Tn.
# It then returns a type checker.
class Choice:
    def __init__(self, types, select_fun):
        self.types = types
        self.select_fun = select_fun

    def __class_getitem__(cls, args):
        if len(args) < 2:
            raise untypy.error.WyppTypeError(f'Choice requires at least two arguments: Choice[TYPE_1, ..., FUN]')
        return Choice(args[:-1], args[-1])

class ChoiceFactory(TypeCheckerFactory):

    def create_from(self, annotation: Any, ctx: CreationContext) -> Optional[TypeChecker]:
        if isinstance(annotation, Choice):
            checkers = []
            for t in annotation.types:
                checker = ctx.find_checker(t)
                if checker is None:
                    return None
                checkers.append(checker)
            return ChoiceChecker(checkers, annotation.select_fun)
        else:
            return None

class ChoiceChecker(TypeChecker):

    def __init__(self, checkers: list[TypeChecker], select_fun):
        self.checkers = checkers
        self.select_fun = select_fun

    def describe(self) -> str:
        l = [c.describe() for c in self.checkers]
        return f"Choice[{', '.join(l)}, <fun>]"

    def may_be_wrapped(self) -> bool:
        return True

    def __illegal_use(self):
        raise untypy.error.WyppTypeError(f"{self.describe()} can only be used as the return type of a function or method")

    def base_type(self) -> list[Any]:
        self.__illegal_use()

    def base_type_priority(self) -> int:
        return 0

    def check_and_wrap(self, arg: Any, ctx: ExecutionContext) -> Any:
        self.__illegal_use()

    def get_checker(self, args: list[Any], kwds: dict[str, Any]) -> TypeChecker:
        c = self.select_fun(*args, kwds, *self.checkers)
        if isDebug:
            all = [c.describe() for c in self.checkers]
            debug(f'Choice returned checker {c.describe()} for args={args}, kwds={kwds}. All checkers: {",".join(all)}')
        return c
