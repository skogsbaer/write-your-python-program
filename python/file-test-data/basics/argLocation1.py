class C:
    def m(self, a: int, b: int, c: int) -> int:
        return a + b + c

# The second argument must be highlighted
x = C().m(1, 'zwei', 3)
