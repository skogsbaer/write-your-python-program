# DeliberateError instances are not reported as bugs
class DeliberateError:
    pass

class WyppTypeError(TypeError, DeliberateError):
    pass

class WyppAttributeError(AttributeError, DeliberateError):
    pass
