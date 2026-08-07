"""
Google Fonts registered for the PDF generators.

Each family has Regular/Bold/Italic/BoldItalic static TTF instances stored in
the ``fonts/`` directory. Families are exposed in a fixed order so the UI can
show the same options everywhere.
"""
import os

from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont

FONT_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "fonts")

# Order matters: this is the order shown to the user.
FONT_OPTIONS = [
    {"key": "Montserrat", "label": "Montserrat"},
    {"key": "Poppins", "label": "Poppins"},
    {"key": "Lato", "label": "Lato"},
    {"key": "OpenSans", "label": "Open Sans"},
    {"key": "Nunito", "label": "Nunito"},
    {"key": "Roboto", "label": "Roboto"},
    {"key": "Inter", "label": "Inter"},
    {"key": "Quicksand", "label": "Quicksand"},
    {"key": "PlayfairDisplay", "label": "Playfair Display"},
    {"key": "CormorantGaramond", "label": "Cormorant Garamond"},
]

_STYLE_SUFFIX = {
    "regular": "Regular",
    "bold": "Bold",
    "italic": "Italic",
    "bolditalic": "BoldItalic",
}

_registered = {}


def _register():
    for fam in FONT_OPTIONS:
        variants = {}
        for style, suffix in _STYLE_SUFFIX.items():
            path = os.path.join(FONT_DIR, f"{fam['key']}-{suffix}.ttf")
            if os.path.exists(path):
                rl_name = f"AGF-{fam['key']}-{style}"
                pdfmetrics.registerFont(TTFont(rl_name, path))
                variants[style] = rl_name
        if variants:
            _registered[fam["key"]] = variants


_register()


def resolve_font(family, bold=False, italic=False):
    """Map a family name + style to a registered reportlab font name.

    Returns None when the family is unknown or missing files, so callers can
    fall back to their default font.
    """
    fam = (family or "").strip()
    if not fam:
        return None
    key = fam.replace(" ", "").replace("_", "-")
    variants = _registered.get(fam) or _registered.get(key)
    if not variants:
        return None
    if bold and italic and variants.get("bolditalic"):
        return variants["bolditalic"]
    if bold and variants.get("bold"):
        return variants["bold"]
    if italic and variants.get("italic"):
        return variants["italic"]
    return variants.get("regular")
