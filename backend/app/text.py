"""Umlaut- and accent tolerant text normalisation used for search."""

import re
import unicodedata

_UMLAUT_MAP = {
    "ä": "ae", "ö": "oe", "ü": "ue", "ß": "ss",
    "Ä": "ae", "Ö": "oe", "Ü": "ue",
    "æ": "ae", "ø": "oe", "å": "aa",
}


def normalize(text: str | None) -> str:
    """`Mäusebussard` -> `maeusebussard`, also matches `mausebussard`."""
    if not text:
        return ""
    out = "".join(_UMLAUT_MAP.get(ch, ch) for ch in text)
    out = unicodedata.normalize("NFKD", out)
    out = "".join(ch for ch in out if not unicodedata.combining(ch))
    return out.lower().strip()


def slugify(text: str) -> str:
    base = normalize(text)
    base = re.sub(r"[^a-z0-9]+", "-", base).strip("-")
    return base or "art"


def search_variants(text: str | None) -> str:
    """Both the ae-expanded and the accent-stripped form, so `mausebussard`,
    `maeusebussard` and `mäusebussard` all hit the same row."""
    if not text:
        return ""
    expanded = normalize(text)
    stripped = "".join(
        ch
        for ch in unicodedata.normalize("NFKD", (text or "").replace("ß", "ss"))
        if not unicodedata.combining(ch)
    ).lower()
    return expanded if expanded == stripped else f"{expanded} {stripped}"
