import typing
import dataclasses
import inspect
import sys
import myTypeguard
import errors
import typecheck
import location
import stacktrace
from utils import _call_with_frames_removed

EQ_ATTRS_ATTR = '__eqAttrs__'

_typeCheckingEnabled = False

def init(enableTypeChecking=True):
    global _typeCheckingEnabled
    _typeCheckingEnabled = enableTypeChecking

def _collectDataClassAttributes(cls):
    result = dict()
    for c in cls.mro():
        if hasattr(c, '__kind') and c.__kind == 'record' and hasattr(c, '__annotations__'):
            result = c.__annotations__ | result
    return result

def _getNamespacesOfClass(cls):
    mod = sys.modules.get(cls.__module__) or inspect.getmodule(cls)
    globals = vars(mod) if mod else {}
    owner = getattr(cls, "__qualname__", "").split(".")[0]
    locals = globals.get(owner, {})
    return myTypeguard.Namespaces(globals, locals)

def _checkRecordAttr(cls: typing.Any,
                     ns: myTypeguard.Namespaces,
                     name: str,
                     ty: typing.Any,
                     tyLoc: typing.Optional[location.Loc],
                     v: typing.Any):
    if not typecheck.handleMatchesTyResult(myTypeguard.matchesTy(v, ty, ns), tyLoc):
        fi = stacktrace.callerOutsideWypp()
        if fi:
            loc = location.Loc.fromFrameInfo(fi)
        else:
            loc = None
        # FIXME: i18n
        raise errors.WyppTypeError.recordAssignError(cls.__name__,
                                                        name,
                                                        ty,
                                                        tyLoc,
                                                        v,
                                                        loc)
    return v

def _patchDataClass(cls, mutable: bool):
    fieldNames = [f.name for f in dataclasses.fields(cls)]
    setattr(cls, EQ_ATTRS_ATTR, fieldNames)

    if hasattr(cls, '__annotations__'):
        # add annotions for type checked constructor.
        cls.__kind = 'record'
        cls.__init__.__annotations__ = _collectDataClassAttributes(cls)
        cls.__init__ = typecheck.wrapTypecheckRecordConstructor(cls)

    if mutable:
        # prevent new fields being added
        fields = set(fieldNames)
        ns = _getNamespacesOfClass(cls)
        info = location.RecordConstructorInfo(cls)
        types = typing.get_type_hints(cls, include_extras=True)
        locs = {}
        for name in fields:
            if not name in cls.__annotations__:
                raise errors.WyppTypeError.noTypeAnnotationForRecordAttribute(name, cls.__name__)
            else:
                locs[name] = info.getParamSourceLocation(name)

        oldSetattr = cls.__setattr__
        def _setattr(obj, name, v):
            ty = types[name]
            tyLoc = locs[name]
            v = _checkRecordAttr(cls, ns, name, ty, tyLoc, v)
            if name in fields:
                oldSetattr(obj, name, v)
            else:
                raise errors.WyppAttributeError(f'Unknown attribute {name} for record {cls.__name__}')
        setattr(cls, "__setattr__", lambda obj, k, v: _call_with_frames_removed(_setattr, obj, k, v))
    return cls

@typing.dataclass_transform()
def record(cls=None, mutable=False):
    def wrap(cls: type):
        newCls = dataclasses.dataclass(cls, frozen=not mutable)
        if _typeCheckingEnabled:
            return _patchDataClass(newCls, mutable)
        else:
            return newCls
    # See if we're being called as @record or @record().
    if cls is None:
        # We're called with parens.
        return wrap
    else:
        # We're called as @dataclass without parens.
        return wrap(cls)
