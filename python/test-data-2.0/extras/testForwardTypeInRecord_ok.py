from wypp import *

type RiverSection = Union[Creek, Confluence]

@record
class Creek:
    origin: str
    name: str

@record
class Confluence:
    location: str
    mainStem: RiverSection
    tributary: RiverSection

kinzig1 = Creek('Loßburg', 'Kinzig')
gutach1 = Creek('Schönwald', 'Gutach')
kinzig2 = Confluence('Hausach', kinzig1, gutach1)
schutter1 = Creek('Schweighausen', 'Schutter')
heidengraben1 = Creek('Lahr', 'Heidengraben')
schutter2 = Confluence('Lahr', schutter1, heidengraben1)
kinzig3 = Confluence('Kehl', kinzig2, schutter2)

def riverName(section: RiverSection) -> str:
    if isinstance(section, Creek): # es handelt sich um einen Bach
        return section.name
    else:  # es handelt sich um einen Zusammenfluss
        return riverName(section.mainStem)

check(riverName(kinzig1), 'Kinzig')
check(riverName(kinzig2), 'Kinzig')
check(riverName(kinzig3), 'Kinzig')
