from __future__ import annotations
from typing import *
from dataclasses import dataclass
import inspect
import linecache
import dis
import ast
import ansi
import utils
import myLogging
import sys
import abc
import parsecache
from parsecache import FunMatcher
import paths
import tokenize
import os

@dataclass
class EncodedBytes:
    bytes: bytes
    encoding: str
    def __len__(self):
        return len(self.bytes)
    def countLeadingSpaces(self) -> int:
        return len(self.bytes) - len(self.bytes.lstrip())
    def decoded(self) -> str:
        return self.bytes.decode(self.encoding, errors='replace')
    @overload
    def __getitem__(self, key: int) -> int: ...
    @overload
    def __getitem__(self, key: slice) -> str: ...
    def __getitem__(self, key: int | slice) -> int | str:
        if isinstance(key, int):
            return self.bytes[key]
        else:
            b = self.bytes[key]
            return b.decode(self.encoding, errors='replace')

@dataclass
class EncodedByteLines:
    bytes: list[bytes]
    encoding: str

_cache: dict[str, EncodedByteLines] = {}
def getline(filename, lineno):
    """
    Returns a line of some source file as a bytearray. We use byte arrays because
    location offsets are byte offsets.
    """
    p = os.path.normpath(os.path.abspath(filename))
    if p in _cache:
        lines = _cache[p]
    else:
        try:
            with open(filename, 'rb') as f:
                byteLines = f.readlines()
        except Exception:
            byteLines = []
        i = 0
        def nextLine() -> bytes:
            nonlocal i
            if i < len(byteLines):
                x = byteLines[i]
                i = i + 1
                return x
            else:
                return b''
        encoding, _ = tokenize.detect_encoding(nextLine)
        lines = EncodedByteLines(byteLines, encoding)
    if 1 <= lineno <= len(lines.bytes):
        x = lines.bytes[lineno - 1].rstrip(b'\n')
    else:
        x = b''
    return EncodedBytes(x, encoding)

@dataclass
class Loc:
    filename: str
    startLine: int
    startCol: Optional[int]
    endLine: Optional[int]
    endCol: Optional[int]

    def __post_init__(self):
        self.filename = paths.canonicalizePath(self.filename)

    def fullSpan(self) -> Optional[tuple[int, int, int, int]]:
        if self.startCol and self.endLine and self.endCol:
            return (self.startLine, self.startCol, self.endLine, self.endCol)
        else:
            return None

    def code(self) -> Optional[str]:
        match self.fullSpan():
            case None:
                return None
            case (startLine, startCol, endLine, endCol):
                result = []
                for lineNo in range(startLine, startLine+1):
                    line = getline(self.filename, lineNo)
                    c1 = startCol if lineNo == startLine else 0
                    c2 = endCol if lineNo == endLine else len(line)
                    result.append(line[c1:c2])
                return '\n'.join(result)

    @staticmethod
    def fromFrameInfo(fi: inspect.FrameInfo) -> Loc:
        default = Loc(fi.filename, fi.lineno, None, None, None)
        if fi.positions is None:
            return default
        p: dis.Positions = fi.positions
        startLine = p.lineno
        endLine = p.end_lineno
        startCol = p.col_offset
        endCol = p.end_col_offset
        if startLine is None or endLine is None or startCol is None or endCol is None:
            return default
        else:
            return Loc(fi.filename, startLine, startCol, endLine, endCol)

HIGHLIGHTING_ENV_VAR = 'WYPP_HIGHLIGHTING'
type HighlightMode = Literal['color', 'text', 'off']

def getHighlightMode(mode: HighlightMode | Literal['fromEnv']) -> HighlightMode:
    if mode == 'fromEnv':
        fromEnv = utils.getEnv(HIGHLIGHTING_ENV_VAR, lambda x: x, None)
        match fromEnv:
            case 'color': return 'color'
            case 'text': return 'text'
            case 'off': return 'off'
            case None: return 'color'
            case _:
                myLogging.warn(f'Invalid highlighting mode in environment variable {HIGHLIGHTING_ENV_VAR}: {fromEnv} (supported: color, text, off)')
                return 'off'
    else:
        return mode

def highlight(s: str, mode: HighlightMode) -> str:
    match mode:
        case 'color': return ansi.red(s)
        case 'off': return s
        case 'text': return f'<<{s}>>'

@dataclass
class SourceLine:
    line: EncodedBytes               # without trailing \n
    span: Optional[tuple[int, int]]  # (inclusive, exclusive)

    def highlight(self, mode: HighlightMode | Literal['fromEnv'] = 'fromEnv') -> str:
        mode = getHighlightMode(mode)
        if self.span:
            l = self.line
            return l[:self.span[0]] + highlight(l[self.span[0]:self.span[1]], mode) + l[self.span[1]:]
        else:
            return self.line.decoded()

def highlightedLines(loc: Loc) -> list[SourceLine]:
    match loc.fullSpan():
        case None:
            line = getline(loc.filename, loc.startLine)
            return [SourceLine(line, None)]
        case (startLine, startCol, endLine, endCol):
            result = []
            for lineNo in range(startLine, startLine+1):
                line = getline(loc.filename, lineNo)
                leadingSpaces = line.countLeadingSpaces()
                c1 = startCol if lineNo == startLine else leadingSpaces
                c2 = endCol if lineNo == endLine else len(line)
                result.append(SourceLine(line, (c1, c2)))
            return result

@dataclass
class ClassMember:
    kind: Literal['method', 'recordConstructor']
    className: str

type CallableKind = Literal['function'] | ClassMember

@dataclass
class CallableName:
    name: str
    kind: CallableKind
    @staticmethod
    def mk(c: CallableInfo) -> CallableName:
        return CallableName(c.name, c.kind)

