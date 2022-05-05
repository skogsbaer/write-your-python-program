from __future__ import annotations
import unittest
from wypp import *

# Measured 2022-05-05 on a Macbook pro with a 2,3 GHz 8-Core Intel Core i9
#
# * Without type annotations
#
# Run 1
# ['0.004', '0.258', '0.054']
# Run 2
# ['0.004', '0.258', '0.054']
# Run 3
# ['0.005', '0.262', '0.055']
# Median of total: 0.317
#
# * With type annotations (slow way)
#
# Run 1
# ['0.005', '0.271', '2.548']
# Run 2
# ['0.005', '0.272', '2.509']
# Run 3
# ['0.005', '0.271', '2.526']
# Median of total: 2.803
# Factor: 8.8
#
# * With type annotations (fast way)
# Run 1
# ['0.005', '0.126', '1.128']
# Run 2
# ['0.005', '0.120', '1.072']
# Run 3
# ['0.005', '0.119', '1.073']
# Median of total: 1.197
# Factor: 3.7

@dataclass
class SearchTreeNode:
    key: any
    value: any
    left: Optional[SearchTreeNode]
    right: Optional[SearchTreeNode]

class SearchTree:
    def __init__(self, root = None):
        self.root = root

    # SEITENEFFEKT: verändert den Suchbaum
    def insert(self, key: any, value: any):
        self.root = self.__insertAux(self.root, key, value)

    def __insertAux(self, node: Optional[SearchTreeNode], key: any, value: any) -> SearchTreeNode:
        if node is None:
            return SearchTreeNode(key, value, None, None)
        elif node.key == key:
            node.value = value
            return node
        elif key < node.key:
            node.left = self.__insertAux(node.left, key, value)
            return node
        else: # key > node.key
            node.right = self.__insertAux(node.right, key, value)
            return node

def inorder(node: any):
    if node is not None:
        inorder(node.left)
        inorder(node.right)

# Tests
import random

def randomInts(n, low, high):
    res = []
    for _ in range(n):
        i = random.randint(low, high)
        res.append(i)
    return res

def assertSearchTree(node):
    if node == None:
        return
    inorder(node.left)
    inorder(node.right)
    assertSearchTree(node.left)
    assertSearchTree(node.right)
    return

def measure(start, times, i):
    import time
    end = time.time()
    times[i] = times[i] + (end - start)
    return end

def run(f):
    times = [0,0,0]
    import time
    for _ in range(100):
        start = time.time()
        l = randomInts(30, 0, 50)
        t = SearchTree()
        for i in l:
            start = measure(start, times, 0)
            t.insert(i, "value_" + str(i))
            start = measure(start, times, 1)
            f(t.root)
            start = measure(start, times, 2)
    print([f'{x:.3f}' for x in times])

def bench(f):
    import time
    times = []
    for i in [1,2,3]:
        print(f'Run {i}')
        start = time.time()
        run(f)
        end = time.time()
        times.append(end - start)
    times.sort()
    print(f'Median of total: {times[1]:.3f}')

import cProfile
#cProfile.run('run()', 'profile')
bench(assertSearchTree)
