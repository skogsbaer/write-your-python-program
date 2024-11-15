from wypp import *

@record
class Pizza:
    nameP: str

@record
class Noodles:
    nameN: str

type Food = Union[Pizza, Noodles]

@record
class Beer:
    nameB: str

type All = Union[Food, Beer]

def foo(a: All):
    if isinstance(a, Pizza):
        print(f'pizza: {a.nameP}')
    elif isinstance(a, Noodles):
        print(f'noodles: {a.nameN}')
    elif isinstance(a, Beer):
        print(f'beer: {a.nameB}')
    else:
        impossible()

foo(Pizza('Napoli'))
foo(Noodles('Penne'))
foo(Beer('Export'))
