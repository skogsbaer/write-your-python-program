from wypp import *

Color = Literal['red', 'yellow', 'green']

def colorToNumber(c: Color) -> int:
    if c == 'red':
        return 0
    elif c == 'yellow':
        return 1
    else:
        return 2

