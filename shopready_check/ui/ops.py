# SPDX-License-Identifier: GPL-3.0-or-later
import time

import bpy
from bpy.props import IntProperty

from ..checks import run_profile, verdict
from ..core.gather import gather, scope_objects
from ..edition import PREFIX
from .. import i18n
from . import state
from .props import settings

OP = PREFIX.lower()


def run_check(context):
    """Check the product in scope. Returns the stored entry or raises ValueError."""
    s = settings(context)
    prof = state.profile(s.profile)
    if prof is None:
        raise ValueError("No store profile could be loaded")
    objs = scope_objects(context, s.scope)
    if not any(o.type == "MESH" for o in objs):
        raise ValueError("Nothing to check. Select the product first")
    t0 = time.perf_counter()
    model = gather(objs, context.evaluated_depsgraph_get(), state.grid_of(prof))
    results = run_profile(model, prof, s.real_cm(), state.QUEUED.get(context.scene.name, ()))
    for r in results:
        if r.status == "manual":
            s.tick(r.rule_id, create=True)
    entry = {"profile": prof, "results": results, "verdict": verdict([r for r in results if not r.fixed]),
             "model": model,
             "objects": [o.name for o in objs], "seconds": time.perf_counter() - t0}
    state.STORE[context.scene.name] = entry
    return entry


class Check(bpy.types.Operator):
    bl_idname = f"{OP}.check"
    bl_label = "Check model"
    bl_description = "Check the product against the store's rules. Your scene is not changed"
    bl_options = {"REGISTER"}

    def execute(self, context):
        try:
            run_check(context)
        except ValueError as e:
            self.report({"WARNING"}, bpy.app.translations.pgettext_iface(str(e)))
            return {"CANCELLED"}
        for area in context.screen.areas if context.screen else ():
            area.tag_redraw()
        return {"FINISHED"}


def _result(context, index):
    entry = state.STORE.get(context.scene.name)
    if not entry or not 0 <= index < len(entry["results"]):
        return None
    return entry["results"][index]


def _frame(context):
    for area in context.screen.areas if context.screen else ():
        if area.type == "VIEW_3D":
            region = next((r for r in area.regions if r.type == "WINDOW"), None)
            if region:
                with context.temp_override(area=area, region=region):
                    bpy.ops.view3d.view_selected()
            return


class Select(bpy.types.Operator):
    bl_idname = f"{OP}.select"
    bl_label = "Select"
    bl_description = "Select what this line is about and frame it in the view"
    bl_options = {"REGISTER", "UNDO"}
    index: IntProperty(options={"HIDDEN"})

    def execute(self, context):
        r = _result(context, self.index)
        if r is None or not r.select:
            return {"CANCELLED"}
        if context.object and context.object.mode != "OBJECT":
            bpy.ops.object.mode_set(mode="OBJECT")
        for ob in context.view_layer.objects:
            ob.select_set(False)
        names = list(r.select.get("objects", []))
        faces = r.select.get("faces", {})
        mats = set(r.select.get("materials", []))
        names += list(faces)
        if mats:
            for ob in context.view_layer.objects:
                if any(sl.material and sl.material.name in mats for sl in getattr(ob, "material_slots", [])):
                    names.append(ob.name)
        obs = [context.view_layer.objects.get(n) for n in names]
        obs = [o for o in obs if o is not None]
        if not obs:
            self.report({"WARNING"}, bpy.app.translations.pgettext_iface("Not found in this scene any more"))
            return {"CANCELLED"}
        for o in obs:
            o.select_set(True)
        context.view_layer.objects.active = obs[0]
        if faces:
            context.tool_settings.mesh_select_mode = (False, False, True)
            for o in obs:
                idx = set(faces.get(o.name, ()))
                if o.type == "MESH":
                    for p in o.data.polygons:
                        p.select = p.index in idx
                    keys = {k for p in o.data.polygons if p.select for k in p.edge_keys}
                    for e in o.data.edges:
                        e.select = e.key in keys
                    verts = {v for k in keys for v in k}
                    for v in o.data.vertices:
                        v.select = v.index in verts
            bpy.ops.object.mode_set(mode="EDIT")
        if mats and obs[0].type == "MESH":
            for i, sl in enumerate(obs[0].material_slots):
                if sl.material and sl.material.name in mats:
                    obs[0].active_material_index = i
                    break
        _frame(context)
        return {"FINISHED"}


class Source(bpy.types.Operator):
    bl_idname = f"{OP}.source"
    bl_label = "Rule source"
    bl_options = {"INTERNAL"}
    index: IntProperty(options={"HIDDEN"})

    @classmethod
    def description(cls, context, props):
        r = _result(context, props.index)
        if r is None:
            return ""
        lang = i18n.current_lang()
        return i18n.tr(r.why, lang) + "\n" + i18n.tr("Opens the store's own page for this rule", lang)

    def execute(self, context):
        r = _result(context, self.index)
        if r is None or not r.source:
            return {"CANCELLED"}
        bpy.ops.wm.url_open(url=r.source)
        return {"FINISHED"}


class Reload(bpy.types.Operator):
    bl_idname = f"{OP}.reload_profiles"
    bl_label = "Reload profiles"
    bl_description = "Read the store profiles again from disk"
    bl_options = {"INTERNAL"}

    def execute(self, context):
        state.profiles(reload=True)
        for e in state.errors():
            self.report({"WARNING"}, e)
        return {"FINISHED"}


for _c, _n in ((Check, "check"), (Select, "select"), (Source, "source"), (Reload, "reload")):
    _c.__name__ = f"{PREFIX}_OT_{_n}"
CLASSES = (Check, Select, Source, Reload)


def register():
    for c in CLASSES:
        bpy.utils.register_class(c)


def unregister():
    for c in reversed(CLASSES):
        bpy.utils.unregister_class(c)
