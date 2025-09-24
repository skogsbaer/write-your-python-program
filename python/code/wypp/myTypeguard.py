# Wrapper module for typeguard. Do not import typeguard directly but always via myTypeguard
from __future__ import annotations
from typing import *
from dataclasses import dataclass
from myLogging import *

# We externally adjust the PYTHONPATH so that the typeguard module can be resolved
import typeguard # type: ignore

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

def matchesTy(a: Any, ty: Any, ns: Namespaces) -> MatchesTyResult:
    try:
        typeguard.check_type(a,
                             ty,
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
