class Test:
    def __init__(self, foo: 'Foo'):
        pass
    def __repr__(self):
        return 'Test'

class Foo:
    pass

t = Test(Foo())
print(t)
