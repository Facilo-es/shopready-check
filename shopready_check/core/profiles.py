# SPDX-License-Identifier: GPL-3.0-or-later
"""Load store profiles from JSON. Limits live in the files, not in code."""
import json
import os

BUILTIN_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "profiles")
SEVERITIES = {"fail", "warn", "manual"}


class ProfileError(ValueError):
    pass


def validate(data, known_kinds):
    for key in ("id", "name", "checked", "rules"):
        if key not in data:
            raise ProfileError(f"Profile is missing '{key}'")
    seen = set()
    for rule in data["rules"]:
        rid = rule.get("id", "?")
        if rule.get("kind") not in known_kinds:
            raise ProfileError(f"Profile '{data['id']}': rule {rid} has unknown kind '{rule.get('kind')}'")
        if rule.get("severity") not in SEVERITIES:
            raise ProfileError(f"Profile '{data['id']}': rule {rid} has unknown severity '{rule.get('severity')}'")
        if rid in seen:
            raise ProfileError(f"Profile '{data['id']}': rule {rid} appears twice")
        seen.add(rid)
    return data


def custom_dir():
    """Folder for the user's own profiles, or None when unavailable."""
    try:
        import bpy
        from .. import __package__ as pkg
        return bpy.utils.extension_path_user(pkg, path="profiles", create=True)
    except Exception:
        return os.environ.get("SHOPREADY_PROFILE_DIR")


def load_file(path, known_kinds, custom=False):
    with open(path, encoding="utf-8") as fh:
        data = json.load(fh)
    validate(data, known_kinds)
    data["custom"] = custom
    data["path"] = path
    return data


def load_all(known_kinds):
    """Return (profiles in display order, errors)."""
    out, errors = [], []
    folders = [(BUILTIN_DIR, False)]
    cdir = custom_dir()
    if cdir and os.path.isdir(cdir):
        folders.append((cdir, True))
    order = {"shopify": 0, "amazon": 1, "web": 2}
    for folder, custom in folders:
        for name in sorted(os.listdir(folder)):
            if not name.endswith(".json"):
                continue
            try:
                out.append(load_file(os.path.join(folder, name), known_kinds, custom))
            except (ProfileError, ValueError, OSError) as exc:
                errors.append(f"{name}: {exc}")
    out.sort(key=lambda p: (p["custom"], order.get(p["id"], 9), p["name"]))
    return out, errors
