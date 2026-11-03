# from __future__ import annotations
# Leave the comment, it's needed for tests with python versions <= 3.13
from wypp import *

# Der Lebensstatus ist entweder tot oder lebendig
type Lebensstatus = Literal['tot', 'lebendig']

# Ein Gürteltiert hat folgende Eigenschaften
# - Lebensstatus: tot oder lebendig (Typ: Lebensstatus)
# - Gewicht in Gramm (Typ: int)
@record
class Gürteltier:
    lebenstatus: Lebensstatus
    gewicht: int

# Ein Tier ist eins der folgenden:
# - Gürteltier (Typ: Gürteltier) oder
# - Papagei (Typ: Papagei)
type Tier = Union[Gürteltier, Papagei]

# Ein Papagei hat folgende Eigenschaften:
# - Gewichtsklasse (Typ: Gewichtsklasse)
# - Satz den er sagt (Typ: string)
@record
class Papagei:
    gewichtsklasse: Gewichtsklasse
    satz: str

# Die Gewichtsklasse eines Papageis ist leicht, mittel oder schwer
type Gewichtsklasse = Literal['leicht', 'mittel', 'schwer']

# Funktion zur Bestimmung des Gewichts von Tieren
# Eingabe: ein Tier (Typ: Tier)
# Ergebnis: Gewicht in Gramm (Typ: int)
def wiegeTier(tier: Tier) -> int:
    if isinstance(tier, Gürteltier):
        return tier.gewicht
    elif tier.gewichtsklasse == 'leicht':
        return 900
    elif tier.gewichtsklasse == 'mittel':
        return 1200
    else:
        return 1500

# All types are defined at this point
dora = Gürteltier('lebendig', 25000)
daniel = Gürteltier('tot', 30000)
paula = Papagei('mittel', "Let's go to the punkrock show")
peter = Papagei('leicht', 'oh not, not again')

check(wiegeTier(dora), 25000)
check(wiegeTier(daniel), 30000)
check(wiegeTier(paula), 1200)
check(wiegeTier(peter), 900)
