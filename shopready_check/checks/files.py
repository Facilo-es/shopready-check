# SPDX-License-Identifier: GPL-3.0-or-later
from . import base, kind
from .util import mb


@kind("format")
def fmt(ctx, rule):
    f = ctx.model.fmt
    ok = f in rule.get("formats", [])
    return [base(rule, "pass" if ok else rule["severity"], measured="{fmt}", limit="{formats}",
                 message="" if ok else "{fmt} is not accepted",
                 args={"fmt": f.upper(), "formats": " / ".join(x.upper() for x in rule.get("formats", []))})]


@kind("file_size")
def file_size(ctx, rule):
    m = ctx.model
    real = m.file_bytes is not None
    n = m.file_bytes if real else (m.est_bytes or 0)
    measured = "{size}" if real else "about {size}"
    fix = "" if real else "textures"

    def res(status, limit_t, lim, msg=""):
        return [base(rule, status, measured, limit_t, msg, args={"size": mb(n), "lim": mb(lim)},
                     fix=fix if status != "pass" else "")]
    if "max_bytes" in rule:
        ok = n <= rule["max_bytes"]
        return res("pass" if ok else rule["severity"], "max {lim}", rule["max_bytes"],
                   "" if ok else "Larger than advised")
    p, w, f = rule["pass_max_bytes"], rule["warn_max_bytes"], rule["fail_max_bytes"]
    if n <= p:
        return res("pass", "target {lim}", p)
    if n <= w:
        return res("warn", "target {lim}", p, "Over the target; loads slower")
    if n <= f:
        return res(rule["severity"], "max {lim}", w,
                   "The store will optimize it automatically, which can change how it looks")
    return res(rule["severity"], "max {lim}", f, "Upload refused")


@kind("draco")
def draco(ctx, rule):
    on = ctx.model.draco if ctx.model.draco is not None else ctx.profile.get("draco", False)
    return [base(rule, "pass" if on else rule["severity"], "On" if on else "Off", "On",
                 "" if on else "Turn on Draco compression in the export")]


@kind("extensions")
def extensions(ctx, rule):
    allowed = set(rule.get("allowed", []))
    bad = [e for e in ctx.model.extensions if e not in allowed]
    if not bad:
        return [base(rule, "pass", "{n}", "allowed list", args={"n": len(ctx.model.extensions)})]
    sel = [n for n, mt in ctx.model.materials.items() if set(mt.extensions) & set(bad)]
    return [base(rule, rule["severity"], "{ext}", "allowed list",
                 "Not allowed: {ext}. Reset those material settings to default.", args={"ext": ", ".join(bad)},
                 select={"materials": sel} if sel else {})]
