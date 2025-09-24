def foo(i, j):
    return i + j

class C:
    def bar(self, x):
        return x + 1

k = foo(1, 2)
c = C()
r = c.bar(k)
if r == 4:
    print('ok')
else:
    raise ValueError('unexpected result')
