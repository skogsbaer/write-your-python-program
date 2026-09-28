from wypp import *

# Aus Vorlesung kopiert:
# -------------------------------------------------------------------

test = Literal['a', 'b']

# Ein Bach besteht aus
# - einem Namen
# - einem Ort der Quelle
@record
class Creek:
    origin: str
    name: str

# Ein Zusammenfluss besteht aus
# - Name des Orts
# - Hauptflussabschnitt
# - Nebenflussabschnitt
@record
class Confluence:
    name: str
    mainStem: 'RiverSection'
    tributary: 'RiverSection'

# Ein Flussabschnitt ist entweder
# - ein Bach
# - oder ein Zusammenfluss
RiverSection = Union[Creek, Confluence]

# Beispielflüsse
kinzig1 = Creek('Loßburg', 'Kinzig')
gutach = Creek('Schönwald', 'Gutach')
kinzig2 = Confluence('Hausach', kinzig1, gutach)

heidengraben = Creek('Lahr', 'Heidengraben')
schutter1 = Creek('Schweighausen', 'Schutter')
schutter2 = Confluence('Lahr', schutter1, heidengraben)

kinzig3 = Confluence('Kehl', kinzig2, schutter2)

# -------------------------------------------------------------------

# a) Weitere Flüsse modellieren

elz1 = Creek('Furtwangen', 'Elz')
glotter = Creek('Kandel', 'Glotter')
dreisam1 = Creek('Stegen', 'Dreisam')
ettenbach = Creek('Ettenheimmünster', 'Ettenbach')

dreisam2 = Confluence('Bahlingen', dreisam1, glotter)
elz2 = Confluence('Riegel', elz1, dreisam2)
elz3 = Confluence('Kappel-Graphenhausen', elz2, ettenbach)


# b) Hauptabschnitte zählen

# Zählen, aus wie vielen Hauptabschnitten ein Fluss besteht.
# Eingabe: ein Flussabschnitt
# Ausgabe: anzahl der Hauptabschnitte als int
def howManySections(section: RiverSection) -> int:
    if isinstance(section, Creek):
        return 1
    return 1 + howManySections(section.mainStem)

check(howManySections(kinzig3), 3)
check(howManySections(kinzig2), 2)
check(howManySections(kinzig1), 1)
check(howManySections(schutter2), 2)
check(howManySections(schutter1), 1)
check(howManySections(elz3), 3)
check(howManySections(elz2), 2)
check(howManySections(elz1), 1)


# c) Prüfen, ob man flussaufwärts zu einem Ort gelangt

# Prüft, ob man von einem Flussabschnitt flussaufwärts zu einem Ort gelangt.
# Eingabe:
# - startpunkt als RiverSection
# - zielort als String
# Ausgabe: Antwort als bool
def canSwimUpstream(start: RiverSection, goal: str) -> bool:
    if isinstance(start, Creek):
        return start.origin == goal

    return start.name == goal or \
            canSwimUpstream(start.mainStem, goal) or \
            canSwimUpstream(start.tributary, goal)

check(canSwimUpstream(elz3, 'Riegel'), True)
check(canSwimUpstream(elz3, 'Ettenheimmünster'), True)
check(canSwimUpstream(elz2, 'Ettenheimmünster'), False)
check(canSwimUpstream(elz2, 'Furtwangen'), True)
check(canSwimUpstream(elz2, 'Bahlingen'), True)
check(canSwimUpstream(kinzig3, 'Lahr'), True)
check(canSwimUpstream(kinzig3, 'Schönwald'), True)
check(canSwimUpstream(kinzig2, 'Lahr'), False)
check(canSwimUpstream(kinzig3, 'Kehl'), True) # Per Definition ist der Ort des Zusammenflusses inbegriffen.
