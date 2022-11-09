from wypp import *

@record
class Pizza:
    pass

@record
class Beer:
    pass

def foo(x: Beer | Pizza) -> None:
    print(x)

foo(Beer())
