from wypp import *

BoolOp = Literal['AND', 'NOT', 'OR']

@record
class BoolExpr:
    op: BoolOp
    args: list

BoolFormula = Union[BoolExpr, bool, str]

t1 = "p"
t2 = BoolExpr('AND', [t1, "q"])
t3 = BoolExpr('OR', [True, BoolExpr('NOT', [t2])])

def mapBool(formula: BoolFormula, fun: Callable[[Union[bool, str]], Union[bool, str]]) -> BoolFormula:
    if isinstance(formula, BoolExpr):
        return BoolExpr(formula.op, [mapBool(x, fun) for x in formula.args])
    else:
        return fun(formula)

def invert(formula: BoolFormula) -> BoolFormula:
    def f(y):
        if y == True:
            return False
        elif y == False:
            return True
        else:
            return y
    return mapBool(formula, f)

check(invert(t1), t1)
check(invert(t2), t2)
check(invert(t3), BoolExpr('OR', [False, BoolExpr('NOT', [t2])]))
