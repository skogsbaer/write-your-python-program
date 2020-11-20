from . import writeYourProgram as w

blacklist = ['writeYourProgram', 'drawingLib']
__all__ = ['drawingLib']

for k in dir(w):
    if k not in blacklist and k and k[0] != '_':
        globals()[k] = getattr(w, k)
        __all__.append(k)
