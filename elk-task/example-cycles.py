from wypp import *

# Definition-of-done case: heap shapes that example.py never produces.
# Covers reference cycles (the traversal must terminate), dicts with reference
# keys and reference values, tuples, and sets.

# Self-referencing list: selfRef[0] is selfRef.
selfRef = []
selfRef.append(selfRef)

# Two-object cycle: left -> right -> left.
left = []
right = [left]
left.append(right)

# Dict with reference values, both anonymous -> collapsing `lookup` removes them.
lookup = {'evens': [2, 4], 'odds': [1, 3]}

# Dict with reference keys (tuples are hashable, and appear as heap objects).
byPair = {(1, 2): ['a'], (3, 4): ['b']}

# Set of plain values, and a tuple mixing references with plain values.
letters = {'a', 'b', 'c'}
mixed = (selfRef, 42, 'text')

# A dict pointing at something that also has its own name.
named = [1, 2, 3]
container = {'named': named, 'anonymous': [4, 5, 6]}
