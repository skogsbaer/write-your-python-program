from wypp import *

class ConstIterable:
    def __iter__(self):
        return ConstIterator(10)

class ConstIterator:
    def __init__(self, count):
        self.count = count
    def __iter__(self):
        return self
    def __next__(self):
        self.count = self.count - 1
        if self.count < 0:
            raise StopIteration
        else:
            return 1

def mkIterable() -> Iterable:
    return ConstIterable()

i = mkIterable()
j = iter(i)
print(next(j))
