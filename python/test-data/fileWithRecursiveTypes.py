from __future__ import annotations

class C:
    def foo(self: C, d: D) -> C:
        return C

class D:
    pass
