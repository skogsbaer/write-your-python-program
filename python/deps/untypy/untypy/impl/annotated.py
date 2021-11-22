from typing import Optional, Any, Iterator

from untypy.error import UntypyTypeError, UntypyAttributeError, Frame, AttributeTree
from untypy.interfaces import TypeCheckerFactory, TypeChecker, ExecutionContext, CreationContext, WrappedFunction


class AnnotatedChecker:
    def check(self, arg: Any, ctx: ExecutionContext) -> None:
        pass


class AnnotatedCheckerCallable(AnnotatedChecker):
    def __init__(self, annotated, callable):
        self.callable = callable
        self.annotated = annotated

    def check(self, arg: Any, ctx: ExecutionContext) -> None:
        res = self.callable(arg)
        if not res:
            exp = self.annotated.describe()
            # raise error on falsy value
            err = UntypyTypeError(
                given=arg,
                expected=exp
            )
            if self.annotated.is_anonymous:
                err = err.with_note(f"condition in {exp} does not hold")
            for info in self.annotated.info:
                err = err.with_note("    - " + info)
            raise ctx.wrap(err)


class AnnotatedCheckerContainer(AnnotatedChecker):
    def __init__(self, annotated, cont):
        self.cont = cont
        self.annotated = annotated

    def check(self, arg: Any, ctx: ExecutionContext) -> None:
        if arg not in self.cont:
            # raise error on falsy value

            err = UntypyTypeError(
                given=arg,
                expected=self.annotated.describe(),
                declared_path=["0"],# mark 1st base type
            )
            if self.annotated.is_anonymous:
                err = err.with_note(f"{repr(arg)} is not in {repr(self.cont)}.")

            for info in self.annotated.info:
                err = err.with_note("    - " + info)

            raise ctx.wrap(err)


class AnnotatedFactory(TypeCheckerFactory):

    def create_from(self, annotation: Any, ctx: CreationContext) -> Optional[TypeChecker]:
        if hasattr(annotation, '__metadata__') and hasattr(annotation, '__origin__'):
            inner = ctx.find_checker(annotation.__origin__)
            if inner is None:
                raise ctx.wrap(UntypyAttributeError(f"Could not resolve annotation "
                                                    f"'{repr(annotation.__origin__)}' "
                                                    f"inside of '{annotation}'."))

            return AnnotatedChecker(annotation, inner, annotation.__metadata__, ctx)
        else:
            return None


class AnnotatedChecker(TypeChecker):
    def __init__(self, annotated, inner: TypeChecker, metadata: Iterator, ctx: CreationContext):
        self.annotated = annotated
        self.inner = inner

        meta = []
        info = []
        for m in metadata:
            if callable(m):
                meta.append(AnnotatedCheckerCallable(self, m))
            elif isinstance(m, str):
                info.append(m)
            elif hasattr(m, '__contains__'):
                meta.append(AnnotatedCheckerContainer(self, m))
            else:
                raise ctx.wrap(UntypyAttributeError(f"Unsupported metadata '{repr(m)}' in '{repr(self.annotated)}'.\n"
                                                    f"Only callables or objects providing __contains__ are allowed."))
        self.meta = meta
        self.info = info
        if len(info) == 1:
            self.name = info[0]
            self.info = []
        else:
            self.name = None

    def check_and_wrap(self, arg: Any, ctx: ExecutionContext) -> Any:
        wrapped = self.inner.check_and_wrap(arg, AnnotatedCheckerExecutionContext(self, ctx))
        for ck in self.meta:
            ck.check(wrapped, ctx)
        return wrapped

    def describe(self) -> str:
        tree = AttributeTree("Annotated")
        tree.append("[")
        if self.name:
            tree.append(self.name)
        elif len(self.info) > 0:
            for i,a in enumerate(self.info):
                if i != 0:
                    tree.append(", ")
                tree.append(f"'{a}'", str(i))
        else:
            for i,a in enumerate(self.annotated.__args__):
                if i != 0:
                    tree.append(", ")
                tree.append(f"'{a}'", str(i))
        tree.append("]")
        return tree

    def base_type(self):
        return self.inner.base_type()

    @property
    def is_anonymous(self):
        return self.name is None


class AnnotatedCheckerExecutionContext(ExecutionContext):
    def __init__(self, ch: AnnotatedChecker, upper: ExecutionContext):
        self.ch = ch
        self.upper = upper

    def wrap(self, err: UntypyTypeError) -> UntypyTypeError:
        err = err.with_frame(Frame(
            expected=self.ch.describe(),
            declared_path=["0"],
        ))

        return self.upper.wrap(err)
