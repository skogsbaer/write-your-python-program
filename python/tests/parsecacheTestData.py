# Keep line numbers intact, otherwise you have to adjust the tests.

def bar():
    pass

def foo():
    pass

class C:
    x: int
    y: str

class D:
    x: int
    z: str
    def foo(self):
        pass

def spam() -> int:
    return 1

def spam() -> int:
    def foo():
        pass
    return 2
