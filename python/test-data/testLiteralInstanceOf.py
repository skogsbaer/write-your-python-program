from wypp import *

print(isinstance(1, Literal[1,2,3]))
print(not isinstance(1, Literal["1", "2"]))

# nested
print(isinstance(1, Literal[1, Literal[Literal[2], 3]]))
print(isinstance(2, Literal[1, Literal[Literal[2], 3]]))
print(isinstance(3, Literal[1, Literal[Literal[2], 3]]))

print(Literal[1, Literal[Literal[2], 3]] == Literal[1, 2, 3])
print(Literal[1, Literal[Literal[2], 3]] != Literal[1, 2, 3, 4])

@record
class Car:
    licensePlate: str
    color: str

x = Car("AAAA", 'blue')
y = Car("AAAA", 'blue')

# record
print(isinstance(y, Literal['aaa', x]))


