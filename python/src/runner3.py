from __future__ import annotations
import sys
import importlib.abc
import types
from collections.abc import Callable, Iterable, Sequence
from importlib.machinery import ModuleSpec, SourceFileLoader
from importlib.util import decode_source
import ast
from os import PathLike
import io
if sys.version_info >= (3, 12):
    from collections.abc import Buffer
else:
    from typing_extensions import Buffer
if sys.version_info >= (3, 11):
    from typing import ParamSpec
else:
    from typing_extensions import ParamSpec
from typing import TypeVar, Any
import inspect
import typing
import os
from dataclasses import dataclass

from myTypeguard import matchesTy, renderTy

def printVars(what: str, *l):
    s = what + ": " + ', '.join([str(x) for x in l])
    print(s)

P = ParamSpec("P")
T = TypeVar("T")

# The name of this function is magical
def _call_with_frames_removed(
    f: Callable[P, T], *args: P.args, **kwargs: P.kwargs
) -> T:
    return f(*args, **kwargs)

def isEmptyAnnotation(t: Any) -> bool:
    return t is inspect.Signature.empty or t is inspect.Parameter.empty

def checkArguments(sig: inspect.Signature, args: tuple, kwargs: dict, cfg: CheckCfg) -> None:
    params = list(sig.parameters)
    if len(params) != len(args):
        raise TypeError(f"Expected {len(params)} arguments, got {len(args)}")
    for i in range(len(args)):
        name = params[i]
        t = sig.parameters[name].annotation
        if isEmptyAnnotation(t):
            if i == 0 and cfg.kind == 'method':
                if name != 'self':
                    raise TypeError(f'Name of first parameter of method {name} must be self not {name}')
            else:
                raise TypeError(f'Missing type for parameter {name}')
        else:
            a = args[i]
            if not matchesTy(a, t):
                raise TypeError(f'Expected argument of type {renderTy(t)} for parameter {name}, got {renderTy(type(a))}: {a}')

def checkReturn(sig: inspect.Signature, result: Any) -> None:
    t = sig.return_annotation
    if isEmptyAnnotation(t):
        t = None
    if not matchesTy(result, t):
        raise TypeError(f"Expected return type {renderTy(t)}, got {renderTy(type(result))}: {result}")

FunKind = typing.Literal['function', 'method', 'staticmethod']
@dataclass
class CheckCfg:
    kind: FunKind
    @staticmethod
    def fromDict(d: dict) -> CheckCfg:
        return CheckCfg(kind=d['kind'])

def wrap(cfg: dict) -> Callable[[Callable[P, T]], Callable[P, T]]:
    checkCfg = CheckCfg.fromDict(cfg)
    def _wrap(f: Callable[P, T]) -> Callable[P, T]:
        sig = inspect.signature(f)
        def wrapped(*args, **kwargs) -> T:
            checkArguments(sig, args, kwargs, checkCfg)
            result = _call_with_frames_removed(f, *args, **kwargs)
            checkReturn(sig, result)
            return result
        return wrapped
    return _wrap

def parseExp(s: str) -> ast.expr:
    match ast.parse(s):
        case ast.Module([ast.Expr(e)], type_ignores):
            return e
        case m:
            raise ValueError(f'String {repr(s)} does not parse as an expression: {m}')

class Configs:
    funConfig: ast.expr = parseExp("{'kind': 'function'}")
    methodConfig: ast.expr = parseExp("{'kind': 'method'}")

def transformStmt(stmt: ast.stmt, insideClass: bool) -> ast.stmt:
    # FIXME: static methods
    cfg = Configs.methodConfig if insideClass else Configs.funConfig
    wrapExp = ast.Call(ast.Name(id='wrap', ctx=ast.Load()), [cfg], [])
    match stmt:
        case ast.FunctionDef(name, args, body, decorators, returns, tyComment, tyParams):
            return ast.FunctionDef(name, args, body, decorators + [wrapExp], returns, tyComment, tyParams)
        case ast.ClassDef(name, bases, keywords, body, decorator_list, type_params):
            newBody = [transformStmt(s, insideClass=True) for s in body]
            return ast.ClassDef(name, bases, keywords, newBody, decorator_list, type_params)
        case _:
            return stmt

def transformModule(m: ast.Module | ast.Expression | ast.Interactive) -> ast.Module | ast.Expression | ast.Interactive:
    match m:
        case ast.Module(body, type_ignores):
            newStmts = [transformStmt(stmt, insideClass=False) for stmt in body]
            return ast.Module(newStmts, type_ignores)
        case _:
            return m

class InstrumentingLoader(SourceFileLoader):
    @staticmethod
    def source_to_code(
        data: Buffer | str | ast.Module | ast.Expression | ast.Interactive,
        path: Buffer | str | PathLike[str] = "<string>",
    ) -> types.CodeType:
        if isinstance(data, (ast.Module, ast.Expression, ast.Interactive)):
            tree = data
        else:
            if isinstance(data, str):
                source = data
            else:
                source = decode_source(data)
            tree = _call_with_frames_removed(ast.parse, source, path, "exec")
        tree = transformModule(tree)
        ast.fix_missing_locations(tree)

        print(
            f"Source code of {path!r} after instrumentation:\n"
            "----------------------------------------------",
            file=sys.stderr,
        )
        print(ast.unparse(tree), file=sys.stderr)
        print("----------------------------------------------", file=sys.stderr)

        code = _call_with_frames_removed(compile, tree, path, "exec", 0, dont_inherit=True)
        return code

class InstrumentingFinder(importlib.abc.MetaPathFinder):
    def __init__(self, finder, modDir):
        self._origFinder = finder
        self.modDir = os.path.realpath(modDir) + '/'

    def find_spec(
            self,
            fullname: str,
            path: Sequence[str] | None,
            target: types.ModuleType | None = None,
        ) -> ModuleSpec | None:
        spec = self._origFinder.find_spec(fullname, path, target)
        origin = os.path.realpath(spec.origin)
        isLocalModule = origin.startswith(self.modDir)
        if spec and spec.loader and isLocalModule:
            spec.loader = InstrumentingLoader(spec.loader.name, spec.loader.path)
        return spec

def setupFinder(modDir: str):
    for finder in sys.meta_path:
        if (
            isinstance(finder, type)
            and finder.__name__ == "PathFinder"
            and hasattr(finder, "find_spec")
        ):
            break
    else:
        raise RuntimeError("Cannot find a PathFinder in sys.meta_path")
    sys.meta_path.insert(0, InstrumentingFinder(finder, modDir))

import runner as r
import os
import runpy
def main(globals, argList=None):
    print('runner3')
    (args, restArgs) = r.parseCmdlineArgs(argList)
    fileToRun = args.file
    if args.changeDir:
        os.chdir(os.path.dirname(fileToRun))
        fileToRun = os.path.basename(fileToRun)
    modDir = os.path.dirname(fileToRun)
    setupFinder(modDir)
    sys.path.insert(0, modDir)
    modName = os.path.basename(os.path.splitext(fileToRun)[0])
    globals['wrap'] = wrap
    runpy.run_module(modName, init_globals=globals, run_name=modName)
    # __import__(modName)
    # importlib.import_module(modName)
    # import iterator
