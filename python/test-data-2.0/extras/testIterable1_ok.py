from wypp import *

def walkThrough(iterable: Iterable):
    for x in iterable:
        print(x)

walkThrough("abc")                 # Strings
walkThrough({1,2,3})               # Mengen
walkThrough({"foo": 13, "bar": 2}) # Dictionaries
