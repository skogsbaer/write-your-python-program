import unittest
import i18n
import location
import inspect
import utils

class TestI18nTranslations(unittest.TestCase):
    def setUp(self):
        # Get all functions that return strings
        blacklist = ['tr']
        self.stringFunctions = []
        for name, func in inspect.getmembers(i18n, inspect.isfunction):
            if not name in blacklist and \
                hasattr(func, '__annotations__') and func.__annotations__.get('return') == str:
                self.stringFunctions.append((name, func))

    def _getCallableNameVariants(self):
        return [
            location.CallableName('foo', 'function'),
            location.CallableName('foo', location.ClassMember('method', 'foo')),
            location.CallableName('foo', location.ClassMember('recordConstructor', 'foo'))
        ]

    def _getTestArgs(self, func):
        sig = inspect.signature(func)
        args = []
        hasCallableName = False

        for paramName, param in sig.parameters.items():
            if param.annotation == str:
                args.append('foo')
            elif param.annotation == int:
                args.append(1)
            elif param.annotation == location.CallableName:
                args.append(None)  # Placeholder
                hasCallableName = True
            else:
                args.append('foo')  # Default fallback

        if hasCallableName:
            # Generate variants for each CallableName parameter
            variants = []
            for variant in self._getCallableNameVariants():
                testArgs = []
                for i, arg in enumerate(args):
                    if arg is None:  # CallableName placeholder
                        testArgs.append(variant)
                    else:
                        testArgs.append(arg)
                variants.append(testArgs)
            return variants
        else:
            return [args] if args else [[]]

    def testAllI18NFunctions(self):
        with utils.underTest(True):
            for lang in i18n.allLanguages:
                with i18n.explicitLang(lang):
                    with self.subTest(lang=lang):
                        for funcName, func in self.stringFunctions:
                            with self.subTest(function=funcName):
                                argVariants = self._getTestArgs(func)
                                for args in argVariants:
                                    with self.subTest(args=args):
                                        result = func(*args)
                                        self.assertIsInstance(result, str)
                                        self.assertGreater(len(result), 0)

if __name__ == '__main__':
    unittest.main()
