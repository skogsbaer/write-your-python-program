from wypp import *

# The types of the default values refer to a type defined later
@record
class Bar:
    x: int
    other: Optional[Baz] = None

def f(b: Optional[Baz] = None) -> int:
    return 1

@record
class Baz:
    y: int

print(Bar(1))
print(Bar(1, Baz(2)))
print(f())
print(f(Baz(3)))
