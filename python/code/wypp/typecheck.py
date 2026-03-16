from __future__ import annotations
from collections.abc import Callable
from typing import ParamSpec, TypeVar, Any, Optional, Literal
import inspect
from dataclasses import dataclass
import utils
from myTypeguard import matchesTy, MatchesTyResult, MatchesTyFailure, Namespaces
import stacktrace
import location
import errors
from myLogging import *

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

def handleMatchesTyResult(res: MatchesTyResult, getTyLoc: Callable[[], Optional[location.Loc]]) -> bool:
    match res:
        case MatchesTyFailure(exc, ty):
            if isDebug():
                debug(f'Exception occurred while calling matchesTy with type {ty}, re-raising')
                raise exc
            else:
                raise errors.WyppTypeError.invalidType(ty, getTyLoc())
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
            locDecl = lambda: info.getParamSourceLocation(name)
            if not handleMatchesTyResult(matchesTy(p.default, ty, cfg.ns), locDecl):
                raise errors.WyppTypeError.defaultError(location.CallableName.mk(info), name,
                                                        locDecl(), ty, p.default)

_argCountCache = {}

def mandatoryArgCount(sig: inspect.Signature) -> int:
    x = _argCountCache.get(sig)
    if x is not None:
        return x
    required_kinds = {
        inspect.Parameter.POSITIONAL_ONLY,
        inspect.Parameter.POSITIONAL_OR_KEYWORD,
        inspect.Parameter.KEYWORD_ONLY,
    }
    res = 0
    for p in sig.parameters.values():
        if p.kind in required_kinds and p.default is inspect._empty:
            res = res + 1
    _argCountCache[sig] = res
    return res

def checkArgument(p: inspect.Parameter, name: str, idx: Optional[int], a: Any,
                  getLocArg: Callable[[], Optional[location.Loc]],
                  info: location.CallableInfo, cfg: CheckCfg):
    t = p.annotation
    if not isEmptyAnnotation(t):
        if p.kind == inspect.Parameter.VAR_POSITIONAL:
            argT = None
            # For *args annotated as tuple[X, ...], extract the element type X
            origin = getattr(t, '__origin__', None)
            if origin is tuple:
                args = getattr(t, '__args__', None)
                if args:
                    argT = args[0]
            elif t is tuple:
                # bare `tuple` without type parameters, nothing to check
                return
            else:
                raise ValueError(f'Invalid type for rest argument: {t}')
            t = argT
        elif p.kind == inspect.Parameter.VAR_KEYWORD:
            valT = None
            # For **kwargs annotated as dict[str, X], extract the value type X
            origin = getattr(t, '__origin__', None)
            if origin is dict:
                type_args = getattr(t, '__args__', None)
                if type_args and len(type_args) >= 2:
                    valT = type_args[1]
            elif t is dict:
                return
            else:
                raise ValueError(f'Invalid type for keyword argument: {t}')
            t = valT
        locDecl = lambda: info.getParamSourceLocation(name)
        if not handleMatchesTyResult(matchesTy(a, t, cfg.ns), locDecl):
            cn = location.CallableName.mk(info)
            raise errors.WyppTypeError.argumentError(cn,
                                                     name,
                                                     idx,
                                                     locDecl(),
                                                     t,
                                                     a,
                                                     getLocArg())

