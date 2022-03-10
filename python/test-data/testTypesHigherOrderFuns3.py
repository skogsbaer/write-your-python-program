from wypp import *

@record
class GameResult:
    homeTeam: str
    homeGoals: int
    guestTeam: str
    guestGoals: int

# Ergebnisse des Spieltags der Frauen-Bundesliga vom 18.12. - 20.12.2020
game1 = GameResult("Essen", 0, "Wolfsburg", 2)
game2 = GameResult("Bremen", 0, "Frankfurt", 5)
game3 = GameResult("Sand", 0, "Bayern", 8)
game4 = GameResult("Leverkusen", 2, "Freiburg", 1)
game5 = GameResult("Hoffenheim", 5, "Potsdam", 0)
game6 = GameResult("Meppen", 0, "Duisburg", 0)

# Berechnet die Punkte eines Fußballspiels für eine der beiden Mannschaften.
# Eingaben:
# - Ergebnis des Spiels
# - Funktion zum Vergleich der Tore. Bekommt die Tore der Heim- und Gastmannschaft
#   übergeben und liefert True, falls die Mannschaft, für die die Punkte ermittelt
#   werden soll, gewinnt.
# Ausgabe: Punktzahl
def gamePoints(game: GameResult, cmp: Callable[[int, int], bool]) -> int:
    h = game.homeGoals
    g = game.guestGoals
    if h == g:
        return 1
    elif cmp(h, g):
        return 3
    else:
        return 0

def mkGamePoints(cmp: Callable[[int, int], bool]) -> Callable[[GameResult], int]:
    return lambda game: gamePoints(game, cmp)

homePoints: Callable[[GameResult], int] = mkGamePoints(lambda g, h: "foo")
guestPoints: Callable[[GameResult], int] = mkGamePoints(lambda g, h: h > g)

check(homePoints(game1), 0)
