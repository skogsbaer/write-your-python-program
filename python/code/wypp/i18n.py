from dataclasses import dataclass
import location
from typing import *
from contextlib import contextmanager
import lang
import utils

type Lang = Literal['en', 'de']

allLanguages: list[Lang] = ['en', 'de']

# If not set explicitly, the current locale is asked for the language
_lang: Optional[Lang] = None

@contextmanager
def explicitLang(newLang: Lang):
    """Context manager to temporarily set the language."""
    global _lang
    oldLang = _lang
    _lang = newLang
    try:
        yield
    finally:
        _lang = oldLang

def getLang() -> Lang:
    if _lang:
        return _lang
    else:
        return lang.pickLanguage(allLanguages, 'en')

def setLang(lang: Lang):
    global _lang
    _lang = lang

def tr(key: str, **kws) -> str:
    match getLang():
        case 'en':
            tmpl = key
        case 'de':
            if key not in DE and utils.isUnderTest():
                raise ValueError(f'Untranslated string: {key}')
            tmpl = DE.get(key, key)
        case x:
            if utils.underTest():
                raise ValueError(f'Unknown language: {x}')
    return tmpl.format(**kws)

DE = {
    'Expecting no return value when calling function `{fun}`.':
        'Kein Rückgabewert erwartet bei Aufruf der Funktion `{fun}`.',
    'Expecting no return value when calling method `{method}` of class `{cls}`.':
        'Kein Rückgabewert erwartet bei Aufruf der Methode `{method}` der Klasse `{cls}`.',
    'Expecting no return value when calling constructor of record `{cls}`.':
        'Kein Rückgabewert erwartet bei Aufruf des Konstruktors des Records `{cls}`.',

    'Expecting return value of type `{ty}` when calling function `{fun}`.':
        'Rückgabewert vom Typ `{ty}` erwartet bei Aufruf der Funktion `{fun}`.',
    'Expecting return value of type `{ty}` when calling method `{method}` of class `{cls}`.':
        'Rückgabewert vom Typ `{ty}` erwartet bei Aufruf der Methode `{method}` der Klasse `{cls}`.',
    'Expecting return value of type `{ty}` when calling constructor of record `{cls}`.':
        'Rückgabewert vom Typ `{ty}` erwartet bei Aufruf des Konstruktors des Records `{cls}`.',

    'But the call returns a value of type `{ty}`.':
        'Aber der Aufruf gibt einen Wert vom Typ `{ty}` zurück.',

    'But no value returned.':
        'Aber kein Rückgabewert vorhanden.',
    'no result returned': 'kein Rückgabewert vorhanden',
    'Call in line {line} causes the function to return no value:':
        'Aufruf in Zeile {line} führt dazu, dass die Funktion keinen Wert zurückgibt:',

    'The call of function `{fun}` expects value of type `{ty}` as {arg}.':
        'Der Aufruf der Funktion `{fun}` erwartet einen Wert vom Typ `{ty}` als {arg}.',
    'The call of method `{method}` of class `{cls}` expects value of type `{ty}` as {arg}.':
        'Der Aufruf der Methode `{method}` der Klasse `{cls}` erwartet einen Wert vom Typ `{ty}` als {arg}.',
    'The call of the constructor of record `{cls}` expects value of type `{ty}` as {arg}.':
        'Der Aufruf des Konstruktors des Records `{cls}` erwartet einen Wert vom Typ `{ty}` als {arg}.',

    'But the value given has type `{ty}`.': 'Aber der übergebene Wert hat den Typ `{ty}`.',
    'But the default value has type `{ty}`.': 'Aber der Default-Wert hat den Typ `{ty}`.',

    'File': 'Datei',
    'Line': 'Zeile',
    'Result type declared in line': 'Rückgabetyp deklariert in Zeile',
    'Type declared in line': 'Typ deklariert in Zeile',
    'Parameter declared in line': 'Parameter deklariert in Zeile',
    'Problematic return in line': 'Fehlerhaftes return in Zeile',
    'Problematic call in line': 'Fehlerhafter Aufruf in Zeile',
    'Call in line {line} causes the problematic return:':
        'Aufruf in Zeile {line} verursacht das fehlerhafte return:',

    'Parameter `{param}` of function `{fun}` requires a type annotation.':
        'Parameter `{param}` der Funktion `{fun}` benötigt eine Typannotation.',
    'Parameter `{param}` of method `{method}` from class `{cls}` requires a type annotation.':
        'Parameter `{param}` der Methode `{method}` der Klasse `{cls}` benötigt eine Typannotation.',
    'Parameter `{param}` of constructor of record `{cls}` requires a type annotation.':
        'Parameter `{param}` des Konstruktors des Records `{cls}` benötigt eine Typannotation.',

    'Attribute `{name}` of record `{record}` requires a type annotation.':
        'Attribut `{name}` des Records `{record}` benötigt eine Typannotation.',

    'invalid type `{ty}`':
        'ungültiger Typ `{ty}`',
    'Cannot set attribute to value of type `{ty}`.':
        'Das Attribut kann nicht auf einen Wert vom Typ `{ty}` gesetzt werden.',
    'Problematic assignment in line': 'Fehlerhafte Zuweisung in Zeile',
    'Attribute `{attrName}` of record `{recordName}` declared with type `{ty}`.':
        'Attribut `{attrName}` des Records `{recordName}` deklariert als Typ `{ty}`.',

    'argument count mismatch': 'Anzahl der Argumente stimmt nicht',
    'Call in line': 'Aufruf in Zeile',
    'Function `{fun}` takes ': 'Funktion `{fun}` benötigt ',
    'Function `{fun}` takes at least ': 'Funktion `{fun}` benötigt mindestens ',
    'Function `{fun}` takes at most ': 'Funktion `{fun}` akzeptiert höchstens ',
    'Method `{method}` of class `{cls}` takes ': 'Methode `{method}` der Klasse `{cls}` benötigt ',
    'Method `{method}` of class `{cls}` takes at least ': 'Methode `{method}` der Klasse `{cls}` benötigt mindestens ',
    'Method `{method}` of class `{cls}` takes at most ': 'Methode `{method}` der Klasse `{cls}` akzeptiert höchstens ',
    'Constructor of record `{cls}` takes ': 'Konstruktor des Records `{cls}` benötigt ',
    'Constructor of record `{cls}` takes at least ': 'Konstruktor des Records `{cls}` benötigt mindestens ',
    'Constructor of record `{cls}` takes at most ': 'Konstruktor des Records `{cls}` akzeptiert höchstens ',
    'Given: ': 'Gegeben: ',

    'Default value for parameter `{paramName}` of function `{fun}` must have type `{ty}`.':
        'Default-Wert des Parameters `{paramName}` der Funktion `{fun}` muss vom Typ `{ty}` sein.',
    'Default value for parameter `{paramName}` of method `{method}` in class `{cls}` must have type `{ty}`.':
        'Default-Wert des Parameters `{paramName}` der Methode `{method}` der Klasse `{cls}` muss vom Typ `{ty}` sein.',
    'Default value for attribute `{paramName}` of record `{cls}` must have type `{ty}`.':
        'Default-Wert des Attributs `{paramName}` des Records `{cls}` muss vom Typ `{ty}` sein.',

    'Unknown attribute {attrName} for record {clsName}':
        'Attribut {attrName} ist nicht bekannt für den Record {clsName}',
    'Did you mean `{ty}`?': 'Wolltest du `{ty}` schreiben?',

    'unknown keyword argument': 'unbekanntes Schlüsselwort-Argument',
    'Function `{fun}` does not accept keyword argument `{name}`.':
        'Funktion `{fun}` akzeptiert kein Schlüsselwort-Argument `{name}`.',
    'Method `{method}` from class `{cls}` does not accept keyword argument `{name}`.':
        'Methode `{method}` der Klasse `{cls}` akzeptiert kein Schlüsselwort-Argument `{name}`.',
    'Constructor of record `{cls}` does not accept keyword argument `{name}`.':
        'Konstruktor des Records `{cls}` akzeptiert kein Schlüsselwort-Argument `{name}`.',

    'invalid record definition': 'ungültige Record-Definition',

    'Expected {expected}, but the result is {actual}':
        'Erwartet wird {expected}, aber das Ergebnis ist {actual}',
    'ERROR: ': 'FEHLER: ',
    'ERROR in ': 'FEHLER in ',
    'File {filename}, line {lineno}: ': 'Datei {filename}, Zeile {lineno}: ',
    'Uncovered case': 'Ein Fall ist nicht abgedeckt',
    'uncovered case': 'ein Fall ist nicht abgedeckt',
    'The impossible happened!': 'Das Unmögliche ist passiert!',
    'Stop of execution': 'Abbruch der Ausführung',
    '1 successful test': '1 erfolgreicher Test',
    'all successful': 'alle erfolgreich',
    'and stop of execution': 'und Abbruch der Ausführung',

    '=== WELCOME to ': '=== WILLKOMMEN bei '
}

