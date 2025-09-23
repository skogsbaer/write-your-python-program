from __future__ import annotations
from typing import *
import abc
import inspect
import location
import i18n
from renderTy import renderTy

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

def shouldReportTyMismatch(expected: Any, given: Any) -> bool:
    if isParameterizedType(expected) and get_origin(expected) == given:
        # don't report a mismatch because givenTy will not be properly parameterized.
        # Example: resultTy is `list[int]` and givenValue is [1, "blub"]. Then
        # givenTy will be just `list`
        return False
    else:
        return True

def rewriteInvalidType(s: str) -> Optional[str]:
    prefixes = ['Union', 'Literal', 'Optional', 'list', 'dict', 'tuple', 'set']
    for p in prefixes:
        if s.startswith(f'{p}(') and s.endswith(')'):
            args = s[len(p)+1:-1]
            return f'{p}[{args}]'

class WyppTypeError(TypeError, WyppError):

    def __init__(self, msg: str, extraFrames: list[inspect.FrameInfo] = []):
        WyppError.__init__(self, extraFrames)
        self.msg = msg
        self.add_note(msg)

    def __str__(self):
        return f'WyppTypeError: {self.msg}'

    @staticmethod
    def invalidType(ty: Any, loc: Optional[location.Loc]) -> WyppTypeError:
        lines = []
        tyStr = renderTy(ty)
        lines.append(i18n.invalidTy(tyStr))
        lines.append('')
        rew = rewriteInvalidType(tyStr)
        if rew:
            lines.append(i18n.didYouMean(rew))
            lines.append('')
        if loc is not None:
            lines.append(f'## {i18n.tr("File")} {loc.filename}')
            lines.append(f'## {i18n.tr("Type declared in line")} {loc.startLine}:\n')
            lines.append(renderLoc(loc))
        raise WyppTypeError('\n'.join(lines))

    @staticmethod
    def unknownKeywordArgument(callableName: location.CallableName, callLoc: Optional[location.Loc], name: str) -> WyppTypeError:
        lines = []
        lines.append(i18n.tr('unknown keyword argument'))
        lines.append('')
        lines.append(i18n.unknownKeywordArgument(callableName, name))
        if callLoc and (callLocR := renderLoc(callLoc)):
            lines.append('')
            lines.append(f'## {i18n.tr("File")} {callLoc.filename}')
            lines.append(f'## {i18n.tr("Problematic call in line")} {callLoc.startLine}:\n')
            lines.append(callLocR)
        raise WyppTypeError('\n'.join(lines))

    @staticmethod
    def invalidRecordAnnotation(loc: Optional[location.Loc]) -> WyppTypeError:
        lines = []
        lines.append(i18n.tr('invalid record definition'))
        lines.append('')
        if loc and (locR := renderLoc(loc)):
            lines.append(f'## {i18n.tr("File")} {loc.filename}')
            lines.append(f'## {i18n.tr("Line")} {loc.startLine}:\n')
            lines.append(locR)
        raise WyppTypeError('\n'.join(lines))

    @staticmethod
    def resultError(callableName: location.CallableName, resultTypeLoc: Optional[location.Loc], resultTy: Any,
                    returnLoc: Optional[location.Loc], givenValue: Any,
                    callLoc: Optional[location.Loc],
                    extraFrames: list[inspect.FrameInfo]) -> WyppTypeError:
        lines = []
        if givenValue is None:
            lines.append(i18n.tr('no result returned'))
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
            givenTy = type(givenValue)
            if shouldReportTyMismatch(resultTy, givenTy):
                lines.append(i18n.wrongReturnValue(renderTy(givenTy)))
        printedFileName = None
        if resultTypeLoc and (resultTypeLocR := renderLoc(resultTypeLoc)):
            lines.append('')
            lines.append(f'## {i18n.tr("File")} {resultTypeLoc.filename}')
            printedFileName = resultTypeLoc.filename
            lines.append(f'## {i18n.tr("Result type declared in line")} {resultTypeLoc.startLine}:\n')
            lines.append(resultTypeLocR)
        if givenValue is not None and returnLoc and (returnLocR := renderLoc(returnLoc)):
            lines.append('')
            if printedFileName != returnLoc.filename:
                lines.append(f'## {i18n.tr("File")} {returnLoc.filename}')
                printedFileName = returnLoc.filename
            lines.append(f'## {i18n.tr("Problematic return in line")} {returnLoc.startLine}:\n')
            lines.append(returnLocR)
        if callLoc and (callLocR := renderLoc(callLoc)):
            lines.append('')
            if printedFileName != callLoc.filename:
                lines.append(f'## {i18n.tr("File")} {callLoc.filename}')
            if givenValue is None:
                lines.append(f'## {i18n.unexpectedNoReturn(callLoc.startLine)}\n')
            else:
                lines.append(f'## {i18n.unexpectedReturn(callLoc.startLine)}\n')
            lines.append(callLocR)
        raise WyppTypeError('\n'.join(lines), extraFrames)

    @staticmethod
    def argumentError(callableName: location.CallableName, paramName: str, paramIndex: Optional[int],
                      paramLoc: Optional[location.Loc],
                      paramTy: Any, givenValue: Any, givenLoc: Optional[location.Loc]) -> WyppTypeError:
        lines = []
        givenStr = renderGiven(givenValue, givenLoc)
        lines.append(givenStr)
        lines.append('')
        if paramIndex is not None:
            lines.append(i18n.expectingArgumentOfTy(callableName, renderTy(paramTy), paramIndex + 1))
        else:
            lines.append(i18n.expectingArgumentOfTy(callableName, renderTy(paramTy), paramName))
        if shouldReportTyMismatch(paramTy, type(givenValue)):
            lines.append(i18n.realArgumentTy(renderTy(type(givenValue))))
        if givenLoc and (givenLocR := renderLoc(givenLoc)):
            lines.append('')
            lines.append(f'## {i18n.tr("File")} {givenLoc.filename}')
            lines.append(f'## {i18n.tr("Problematic call in line")} {givenLoc.startLine}:\n')
            lines.append(givenLocR)
        if paramLoc and (paramLocR := renderLoc(paramLoc)):
            lines.append('')
            if not givenLoc or paramLoc.filename != givenLoc.filename:
                lines.append(f'## {i18n.tr("File")} {paramLoc.filename}')
            lines.append(f'## {i18n.tr("Type declared in line")} {paramLoc.startLine}:\n')
            lines.append(paramLocR)
        raise WyppTypeError('\n'.join(lines))

    @staticmethod
    def defaultError(callableName: location.CallableName, paramName: str, paramLoc: Optional[location.Loc],
                      paramTy: Any, givenValue: Any) -> WyppTypeError:
        lines = []
        givenStr = renderGiven(givenValue, paramLoc)
        lines.append(givenStr)
        lines.append('')
        lines.append(i18n.expectingDefaultValueOfTy(callableName, renderTy(paramTy), paramName))
        if shouldReportTyMismatch(paramTy, type(givenValue)):
            lines.append(i18n.realDefaultValueTy(renderTy(type(givenValue))))
        if paramLoc and (paramLocR := renderLoc(paramLoc)):
            lines.append('')
            lines.append(f'## {i18n.tr("File")} {paramLoc.filename}')
            lines.append(f'## {i18n.tr("Parameter declared in line")} {paramLoc.startLine}:\n')
            lines.append(paramLocR)
        raise WyppTypeError('\n'.join(lines))

    @staticmethod
    def argCountMismatch(callableName: location.CallableName, callLoc: Optional[location.Loc],
                         numParams: int, numMandatoryParams: int, numArgs: int) -> WyppTypeError:
        lines = []
        lines.append(i18n.tr('argument count mismatch'))
        lines.append('')
        if numArgs < numMandatoryParams:
            if numParams == numMandatoryParams:
                lines.append(i18n.argCountExact(callableName, numParams))
            else:
                lines.append(i18n.argCountMin(callableName, numMandatoryParams))
        else:
            if numParams == numMandatoryParams:
                lines.append(i18n.argCountExact(callableName, numParams))
            else:
                lines.append(i18n.argCountMax(callableName, numParams))
        lines.append(i18n.tr('Given: ') + i18n.argCount(numArgs))
        if callLoc and (callLocR := renderLoc(callLoc)):
            lines.append('')
            lines.append(f'## {i18n.tr("File")} {callLoc.filename}')
            lines.append(f'## {i18n.tr("Call in line")} {callLoc.startLine}:\n')
            lines.append(callLocR)
        raise WyppTypeError('\n'.join(lines))

    @staticmethod
    def partialAnnotationError(callableName: location.CallableName, paramName: str, paramLoc: Optional[location.Loc]) -> WyppTypeError:
        lines = []
        lines.append(i18n.expectingTypeAnnotation(callableName, paramName))
        if paramLoc and (paramLocR := renderLoc(paramLoc)):
            lines.append('')
            lines.append(f'## {i18n.tr("File")} {paramLoc.filename}')
            lines.append(f'## {i18n.tr("Parameter declared in line")} {paramLoc.startLine}:\n')
            lines.append(paramLocR)
        raise WyppTypeError('\n'.join(lines))

    @staticmethod
    def noTypeAnnotationForRecordAttribute(attrName: str, recordName: str) -> WyppTypeError:
        return WyppTypeError(i18n.noTypeAnnotationForAttribute(attrName, recordName))

    @staticmethod
    def recordAssignError(recordName: str,
                          attrName: str,
                          attrTy: Any,
                          attrLoc: Optional[location.Loc],
                          setterValue: Any,
                          setterLoc: Optional[location.Loc]) -> WyppTypeError:
        lines = []
        givenStr = renderGiven(setterValue, setterLoc)
        lines.append(givenStr)
        lines.append('')
        lines.append(i18n.recordAttrDeclTy(recordName, attrName, renderTy(attrTy)))
        if shouldReportTyMismatch(attrTy, type(setterValue)):
            lines.append(i18n.realSetAttrTy(renderTy(type(setterValue))))
        if setterLoc and (setterLocR := renderLoc(setterLoc)):
            lines.append('')
            lines.append(f'## {i18n.tr("File")} {setterLoc.filename}')
            lines.append(f'## {i18n.tr("Problematic assignment in line")} {setterLoc.startLine}:\n')
            lines.append(setterLocR)
        if attrLoc and (attrLocR := renderLoc(attrLoc)):
            lines.append('')
            if not setterLoc or setterLoc.filename != attrLoc.filename:
                lines.append(f'## {i18n.tr("File")} {attrLoc.filename}')
            lines.append(f'## {i18n.tr("Type declared in line")} {attrLoc.startLine}:\n')
            lines.append(attrLocR)
        raise WyppTypeError('\n'.join(lines))

class WyppAttributeError(AttributeError, WyppError):
    def __init__(self, msg: str, extraFrames: list[inspect.FrameInfo] = []):
        WyppError.__init__(self, extraFrames)
        self.msg = msg
        self.add_note(msg)

    @staticmethod
    def unknownAttr(clsName: str, attrName: str) -> WyppAttributeError:
        return WyppAttributeError(i18n.tr('Unknown attribute {attrName} for record {clsName}',
                                          clsName=clsName, attrName=attrName))

class TodoError(Exception, WyppError):
    def __init__(self, msg: str, extraFrames: list[inspect.FrameInfo] = []):
        WyppError.__init__(self, extraFrames)
        self.msg = msg
        self.add_note(msg)


class ImpossibleError(Exception, WyppError):
    def __init__(self, msg: str, extraFrames: list[inspect.FrameInfo] = []):
        WyppError.__init__(self, extraFrames)
        self.msg = msg
        self.add_note(msg)

