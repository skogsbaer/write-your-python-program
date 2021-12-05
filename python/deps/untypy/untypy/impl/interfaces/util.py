def overwrite(typ):
    def inner(fn):
        setattr(fn, '__overwrite', typ)
        return fn

    return inner
