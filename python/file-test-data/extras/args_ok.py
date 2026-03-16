from wypp import *

def f(x: int, *rest: tuple[int,...]):
    print(f'x={x}, rest={rest}')

f(1)
f(1, 2)
f(1, 2, 3)
f(1, *[2,3,4]) 
