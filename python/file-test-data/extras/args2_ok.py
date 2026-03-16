from wypp import *

def f(x: int, **kw: dict[str, int]):
    print(f'x={x}, kw={kw}')

f(1)
f(1, y=2)
f(1, y=2, z=3)
f(1, **{'y': 2, 'z': 3}) 
