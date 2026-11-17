# SPDX-License-Identifier: GPL-3.0-or-later
"""Translations. English msgids live in the code and profiles; the other
languages live in JSON files next to this one, loaded in name order."""
import glob
import json
import os

LANGS = ("es", "de_DE", "fr_FR", "it_IT", "pt_PT", "pt_BR")
_HERE = os.path.dirname(__file__)
TABLE = {}          # msgid -> {lang: text}


def load():
    TABLE.clear()
    for path in sorted(glob.glob(os.path.join(_HERE, "*.json"))):
        with open(path, encoding="utf-8") as fh:
            TABLE.update(json.load(fh))
    return TABLE


def lang_of(locale):
    """Blender locale -> one of LANGS or 'en'."""
    if not locale or locale.startswith("en"):
        return "en"
    if locale in LANGS:
        return locale
    if locale.startswith("pt"):
        return "pt_PT"
    short = locale.split("_")[0]
    for code in LANGS:
        if code.split("_")[0] == short:
            return code
    return "en"


def tr(msgid, lang):
    if lang == "en" or not msgid:
        return msgid
    row = TABLE.get(msgid)
    if not row:
        return msgid
    return row.get(lang) or row.get(lang.split("_")[0]) or (lang == "pt_BR" and row.get("pt_PT")) or msgid


_SEP = {"es": ".", "de_DE": ".", "it_IT": ".", "pt_PT": " ", "pt_BR": ".", "fr_FR": " ", "en": ","}
_DEC = {"en": "."}


def num(v, lang):
    """Group thousands and pick the decimal mark for the language."""
    if isinstance(v, bool):
        return str(v)
    if isinstance(v, int):
        s = f"{v:,}"
        return s.replace(",", _SEP.get(lang, ","))
    if isinstance(v, float):
        s = f"{v:,.1f}" if abs(v) < 100 else f"{v:,.0f}"
        dec = _DEC.get(lang, ",")
        return s.replace(",", "\0").replace(".", dec).replace("\0", _SEP.get(lang, ","))
    return v


def fmt(template, args, lang):
    """Translate a template, then fill it. Args that are strings are translated too."""
    text = tr(template, lang)
    if not args:
        return text
    filled = {k: (tr(v, lang) if isinstance(v, str) else num(v, lang)) for k, v in args.items()}
    try:
        return text.format(**filled)
    except (KeyError, IndexError, ValueError):
        return tr(template, "en").format(**{k: num(v, "en") for k, v in args.items()})


def current_lang():
    import bpy
    prefs = bpy.context.preferences.view
    if hasattr(prefs, "use_translate_interface") and not prefs.use_translate_interface:
        return "en"
    return lang_of(prefs.language if prefs.language != "DEFAULT" else bpy.app.translations.locale)


def _blender_dict():
    out = {}
    for msgid, row in TABLE.items():
        if "pt_PT" in row:
            row = {"pt_BR": row["pt_PT"], **row}
        for lang, text in row.items():
            for ctx in ("*", "Operator"):
                out.setdefault(lang, {})[(ctx, msgid)] = text
    return out


def register():
    import bpy
    load()
    bpy.app.translations.register(__package__, _blender_dict())


def unregister():
    import bpy
    try:
        bpy.app.translations.unregister(__package__)
    except (ValueError, RuntimeError):
        pass
