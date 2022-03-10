import inspect


class IndicatorStr:
    ty: str
    indicator: str

    def __init__(self, ty: str, indicator: str = ""):
        n = 0 if ty is None else len(ty)
        while len(indicator) < n:
            indicator += " "

        self.ty = ty
        self.indicator = indicator

    def __add__(self, other):
        return IndicatorStr(self.ty + other.ty, self.indicator + other.indicator)

    def join(self, lst):
        return IndicatorStr(
            self.ty.join(map(lambda s: s.ty, lst)),
            self.indicator.join(map(lambda s: s.indicator, lst)),
        )


def format_argument_values(args, kwargs):
    allargs = []
    for a in args:
        allargs.append(a.__repr__())
    for k,v in kwargs.items():
        allargs.append(k + "=" + v.__repr__())

    return "(" + ", ".join(allargs) + ")"


def withIndefiniteArticle(s):
    if s:
        first = s[0]
        if first in "aeiouyAEIOUY":
            return 'an ' + s
        else:
            return 'a ' + s
    else:
        return s
