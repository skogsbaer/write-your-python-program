import inspect
import types
from typing import Optional, Union, List

from untypy.error import UntypyTypeError, Frame, Location, AttributeTree
from untypy.interfaces import ExecutionContext, TypeChecker, WrappedFunction
from untypy.util.display import IndicatorStr
from untypy.util.return_traces import get_last_return
from untypy.util.source_utils import mark_source


class ReplaceTypeExecutionContext(ExecutionContext):

    def __init__(self, upper: Optional[ExecutionContext], name: str):
        self.upper = upper
        self.name = name

    def wrap(self, err: UntypyTypeError) -> UntypyTypeError:
        err = err.with_frame(Frame(
            self.name,
            None, None, None
        ))

        if self.upper is not None:
            err = self.upper.wrap(err)
        return err


class CompoundTypeExecutionContext(ExecutionContext):
    upper: ExecutionContext
    checkers: list[TypeChecker]
    idx: int

    def __init__(self, upper: ExecutionContext, checkers: list[TypeChecker], idx: int):
        self.upper = upper
        self.checkers = checkers
        self.idx = idx

    def declared(self) -> Optional[Location]:
        return None

    def responsable(self) -> Optional[Location]:
        return None

    def name(self) -> str:
        raise NotImplementedError

    def wrap(self, err: UntypyTypeError) -> UntypyTypeError:
        type_declared = self.name() + "["
        indicator = " " * len(type_declared)

        for i, checker in enumerate(self.checkers):
            if i == self.idx:
                next_type, next_indicator = err.next_type_and_indicator()
                type_declared += next_type
                indicator += next_indicator
            else:
                type_declared += checker.describe()
                indicator += " " * len(checker.describe())

            if i != len(self.checkers) - 1:  # not last element
                type_declared += ", "
                indicator += "  "

        type_declared += "]"

        err = err.with_frame(Frame(
            type_declared,
            indicator,
            declared=self.declared(),
            responsable=self.responsable(),
        ))

        return self.upper.wrap(err)


class NoResponsabilityWrapper(ExecutionContext):
    upper: ExecutionContext

    def __init__(self, upper: ExecutionContext):
        self.upper = upper

    def wrap(self, err: UntypyTypeError) -> UntypyTypeError:
        full = self.upper.wrap(err)

        # now remove responsability in frames:
        frames_to_add = []
        for frame in full.frames:
            if frame not in err.frames:
                frame.responsable = None
                frames_to_add.append(frame)

        for frame in frames_to_add:
            err = err.with_frame(frame)

        for note in full.notes:
            err = err.with_note(note)

        if full.previous_chain is not None:
            err = err.with_previous_chain(full.previous_chain)

        return err


class ReturnExecutionContext(ExecutionContext):
    fn: WrappedFunction

    def __init__(self, fn: WrappedFunction):
        self.reti_loc = get_last_return()
        self.fn = fn

    def wrap(self, err: UntypyTypeError) -> UntypyTypeError:
        (next_ty, indicator) = err.next_type_and_indicator()
        return_id = IndicatorStr(next_ty, indicator)

        original = WrappedFunction.find_original(self.fn)

        try:
            signature = inspect.signature(original)  # TODO:!!! FIX BUILTINS
            front_sig = []
            for name in signature.parameters:
                front_sig.append(f"{name}: {self.fn.checker_for(name).describe()}")
            front_sig = f"{format_name(original)}(" + (", ".join(front_sig)) + ") -> "
            return_id = IndicatorStr(front_sig) + return_id
        except:
            return_id = IndicatorStr("???")

        declared = WrappedFunction.find_location(self.fn)
        responsable = declared
        if responsable is not None:
            responsable = responsable.narrow_in_span(self.reti_loc)

        return err.with_frame(Frame(
            return_id.ty,
            return_id.indicator,
            declared=declared,
            responsable=responsable,
        ))

def format_name(orig):
    n = orig.__name__
    if inspect.isclass(orig):
        k = 'class'
        if hasattr(orig, '__kind'):
            k = getattr(orig, '__kind')
        if k:
            return f"{k} constructor {n}"
    return n


class ArgumentExecutionContext(ExecutionContext):
    n: WrappedFunction
    stack: inspect.FrameInfo
    argument_name: str
    upper: Optional[ExecutionContext]

    def __init__(self,
                 fn: Union[WrappedFunction, types.FunctionType],
                 stack: Optional[inspect.FrameInfo],
                 argument_name: str,
                 declared: Optional[Location] = None,
                 upper: ExecutionContext = None):
        self.fn = fn
        self.stack = stack
        self.argument_name = argument_name
        self.declared = declared
        self.upper = upper

    def wrap(self, err: UntypyTypeError) -> UntypyTypeError:
        original = WrappedFunction.find_original(self.fn)
        if self.stack is not None:
            responsable = Location.from_stack(self.stack)
        else:
            responsable = None

        path = err.declared_ast_path()
        path = [self.argument_name] + path
        try:
            mark = mark_source(Location.from_code(original), path)
            err = err.with_frame(Frame(
                declared=Location.from_code(original),
                declared_show=mark,
                responsable=responsable
            ))
        except:
            tree = AttributeTree.from_function(original)
            tree.replace(self.argument_name, err.last_expected())
            tree.append("\n")
            tree.append("\t...")
            err = err.with_frame(Frame(
                declared=Location.from_code(original),
                declared_show=str(tree),
                responsable=responsable
            ))

        if self.upper:
            err = self.upper.wrap(err)
        return err


class GenericExecutionContext(ExecutionContext):
    def __init__(self, *, declared: Union[None, Location, List[Location]] = None,
                 responsable: Union[None, Location, List[Location]] = None,
                 upper_ctx: Optional[ExecutionContext] = None):
        self.declared = declared
        self.responsable = responsable
        self.upper_ctx = upper_ctx

    def wrap(self, err: UntypyTypeError) -> UntypyTypeError:
        declared = []
        if isinstance(self.declared, Location):
            declared.append(self.declared)
        if isinstance(self.declared, list):
            declared.extend(self.declared)

        responsable = []
        if isinstance(self.responsable, Location):
            responsable.append(self.responsable)
        if isinstance(self.responsable, list):
            responsable.extend(self.responsable)

        while len(declared) < len(responsable): declared.append(None)
        while len(declared) > len(responsable): responsable.append(None)

        for (d, r) in zip(declared, responsable):
            (t, i) = err.next_type_and_indicator()
            err = err.with_frame(Frame(t, i, d, r))

        if self.upper_ctx is not None:
            return self.upper_ctx.wrap(err)
        else:
            return err
