# Wrapper module for typeguard. Do not import typeguard directly but always via myTypeguard

from typing import Any
# We externally adjust the PYTHONPATH so that the typeguard module can be resolved
import typeguard # type: ignore

def matchesTy(a: Any, ty: Any) -> bool:
    try:
        typeguard.check_type(a, ty, collection_check_strategy=typeguard.CollectionCheckStrategy.ALL_ITEMS)
        return True
    except typeguard.TypeCheckError as e:
        return False

def renderTy(t: Any) -> str:
    return typeguard._utils.get_type_name(t)

