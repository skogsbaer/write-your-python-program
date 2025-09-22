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
from contextlib import contextmanager

def parseExp(s: str) -> ast.expr:
    match ast.parse(s):
        case ast.Module([ast.Expr(e)], type_ignores):
            return e
        case m:
            raise ValueError(f'String {repr(s)} does not parse as an expression: {m}')

class Configs:
    funConfig: ast.expr = parseExp("{'kind': 'function'}")
    @staticmethod
    def methodConfig(clsName: str) -> ast.expr:
        return parseExp("{'kind': 'method', 'className': " + repr(clsName) + "}")

def transformStmt(stmt: ast.stmt, outerClassName: Optional[str]) -> ast.stmt:
    cfg = Configs.methodConfig(outerClassName) if outerClassName else Configs.funConfig
    wrapExp = ast.Call(ast.Name(id='wrapTypecheck', ctx=ast.Load()), [cfg], [])
    match stmt:
        case ast.FunctionDef(name, args, body, decorators, returns, tyComment, tyParams):
            return ast.FunctionDef(name, args, body, decorators + [wrapExp], returns, tyComment, tyParams)
        case ast.ClassDef(className, bases, keywords, body, decorator_list, type_params):
            newBody = [transformStmt(s, outerClassName=className) for s in body]
            return ast.ClassDef(className, bases, keywords, newBody, decorator_list, type_params)
        case _:
            return stmt

def isImport(t: ast.stmt) -> bool:
    match t:
        case ast.Import(): return True
        case ast.ImportFrom(): return True
        case _: return False

importWrapTypecheck = ast.parse("from wypp import wrapTypecheck", mode="exec").body[0]

def transformModule(m: ast.Module | ast.Expression | ast.Interactive) -> ast.Module | ast.Expression | ast.Interactive:
    match m:
        case ast.Module(body, type_ignores):
            newStmts = [transformStmt(stmt, outerClassName=None) for stmt in body]
            (imports, noImports) = utils.split(newStmts, isImport)
            # avoid inserting before from __future__
            newStmts = imports + [importWrapTypecheck] + noImports
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
    def __init__(self, finder, modDir: str, extraDirs: list[str]):
        self._origFinder = finder
        self.modDir = os.path.realpath(modDir) + '/'
        self.extraDirs = [os.path.realpath(d) for d in extraDirs]

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
        dirs = [self.modDir] + self.extraDirs
        isLocalModule = False
        for d in dirs:
            if origin.startswith(d):
                isLocalModule = True
                break
        # print(f'Module {fullname} is locale: {isLocalModule} ({origin})')
        if spec and spec.loader and isLocalModule:
            spec.loader = InstrumentingLoader(spec.loader.name, spec.loader.path)
        return spec

@contextmanager
def setupFinder(modDir: str, extraDirs: list[str], typechecking: bool):
    if not typechecking:
        yield
    else:
        # Find the PathFinder
        for finder in sys.meta_path:
            if (
                isinstance(finder, type)
                and finder.__name__ == "PathFinder"
                and hasattr(finder, "find_spec")
            ):
                break
        else:
            raise RuntimeError("Cannot find a PathFinder in sys.meta_path")

        # Create and install our custom finder
        instrumenting_finder = InstrumentingFinder(finder, modDir, extraDirs)
        sys.meta_path.insert(0, instrumenting_finder)

        try:
            yield
        finally:
            # Remove our custom finder when exiting the context
            if instrumenting_finder in sys.meta_path:
                sys.meta_path.remove(instrumenting_finder)
