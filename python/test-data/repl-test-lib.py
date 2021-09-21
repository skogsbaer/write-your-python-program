from wypp import *

Status = Literal['tot', 'lebendig']

@record
class Gürteltier:
    gewicht: int
    totOderLebendig: Status

dora = Gürteltier(25000, 'lebendig')
