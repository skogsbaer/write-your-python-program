from __future__ import annotations

import inspect
from enum import Enum
from os.path import relpath
from typing import Optional, Tuple, Iterable


def readFile(path):
    try:
        with open(path, encoding='utf-8') as f:
            return f.read()
    except UnicodeDecodeError:
        with open(path) as f:
            return f.read()


class Location:
    file: str
    line_no: int
    line_span : int
    source_lines: Optional[str]

    def __init__(self, file: str, line_no: int, line_span : int):
        self.file = file
        self.line_no = line_no
        self.line_span = line_span
        self.source_lines = None

    def source(self) -> Optional[str]:
        if self.source_lines is None:
            try:
                self.source_lines = readFile(self.file)
            except OSError:
                self.source_lines = ''
        return self.source_lines

    def source_lines_span(self) -> Optional[str]:
        # This is still used for unit testing

        source = self.source()
        if source is None:
            return None

        buf = ""

        for i, line in enumerate(source.splitlines()):
            if (i + 1) in range(self.line_no, self.line_no + self.line_span):
                buf += f"\n{line}"

        return buf

    def __str__(self):
        return f"{relpath(self.file)}:{self.line_no}"

    def formatWithCode(self):
        buf = str(self)
        source = self.source()
        if not source:
            return buf
        lines = source.splitlines()
        idx = self.line_no - 1
        if idx < 0 or idx > len(lines):
            return buf
        else:
            return buf + '\n  | ' + lines[idx]

    def __repr__(self):
        return f"Location(file={self.file.__repr__()}, line_no={self.line_no.__repr__()}, line_span={self.line_span})"

    def __eq__(self, other):
        if not isinstance(other, Location):
            return False
        return self.file == other.file and self.line_no == other.line_no

    @staticmethod
    def from_code(obj) -> Location:
        try:
            return Location(
                file=inspect.getfile(obj),
                line_no=inspect.getsourcelines(obj)[1],
                line_span=len(inspect.getsourcelines(obj)[0]),
            )
        except Exception:
            return Location(
                file=inspect.getfile(obj),
                line_no=1,
                line_span=1,
            )

    @staticmethod
    def from_stack(stack) -> Location:
        if isinstance(stack, inspect.FrameInfo):
            try:
                return Location(
                    file=stack.filename,
                    line_no=stack.lineno,
                    line_span=1
                )
            except Exception:
                return Location(
                    file=stack.filename,
                    line_no=stack.lineno,
                    line_span=1
                )
        else:  # assume sys._getframe(...)
            try:
                return Location(
                    file=stack.f_code.co_filename,
                    line_no=stack.f_lineno,
                    line_span=1
                )
            except Exception:
                return Location(
                    file=stack.f_code.co_filename,
                    line_no=stack.f_lineno,
                    line_span=1
                )

    def __contains__(self, other: Location):
        file, line = (other.file, other.line_no)
        return self.file == file and line in range(self.line_no, self.line_no + self.line_span)

    def narrow_in_span(self, reti_loc: Tuple[str, int]):
        """
        Use new Location if inside of span of this Location
        :param reti_loc: filename and line_no
        :return: a new Location, else self
        """
        file, line = reti_loc
        if self.file == file and line in range(self.line_no, self.line_no + self.line_span):
            return Location(
                file=file,
                line_no=line,
                line_span=1
            )
        else:
            return self


class Frame:
    declared: Optional[Location]
    declared_tree: Optional[AttributeTree]
    declared_path: list[str]
    declared_show: Optional[str]
    responsable: Optional[Location]
    given: Optional[str]
    expected: AttributeTree
    note: Optional[str]

    responsibility_type: Optional[ResponsibilityType]

    def __init__(self,
                 declared: Optional[Location] = None,
                 responsable: Optional[Location] = None,
                 declared_tree: Optional[AttributeTree] = None,
                 declared_path: list[str] = [],
                 declared_show: Optional[str] = None,
                 given: Optional[str] = None,
                 expected: AttributeTree = None,
                 note: str = None):
        self.declared = declared
        self.responsable = responsable
        self.declared_tree = declared_tree
        self.declared_path = declared_path[:]
        self.declared_show = declared_show
        self.given = given
        self.expected = expected
        self.note = note

        if self.declared_show and self.declared is None:
            raise "Location: declared is required when declared_show is set."

    def __str__(self):
        raise NotImplementedError


