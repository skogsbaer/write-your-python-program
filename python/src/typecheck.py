from __future__ import annotations
from collections.abc import Callable
from typing import ParamSpec
from typing import TypeVar, Any
import inspect
import typing
from dataclasses import dataclass
import utils
from myTypeguard import matchesTy, renderTy

def printVars(what: str, *l):
    s = what + ": " + ', '.join([str(x) for x in l])
    print(s)

def isEmptyAnnotation(t: Any) -> bool:
    return t is inspect.Signature.empty or t is inspect.Parameter.empty

def checkArguments(sig: inspect.Signature, args: tuple, kwargs: dict, cfg: CheckCfg) -> None:
    params = list(sig.parameters)
    if len(params) != len(args):
        raise TypeError(f"Expected {len(params)} arguments, got {len(args)}")
    for i in range(len(args)):
        name = params[i]
        t = sig.parameters[name].annotation
        if isEmptyAnnotation(t):
            if i == 0 and cfg.kind == 'method':
                if name != 'self':
                    raise TypeError(f'Name of first parameter of method {name} must be self not {name}')
            else:
                raise TypeError(f'Missing type for parameter {name}')
        else:
            a = args[i]
            if not matchesTy(a, t):
                raise TypeError(f'Expected argument of type {renderTy(t)} for parameter {name}, got {renderTy(type(a))}: {a}')

def checkReturn(sig: inspect.Signature, result: Any) -> None:
    t = sig.return_annotation
    if isEmptyAnnotation(t):
        t = None
    if not matchesTy(result, t):
        print(t)
        raise TypeError(f"Expected return value of type {renderTy(t)}, got {renderTy(type(result))}: {result}")

FunKind = typing.Literal['function', 'method', 'staticmethod']
@dataclass
class CheckCfg:
    kind: FunKind
    @staticmethod
    def fromDict(d: dict) -> CheckCfg:
        return CheckCfg(kind=d['kind'])

P = ParamSpec("P")
T = TypeVar("T")

def wrapTypecheck(cfg: dict) -> Callable[[Callable[P, T]], Callable[P, T]]:
    checkCfg = CheckCfg.fromDict(cfg)
    def _wrap(f: Callable[P, T]) -> Callable[P, T]:
        sig = inspect.signature(f)
        def wrapped(*args, **kwargs) -> T:
            checkArguments(sig, args, kwargs, checkCfg)
            result = utils._call_with_frames_removed(f, *args, **kwargs)
            checkReturn(sig, result)
            return result
        return wrapped
    return _wrap
