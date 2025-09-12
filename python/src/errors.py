from __future__ import annotations
from typing import *
from dataclasses import dataclass
import abc
import inspect
import location
from myTypeguard import renderTy

class WyppError(abc.ABC):
    def __init__(self, extraFrames: list[inspect.FrameInfo] = []):
        self.extraFrames = extraFrames[:]

def renderLoc(loc: location.Loc) -> str:
    s = '\n'.join([l.highlight() for l in location.highlightedLines(loc)])
    return s.rstrip()

def ordinal(i: int) -> str:
    i = i + 1 # number starts at zero
    match i:
        case 1: return '1st'
        case 2: return '2nd'
        case 3: return '3rd'
        case _: return f'{i}th'

def renderStr(s: str, quote: str):
    x = repr(s)
    return quote + x[1:-1] + quote

def renderGiven(givenValue: Any, givenLoc: Optional[location.Loc]) -> str:
    if type(givenValue) == str and givenLoc is not None:
        code = renderLoc(givenLoc)
        single = renderStr(givenValue, "'")
        double = renderStr(givenValue, '"')
        if double in code and single not in code:
            return double
        elif '"' in code and "'" not in code:
            return double
        else:
            return single
    else:
        return repr(givenValue)

def isParameterizedType(t: Any) -> bool:
    """True for any parameterized typing construct (incl. Union, Annotated, etc.)."""
    return get_origin(t) is not None and len(get_args(t)) > 0

@dataclass
class CallableName:
    name: str
    kind: location.CallableKind

    def __str__(self):
        match self.kind:
            case 'function':
                return f'function `{self.name}`'
            case location.ClassMember(_, clsName):
                return f'method `{self.name}` of class `{clsName}`'
    @property
    def short(self):
        match self.kind:
            case 'function':
                return 'function'
            case location.ClassMember('method', _):
                return 'method'
            case location.ClassMember('constructor', _):
                return 'constructor'

class WyppTypeError(TypeError, WyppError):

    def __init__(self, msg: str, extraFrames: list[inspect.FrameInfo] = []):
        WyppError.__init__(self, extraFrames)
        self.msg = msg
        self.add_note(msg)

    def __str__(self):
        return f'WyppTypeError: {self.msg}'

    @staticmethod
    def resultError(callableName: CallableName, resultTypeLoc: Optional[location.Loc], resultTy: Any,
                    returnLoc: Optional[location.Loc], givenValue: Any,
                    callLoc: Optional[location.Loc],
                    extraFrames: list[inspect.FrameInfo]) -> WyppTypeError:
        lines = []
        if givenValue is None:
            lines.append('no return found')
        else:
            lines.append(renderGiven(givenValue, returnLoc))
        lines.append('')
        if resultTy is None:
            # no result type expected but given
            lines.append(f'When executing {callableName}, expecting no return value.')
            lines.append(
                f'But the {callableName.short} returned a value of type `{renderTy(type(givenValue))}`.'
            )
        elif givenValue is None:
            # result type expected but none given
            lines.append(
                f'When executing {callableName}, expecting return value of type `{renderTy(resultTy)}`.'
            )
            lines.append('But no return found.')
        else:
            # result type expected but different type given
            lines.append(
                f'When executing {callableName}, expecting return value of type `{renderTy(resultTy)}`.'
            )
            if not isParameterizedType(resultTy):
                lines.append(
                    f'But the call returned a value of type `{renderTy(type(givenValue))}`.'
                )
        if resultTypeLoc and callLoc:
            lines.append('')
            lines.append(f'## File {resultTypeLoc.filename}')
            lines.append(f'## Result type declared in line {resultTypeLoc.startLine}:\n')
            lines.append(renderLoc(resultTypeLoc))
            lines.append('')
            if returnLoc:
                if resultTypeLoc.filename != returnLoc.filename:
                    lines.append(f'## File {returnLoc.filename}')
                lines.append(f'## Problematic return in line {returnLoc.startLine}:\n')
                lines.append(renderLoc(returnLoc))
                lines.append('')
            if resultTypeLoc.filename != callLoc.filename:
                lines.append(f'## File {callLoc.filename}')
            lines.append(f'## Call causing the problematic return in line {callLoc.startLine}:\n')
            lines.append(renderLoc(callLoc))
        raise WyppTypeError('\n'.join(lines), extraFrames)

    @staticmethod
    def argumentError(callableName: CallableName, paramName: str, paramIndex: int, paramLoc: Optional[location.Loc],
                      paramTy: Any, givenValue: Any, givenLoc: Optional[location.Loc]) -> WyppTypeError:
        lines = []
        givenStr = renderGiven(givenValue, givenLoc)
        lines.append(givenStr)
        lines.append('')
        match callableName.kind:
            case 'function' | location.ClassMember('method', _):
                lines.append(
                    f'The call of {callableName} expects argument of type `{renderTy(paramTy)}` ' \
                    f'as {ordinal(paramIndex)} parameter.'
                )
                paramWhat = 'Parameter'
            case location.ClassMember('constructor', clsName):
                lines.append(
                    f'When constructing `{clsName}` object, expecting argument of type `{renderTy(paramTy)}` ' \
                    f'for {ordinal(paramIndex)} attribute `{paramName}`.'
                )
                paramWhat = 'Attribute'
        if not isParameterizedType(paramTy):
            lines.append(f'But the argument has type `{renderTy(type(givenValue))}`.')
        if givenLoc:
            lines.append('')
            lines.append(f'## File {givenLoc.filename}')
            lines.append(f'## Problematic call in line {givenLoc.startLine}:\n')
            lines.append(renderLoc(givenLoc))
        if paramLoc:
            lines.append('')
            if not givenLoc or paramLoc.filename != givenLoc.filename:
                lines.append(f'## File {paramLoc.filename}')
            lines.append(f'## {paramWhat} type declared in line {paramLoc.startLine}:\n')
            lines.append(renderLoc(paramLoc))
        raise WyppTypeError('\n'.join(lines))

    @staticmethod
    def partialAnnotationError(name: str, paramName: str, paramLoc: Optional[location.Loc]) -> WyppTypeError:
        lines = []
        lines.append(
            f'Expected type annotation for parameter {paramName} of {name}.'
        )
        if paramLoc:
            lines.append('')
            lines.append(f'## File {paramLoc.filename}')
            lines.append(f'## Parameter declared in line {paramLoc.startLine}:\n')
            lines.append(renderLoc(paramLoc))
        raise WyppTypeError('\n'.join(lines))

class WyppAttributeError(AttributeError, WyppError):
    pass