def checkArguments(sig: inspect.Signature, args: tuple, kwargs: dict,
                   info: location.CallableInfo, cfg: CheckCfg) -> None:
    if isDebug():
        debug(f'Checking arguments when calling {info}')
    paramNames = list(sig.parameters)
    mandatory = mandatoryArgCount(sig)
    kind = getKind(cfg, paramNames)
    offset = 1 if kind == 'method' else 0
    cn = location.CallableName.mk(info)
    # stacktrace.callerOutsideWypp() is expensive, only access it lazily
    def getCallLoc() -> Optional[location.Loc]:
        fi = stacktrace.callerOutsideWypp()
        return None if not fi else location.Loc.fromFrameInfo(fi)
    def getLocArg(idxOrName: int | str) -> Callable[[], Optional[location.Loc]]:
        def f():
            fi = stacktrace.callerOutsideWypp()
            return None if fi is None else location.locationOfArgument(fi, i)
        return f
    def raiseArgMismatch():
        raise errors.WyppTypeError.argCountMismatch(cn,
                                                    getCallLoc(),
                                                    len(paramNames) - offset,
                                                    mandatory - offset,
                                                    len(args) - offset)
    # Classify parameters by kind
    varPositionalParam: Optional[inspect.Parameter] = None
    varKeywordParam: Optional[inspect.Parameter] = None
    positionalNames: list[str] = []
    for pName in paramNames:
        p = sig.parameters[pName]
        if p.kind == inspect.Parameter.VAR_POSITIONAL:
            varPositionalParam = p
        elif p.kind == inspect.Parameter.VAR_KEYWORD:
            varKeywordParam = p
        elif p.kind in (inspect.Parameter.POSITIONAL_ONLY, inspect.Parameter.POSITIONAL_OR_KEYWORD):
            positionalNames.append(pName)
    if len(args) + len(kwargs) < mandatory:
        raiseArgMismatch()
    # Check positional args
    for i in range(len(args)):
        if i < len(positionalNames):
            name = positionalNames[i]
            p = sig.parameters[name]
            checkArgument(p, name, i - offset, args[i], getLocArg(i), info, cfg)
        elif varPositionalParam is not None:
            checkArgument(varPositionalParam, varPositionalParam.name, i - offset, args[i], getLocArg(i), info, cfg)
        else:
            raiseArgMismatch()
    # Check keyword args
    for name in kwargs:
        if name in sig.parameters and sig.parameters[name].kind not in (
            inspect.Parameter.VAR_POSITIONAL, inspect.Parameter.VAR_KEYWORD
        ):
            checkArgument(sig.parameters[name], name, None, kwargs[name], getLocArg(name), info, cfg)
        elif varKeywordParam is not None:
            checkArgument(varKeywordParam, name, None, kwargs[name], getLocArg(name), info, cfg)
        else:
            raise errors.WyppTypeError.unknownKeywordArgument(cn, getCallLoc(), name)

def checkReturn(sig: inspect.Signature, getReturnFrame: Callable[[], Optional[inspect.FrameInfo]],
                result: Any, info: location.CallableInfo, cfg: CheckCfg) -> None:
    if info.isAsync:
        return
    t = sig.return_annotation
    if isEmptyAnnotation(t):
        t = None
    if isDebug():
        debug(f'Checking return value when calling {info}, return type: {t}')
    locDecl = lambda: info.getResultTypeLocation()
    if not handleMatchesTyResult(matchesTy(result, t, cfg.ns), locDecl):
        fi = stacktrace.callerOutsideWypp()
        if fi is not None:
            locRes = location.Loc.fromFrameInfo(fi)
        returnLoc = None
        extraFrames = []
        returnFrame = getReturnFrame()
        if returnFrame:
            returnLoc = location.Loc.fromFrameInfo(returnFrame)
            extraFrames = [returnFrame]
        raise errors.WyppTypeError.resultError(location.CallableName.mk(info), locDecl(), t, returnLoc, result,
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
        return CheckCfg(kind=kind, ns=Namespaces(d['globals'], d['locals']))

P = ParamSpec("P")
T = TypeVar("T")

def wrapTypecheck(cfg: dict | CheckCfg, outerInfo: Optional[location.CallableInfo]=None) -> Callable[[Callable[P, T]], Callable[P, T]]:
    if isinstance(cfg, CheckCfg):
        checkCfg = cfg
    else:
        checkCfg = CheckCfg.fromDict(cfg)
    def _wrap(f: Callable[P, T]) -> Callable[P, T]:
        sig = inspect.signature(f)
        if isEmptySignature(sig):
            return f
        if outerInfo is None:
            # we have a regular function or method
            info = location.StdCallableInfo(f, checkCfg.kind)
        else:
            # special case: constructor of a record
            info = outerInfo
        utils._call_with_frames_removed(checkSignature, sig, info, checkCfg)
        def wrapped(*args, **kwargs) -> T:
            utils._call_with_frames_removed(checkArguments, sig, args, kwargs, info, checkCfg)
            returnTracker = stacktrace.getReturnTracker()
            result = utils._call_with_next_frame_removed(f, *args, **kwargs)
            getRetFrame = lambda: returnTracker.getReturnFrame(0)
            utils._call_with_frames_removed(
                checkReturn, sig, getRetFrame, result, info, checkCfg
            )
            return result
        return wrapped
    return _wrap

def wrapTypecheckRecordConstructor(cls: type, ns: Namespaces) -> Callable:
    checkCfg = CheckCfg.fromDict({'kind': 'method', 'className': cls.__name__,
                                  'globals': ns.globals, 'locals': ns.locals})
    info = location.RecordConstructorInfo(cls)
    return wrapTypecheck(checkCfg, info)(cls.__init__)
