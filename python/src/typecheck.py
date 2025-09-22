from __future__ import annotations
import sys
from collections.abc import Callable
from typing import ParamSpec, TypeVar, Any, Optional, Literal
import inspect
import typing
from dataclasses import dataclass
import utils
from myTypeguard import matchesTy, MatchesTyResult, MatchesTyFailure, Namespaces
import stacktrace
import location
import errors

def printVars(what: str, *l):
    s = what + ": " + ', '.join([str(x) for x in l])
    print(s)

def isEmptyAnnotation(t: Any) -> bool:
    return t is inspect.Signature.empty or t is inspect.Parameter.empty

def isEmptySignature(sig: inspect.Signature) -> bool:
    for x in sig.parameters:
         p = sig.parameters[x]
         if not isEmptyAnnotation(p.annotation):
             return False
    return isEmptyAnnotation(sig.return_annotation)

def handleMatchesTyResult(res: MatchesTyResult, tyLoc: Optional[location.Loc]) -> bool:
    match res:
        case MatchesTyFailure(exc, ty):
            # We want to detect errors such as writing list(int) instead of list[int].
            # Below is a heuristic...
            s = str(ty)
            if '(' in s:
                raise errors.WyppTypeError.invalidType(ty, tyLoc)
            else:
                raise exc
        case b:
            return b

def getKind(cfg: CheckCfg, paramNames: list[str]) -> Literal['function', 'method', 'staticmethod']:
    kind: Literal['function', 'method', 'staticmethod'] = 'function'
    match cfg.kind:
        case location.ClassMember('recordConstructor', _):
            kind = 'method'
        case location.ClassMember('method', _):
            if len(paramNames) > 0 and paramNames[0] == 'self':
                kind = 'method'
            else:
                kind = 'staticmethod'
        case 'function':
            kind = 'function'
    return kind

def checkSignature(sig: inspect.Signature, info: location.CallableInfo, cfg: CheckCfg) -> None:
    paramNames = list(sig.parameters)
    kind = getKind(cfg, paramNames)
    for i in range(len(paramNames)):
        name = paramNames[i]
        p = sig.parameters[name]
        ty = p.annotation
        if isEmptyAnnotation(ty):
            if i == 0 and kind == 'method':
                pass
            else:
                locDecl = info.getParamSourceLocation(name)
                raise errors.WyppTypeError.partialAnnotationError(location.CallableName.mk(info), name, locDecl)
        if p.default is not inspect.Parameter.empty:
            locDecl = info.getParamSourceLocation(name)
            if not handleMatchesTyResult(matchesTy(p.default, ty, cfg.ns), locDecl):
                raise errors.WyppTypeError.defaultError(location.CallableName.mk(info), name, locDecl, ty, p.default)

def mandatoryArgCount(sig: inspect.Signature) -> int:
    required_kinds = {
        inspect.Parameter.POSITIONAL_ONLY,
        inspect.Parameter.POSITIONAL_OR_KEYWORD,
        inspect.Parameter.KEYWORD_ONLY,
    }
    res = 0
    for p in sig.parameters.values():
        if p.kind in required_kinds and p.default is inspect._empty:
            res = res + 1
    return res

def checkArguments(sig: inspect.Signature, args: tuple, kwargs: dict,
                   info: location.CallableInfo, cfg: CheckCfg) -> None:
    paramNames = list(sig.parameters)
    mandatory = mandatoryArgCount(sig)
    kind = getKind(cfg, paramNames)
    offset = 1 if kind == 'method' else 0
    cn = location.CallableName.mk(info)
    fi = stacktrace.callerOutsideWypp()
    def raiseArgMismatch():
        callLoc = None if not fi else location.Loc.fromFrameInfo(fi)
        raise errors.WyppTypeError.argCountMismatch(cn,
                                                    callLoc,
                                                    len(paramNames) - offset,
                                                    mandatory - offset,
                                                    len(args) - offset)
    if len(args) < mandatory:
        raiseArgMismatch()
    for i in range(len(args)):
        if i >= len(paramNames):
            raiseArgMismatch()
        name = paramNames[i]
        p = sig.parameters[name]
        t = p.annotation
        if not isEmptyAnnotation(t):
            a = args[i]
            locDecl = info.getParamSourceLocation(name)
            if not handleMatchesTyResult(matchesTy(a, t, cfg.ns), locDecl):
                if fi is not None:
                    locArg = location.locationOfArgument(fi, i)
                else:
                    locArg = None
                raise errors.WyppTypeError.argumentError(cn,
                                                         name,
                                                         i - offset,
                                                         locDecl,
                                                         t,
                                                         a,
                                                         locArg)

def checkReturn(sig: inspect.Signature, returnFrame: Optional[inspect.FrameInfo],
                result: Any, code: location.CallableInfo, cfg: CheckCfg) -> None:
    t = sig.return_annotation
    if isEmptyAnnotation(t):
        t = None
    locDecl = code.getResultTypeLocation()
    if not handleMatchesTyResult(matchesTy(result, t, cfg.ns), locDecl):
        fi = stacktrace.callerOutsideWypp()
        if fi is not None:
            locRes = location.Loc.fromFrameInfo(fi)
        returnLoc = None
        extraFrames = []
        if returnFrame:
            returnLoc = location.Loc.fromFrameInfo(returnFrame)
            extraFrames = [returnFrame]
        raise errors.WyppTypeError.resultError(location.CallableName.mk(code), locDecl, t, returnLoc, result,
                                               locRes, extraFrames)


@dataclass
class CheckCfg:
    kind: location.CallableKind
    ns: Namespaces
    @staticmethod
    def fromDict(d: dict) -> CheckCfg:
        k = d['kind']
        match k:
            case 'function':
                kind = 'function'
            case 'method':
                kind = location.ClassMember('method', d['className'])
        return CheckCfg(kind=kind, ns=Namespaces.empty())
    def setNamespaces(self, ns: Namespaces) -> CheckCfg:
        return CheckCfg(kind=self.kind, ns=ns)

P = ParamSpec("P")
T = TypeVar("T")

def getNamespacesOfCallable(func: Callable):
    globals = func.__globals__
    # if it's a method, let it see the owning class namespace
    owner = getattr(func, "__qualname__", "").split(".")[0]
    locals = globals.get(owner, {})
    return Namespaces(globals, locals)

def wrapTypecheck(cfg: dict, outerInfo: Optional[location.CallableInfo]=None) -> Callable[[Callable[P, T]], Callable[P, T]]:
    outerCheckCfg = CheckCfg.fromDict(cfg)
    def _wrap(f: Callable[P, T]) -> Callable[P, T]:
        sig = inspect.signature(f)
        if isEmptySignature(sig):
            return f
        checkCfg = outerCheckCfg.setNamespaces(getNamespacesOfCallable(f))
        if outerInfo is None:
            info = location.StdCallableInfo(f, checkCfg.kind)
        else:
            info = outerInfo
        utils._call_with_frames_removed(checkSignature, sig, info, checkCfg)
        def wrapped(*args, **kwargs) -> T:
            returnTracker = stacktrace.installProfileHook()
            utils._call_with_frames_removed(checkArguments, sig, args, kwargs, info, checkCfg)
            result = f(*args, **kwargs)
            utils._call_with_frames_removed(
                checkReturn, sig, returnTracker.getReturnFrame(), result, info, checkCfg
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
