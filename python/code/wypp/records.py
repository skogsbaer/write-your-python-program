import typing
import dataclasses
import utils
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
        raise errors.WyppTypeError.recordAssignError(cls.__name__,
                                                        name,
                                                        ty,
                                                        tyLoc,
                                                        v,
                                                        loc)
    return v

def _patchDataClass(cls, mutable: bool, ns: myTypeguard.Namespaces):
    fieldNames = [f.name for f in dataclasses.fields(cls)]
    setattr(cls, EQ_ATTRS_ATTR, fieldNames)

    cls.__kind = 'record'
    cls.__init__ = typecheck.wrapTypecheckRecordConstructor(cls, ns)

    if mutable:
        # prevent new fields being added
        fields = set(fieldNames)
        info = location.RecordConstructorInfo(cls)
        locs = {}
        for name in fields:
            if not name in cls.__annotations__:
                raise errors.WyppTypeError.noTypeAnnotationForRecordAttribute(name, cls.__name__)
            else:
                locs[name] = info.getParamSourceLocation(name)
        types = None # lazily initialized because forward references are not available at this point
        oldSetattr = cls.__setattr__
        def _setattr(obj, name, v):
            nonlocal types
            if types is None:
                types = typing.get_type_hints(cls, globalns=ns.globals, localns=ns.locals,
                                              include_extras=True)
            if name in types:
                ty = types[name]
                tyLoc = locs[name]
                v = _checkRecordAttr(cls, ns, name, ty, tyLoc, v)
                oldSetattr(obj, name, v)
            else:
                raise errors.WyppAttributeError(f'Unknown attribute {name} for record {cls.__name__}')
        setattr(cls, "__setattr__", lambda obj, k, v: _call_with_frames_removed(_setattr, obj, k, v))
    return cls

def record(cls=None, mutable=False, globals={}, locals={}):
    ns = myTypeguard.Namespaces(globals, locals)
    def wrap(cls: type):
        newCls = dataclasses.dataclass(cls, frozen=not mutable)
        if _typeCheckingEnabled:
            return utils._call_with_frames_removed(_patchDataClass, newCls, mutable, ns)
        else:
            return newCls
    # See if we're being called as @record or @record().
    if cls is None:
        # We're called with parens.
        return wrap
    else:
        # We're called as @dataclass without parens.
        return _call_with_frames_removed(wrap, cls)
