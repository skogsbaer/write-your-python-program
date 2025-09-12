# Wrapper module for typeguard. Do not import typeguard directly but always via myTypeguard
from __future__ import annotations
from typing import *
# We externally adjust the PYTHONPATH so that the typeguard module can be resolved
import typeguard # type: ignore
from dataclasses import dataclass
import sys

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

def renderTy(t: Any) -> str:
    if isinstance(t, str):
        return t
    return typeguard._utils.get_type_name(t, ['__wypp__'])