class ResponsibilityType(Enum):
    IN = 0
    OUT = 1

    def invert(self):
        if self is ResponsibilityType.IN:
            return ResponsibilityType.OUT
        else:
            return ResponsibilityType.IN

def joinLines(l: Iterable[str]) -> str:
    return '\n'.join([x.rstrip() for x in l])

# Note: the visual studio code plugin uses the prefixes "caused by: " and "declared at: "
# for finding source locations. Do not change without changing the plugin code!!
CAUSED_BY_PREFIX = "caused by: "
DECLARED_AT_PREFIX = "declared at: "

def formatLocations(prefix: str, locs: list[Location]) -> str:
    return joinLines(map(lambda s: prefix + str(s), locs))

# All error types must be subclasses from UntypyError.
class UntypyError:
    def simpleName(self):
        raise Exception('abstract method')

class UntypyTypeError(TypeError, UntypyError):
    header: str
    frames: list[Frame]
    previous_chain: Optional[UntypyTypeError]
    responsibility_type: ResponsibilityType

    def __init__(self,
                 frames: list[Frame] = [],
                 previous_chain: Optional[UntypyTypeError] = None,
                 responsibility_type: ResponsibilityType = ResponsibilityType.IN,
                 header: str = '', **kwargs):
        self.responsibility_type = responsibility_type
        self.frames = frames.copy()
        for frame in self.frames:
            if frame.responsibility_type is None:
                frame.responsibility_type = responsibility_type
        self.previous_chain = previous_chain
        self.header = header

        if len(kwargs) > 0:
            self.frames.append(Frame(**kwargs))

        super().__init__('\n' + self.__str__())

    def simpleName(self):
        return 'TypeError'

    def with_frame(self, frame: Frame) -> UntypyTypeError:
        frame.responsibility_type = self.responsibility_type
        return UntypyTypeError(self.frames + [frame],
                               self.previous_chain, self.responsibility_type,
                               self.header)

    def with_previous_chain(self, previous_chain: UntypyTypeError):
        return UntypyTypeError(self.frames,
                               previous_chain, self.responsibility_type, self.header)

    def with_note(self, note: str) -> UntypyTypeError:
        return self.with_frame(Frame(note=note))

    def with_inverted_responsibility_type(self):
        return UntypyTypeError(self.frames,
                               self.previous_chain, self.responsibility_type.invert(),
                               self.header)

    def with_header(self, header: str):
        return UntypyTypeError(self.frames,
                               self.previous_chain, self.responsibility_type, header)

    def last_responsable(self):
        for f in reversed(self.frames):
            if f.responsable is not None and f.responsibility_type is ResponsibilityType.IN:
                return f.responsable
        return None

    def last_declared(self):
        for f in reversed(self.frames):
            if f.declared is not None:
                return f.declared
        return None

    def last_expected(self):
        for f in reversed(self.frames):
            if f.expected is not None:
                return f.expected
        return None

    def declared_ast_path(self):
        path = []
        for f in reversed(self.frames):
            path.extend(f.declared_path)
        return path

    def __str__(self):
        responsable_locs = []
        declared_locs = []

        given = None
        expected = None
        notes = []

        for f in self.frames:
            if f.responsable is not None and f.responsibility_type is ResponsibilityType.IN:
                s = f.responsable.formatWithCode()
                if s not in responsable_locs:
                    responsable_locs.append(s)
            if f.declared_show is not None:
                s = f"{f.declared.file}:{f.declared.line_no}\n{f.declared_show}"
                if s not in declared_locs:
                    declared_locs.append(s)
            if given is None:
                given = f.given
            if expected is None:
                expected = f.expected
            if f.note:
                notes.append(f.note)

        cause = formatLocations(CAUSED_BY_PREFIX, responsable_locs)
        declared = formatLocations(DECLARED_AT_PREFIX, declared_locs)

        notes = joinLines(notes)
        if notes:
            notes = notes + "\n"

        if self.previous_chain is None:
            previous_chain = ""
            preHeader = self.header or 'got value of wrong type'
            postHeader = ''
        else:
            previous_chain = self.previous_chain.__str__().strip()
            preHeader = ''
            postHeader = self.header
        if postHeader:
            postHeader = postHeader + "\n"
        if preHeader:
            preHeader = preHeader + "\n"
        if previous_chain:
            previous_chain = previous_chain + "\n\n"

        expected = None if expected is None else str(expected).splitlines()[0].strip()
        given = None if given is None else given

        if given is not None:
            given = f"given:    {given.rstrip()}\n"
        else:
            given = ""

        if expected is not None and expected != 'None':
            expected = f'value of type {expected}'
        if given is not None:
            given = f"given:    {given.rstrip()}\n"
        else:
            given = ""
        if expected is not None:
            expected = f"expected: {expected}\n"
        else:
            expected = ""
        return (f"""{preHeader}{previous_chain}{postHeader}{notes}{given}{expected}
{declared}
{cause}""")

