class Test:
    def __init__(self, foo: 'Foo'):
        pass
    def __repr__(self):
        return 'Test'

class FooX:
    pass

t = Test(FooX())
print(t)
