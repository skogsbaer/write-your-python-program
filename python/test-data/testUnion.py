from wypp import *

@record
class Pizza:
    pass

@record
class Noodle:
    pass

Beer = Literal['pils', 'weizen']
Food = Union[Pizza, Noodle]
T = Union[Food, Beer, int]


def foo(t: T) -> str:
    if isinstance(t, Beer):
        return 'beer'
    elif isinstance(t, Food):
        if isinstance(t, Pizza):
            return 'pizza'
        elif isinstance(t, Noodle):
            return 'noodle'

print(foo(Pizza()))
print(foo(Noodle()))
print(foo('pils'))
