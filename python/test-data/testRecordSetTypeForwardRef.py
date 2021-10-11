from wypp import * 

@record(mutable=True)
class Record:
    x : A

class A:
    pass

def m():
    r = Record(x=A())
    r.x = "hello"

m()