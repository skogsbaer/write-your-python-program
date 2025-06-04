# Wrapper module for typeguard. Do not import typeguard directly but always via myTypeguard

from typing import Any
import typeguard.src.typeguard as typeguard


def matchesTy(a: Any, ty: Any) -> bool:
    try:
        typeguard.check_type(a, ty, collection_check_strategy=typeguard.CollectionCheckStrategy.ALL_ITEMS)
        return True
    except typeguard.TypeCheckError as e:
        return False

def renderTy(t: Any) -> str:
    return typeguard._utils.qualified_name(t)

