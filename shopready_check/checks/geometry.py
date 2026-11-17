# SPDX-License-Identifier: GPL-3.0-or-later
from . import base, kind
from .util import faces_payload


def _scene(ctx):
    return ctx.model.source == "scene"


@kind("mesh_count")
def mesh_count(ctx, rule):
    n, mx = len(ctx.model.meshes), rule.get("max", 1)
    ok = n <= mx
    return [base(rule, "pass" if ok else rule["severity"], "{n}", "max {max}",
                 "" if ok else "Join the meshes into one object", args={"n": n, "max": mx},
                 select={} if ok else {"objects": [m.name for m in ctx.model.meshes]},
                 fix="" if ok else "join")]


@kind("triangles")
def triangles(ctx, rule):
    n, mx = ctx.model.tris, rule["max"]
    ok = n <= mx
    return [base(rule, "pass" if ok else rule["severity"], "{n}", "max {max}",
                 "" if ok else "Reduce to {max} or fewer. Optional decimation is off by default, because it can damage shape",
                 args={"n": n, "max": mx}, fix="" if ok else "decimate")]


def _face_rule(ctx, rule, attr, msg, fix):
    if not _scene(ctx):
        return []
    pairs = [(m.name, getattr(m, attr)) for m in ctx.model.meshes]
    n = sum(len(i) for _, i in pairs)
    ok = n == 0
    return [base(rule, "pass" if ok else rule["severity"], "{n} faces", "0",
                 "" if ok else msg, args={"n": n}, select=faces_payload(pairs), fix="" if ok else fix)]


@kind("ngons")
def ngons(ctx, rule):
    return _face_rule(ctx, rule, "ngons", "Faces with 5 or more sides", "triangulate")


@kind("degenerate")
def degenerate(ctx, rule):
    return _face_rule(ctx, rule, "degenerate", "Faces with no area", "clean")


@kind("uv_range")
def uv_range(ctx, rule):
    return _face_rule(ctx, rule, "uv_out", "Faces with UVs outside the 0–1 square", "bake")


@kind("nonmanifold")
def nonmanifold(ctx, rule):
    if not _scene(ctx):
        return []
    n = sum(m.nonmanifold_edges for m in ctx.model.meshes)
    ok = n == 0
    return [base(rule, "pass" if ok else rule["severity"], "{n} edges", "0",
                 "" if ok else "Open or tangled edges: close holes and merge loose points", args={"n": n},
                 select=faces_payload([(m.name, m.nonmanifold_faces) for m in ctx.model.meshes]))]


@kind("normals")
def normals(ctx, rule):
    if not _scene(ctx):
        return []
    bad = [m.name for m in ctx.model.meshes if m.inconsistent_edges or m.flipped]
    ok = not bad
    return [base(rule, "pass" if ok else rule["severity"], "{n} objects", "0",
                 "" if ok else "Some faces point inward", args={"n": len(bad)},
                 select={"objects": bad} if bad else {}, fix="" if ok else "clean")]


@kind("uv_sets")
def uv_sets(ctx, rule):
    if not _scene(ctx):
        return []
    want = rule.get("count", 1)
    bad = [m.name for m in ctx.model.meshes if m.uv_layers != want]
    worst = max((m.uv_layers for m in ctx.model.meshes), key=lambda v: abs(v - want), default=want)
    ok = not bad
    return [base(rule, "pass" if ok else rule["severity"], "{n}", "{want}",
                 "" if ok else ("No UV map: unwrap the model" if worst == 0 else "More than one UV map"),
                 args={"n": worst, "want": want}, select={"objects": bad} if bad else {},
                 fix="" if ok else "bake")]


@kind("uv_overlap")
def uv_overlap(ctx, rule):
    if not _scene(ctx):
        return []
    grid = rule.get("grid", 256)
    cells = sum(m.uv_overlap_cells for m in ctx.model.meshes)
    pct = 100.0 * cells / (grid * grid)
    ok = cells == 0
    return [base(rule, "pass" if ok else rule["severity"], "{pct}% of texture", "0%",
                 "" if ok else "Faces share the same texture space", args={"pct": f"{pct:.1f}"},
                 select=faces_payload([(m.name, m.uv_overlap_faces) for m in ctx.model.meshes]),
                 fix="" if ok else "bake")]
