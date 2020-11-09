def _isNumber(x):
    t = type(x)
    return (t is int or t is float)

_EPSILON = 0.00001

def _seqEq(seq1, seq2, structuralObjEq):
    if len(seq1) != len(seq2):
        return False
    for i, x in enumerate(seq1):
        y = seq2[i]
        if not deepEq(x, y, structuralObjEq):
            return False
    return True

def _dictEq(d1, d2, structuralObjEq):
    ks1 = sorted(d1.keys())
    ks2 = sorted(d2.keys())
    if ks1 != ks2: # keys should be exactly equal
        return False
    for k in ks1:
        if not deepEq(d1[k], d2[k], structuralObjEq):
            return False
    return True

def _objToDict(o):
    d = {}
    for n in dir(o):
        if n and n[0] == '_':
            continue
        x = getattr(o, n)
        d[n] = x
    return d

def _objEq(o1, o2, structuralObjEq):
    return _dictEq(_objToDict(o1), _objToDict(o2), structuralObjEq)

def deepEq(v1, v2, structuralObjEq=False):
    """
    Computes deep equality of v1 and v2. With structuralObjEq=False, objects are compared
    by __eq__. Otherwise, objects are compared attribute-wise, only those attributes
    returned by dir that do not start with an underscore are compared.
    """
    # print(f'v1={v1}, v2={v2}, structuralObjEq={structuralObjEq}')
    if v1 == v2:
        return True
    if _isNumber(v1) and _isNumber(v2):
        diff = v1 - v2
        if abs(diff) < _EPSILON:
            return True
        else:
            return False
    ty1 = type(v1)
    if ty1 != type(v2):
        return False
    if ty1 == list or ty1 == tuple:
        return _seqEq(v1, v2, structuralObjEq)
    if ty1 == dict:
        return _dictEq(v1, v2, structuralObjEq)
    if ty1 == str:
        return False
    if hasattr(v1, '__class__'):
        if structuralObjEq:
            return _objEq(v1, v2, structuralObjEq)
        else:
            return False # v1 == v2 already checked
    return False