def expectingNoReturn(cn: location.CallableName) -> str:
    match cn.kind:
        case 'function':
            return tr('Expecting no return value when calling function `{fun}`.',
                    fun=cn.name)
        case location.ClassMember('method', cls):
            return tr('Expecting no return value when calling method `{method}` of class `{cls}`.',
                    method=cn.name, cls=cls)
        case location.ClassMember('recordConstructor', cls):
            return tr('Expecting no return value when calling constructor of record `{cls}`.',
                    cls=cls)
    raise ValueError(f'Unexpected: {cn}')

def wrongReturnValue(ty: str) -> str:
    return tr('But the call returns a value of type `{ty}`.', ty=ty)

def unexpectedReturn(line: int) -> str:
    return tr('Call in line {line} causes the problematic return:', line=line)

def unexpectedNoReturn(line: int) -> str:
    return tr('Call in line {line} causes the function to return no value:', line=line)

def expectingReturnOfType(cn: location.CallableName, ty: str) -> str:
    match cn.kind:
        case 'function':
            return tr('Expecting return value of type `{ty}` when calling function `{fun}`.',
                    fun=cn.name, ty=ty)
        case location.ClassMember('method', cls):
            return tr('Expecting return value of type `{ty}` when calling method `{method}` of class `{cls}`.',
                    method=cn.name, cls=cls, ty=ty)
        case location.ClassMember('recordConstructor', cls):
            return tr('Expecting return value of type `{ty}` when calling constructor of record `{cls}`.',
                    cls=cls, ty=ty)
    raise ValueError(f'Unexpected: {cn}')

