# SPDX-License-Identifier: GPL-3.0-or-later
from . import base, kind
from .util import cm


def _objs(ctx):
    return {"objects": [m.name for m in ctx.model.meshes]} if ctx.model.source == "scene" else {}


@kind("transforms")
def transforms(ctx, rule):
    if ctx.model.source != "scene":
        return []
    bad = [m.name for m in ctx.model.meshes if m.rotated or m.scaled]
    ok = not bad
    return [base(rule, "pass" if ok else rule["severity"], "{n} objects", "0",
                 "" if ok else "Rotation or scale not applied", args={"n": len(bad)},
                 select={"objects": bad} if bad else {}, fix="" if ok else "transforms")]


@kind("origin")
def origin(ctx, rule):
    m = ctx.model
    if m.bmin is None:
        return []
    tol = rule.get("tolerance_m", 0.001)
    base_y = m.bmin[1]
    cx = (m.bmin[0] + m.bmax[0]) / 2
    cz = (m.bmin[2] + m.bmax[2]) / 2
    off = max(abs(cx), abs(cz))
    if abs(base_y) > tol:
        msg = "Base {d} cm above the floor" if base_y > 0 else "Base {d} cm below the floor"
        return [base(rule, rule["severity"], msg, "{tol} mm", "Move the base to the world origin",
                     args={"d": cm(abs(base_y)), "tol": f"{tol * 1000:g}"}, fix="origin", select=_objs(ctx))]
    if off > tol:
        return [base(rule, rule["severity"], "Centre {d} cm off", "{tol} mm", "Centre the base on the world origin",
                     args={"d": cm(off), "tol": f"{tol * 1000:g}"}, fix="origin", select=_objs(ctx))]
    return [base(rule, "pass", "On the floor, centred", "{tol} mm", args={"tol": f"{tol * 1000:g}"})]


@kind("real_size")
def real_size(ctx, rule):
    dims = ctx.model.dims
    if dims is None:
        return []
    w, d, h = dims
    size = {"w": cm(w), "d": cm(d), "h": cm(h)}
    if ctx.real_cm and any(ctx.real_cm):
        tol = rule.get("tolerance", 0.02)
        rw, rd, rh = ctx.real_cm
        pairs = [(a * 100, b) for a, b in ((w, rw), (d, rd), (h, rh)) if b > 0]
        ratios = [a / b for a, b in pairs]
        lim = {"rw": f"{rw:g}", "rd": f"{rd:g}", "rh": f"{rh:g}"}
        if all(abs(r - 1) <= tol for r in ratios):
            return [base(rule, "pass", "{w} × {d} × {h} cm", "{rw} × {rd} × {rh} cm", args={**size, **lim})]
        if max(ratios) / min(ratios) <= 1 + tol:
            r = sum(ratios) / len(ratios)
            msg = "{r}× its real size" if r > 1 else "{r}× smaller than its real size"
            rr = r if r > 1 else 1 / r
            return [base(rule, rule["severity"], "{w} × {d} × {h} cm", "{rw} × {rd} × {rh} cm", msg,
                         args={**size, **lim, "r": f"{rr:.3g}"}, fix="real_size", select=_objs(ctx))]
        return [base(rule, rule["severity"], "{w} × {d} × {h} cm", "{rw} × {rd} × {rh} cm",
                     "The proportions don't match the real size", args={**size, **lim}, fix="real_size", select=_objs(ctx))]
    big = max(dims)
    lo, hi = rule.get("sanity_min_m", 0.01), rule.get("sanity_max_m", 10.0)
    if big < lo or big > hi:
        return [base(rule, "warn", "{w} × {d} × {h} cm", "1 cm – 10 m",
                     "Size looks wrong. Enter the real size to check scale", args=size)]
    return [base(rule, "info", "{w} × {d} × {h} cm", "", "Enter the real size to check scale", args=size)]


@kind("no_extras")
def no_extras(ctx, rule):
    m = ctx.model
    found = {
        "modifiers": [x.name for x in m.meshes if x.modifiers],
        "animation": list(m.animated),
        "cameras": list(m.cameras),
        "lights": list(m.lights),
    }
    names = {"modifiers": "No modifiers", "animation": "No animation", "cameras": "No cameras", "lights": "No lights"}
    fixes = {"modifiers": "modifiers", "animation": "extras", "cameras": "extras", "lights": "extras"}
    out = []
    for item in rule.get("items", list(found)):
        bad = found[item]
        r = base(rule, "pass" if not bad else rule["severity"], "{n}", "0",
                 "" if not bad else "Found: {names}", args={"n": len(bad), "names": ", ".join(bad[:4])},
                 select={"objects": bad} if bad else {}, fix=fixes[item] if bad else "")
        r.rule_id = f"{rule['id']}:{item}"
        r.name = names[item]
        out.append(r)
    return out
