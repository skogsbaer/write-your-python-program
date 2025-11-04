from wypp import *

# Ein Flussabschnitt ist entweder
# - ein Bach mit Namen und Quelle, oder
# - ein Zusammenfluss eines Haupt- und Nebenflussabschnitts an einem bestimmten Ort.

@record
class Creek:
    origin: str
    name: str

@record
class Confluence:
    location: str
    mainStem: RiverSection
    tributary: RiverSection

type RiverSection = Union[Creek, Confluence]

kinzig1 = Creek('Loßburg', 'Kinzig')
gutach = Creek('Schönwald', 'Gutach')
kinzig2 = Confluence('Hausach', kinzig1, gutach)
schutter1 = Creek('Schweighausen', 'Schutter')
heidengraben = Creek('Lahr', 'Heidengraben')
schutter2 = Confluence('Lahr', schutter1, heidengraben)
kinzig3 = Confluence('Kehl', kinzig2, schutter2)

# Name eines Flussabschnitts bestimmen
# Eingabe: den Flussabschnitt (Typ: RiverSection)
# Ergebnis: der Name (Typ: str)
def riverName(r: RiverSection) -> str:
    if isinstance(r, Creek):
        return r.name
    elif isinstance(r, Confluence):
        return riverName(r.mainStem)

print(riverName(kinzig3))
