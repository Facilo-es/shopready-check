# SPDX-License-Identifier: GPL-3.0-or-later
from . import base, kind


def _pow2(n):
    return n > 0 and (n & (n - 1)) == 0


def _mats_with(ctx, names):
    names = set(names)
    return [n for n, m in ctx.model.materials.items() if names & set(m.images)]


@kind("material_count")
def material_count(ctx, rule):
    n, mx = len(ctx.model.materials), rule.get("max", 1)
    ok = n <= mx
    return [base(rule, "pass" if ok else rule["severity"], "{n}", "max {max}",
                 "" if ok else "Bake to one material", args={"n": n, "max": mx},
                 select={"materials": list(ctx.model.materials)} if not ok else {}, fix="" if ok else "bake")]


@kind("texture_max")
def texture_max(ctx, rule):
    mx = rule["max_px"]
    imgs = ctx.model.images.values()
    big = [i for i in imgs if max(i.width, i.height) > mx]
    top = max((max(i.width, i.height) for i in imgs), default=0)
    tip = rule.get("tip_px")
    if big:
        return [base(rule, rule["severity"], "{top} px", "max {max} px", "{n} textures too large",
                     args={"top": top, "max": mx, "n": len(big)}, fix="textures",
                     select={"materials": _mats_with(ctx, [i.name for i in big])})]
    msg = "Tip: use {tip} px where you can" if tip and top > tip else ""
    return [base(rule, "pass", "{top} px", "max {max} px", msg, args={"top": top, "max": mx, "tip": tip})]


@kind("texture_range")
def texture_range(ctx, rule):
    lo, hi = rule.get("min_px", 1), rule.get("max_px", 1 << 16)
    bad = []
    for i in ctx.model.images.values():
        if (rule.get("square") and i.width != i.height) or \
                (rule.get("pow2") and not (_pow2(i.width) and _pow2(i.height))) or \
                min(i.width, i.height) < lo or max(i.width, i.height) > hi:
            bad.append(i)
    if not ctx.model.images:
        return [base(rule, "pass", "No textures", "{lo}–{hi} px", args={"lo": lo, "hi": hi})]
    if not bad:
        return [base(rule, "pass", "{n} textures", "{lo}–{hi} px", args={"n": len(ctx.model.images), "lo": lo, "hi": hi})]
    first = bad[0]
    return [base(rule, rule["severity"], "{w} × {h} px", "square, power of two, {lo}–{hi} px",
                 "{n} textures outside the range", fix="textures",
                 args={"w": first.width, "h": first.height, "lo": lo, "hi": hi, "n": len(bad)},
                 select={"materials": _mats_with(ctx, [i.name for i in bad])})]


@kind("texture_format")
def texture_format(ctx, rule):
    mode = rule.get("mode", "png_or_jpg")
    bad = []
    for i in ctx.model.images.values():
        if i.data_uri:
            bad.append(i)
        elif mode == "jpg_unless_alpha":
            if i.fmt != "JPEG" and not i.alpha and not i.normal:
                bad.append(i)
        elif i.fmt not in ("PNG", "JPEG"):
            bad.append(i)
    fmts = sorted({("JPG" if i.fmt == "JPEG" else i.fmt or "?") for i in ctx.model.images.values()})
    if not bad:
        return [base(rule, "pass", "{fmts}", "{lim}", args={"fmts": ", ".join(fmts) or "—",
                                                          "lim": "JPG, PNG with alpha" if mode == "jpg_unless_alpha" else "PNG, JPG"})]
    msg = "{n} textures could be JPG" if mode == "jpg_unless_alpha" else "{n} textures in another format"
    return [base(rule, rule["severity"], "{fmts}", "{lim}", msg, fix="jpg" if mode == "jpg_unless_alpha" else "textures",
                 args={"fmts": ", ".join(fmts), "n": len(bad),
                       "lim": "JPG, PNG with alpha" if mode == "jpg_unless_alpha" else "PNG, JPG"},
                 select={"materials": _mats_with(ctx, [i.name for i in bad])})]


@kind("pbr")
def pbr(ctx, rule):
    mats = ctx.model.materials
    out = []
    if not mats and ctx.model.meshes:
        return [base(rule, rule["severity"] if rule.get("require_principled") else "pass", "No material",
                     "Principled BSDF", "Add a material" if rule.get("require_principled") else "")]
    if rule.get("require_principled"):
        bad = [n for n, m in mats.items() if not m.principled]
        if bad:
            out.append(base(rule, rule["severity"], "{n} materials", "Principled BSDF",
                            "Not a Principled BSDF: {names}", args={"n": len(bad), "names": ", ".join(bad[:4])},
                            select={"materials": bad}, fix="bake"))
    if rule.get("flag_procedural"):
        proc = {n: m.procedural for n, m in mats.items() if m.procedural}
        if proc:
            nodes = sorted({x for v in proc.values() for x in v})
            out.append(base(rule, "warn" if rule["severity"] == "fail" and not rule.get("require_principled") else rule["severity"],
                            "{n} nodes", "image textures only", "Won't export: {nodes}",
                            args={"n": len(nodes), "nodes": ", ".join(nodes[:5])},
                            select={"materials": list(proc)}, fix="bake"))
    if out:
        return out
    return [base(rule, "pass", "{n} materials", "Principled BSDF", args={"n": len(mats)})]


@kind("orm_packed")
def orm_packed(ctx, rule):
    if ctx.model.source != "scene":
        return []
    bad = [n for n, m in ctx.model.materials.items() if len(m.orm_images) > 1]
    if not bad:
        return [base(rule, "pass", "Packed or not used", "1 image")]
    n = max(len(ctx.model.materials[b].orm_images) for b in bad)
    return [base(rule, rule["severity"], "{n} images", "1 image", "Occlusion, roughness and metalness are separate images",
                 args={"n": n}, select={"materials": bad}, fix="pack_orm")]


@kind("double_sided")
def double_sided(ctx, rule):
    bad = [n for n, m in ctx.model.materials.items() if m.double_sided]
    ok = not bad
    return [base(rule, "pass" if ok else rule["severity"], "{n} materials", "0",
                 "" if ok else "Turn on Backface Culling in the material settings", args={"n": len(bad)},
                 select={"materials": bad} if bad else {})]
