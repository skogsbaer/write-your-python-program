from typing import *

def my_generator() -> Iterator[int]:
    return 1

g = my_generator()
for x in my_generator():
    print(x)