def noReturnValue() -> str:
    return tr('But no value returned.')

def transArg(pos: int):
    match getLang():
        case 'en':
            match pos:
                case 1: return '1st argument'
                case 2: return '2nd argument'
                case 3: return '3rd argument'
                case _: return f'{pos}th argument'
        case 'de':
            match pos:
                case 1: return 'erstes Argument'
                case 2: return 'zweites Argument'
                case 3: return 'drittes Argument'
                case 4: return 'viertes Argument'
                case 5: return 'fünftes Argument'
                case 6: return 'sechstes Argument'
                case 7: return 'siebtes Argument'
                case 8: return 'achtes Argument'
                case 9: return 'neuntes Argument'
                case _: return f'{pos}. Argument'
        case l:
            raise ValueError(f'Unexpected language: {l}')


def expectingArgumentOfTy(cn: location.CallableName, ty: str, pos: int | str) -> str:
    if isinstance(pos, int):
        arg = transArg(pos)
    else:
        match getLang():
            case 'en':
                arg = f'argument `{pos}`'
            case 'de':
                arg = f'Argument `{pos}`'
    match cn.kind:
        case 'function':
            return tr('The call of function `{fun}` expects value of type `{ty}` as {arg}.',
                    fun=cn.name, ty=ty, arg=arg)
        case location.ClassMember('method', cls):
            return tr('The call of method `{method}` of class `{cls}` expects value of type `{ty}` as {arg}.',
                    method=cn.name, cls=cls, ty=ty, arg=arg)
        case location.ClassMember('recordConstructor', cls):
            return tr('The call of the constructor of record `{cls}` expects value of type `{ty}` as {arg}.',
                    cls=cls, ty=ty, arg=arg)
    raise ValueError(f'Unexpected: {cn}')

def expectingDefaultValueOfTy(cn: location.CallableName, ty: str, paramName: str) -> str:
    match cn.kind:
        case 'function':
            return tr('Default value for parameter `{paramName}` of function `{fun}` must have type `{ty}`.',
                      paramName=paramName, fun=cn.name, ty=ty)
        case location.ClassMember('method', cls):
            return tr('Default value for parameter `{paramName}` of method `{method}` in class `{cls}` must have type `{ty}`.',
                      paramName=paramName, method=cn.name, cls=cls, ty=ty)
        case location.ClassMember('recordConstructor', cls):
            return tr('Default value for attribute `{paramName}` of record `{cls}` must have type `{ty}`.',
                      paramName=paramName, cls=cls, ty=ty)
    raise ValueError(f'Unexpected: {cn}')

def argCount(n: int) -> str:
    match getLang():
        case 'en':
            if n == 0:
                return 'no arguments'
            elif n == 1:
                return '1 argument'
            else:
                return f'{n} arguments'
        case 'de':
            if n == 0:
                return 'keine Argumente'
            elif n == 1:
                return '1 Argument'
            else:
                return f'{n} Argumente'

