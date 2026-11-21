# SPDX-License-Identifier: GPL-3.0-or-later
"""Rule checks. Each kind maps to one function run(ctx, rule) -> list[Result]."""
from dataclasses import dataclass

from ..core.result import ORDER, Result

KINDS = {}


def kind(name):
    def deco(fn):
        KINDS[name] = fn
        return fn
    return deco


@dataclass
class Ctx:
    model: object
    profile: dict
    real_cm: tuple = None        # (width, depth, height) or None


def base(rule, status, measured="", limit="", message="", **kw):
    return Result(rule_id=rule["id"], status=status, name=rule.get("name", rule["id"]),
                  measured=measured, limit=limit, message=message,
                  why=rule.get("why", ""), source=rule.get("source", ""), **kw)


def run_profile(model, profile, real_cm=None):
    ctx = Ctx(model=model, profile=profile, real_cm=real_cm)
    out = []
    for rule in profile["rules"]:
        out.extend(KINDS[rule["kind"]](ctx, rule))
    out.sort(key=lambda r: ORDER[r.status])
    return out


def verdict(results):
    """PASS, WARN (pass with warnings) or FAIL."""
    st = {r.status for r in results}
    if "fail" in st:
        return "FAIL"
    if "warn" in st:
        return "WARN"
    return "PASS"


from . import files, geometry, materials, placement, manual  # noqa: E402,F401
