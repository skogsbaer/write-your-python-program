from __future__ import annotations
from typing import *
import abc
import inspect
import location
import i18n
from myTypeguard import renderTy

class WyppError(abc.ABC):
    def __init__(self, extraFrames: list[inspect.FrameInfo] = []):
        self.extraFrames = extraFrames[:]

def renderLoc(loc: location.Loc) -> str:
    s = '\n'.join([l.highlight() for l in location.highlightedLines(loc)])
    return s.rstrip()

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

class WyppTypeError(TypeError, WyppError):

    def __init__(self, msg: str, extraFrames: list[inspect.FrameInfo] = []):
        WyppError.__init__(self, extraFrames)
        self.msg = msg
        self.add_note(msg)

    def __str__(self):
        return f'WyppTypeError: {self.msg}'

    @staticmethod
    def resultError(callableName: location.CallableName, resultTypeLoc: Optional[location.Loc], resultTy: Any,
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
            lines.append(i18n.expectingNoReturn(callableName))
            lines.append(i18n.wrongReturnValue(renderTy(type(givenValue))))
        elif givenValue is None:
            # result type expected but none given
            lines.append(i18n.expectingReturnOfType(callableName, renderTy(resultTy)))
            lines.append(i18n.noReturnValue())
        else:
            # result type expected but different type given
            lines.append(i18n.expectingReturnOfType(callableName, renderTy(resultTy)))
            if not isParameterizedType(resultTy):
                lines.append(i18n.wrongReturnValue(renderTy(givenValue)))
        if resultTypeLoc and callLoc:
            lines.append('')
            lines.append(f'## {i18n.tr("File")} {resultTypeLoc.filename}')
            lines.append(f'## {i18n.tr("Result type declared in line")} {resultTypeLoc.startLine}:\n')
            lines.append(renderLoc(resultTypeLoc))
            lines.append('')
            if returnLoc:
                if resultTypeLoc.filename != returnLoc.filename:
                    lines.append(f'## {i18n.tr("File")} {returnLoc.filename}')
                lines.append(f'## {i18n.tr("Problematic return in line")} {returnLoc.startLine}:\n')
                lines.append(renderLoc(returnLoc))
                lines.append('')
            if resultTypeLoc.filename != callLoc.filename:
                lines.append(f'## {i18n.tr("File")} {callLoc.filename}')
            lines.append(f'## {i18n.tr("Call causing the problematic return in line")} {callLoc.startLine}:\n')
            lines.append(renderLoc(callLoc))
        raise WyppTypeError('\n'.join(lines), extraFrames)

    @staticmethod
    def argumentError(callableName: location.CallableName, paramName: str, paramIndex: int, paramLoc: Optional[location.Loc],
                      paramTy: Any, givenValue: Any, givenLoc: Optional[location.Loc]) -> WyppTypeError:
        lines = []
        givenStr = renderGiven(givenValue, givenLoc)
        lines.append(givenStr)
        lines.append('')
        lines.append(i18n.expectingArgumentOfTy(callableName, renderTy(paramTy), paramIndex + 1))
        if not isParameterizedType(paramTy):
            lines.append(i18n.realArgumentTy(renderTy(type(givenValue))))
        if givenLoc:
            lines.append('')
            lines.append(f'## {i18n.tr("File")} {givenLoc.filename}')
            lines.append(f'## {i18n.tr("Problematic call in line")} {givenLoc.startLine}:\n')
            lines.append(renderLoc(givenLoc))
        if paramLoc:
            lines.append('')
            if not givenLoc or paramLoc.filename != givenLoc.filename:
                lines.append(f'## {i18n.tr("File")} {paramLoc.filename}')
            lines.append(f'## {i18n.tr("Type declared in line")} {paramLoc.startLine}:\n')
            lines.append(renderLoc(paramLoc))
        raise WyppTypeError('\n'.join(lines))

    @staticmethod
    def partialAnnotationError(callableName: location.CallableName, paramName: str, paramLoc: Optional[location.Loc]) -> WyppTypeError:
        lines = []
        lines.append(i18n.expectingTypeAnnotation(callableName, paramName))
        if paramLoc:
            lines.append('')
            lines.append(f'## {i18n.tr("File")} {paramLoc.filename}')
            lines.append(f'## {i18n.tr("Parameter declared in line")} {paramLoc.startLine}:\n')
            lines.append(renderLoc(paramLoc))
        raise WyppTypeError('\n'.join(lines))

    @staticmethod
    def noTypeAnnotationForRecordAttribute(attrName: str, recordName: str) -> WyppTypeError:
        return WyppTypeError(i18n.noTypeAnnotationForAttribute(attrName, recordName))

class WyppAttributeError(AttributeError, WyppError):
    pass
