from typing import *
import os
import ast
import importlib
import importlib.abc
from importlib.machinery import ModuleSpec, SourceFileLoader
import importlib.machinery
from importlib.util import decode_source, spec_from_file_location
from collections.abc import Buffer
import types
from os import PathLike
import utils
from myLogging import *
from contextlib import contextmanager
import errors
import location

def parseExp(s: str) -> ast.expr:
    match ast.parse(s):
        case ast.Module([ast.Expr(e)], type_ignores):
            return e
        case m:
            raise ValueError(f'String {repr(s)} does not parse as an expression: {m}')

class Configs:
    funConfig: ast.expr = parseExp("{'kind': 'function', 'globals': globals(), 'locals': locals()}")
    @staticmethod
    def methodConfig(clsName: str) -> ast.expr:
        return parseExp("{'kind': 'method', 'className': " + repr(clsName) + ", 'globals': globals(), 'locals': locals()}")
    immutableRecordConfig: ast.expr = parseExp('record(mutable=False, globals=globals(), locals=locals())')
    mutableRecordConfig: ast.expr = parseExp('record(mutable=True, globals=globals(), locals=locals())')

def transferLocs(old: ast.stmt | ast.expr, new: ast.stmt | ast.expr) -> Any:
    new.lineno = old.lineno
    new.col_offset = old.col_offset
    new.end_lineno = old.end_lineno
    new.end_col_offset = old.end_col_offset
    return new

def transformDecorator(e: ast.expr, path: str) -> ast.expr:
    loc = location.Loc(path, e.lineno, e.col_offset, e.end_lineno, e.col_offset)
    match e:
        case ast.Name('record'):
            return transferLocs(e, Configs.immutableRecordConfig)
        case ast.Call(ast.Name('record'), [], kwArgs):
            match kwArgs:
                case [ast.keyword('mutable', ast.Constant(True))]:
                    return transferLocs(e, Configs.mutableRecordConfig)
                case [ast.keyword('mutable', ast.Constant(False))]:
                    return transferLocs(e, Configs.immutableRecordConfig)
                case _:
                    raise errors.WyppTypeError.invalidRecordAnnotation(loc)
        case ast.Call(ast.Name('record'), _, _):
            raise ValueError(f'Invalid record config')
        case _:
            return e

def transformStmt(stmt: ast.stmt, outerClassName: Optional[str], path: str) -> ast.stmt:
    cfg = Configs.methodConfig(outerClassName) if outerClassName else Configs.funConfig
    wrapExp = ast.Call(ast.Name(id='wrapTypecheck', ctx=ast.Load()), [cfg], [])
    match stmt:
        case ast.FunctionDef(name, args, body, decorators, returns, tyComment, tyParams):
            newBody = [transformStmt(s, outerClassName=outerClassName, path=path) for s in body]
            x = ast.FunctionDef(name, args, newBody, decorators + [wrapExp], returns, tyComment, tyParams)
            return transferLocs(stmt, x)
        case ast.AsyncFunctionDef(name, args, body, decorators, returns, tyComment, tyParams):
            newBody = [transformStmt(s, outerClassName=outerClassName, path=path) for s in body]
            x = ast.AsyncFunctionDef(name, args, newBody, decorators + [wrapExp], returns, tyComment, tyParams)
            return transferLocs(stmt, x)
        case ast.ClassDef(className, bases, keywords, body, decoratorList, type_params):
            newBody = [transformStmt(s, outerClassName=className, path=path) for s in body]
            newDecoratorList = [transformDecorator(e, path=path) for e in decoratorList]
            x = ast.ClassDef(className, bases, keywords, newBody, newDecoratorList, type_params)
            return transferLocs(stmt, x)
        case _:
            return stmt

def isImport(t: ast.stmt) -> bool:
    match t:
        case ast.Import(): return True
        case ast.ImportFrom(): return True
        case _: return False

importWrapTypecheck = ast.parse("from wypp import wrapTypecheck", mode="exec").body[0]

def transformModule(m: ast.Module | ast.Expression | ast.Interactive, path: str) -> ast.Module | ast.Expression | ast.Interactive:
    match m:
        case ast.Module(body, type_ignores):
            newStmts = [transformStmt(stmt, outerClassName=None, path=path) for stmt in body]
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
        if isinstance(path, PathLike):
            pathStr = str(path)
        elif isinstance(path, str):
            pathStr = path
        else:
            pathStr = "<input>"
        tree = transformModule(tree, pathStr)
        ast.fix_missing_locations(tree)

        debug(
            f"Source code of {path!r} after instrumentation:\n" +
            "----------------------------------------------\n" +
            ast.unparse(tree) + "\n"
            "----------------------------------------------")

        code = utils._call_with_frames_removed(compile, tree, path, "exec", 0, dont_inherit=True)
        return code

class InstrumentingFinder(importlib.abc.MetaPathFinder):
    def __init__(self, finder, modDir: str, modName: str, extraDirs: list[str]):
        self._origFinder = finder
        self.mainModName = modName
        self.modDir = os.path.realpath(modDir) + '/'
        self.extraDirs = [os.path.realpath(d) for d in extraDirs]

    def find_spec(
            self,
            fullname: str,
            path: Sequence[str] | None,
            target: types.ModuleType | None = None,
        ) -> ModuleSpec | None:

        debug(f'Consulting InstrumentingFinder.find_spec for fullname={fullname}')
        # 1) The fullname is the name of the main module. This might be a dotted name such as x.y.z.py
        #    so we have special logic here
        fp = os.path.join(self.modDir, f"{fullname}.py")
        if self.mainModName == fullname and os.path.isfile(fp):
            loader = InstrumentingLoader(fullname, fp)
            spec = spec_from_file_location(fullname, fp, loader=loader)
            debug(f'spec for {fullname}: {spec}')
            return spec
        # 2) The fullname is a prefix of the main module. We want to load main modules with
        #    dotted names such as x.y.z.py, hence we synthesize a namespace pkg
        #    e.g. if 'x.y.z.py' exists and we're asked for 'x', return a package spec.
        elif self.mainModName.startswith(fullname + '.'):
            spec = importlib.machinery.ModuleSpec(fullname, loader=None, is_package=True)
            # Namespace package marker (PEP 451)
            spec.submodule_search_locations = []
            debug(f'spec for {fullname}: {spec}')
            return spec
        # 3) Fallback: use the original PathFinder
        spec = self._origFinder.find_spec(fullname, path, target)
        debug(f'spec for {fullname}: {spec}')
        if spec is None:
            return spec

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
def setupFinder(modDir: str, modName: str, extraDirs: list[str], typechecking: bool):
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
        instrumenting_finder = InstrumentingFinder(finder, modDir, modName, extraDirs)
        sys.meta_path.insert(0, instrumenting_finder)
        debug(f'Installed instrument finder {instrumenting_finder}')

        alreadyLoaded = sys.modules.get(modName)
        if alreadyLoaded:
            sys.modules.pop(modName, None)
            importlib.invalidate_caches()

        try:
            yield
        finally:
            if alreadyLoaded:
                sys.modules[modName] = alreadyLoaded

            # Remove our custom finder when exiting the context
            if instrumenting_finder in sys.meta_path:
                sys.meta_path.remove(instrumenting_finder)
