class Base:
    def foo(self, x: int, y: str):
        pass

class Sub(Base):
    def foo(self, y: int, x: float):
        pass

def bar(b: Base):
    b.foo(1, "foo")

bar(Sub())