def argCountExact(cn: location.CallableName, expected: int) -> str:
    match cn.kind:
        case 'function':
            header = tr('Function `{fun}` takes ', fun=cn.name)
        case location.ClassMember('method', cls):
            header = tr('Method `{method}` of class `{cls}` takes ',
                      method=cn.name, cls=cls)
        case location.ClassMember('recordConstructor', cls):
            header = tr('Constructor of record `{cls}` takes ',
                        cls=cls)
        case _:
            raise ValueError(f'Unexpected: {cn}')
    return header + argCount(expected) + '.'

def argCountMin(cn: location.CallableName, expected: int) -> str:
    match cn.kind:
        case 'function':
            header = tr('Function `{fun}` takes at least ', fun=cn.name)
        case location.ClassMember('method', cls):
            header = tr('Method `{method}` of class `{cls}` takes at least ',
                      method=cn.name, cls=cls)
        case location.ClassMember('recordConstructor', cls):
            header = tr('Constructor of record `{cls}` takes at least ',
                        cls=cls)
        case _:
            raise ValueError(f'Unexpected: {cn}')
    return header + argCount(expected) + '.'

def argCountMax(cn: location.CallableName, expected: int) -> str:
    match cn.kind:
        case 'function':
            header = tr('Function `{fun}` takes at most ', fun=cn.name)
        case location.ClassMember('method', cls):
            header = tr('Method `{method}` of class `{cls}` takes at most ',
                      method=cn.name, cls=cls)
        case location.ClassMember('recordConstructor', cls):
            header = tr('Constructor of record `{cls}` takes at most ',
                        cls=cls)
        case _:
            raise ValueError(f'Unexpected: {cn}')
    return header + argCount(expected) + '.'

def realArgumentTy(ty: str) -> str:
    return tr('But the value given has type `{ty}`.', ty=ty)

def realDefaultValueTy(ty: str) -> str:
    return tr('But the default value has type `{ty}`.', ty=ty)

def realSetAttrTy(ty: str) -> str:
    return tr('Cannot set attribute to value of type `{ty}`.', ty=ty)

def expectingTypeAnnotation(cn: location.CallableName, param: str) -> str:
    match cn.kind:
        case 'function':
            return tr('Parameter `{param}` of function `{fun}` requires a type annotation.',
                        fun=cn.name, param=param)
        case location.ClassMember('method', cls):
            return tr('Parameter `{param}` of method `{method}` from class `{cls}` requires a type annotation.',
                        method=cn.name, cls=cls, param=param)
        case location.ClassMember('recordConstructor', cls):
            return tr('Parameter `{param}` of constructor of record `{cls}` requires a type annotation.',
                        cls=cls, param=param)
    raise ValueError(f'Unexpected: {cn}')

def noTypeAnnotationForAttribute(attrName: str, recordName: str) -> str:
    return tr('Attribute `{name}` of record `{record}` requires a type annotation.',
              name=attrName, record=recordName)

def invalidTy(ty: Any) -> str:
    return tr('invalid type `{ty}`', ty=ty)

def didYouMean(ty: str) -> str:
    return tr('Did you mean `{ty}`?', ty=ty)

def recordAttrDeclTy(recordName: str, attrName: str, ty: Any) -> str:
    return tr('Attribute `{attrName}` of record `{recordName}` declared with type `{ty}`.',
              recordName=recordName, attrName=attrName, ty=ty)

def unknownKeywordArgument(cn: location.CallableName, name: str) -> str:
    match cn.kind:
        case 'function':
            return tr('Function `{fun}` does not accept keyword argument `{name}`.',
                        fun=cn.name, name=name)
        case location.ClassMember('method', cls):
            return tr('Method `{method}` from class `{cls}` does not accept keyword argument `{name}`.',
                        method=cn.name, cls=cls, name=name)
        case location.ClassMember('recordConstructor', cls):
            return tr('Constructor of record `{cls}` does not accept keyword argument `{name}`.',
                        cls=cls, name=name)
    raise ValueError(f'Unexpected: {cn}')

def checkExpected(expected: str, actual: str) -> str:
    return tr('Expected {expected}, but the result is {actual}', expected=expected,actual=actual)

def numTests(n: int) -> str:
    match getLang():
        case 'en':
            if n == 0:
                return 'no tests'
            elif n == 1:
                return '1 test'
            else:
                return f'{n} tests'
        case 'de':
            if n == 0:
                return 'keine Tests'
            elif n == 1:
                return '1 Test'
            else:
                return f'{n} Tests'

def numFailing(n: int) -> str:
    match getLang():
        case 'en':
            if n == 0:
                return 'no errors'
            elif n == 1:
                return '1 error'
            else:
                return f'{n} errors'
        case 'de':
            if n == 0:
                return 'keine Fehler'
            elif n == 1:
                return '1 Fehler'
            else:
                return f'{n} Fehler'
