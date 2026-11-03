# from __future__ import annotations
# Leave the comment, it's needed for tests with python versions <= 3.13
from wypp import *

# The type Gewichtsklasse is defined after the record but before its first use
@record
class Papagei:
    gewichtsklasse: Gewichtsklasse
    satz: str

type Gewichtsklasse = Literal['leicht', 'mittel', 'schwer']

paula = Papagei('mittel', "Let's go to the punkrock show")
peter = Papagei('superschwer', 'oh not, not again')
