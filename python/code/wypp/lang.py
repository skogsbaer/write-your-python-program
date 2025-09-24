import os
import locale
from _collections_abc import MutableMapping

def _langFromEnv(env: MutableMapping) -> str | None:
    # 1) GNU LANGUAGE: colon-separated fallbacks (e.g., "de:en_US:en")
    lng = env.get("LANGUAGE")
    if lng:
        for part in lng.split(":"):
            part = part.strip()
            if part:
                return part

    # 2) POSIX locale vars in order of precedence
    for var in ("LC_ALL", "LC_MESSAGES", "LANG"):
        val = env.get(var)
        if val and val not in ("C", "POSIX"):
            return val

    # 3) locale module fallback (works cross-platform-ish)
    try:
        locale.setlocale(locale.LC_CTYPE, "")  # load user default
    except locale.Error:
        pass
    lang, _enc = locale.getlocale()  # e.g. "de_DE"
    return lang

def _normLang(tag: str) -> str:
    # "de-DE.UTF-8" -> "de_DE"
    tag = tag.replace("-", "_")
    if "." in tag:
        tag = tag.split(".", 1)[0]
    return tag

def pickLanguage[T: str](supported: list[T], default: T) -> T:
    """Return best match like 'de' or 'de_DE' from supported codes."""
    (raw, _) = locale.getlocale()
    if not raw:
        raw = _langFromEnv(os.environ)
        if not raw:
            return default
    want = _normLang(raw)
    # exact match first
    for s in supported:
        if _normLang(s).lower() == want.lower():
            return s
    # fallback to language-only match (de_DE -> de)
    wantBase = want.split("_")[0].lower()
    for s in supported:
        if _normLang(s).split('_')[0].lower() == wantBase:
            return s
    return default
