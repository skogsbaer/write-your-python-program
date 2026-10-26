# Wrapper module for typeguard. Do not import typeguard directly but always via myTypeguard
from __future__ import annotations
from dataclasses import dataclass
# We externally adjust the PYTHONPATH so that the typeguard module can be resolved
import typeguard  # type: ignore
from typing import *

from .myLogging import *

@dataclass(frozen=True)
class Namespaces:
    globals: dict
    locals: dict
    @staticmethod
    def empty() -> Namespaces:
        return Namespaces({}, {})

@dataclass(frozen=True)
class MatchesTyFailure:
    # This is potentially a failure because of an invalid type
    exception: Exception
    ty: Any

type MatchesTyResult = bool | MatchesTyFailure

def matchesTy(a: Any, ty: Any, ns: Namespaces,
              ignoreUnresolvedForwardRefs: bool = False) -> MatchesTyResult:
    # Since python 3.14, annotations may contain ForwardRef objects (see utils.getAnnotations).
    # If such a ForwardRef cannot be resolved (e.g. because the type is defined after its
    # first use), we want an error, not just a warning. For checks performed at definition time,
    # the type might legitimately be defined later, so these checks can ignore such ForwardRefs.
    if ignoreUnresolvedForwardRefs:
        policy = typeguard.ForwardRefPolicy.IGNORE
    else:
        policy = typeguard.ForwardRefPolicy.ERROR
    try:
        typeguard.check_type(a,
                             ty,
                             forward_ref_policy=policy,
                             collection_check_strategy=typeguard.CollectionCheckStrategy.ALL_ITEMS,
                             ns=(ns.globals, ns.locals))
        return True
    except typeguard.TypeCheckError as e:
        return False
    except Exception as e:
        debug(f'Exception when checking type, ns={ns}: {e}')
        return MatchesTyFailure(e, ty)

def getTypeName(t: Any) -> str:
    res: str = typeguard._utils.get_type_name(t, ['__wypp__'])
    wyppPrefixes = ['wypp.writeYourProgram.']
    for p in wyppPrefixes:
        if res.startswith(p):
            return 'wypp.' + res[len(p):]
    return res
