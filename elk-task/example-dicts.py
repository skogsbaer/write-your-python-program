from wypp import *

# Every shape a dict row can take.
#
# Like example-showcase.py this is a looking-at example, not a definition-of-done case.
# Step to the end, then read the heap from the top down: each dict below is one of the
# four combinations of "key is a reference" and "value is a reference", plus the cases
# where the same object turns up on both sides.
#
# What to look for: the key column of a dict is washed in the dict's own colour, so the
# two halves of a row are told apart without reading them, and every arrow leaving a
# dict carries a K or a V saying which half it left.


@record
class Point:
    x: int
    y: int


# --- 1. Neither half is a reference ----------------------------------------------------
# The ordinary case, and the one that has to stay quiet: no arrows at all, just the two
# tinted columns.

ages = {'lara': 21, 'noah': 19, 'mila': 23}


# --- 2. The value is a reference -------------------------------------------------------
# The value cell reads [value] and sends out one arrow, marked V.

groups = {'evens': [2, 4, 6], 'odds': [1, 3, 5]}


# --- 3. The key is a reference ---------------------------------------------------------
# The mirror image: [key] in the left cell, one arrow marked K. Tuples are the usual
# reason a key ends up on the heap, since a key has to be immutable.

names = {(0, 0): 'origin', (1, 0): 'east'}


# --- 4. Both halves are references -------------------------------------------------------
# Two arrows out of a single row, from two heights: K from the upper third, V from the
# lower. This is the row the badges exist for.

neighbours = {(0, 0): ['east', 'north'], (1, 0): ['origin']}


# --- 5. One object on both sides of the same row ----------------------------------------
# `here` is the key *and* the value, so both arrows point at the same node. Only the
# badges say which arrow is which.

here = Point(2, 3)
itself = {here: here}


# --- 6. The same object as a key in one dict and a value in another ---------------------
# Three arrows reach `shared`: a K, a V, and the plain one from the global frame.

shared = (7, 8)
usedAsKey = {shared: 'as a key'}
usedAsValue = {'as a value': shared}


# --- 7. A dict inside a dict -------------------------------------------------------------
# Nesting: the outer V arrow lands on a dict whose own rows are tinted the same way.

board = {'white': {'king': 'e1'}, 'black': {'king': 'e8'}}


# --- 8. Dicts with nothing in them --------------------------------------------------------
# An empty dict is a header and no rows; an empty key or value column never appears.

empty = {}
holder = {'nothing yet': {}}


# --- 9. A dict reached only through a list ------------------------------------------------
# Collapse `rows` and both dicts go with it: nothing else points at them.

rows = [{'id': 1}, {'id': 2}]
