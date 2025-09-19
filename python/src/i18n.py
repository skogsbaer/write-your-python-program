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
    'Expecting no return value when calling method `{method}` of class `{cls}.':
        'Kein Rückgabewert erwartet bei Aufruf der Methode `{method}` aus Klasse `{cls}`.',
    'Expecting no return value when calling constructor of class `{cls}`.':
        'Kein Rückgabewert erwartet bei Aufruf des Konstruktors der Klasse `{cls}`.',

    'Expecting return value of type `{ty}` when calling function `{fun}`.':
        'Rückgabewert vom Typ `{ty}` erwartet bei Aufruf der Funktion `{fun}`.',
    'Expecting return value of type `{ty}` when calling method `{method}` of class `{cls}`.':
        'Rückgabewert vom Typ `{ty}` erwartet bei Aufruf von Methode `{method}` aus Klasse `{cls}`.',
    'Expecting return value of type `{ty}` when calling constructor of class `{cls}`.':
        'Rückgabewert vom Typ `{ty}` erwartet bei Aufruf des Konstruktors der Klasse `{cls}`.',

    'But the call returns a value of type `{ty}`.':
        'Aber der Aufruf gibt einen Wert vom Typ `{ty}` zurück.',

    'But no value returned.':
        'Aber kein Rückgabewert vorhanden.',
    'no result returned': 'kein Rückgabewert vorhanden',
    'Call in line {line} causes the function to return no value:':
        'Aufruf in Zeile {line} führt dazu, dass die Funktion keinen Wert zurückgibt:',

    'The call of function `{fun}` expects value of type `{ty}` as {arg}.':
        'Der Aufruf der Funktion `{fun}` erwartet Wert vom Typ `{ty}` als {arg}.',
    'The call of method `{method}` of class `{cls}` expects value of type `{ty}` as {arg}.':
        'Der Aufruf der Methode `{method}` aus Klasse `{cls}` erwartet Wert vom Typ `{ty}` als {arg}.',
    'The call of the constructor of class `{cls}` expects value of type `{ty}` as {arg}.':
        'Der Aufruf des Konstruktors der Klasse `{cls}` erwartet Wert vom Typ `{ty}` als {arg}.',

    'But the value given has type `{ty}`.': 'Aber der übergebene Wert hat Typ `{ty}`.',

    'File': 'Datei',
    'Result type declared in line': 'Rückgabetyp deklariert in Zeile',
    'Type declared in line': 'Typ deklariert in Zeile',
    'Parameter declared in line': 'Parameter deklariert in Zeile',
    'Problematic return in line': 'Fehlerhaftes return in Zeile',
    'Problematic call in line': 'Fehlerhafter Aufruf in Zeile',
    'Call in line {line} causes the problematic return:':
        'Aufruf in Zeile {line} verursacht das fehlerhafte return:',

    'Parameter `{param}` of function `{fun}` requires a type annotation.':
        'Parameter `{param}` der Funktion `{fun}` benötigt eine Typangabe.',
    'Parameter `{param}` of method `{method}` from class `{cls}` requires a type annotation.':
        'Parameter `{param}` der Methode `{method}` aus Klasse `{cls}` benötigt eine Typangabe.',
    'Parameter `{param}` of the constructor of class `{cls}` requires a type annotation.':
        'Parameter `{param}` des Konstruktors der Klasse `{cls}` benötigt eine Typangabe.',

    'Attribute `{name}` of record `{record}` required a type annotation.':
        'Attribut `{name}` des Records `{record}` benötigt eine Typannotation.'
}

def expectingNoReturn(cn: location.CallableName) -> str:
    match cn.kind:
        case 'function':
            return tr('Expecting no return value when calling function `{fun}`.',
                    fun=cn.name)
        case location.ClassMember('method', cls):
            return tr('Expecting no return value when calling method `{method}` of class `{cls}.',
                    method=cn.name, cls=cls)
        case location.ClassMember('constructor', cls):
            return tr('Expecting no return value when calling constructor of class `{cls}`.',
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
        case location.ClassMember('constructor', cls):
            return tr('Expecting return value of type `{ty}` when calling constructor of class `{cls}`.',
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


def expectingArgumentOfTy(cn: location.CallableName, ty: str, pos: int) -> str:
    arg = transArg(pos)
    match cn.kind:
        case 'function':
            return tr('The call of function `{fun}` expects value of type `{ty}` as {arg}.',
                    fun=cn.name, ty=ty, arg=arg)
        case location.ClassMember('method', cls):
            return tr('The call of method `{method}` of class `{cls}` expects value of type `{ty}` as {arg}.',
                    method=cn.name, cls=cls, ty=ty, arg=arg)
        case location.ClassMember('constructor', cls):
            return tr('The call of the constructor of class `{cls}` expects value of type `{ty}` as {arg}.',
                    cls=cls, ty=ty, arg=arg)
    raise ValueError(f'Unexpected: {cn}')

def realArgumentTy(ty: str) -> str:
    return tr('But the value given has type `{ty}`.', ty=ty)

def expectingTypeAnnotation(cn: location.CallableName, param: str) -> str:
    match cn.kind:
        case 'function':
            return tr('Parameter `{param}` of function `{fun}` requires a type annotation.',
                        fun=cn.name, param=param)
        case location.ClassMember('method', cls):
            return tr('Parameter `{param}` of method `{method}` from class `{cls}` requires a type annotation.',
                        method=cn.name, cls=cls, param=param)
        case location.ClassMember('constructor', cls):
            return tr('Parameter `{param}` of the constructor of class `{cls}` requires a type annotation.',
                        cls=cls, param=param)
    raise ValueError(f'Unexpected: {cn}')

def noTypeAnnotationForAttribute(attrName: str, recordName: str) -> str:
    return tr('Attribute `{name}` of record `{record}` required a type annotation.',
              name=attrName, record=recordName)
