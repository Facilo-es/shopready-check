# SPDX-License-Identifier: GPL-3.0-or-later
"""Last check per scene, kept in memory (results are cheap to rebuild)."""
from ..checks import KINDS
from ..core import profiles as _profiles

STORE = {}            # scene name -> dict(profile, results, verdict, model)
QUEUED = {}           # scene name -> fix kinds queued on the export copy (empty when fixes are not installed)
_CACHE = {"profiles": None, "errors": []}

# Optional modules add draw hooks here: fn(layout, result, index)
ROW_EXTRAS = []


def profiles(reload=False):
    if reload or _CACHE["profiles"] is None:
        _CACHE["profiles"], _CACHE["errors"] = _profiles.load_all(KINDS)
    return _CACHE["profiles"]


def errors():
    return _CACHE["errors"]


def profile(pid):
    for p in profiles():
        if p["id"] == pid:
            return p
    return profiles()[0] if profiles() else None


def grid_of(profile):
    for rule in profile["rules"]:
        if rule["kind"] == "uv_overlap":
            return int(rule.get("grid", 256))
    return 256