class UntypyAttributeError(AttributeError, UntypyError):

    def __init__(self, message: str, locations: list[Location] = []):
        self.message = message
        self.locations = locations.copy()
        super().__init__(self.__str__())

    def simpleName(self):
        return 'AttributeError'

    def with_location(self, loc: Location) -> UntypyAttributeError:
        return type(self)(self.message, self.locations + [loc])  # preserve type

    def __str__(self):
        return f"{self.message}\n{formatLocations(DECLARED_AT_PREFIX, self.locations)}"


class UntypyNameError(UntypyAttributeError, UntypyError):
    def simpleName(self):
        return 'NameError'


class AttributeTree:
    token_stream_lines: list[list[Tuple[str, Optional[str], bool]]]

    def __init__(self, *tokens):
        self.token_stream_lines = [[]]
        for t in tokens:
            self.append(t, None, True)

    def append(self, token: str, tag: Optional[str] = None, highlight: bool = False):
        token = str(token)
        if token.endswith("\n"):
            self.token_stream_lines.append([])
        token = token.replace("\n", "")
        self.token_stream_lines[-1].append((token, tag, highlight))

    def replace(self, name, other: AttributeTree):
        for line in self.token_stream_lines:
            for i in range(0, len(line)):
                t, ident, h = line[i]
                if ident == name:
                    del line[i]
                    for ol in reversed(other.token_stream_lines):
                        for ot, oi, oh in reversed(ol):
                            line.insert(i, (ot, ident, oh))
                    return

    def find(self, name: str):
        for line in self.token_stream_lines:
            for i in range(0, len(line)):
                t, ident, h = line[i]
                if ident == name:
                    return t

    def __str__(self):
        out = ""
        for token_line in self.token_stream_lines:
            line = ""
            indicator = ""
            second_line = False

            for token, ident, highlight in token_line:
                line += token
                if highlight:
                    second_line = True
                    indicator += len(token) * "^"
                else:
                    indicator += len(token) * " "
            if second_line:
                out += line + "\n"
                out += indicator + "\n"
            else:
                out += line + "\n"
        return out

    @staticmethod
    def from_function(fn):
        signature = inspect.signature(fn)

        tree = AttributeTree()
        tree.append(f"def {fn.__name__}(")
        for i, key in enumerate(signature.parameters):
            parm = signature.parameters[key]

            if i != 0:
                tree.append(", ")

            if parm.kind == inspect.Parameter.VAR_KEYWORD:
                tree.append("**")
            if parm.kind == inspect.Parameter.VAR_POSITIONAL:
                tree.append("*")

            tree.append(parm.name)

            if parm.annotation != inspect.Parameter.empty:
                tree.append(": ")
                tree.append(parm.annotation, key)

            if parm.default != inspect.Parameter.empty:
                tree.append("=")
                tree.append(parm.default.__repr__())
        tree.append(f")")
        if signature.return_annotation != inspect.Parameter.empty:
            tree.append(f" -> ")
            tree.append(signature.return_annotation, 'return')
        tree.append(f":")

        return tree
