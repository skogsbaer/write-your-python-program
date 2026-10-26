from wypp import *

@record(mutable=True)
class Counter:
    # Name des Zählers
    name: str
    count: int

    def inc(self) -> None:
        self.count = self.count + 1

c = Counter('clicks', 0)
c.inc()
# The whole record up to the last attribute must be shown, with count highlighted
c.count = 'eins'
