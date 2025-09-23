# Aufgabe 3

# Aktivitäten eines Kochs modellieren.

from wypp import *

# Teil (c): Pausen modellieren
#Eine Pause ist entweder
#- klein
#- mittag
Art = Literal('klein','mittag')  # <= problem is here

#Eine Pause kann:
# - entweder klein oder mittag sein
# - eine Notiz
@record
class Break:
    pausenart: Art
    note: str
