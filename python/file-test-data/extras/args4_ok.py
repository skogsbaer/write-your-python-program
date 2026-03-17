from wypp import *

def f(x: int, *rest: tuple, **kw: dict):
    print(f'x={x}, kw={kw}')

f(1)
f(1, 10, '11', y=2, z='3')
f(1, *[10, '11'], **{'y': '2', 'z': 3}) 
