from __future__ import annotations

import inspect
from enum import Enum
from os.path import relpath
from typing import Any, Optional, Tuple, Iterable

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

    def narrow_in_span(self, reti_loc : Tuple[str, int]):
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
    type_declared: str
    indicator_line: str

    declared: Optional[Location]
    responsable: Optional[Location]

    responsibility_type: Optional[ResponsibilityType]

    def __init__(self, type_declared: str, indicator_line: Optional[str],
                 declared: Optional[Location], responsable: Optional[Location]):

        self.type_declared = type_declared
        if indicator_line is None:
            indicator_line = '^' * len(type_declared)
        self.indicator_line = indicator_line
        self.declared = declared
        self.responsable = responsable

    def __str__(self):
        buf = f"in: {self.type_declared}\n" \
              f"    {self.indicator_line}\n"

        if self.responsable is not None:
            buf += f"{self.responsable.file}:{self.responsable.line_no}:\n" \
                   f"{self.responsable.source_line}\n" \
                   f"\n"
        return buf


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
    given: Any
    header: str
    expected: str
    frames: list[Frame]
    notes: list[str]
    previous_chain: Optional[UntypyTypeError]
    responsibility_type: ResponsibilityType

    def __init__(self, given: Any, expected: str, frames: list[Frame] = [],
                 notes: list[str] = [],
                 previous_chain: Optional[UntypyTypeError] = None,
                 responsibility_type: ResponsibilityType = ResponsibilityType.IN,
                 header: str = ''):
        self.responsibility_type = responsibility_type
        self.given = given
        self.expected = expected
        self.frames = frames.copy()
        for frame in self.frames:
            if frame.responsibility_type is None:
                frame.responsibility_type = responsibility_type
        self.notes = notes.copy()
        self.previous_chain = previous_chain
        self.header = header
        super().__init__('\n' + self.__str__())

    def simpleName(self):
        return 'TypeError'

    def next_type_and_indicator(self) -> Tuple[str, str]:
        if len(self.frames) >= 1:
            frame = self.frames[-1]
            return frame.type_declared, frame.indicator_line
        else:
            return self.expected, "^" * len(self.expected)

    def with_frame(self, frame: Frame) -> UntypyTypeError:
        frame.responsibility_type = self.responsibility_type
        return UntypyTypeError(self.given, self.expected, self.frames + [frame],
                               self.notes, self.previous_chain, self.responsibility_type,
                               self.header)

    def with_previous_chain(self, previous_chain: UntypyTypeError):
        return UntypyTypeError(self.given, self.expected, self.frames,
                               self.notes, previous_chain, self.responsibility_type, self.header)

    def with_note(self, note: str):
        return UntypyTypeError(self.given, self.expected, self.frames,
                               self.notes + [note], self.previous_chain, self.responsibility_type,
                               self.header)

    def with_inverted_responsibility_type(self):
        return UntypyTypeError(self.given, self.expected, self.frames,
                               self.notes, self.previous_chain, self.responsibility_type.invert(),
                               self.header)

    def with_header(self, header: str):
        return UntypyTypeError(self.given, self.expected, self.frames,
                               self.notes, self.previous_chain, self.responsibility_type, header)

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

    def __str__(self):
        declared_locs = []
        responsable_locs = []

        for f in self.frames:
            if f.responsable is not None and f.responsibility_type is ResponsibilityType.IN:
                s = f.responsable.formatWithCode()
                if s not in responsable_locs:
                    responsable_locs.append(s)
            if f.declared is not None:
                s = str(f.declared)
                if s not in declared_locs:
                    declared_locs.append(str(f.declared))

        cause = formatLocations(CAUSED_BY_PREFIX, responsable_locs)
        declared = formatLocations(DECLARED_AT_PREFIX, declared_locs)

        (ty, ind) = self.next_type_and_indicator()

        notes = joinLines(self.notes)
        if notes:
            notes = notes + "\n\n"

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

        ctx = ""
        if self.expected != ty:
            ctx = f"context: {ty.rstrip()}"
            ind = ind.rstrip()
            if ind:
                ctx = f"{ctx}\n         {ind}"
        if ctx:
            ctx = ctx + "\n"
        given = repr(self.given)
        expected = self.expected.strip()
        if expected != 'None':
            expected = f'value of type {expected}'

        return (f"""{preHeader}{previous_chain}{postHeader}{notes}given:    {given.rstrip()}
expected: {expected}

{ctx}{declared}
{cause}""")


class UntypyAttributeError(AttributeError, UntypyError):

    def __init__(self, message: str, locations: list[Location] = []):
        self.message = message
        self.locations = locations.copy()
        super().__init__(self.__str__())

    def simpleName(self):
        return 'AttributeError'

    def with_location(self, loc: Location) -> UntypyAttributeError:
        return type(self)(self.message, self.locations + [loc]) # preserve type

    def __str__(self):
        return f"{self.message}\n{formatLocations(DECLARED_AT_PREFIX, self.locations)}"


class UntypyNameError(UntypyAttributeError, UntypyError):
    def simpleName(self):
        return 'NameError'
