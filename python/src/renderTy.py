import collections.abc
import types
from typing import *
import myTypeguard
#def renderTy(t: Any) -> str:
#    if isinstance(t, str):
#        return t
#    return str(t)
#    # return typeguard._utils.get_type_name(t, ['__wypp__'])

_NoneType = type(None)

def renderTy(tp: Any) -> str:
    # Does not work: return typeguard._utils.get_type_name(t, ['__wypp__'])
    # For example, Callable[[int, bool], str] is formated as "Callable[list, str]"

    if isinstance(tp, str):
        # forward reference
        return tp

    origin = get_origin(tp)
    args   = get_args(tp)

    # Simple / builtin / classes
    if origin is None:
        # e.g. int, str, custom classes, Any, typing.NoReturn, typing.Never
        if tp is Any: return "Any"
        if tp is _NoneType: return "None"
        if tp is types.EllipsisType: return "..."
        if isinstance(tp, list): return str(tp)
        if isinstance(tp, tuple): return str(tp)
        if isinstance(tp, dict): return str(tp)
        return myTypeguard.getTypeName(tp)

    # Union / Optional (PEP 604)
    if origin is Union or origin is types.UnionType:
        if len(args) == 2:
            if args[0] is _NoneType and args[1] is not _NoneType:
                return f"Optional[{renderTy(args[1])}]"
            elif args[1] is _NoneType and args[0] is not _NoneType:
                return f"Optional[{renderTy(args[0])}]"
        parts = [renderTy(a) for a in args]
        return "Union[" + ", ".join(parts) + "]"

    # Annotated[T, ...]
    if origin is Annotated:
        base, *meta = args
        if len(meta) >= 1 and isinstance(meta[-1], str):
            return meta[-1]
        metas = ", ".join(repr(m) for m in meta)
        return f"Annotated[{renderTy(base)}, {metas}]"

    # Literal[...]
    if origin is Literal:
        return "Literal[" + ", ".join(repr(a) for a in args) + "]"

    # Callable[[A, B], R] or Callable[..., R]
    if origin in (Callable, collections.abc.Callable):
        params, ret = args
        if params is Ellipsis:
            params_s = "..."
        else:
            params_s = ", ".join(renderTy(p) for p in params)
        return f"Callable[[{params_s}], {renderTy(ret)}]"

    # Tuple[T1, T2] or Tuple[T, ...]
    if origin is tuple:
        if len(args) == 2 and args[1] is Ellipsis:
            return f"tuple[{renderTy(args[0])}, ...]"
        elif len(args) == 0:
            return "tuple[()]"
        return "tuple[" + ", ".join(renderTy(a) for a in args) + "]"

    # ClassVar[T], Final[T]
    if origin is ClassVar:
        return f"ClassVar[{renderTy(args[0])}]"
    if origin is Final:
        return f"Final[{renderTy(args[0])}]"

    # Parametrized generics like list[T], dict[K, V], set[T], type[T], etc.
    name = getattr(origin, "__name__", None) or getattr(origin, "__qualname__", repr(origin))
    if args:
        return f"{name}[" + ", ".join(renderTy(a) for a in args) + "]"
    else:
        return name
