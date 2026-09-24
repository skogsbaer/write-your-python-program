from wypp import *

# A tour of everything the visualization can draw.
#
# Unlike the other three examples, this one is not a definition-of-done case - it exists
# to be looked at. Each block puts one particular shape on screen; the comment says what
# to look for. Step to the end first, then walk backwards.


@record
class Book:
    title: str
    pages: int
    rating: float


# --- One node of every kind, so the colour accents can be compared side by side ------
# instance (blue), list (green), tuple (purple), dict (orange), set (yellow).

dune = Book('Dune', 412, 4.5)
sizes = (13, 21)
tags = {'scifi', 'classic', 'reread'}
byTitle = {'Dune': dune}


# --- Plain values, one of each type the renderer formats ------------------------------
# Note that None prints as None rather than as an empty cell.

count = 3
average = 4.25
shelfName = 'Reading list'
finished = True
nextUp = None


# --- Collapsing: nothing in here has a name of its own --------------------------------
# Collapse `shelf` (click its header) and both Books disappear with it, because no other
# arrow reaches them.

shelf = [Book('Emma', 474, 4.0), Book('Ulysses', 730, 3.2)]


# --- ... but a shared object survives -------------------------------------------------
# `dune` has a name of its own and `byTitle` also points at it, so collapsing
# `favourites` removes only the arrow, not the node.

favourites = [dune, Book('Solaris', 204, 4.1)]


# --- Dicts whose keys are references ---------------------------------------------------
# A reference key has no text, so the cell reads [key] and grows its own arrow.

ratingOf = {(4, 5): 'great', (1, 2): 'poor'}

# Here key *and* value are references, so the row sends out two arrows from
# different heights.

pairs = {sizes: shelf}


# --- Cycles: the edges come back on themselves -----------------------------------------

chain = []
chain.append(chain)

alpha = []
beta = [alpha]
alpha.append(beta)


# --- A tall node, to show the row striping ---------------------------------------------

pageCounts = [412, 474, 730, 204, 96, 288, 350, 512]


# --- Several frames at once -------------------------------------------------------------
# While `describe` runs there are three frames on screen: Global, report and describe.
# Only the innermost one gets the current-frame accent. Watch the `return` row appear in
# a frame just before it disappears - it is the one row drawn in the accent colour.

def describe(book: Book) -> str:
    return book.title + ' (' + str(book.pages) + ' pages)'


def report(books: list[Book]) -> list[str]:
    lines = []
    for book in books:
        lines.append(describe(book))
    return lines


def longest(books: list[Book]) -> Book:
    best = books[0]
    for book in books:
        if book.pages > best.pages:
            best = book
    return best


summary = report(favourites)
biggest = longest(favourites)

print(summary)
print(biggest.title)
