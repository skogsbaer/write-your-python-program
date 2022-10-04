from wypp import *

def removeFromSeq(seq: Sequence, x: Any) -> Sequence:
    i = seq.index(x)
    return seq[:i] + seq[i+1:]

print(removeFromSeq(["bar", "foo", "baz"], "foo"))
