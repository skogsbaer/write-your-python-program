# From AKI_Prog2 V06
from wypp import *

def solve(goal: int, i: int, items: list[tuple[str,int]]) -> Iterable[list[str]]:
    if goal == 0:
        yield [] # Lösung gefunden
    elif i >= len(items):
        return   # Keine Dinge mehr übrig, also keine Lösung
    else:
        item, weight = items[i]
        if weight <= goal:   # Lösungen mit item
            for solution in solve(goal - weight, i + 1, items):
                yield [item] + solution
        yield from solve(goal, i + 1, items)

gifts = [('ball', 500), ('radio', 2000), ('racket', 300), ('easter egg', 600),
         ('shoes', 400), ('cake', 400), ('skates', 700)]

print(list(solve(1400, 0, gifts)))