class CallableInfo(abc.ABC):
    """
    Class giving access to various properties of a function, method or constructor.
    """
    def __init__(self, kind: CallableKind):
        self.kind: CallableKind = kind
    @property
    @abc.abstractmethod
    def name(self) -> str:
        pass
    @abc.abstractmethod
    def getResultTypeLocation(self) -> Optional[Loc]:
        pass
    @abc.abstractmethod
    def getParamSourceLocation(self, paramName: str) -> Optional[Loc]:
        pass
    @property
    @abc.abstractmethod
    def isAsync(self) -> bool:
        pass

class StdCallableInfo(CallableInfo):
    """
    Class giving access to various properties of a function
    (arguments, result type etc.)
    """
    def __init__(self, f: Callable, kind: CallableKind):
        super().__init__(kind)
        self.file = f.__code__.co_filename
        self.__lineno = f.__code__.co_firstlineno
        self.__name = f.__name__
        self.__ast = parsecache.getAST(self.file)

    def __repr__(self):
        return f'StdCallableInfo({self.name}, {self.kind})'

    @property
    def name(self):
        return self.__name

    def _findDef(self) -> Optional[ast.FunctionDef | ast.AsyncFunctionDef]:
        m = FunMatcher(self.__name, self.__lineno)
        match self.kind:
            case 'function':
                return self.__ast.getFunDef(m)
            case ClassMember('method', clsName):
                return self.__ast.getMethodDef(clsName, m)
            case k:
                raise ValueError(f'Unexpected CallableKind {k} in StdCallableInfo')

    def getResultTypeLocation(self) -> Optional[Loc]:
        """
        Returns the location of the result type
        """
        node = self._findDef()
        if not node:
            return None
        r = node.returns
        if r:
            return Loc(self.file,
                       r.lineno,
                       r.col_offset,
                       r.end_lineno,
                       r.end_col_offset)
        else:
            # There is no return type annotation
            return None

    def getParamSourceLocation(self, paramName: str) -> Optional[Loc]:
        """
        Returns the location of the parameter with the given name.
        """
        node = self._findDef()
        if not node:
            return None
        res = None
        for arg in node.args.args + node.args.kwonlyargs:
            if arg.arg == paramName:
                res = arg
                break
        if res is None:
            # Look in vararg and kwarg
            if node.args.vararg and node.args.vararg.arg == paramName:
                res = node.args.vararg
            if node.args.kwarg and node.args.kwarg.arg == paramName:
                res = node.args.kwarg
        if res is None:
            return None
        else:
            return Loc(self.file,
                       res.lineno,
                       res.col_offset,
                       res.end_lineno,
                       res.end_col_offset)

    @property
    def isAsync(self) -> bool:
        node = self._findDef()
        return isinstance(node, ast.AsyncFunctionDef)

def classFilename(cls) -> str | None:
    """Best-effort path to the file that defined `cls`."""
    try:
        fn = inspect.getsourcefile(cls) or inspect.getfile(cls)
        if fn:
            return fn
    except TypeError:
        pass
    # Fallback via the owning module (works for some frozen/zip cases)
    mod = sys.modules.get(cls.__module__)
    if mod is not None:
        return getattr(mod, "__file__", None) or getattr(getattr(mod, "__spec__", None), "origin", None)
    return None

class RecordConstructorInfo(CallableInfo):
    """
    Class giving access to various properties of a record constructor.
    """
    def __init__(self, cls: type):
        super().__init__(ClassMember('recordConstructor', cls.__name__))
        self.__cls = cls
    def __repr__(self):
        return f'RecordConstructorInfo({self.name})'
    @property
    def name(self):
        return self.__cls.__name__
    def getResultTypeLocation(self) -> Optional[Loc]:
        return None
    def getParamSourceLocation(self, paramName: str) -> Optional[Loc]:
        file = classFilename(self.__cls)
        if not file:
            return None
        ast = parsecache.getAST(file)
        node = ast.getRecordAttr(self.name, paramName)
        if node:
            return Loc(file, node.lineno, node.col_offset, node.end_lineno, node.end_col_offset)
        else:
            return None
    @property
    def isAsync(self) -> bool:
        return False

def locationOfArgument(fi: inspect.FrameInfo, idxOrName: int | str) -> Optional[Loc]:
    """
    Given a stack frame with a function call f(arg1, arg2, ..., argN), returns
    the source code location of the i-th argument.
    """
    loc = Loc.fromFrameInfo(fi)
    match loc.fullSpan():
        case (startLine, startCol, _endLine, _endCol):
            codeOfCall = loc.code()
            if codeOfCall is None:
                return loc
            try:
                tree = ast.parse(codeOfCall)
            except SyntaxError:
                return loc
            match tree:
                case ast.Module([ast.Expr(ast.Call(_fun, args, kwArgs))]):
                    arg = None
                    if isinstance(idxOrName, int):
                        idx = idxOrName
                        if idx >= 0 and idx < len(args):
                            arg = args[idx]
                    else:
                        matching = [k.value for k in kwArgs if k.arg == idxOrName]
                        if matching:
                            arg = matching[0]
                    if arg is not None:
                        if arg.end_lineno is not None and arg.end_col_offset is not None:
                            callStartLine = startLine + arg.lineno - 1
                            callStartCol = startCol + arg.col_offset
                            callEndLine = startLine + arg.end_lineno - 1
                            if arg.lineno != arg.end_lineno:
                                callEndCol = arg.end_col_offset
                            else:
                                callEndCol = startCol + arg.end_col_offset
                            return Loc(loc.filename, callStartLine, callStartCol,
                                            callEndLine, callEndCol)
    return loc
