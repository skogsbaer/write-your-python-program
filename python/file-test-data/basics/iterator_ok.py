from wypp import *

def my_generator() -> Iterator[int]:
    yield 6
    yield "7"

for x in my_generator():
    print(x)
print('ok')
