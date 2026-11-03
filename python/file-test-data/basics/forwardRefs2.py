# from __future__ import annotations
# Leave the comment, it's needed for tests with python versions <= 3.13
from wypp import *

# The type Gewichtsklasse is used before it is defined
@record
class Papagei:
    gewichtsklasse: Gewichtsklasse
    satz: str

paula = Papagei('mittel', "Let's go to the punkrock show")

type Gewichtsklasse = Literal['leicht', 'mittel', 'schwer']
