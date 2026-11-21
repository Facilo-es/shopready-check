# SPDX-License-Identifier: GPL-3.0-or-later
import textwrap

import bpy

from .. import i18n
from ..edition import PREFIX
from . import state
from .ops import OP
from .props import settings

ICON = {"fail": "CANCEL", "warn": "ERROR", "pass": "CHECKMARK", "info": "INFO", "manual": "CHECKBOX_DEHLT"}
LONG_VALUE = 18     # characters that still fit beside the rule name in a default-width sidebar
CHAR_PX = 7         # rough width of one UI character at scale 1, for wrapping long lines


def columns(context, indent=0):
    """How many characters fit on one line of this sidebar, so long text wraps instead of being cut."""
    scale = context.preferences.view.ui_scale or 1.0
    return max(20, int(context.region.width / (CHAR_PX * scale)) - indent)


def wrapped(lay, text, cols, prefix="", **kw):
    for n, part in enumerate(textwrap.wrap(text, cols) or [""]):
        lay.label(text=prefix + part, translate=False, **(kw if n == 0 else {"icon": "BLANK1"} if "icon" in kw else {}))


WORD = {"fail": "Fail", "warn": "Warn", "manual": "Manual", "pass": "Pass", "info": "Info"}
COUNT = {"fail": "{n} fail", "warn": "{n} warn", "manual": "{n} manual",
         "pass": "{n} pass"}


class _Base:
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_category = "ShopReady"


class Target(_Base, bpy.types.Panel):
    bl_idname = "SHOPREADYCHECK_PT_target"
    bl_label = "Target"
    bl_order = 0

    def draw(self, context):
        s = settings(context)
        lay = self.layout
        lay.use_property_split = True
        lay.use_property_decorate = False
        lay.prop(s, "scope")
        row = lay.row(align=True)
        row.prop(s, "profile")
        row.operator("shopreadycheck.reload_profiles", text="", icon="FILE_REFRESH")
        prof = state.profile(s.profile)
        lang = i18n.current_lang()
        if prof:
            sub = lay.row()
            sub.alignment = "RIGHT"
            sub.label(text=i18n.fmt("Rules checked {date}", {"date": prof["checked"]}, lang), translate=False)
        for err in state.errors():
            lay.label(text=err, icon="ERROR", translate=False)
        lay.label(text=i18n.tr("Real size (cm)", lang), translate=False)
        col = lay.column(align=True)
        col.prop(s, "real_w")
        col.prop(s, "real_d")
        col.prop(s, "real_h")
        if not s.real_cm():
            col.label(text="Optional. Needed to check scale")
        lay.use_property_split = False
        big = lay.row()
        big.scale_y = 1.6
        big.operator("shopreadycheck.check", icon="VIEWZOOM")


def summary_line(results, lang):
    counts = {k: 0 for k in COUNT}
    counts["info"] = 0
    for r in results:
        key = r.status
        counts[key] += 1
    parts = [i18n.fmt(COUNT[k], {"n": counts[k]}, lang) for k in COUNT if counts[k]]
    return " · ".join(parts)


def verdict_line(entry, lang):
    store = entry["profile"]["name"]
    nfail = sum(1 for r in entry["results"] if r.status == "fail")
    if entry["verdict"] == "FAIL":
        if nfail == 1:
            return i18n.fmt("1 thing to fix before {store} accepts this model", {"store": store}, lang)
        return i18n.fmt("{n} things to fix before {store} accepts this model", {"n": nfail, "store": store}, lang)
    if entry["verdict"] == "WARN":
        return i18n.fmt("Ready for {store}, with warnings", {"store": store}, lang)
    return i18n.fmt("Ready for {store}", {"store": store}, lang)


def draw_row(lay, r, i, s, lang, cols=200):
    box = lay.column(align=True)
    row = box.row(align=True)
    if r.status == "manual":
        t = s.tick(r.rule_id)
        if t is not None:
            row.prop(t, "done", text=i18n.tr(r.name, lang), translate=False)
        else:
            row.label(text=i18n.tr(r.name, lang), icon=ICON["manual"], translate=False)
    else:
        status = r.status
        icon = ICON[status]
        val = i18n.fmt(r.measured, r.args, lang)
        if r.limit:
            val += " / " + i18n.fmt(r.limit, r.args, lang)
        if len(val) > LONG_VALUE:
            # long values (sizes in three axes) get their own line instead of being cut off
            row.label(text=i18n.tr(r.name, lang), icon=icon, translate=False)
        else:
            # a split keeps the name visible when the sidebar is narrow
            split = row.split(factor=0.5, align=True)
            split.label(text=i18n.tr(r.name, lang), icon=icon, translate=False)
            right = split.row(align=True)
            right.alignment = "RIGHT"
            right.label(text=val, translate=False)
            val = None
    if r.select:
        row.operator("shopreadycheck.select", text="", icon="RESTRICT_SELECT_OFF").index = i
    if r.source:
        row.operator("shopreadycheck.source", text="", icon="INFO").index = i
    if r.status != "manual" and val:
        line = box.column()
        line.scale_y = 0.7
        wrapped(line, val, cols, "    ")
    note = i18n.fmt(r.message, r.args, lang) if r.message else ""
    if note:
        msg = box.column()
        msg.scale_y = 0.7
        wrapped(msg, note, cols, "    ")


class Results(_Base, bpy.types.Panel):
    bl_idname = "SHOPREADYCHECK_PT_results"
    bl_label = "Results"
    bl_order = 1

    def draw_header(self, context):
        entry = state.STORE.get(context.scene.name)
        if entry:
            self.layout.label(text=summary_line(entry["results"], i18n.current_lang()), translate=False)

    def draw(self, context):
        lay = self.layout
        s = settings(context)
        lang = i18n.current_lang()
        entry = state.STORE.get(context.scene.name)
        if not entry:
            lay.label(text="Press Check model to see what the store will say")
            return
        cols = columns(context, 6)
        stamp = lay.box().column()
        stamp.scale_y = 1.3 if len(verdict_line(entry, lang)) <= cols else 1.0
        icon = {"PASS": "CHECKMARK", "WARN": "ERROR", "FAIL": "CANCEL"}[entry["verdict"]]
        wrapped(stamp, verdict_line(entry, lang), cols, icon=icon)
        results = entry["results"]
        passed = [i for i, r in enumerate(results) if r.status in ("pass", "info")]
        for i, r in enumerate(results):
            if r.status in ("pass", "info") and not s.show_passed:
                continue
            draw_row(lay, r, i, s, lang, cols)
        if passed:
            lay.prop(s, "show_passed", text=i18n.fmt("Show passed ({n})", {"n": len(passed)}, lang),
                     translate=False, icon="TRIA_DOWN" if s.show_passed else "TRIA_RIGHT", emboss=False)


CLASSES = (Target, Results)


def register():
    for c in CLASSES:
        bpy.utils.register_class(c)


def unregister():
    for c in reversed(CLASSES):
        bpy.utils.unregister_class(c)
