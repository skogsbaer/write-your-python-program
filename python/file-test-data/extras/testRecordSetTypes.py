from wypp import * 

@record(mutable=True)
class Record:
    x : int
    y : list[str]

def m():
    r = Record(x=42, y=[])
    r.x = "hello"

m()