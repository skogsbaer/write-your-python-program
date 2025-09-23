class C:
    def __init__(self, x: int):
        self.x = x

    def method(self, y: int) -> int:
        return self.x + y

c = C(1)
c.method(2)
print('ok')
