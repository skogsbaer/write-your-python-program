# Wrapper module for typeguard. Do not import typeguard directly but always via myTypeguard
from __future__ import annotations
from typing import *
from dataclasses import dataclass

# We externally adjust the PYTHONPATH so that the typeguard module can be resolved
import typeguard # type: ignore

@dataclass(frozen=True)
class Namespaces:
    globals: dict
    locals: dict
    @staticmethod
    def empty() -> Namespaces:
        return Namespaces({}, {})

def matchesTy(a: Any, ty: Any, ns: Namespaces) -> bool:
    try:
        typeguard.check_type(a,
                             ty,
                             collection_check_strategy=typeguard.CollectionCheckStrategy.ALL_ITEMS,
                             ns=(ns.globals, ns.locals))
        return True
    except typeguard.TypeCheckError as e:
        return False

def getTypeName(t: Any) -> str:
    return typeguard._utils.get_type_name(t, ['__wypp__'])
