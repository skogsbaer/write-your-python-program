from typing import *
import os
import ast
import importlib
import importlib.abc
from importlib.machinery import ModuleSpec, SourceFileLoader
from importlib.util import decode_source
from collections.abc import Buffer
import types
from os import PathLike
import utils
from myLogging import *

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
    wrapExp = ast.Call(ast.Name(id='wrapTypecheck', ctx=ast.Load()), [cfg], [])
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
            tree = utils._call_with_frames_removed(ast.parse, source, path, "exec")
        tree = transformModule(tree)
        ast.fix_missing_locations(tree)

        debug(
            f"Source code of {path!r} after instrumentation:\n" +
            "----------------------------------------------\n" +
            ast.unparse(tree) + "\n"
            "----------------------------------------------")

        code = utils._call_with_frames_removed(compile, tree, path, "exec", 0, dont_inherit=True)
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
        if spec is None:
            return None
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
