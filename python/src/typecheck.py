from __future__ import annotations
import sys
from collections.abc import Callable
from typing import ParamSpec, TypeVar, Any, Optional, Literal
import inspect
import typing
from dataclasses import dataclass
import utils
from myTypeguard import matchesTy, renderTy
import stacktrace
import location
import errors

def printVars(what: str, *l):
    s = what + ": " + ', '.join([str(x) for x in l])
    print(s)

def isEmptyAnnotation(t: Any) -> bool:
    return t is inspect.Signature.empty or t is inspect.Parameter.empty

def mkCallableName(c: location.CallableInfo) -> errors.CallableName:
    return errors.CallableName(c.name, c.kind)

def checkArguments(sig: inspect.Signature, args: tuple, kwargs: dict,
                   code: location.CallableInfo, cfg: CheckCfg) -> None:
    params = list(sig.parameters)
    if len(params) != len(args):
        raise TypeError(f"Expected {len(params)} arguments, got {len(args)}")
    kind: Literal['function', 'method', 'staticmethod'] = 'function'
    match cfg.kind:
        case location.ClassMember('constructor', _):
            kind = 'method'
        case location.ClassMember('method', _):
            if len(params) > 0 and params[0] == 'self':
                kind = 'method'
            else:
                kind = 'staticmethod'
        case 'function':
            kind = 'function'
    offset = 1 if kind == 'method' else 0
    for i in range(len(args)):
        name = params[i]
        p = sig.parameters[name]
        t = p.annotation
        if i == 0 and kind == 'method' and isEmptyAnnotation(t):
            pass
        elif i != 0 and isEmptyAnnotation(t):
            locDecl = code.getParamSourceLocation(name)
            raise errors.WyppTypeError.partialAnnotationError(code.name, name, locDecl)
        else:
            a = args[i]
            if not matchesTy(a, t):
                fi = stacktrace.callerOutsideWypp()
                if fi is not None:
                    locArg = location.locationOfArgument(fi, i)
                else:
                    locArg = None
                locDecl = code.getParamSourceLocation(name)
                raise errors.WyppTypeError.argumentError(mkCallableName(code), name, i - offset, locDecl, t, a, locArg)

def checkReturn(sig: inspect.Signature, returnFrame: Optional[inspect.FrameInfo],
                result: Any, code: location.CallableInfo) -> None:
    t = sig.return_annotation
    if isEmptyAnnotation(t):
        t = None
    if not matchesTy(result, t):
        fi = stacktrace.callerOutsideWypp()
        if fi is not None:
            locRes = location.Loc.fromFrameInfo(fi)
        locDecl = code.getResultTypeLocation()
        returnLoc = None
        extraFrames = []
        if returnFrame:
            returnLoc = location.Loc.fromFrameInfo(returnFrame)
            extraFrames = [returnFrame]
        raise errors.WyppTypeError.resultError(mkCallableName(code), locDecl, t, returnLoc, result,
                                               locRes, extraFrames)


@dataclass
class CheckCfg:
    kind: location.CallableKind
    @staticmethod
    def fromDict(d: dict) -> CheckCfg:
        k = d['kind']
        match k:
            case 'function':
                kind = 'function'
            case 'method':
                kind = location.ClassMember('method', d['className'])
        return CheckCfg(kind=kind)

P = ParamSpec("P")
T = TypeVar("T")

def wrapTypecheck(cfg: dict, outerCode: Optional[location.CallableInfo]=None) -> Callable[[Callable[P, T]], Callable[P, T]]:
    checkCfg = CheckCfg.fromDict(cfg)
    def _wrap(f: Callable[P, T]) -> Callable[P, T]:
        sig = inspect.signature(f)
        if outerCode is None:
            code = location.StdCallableInfo(f, checkCfg.kind)
        else:
            code = outerCode
        def wrapped(*args, **kwargs) -> T:
            returnTracker = stacktrace.installProfileHook()
            utils._call_with_frames_removed(checkArguments, sig, args, kwargs, code, checkCfg)
            result = f(*args, **kwargs)
            utils._call_with_frames_removed(
                checkReturn, sig, returnTracker.getReturnFrame(), result, code
            )
            return result
        return wrapped
    return _wrap

def wrapTypecheckRecordConstructor(cls: type) -> Callable:
    code = location.RecordConstructorInfo(cls)
    return wrapTypecheck({'kind': 'method', 'className': cls.__name__}, code)(cls.__init__)

def wrapNoTypecheck(cfg: dict) -> Callable[[Callable[P, T]], Callable[P, T]]:
    def _wrap(f: Callable[P, T]) -> Callable[P, T]:
        return f
    return _wrap
