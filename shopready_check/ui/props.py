# SPDX-License-Identifier: GPL-3.0-or-later
import bpy
from bpy.props import (BoolProperty, CollectionProperty, EnumProperty, FloatProperty,
                       PointerProperty, StringProperty)

from ..edition import PREFIX
from . import state

PROP = PREFIX.lower()          # scene.<PROP>, so both editions can sit side by side
_ITEMS = []                     # Blender needs the enum item strings kept alive


def _profile_items(self, context):
    _ITEMS.clear()
    for i, p in enumerate(state.profiles()):
        label = p["name"] + (" (custom)" if p.get("custom") else "")
        desc = bpy.app.translations.pgettext_iface("Rules checked {date}").format(date=p["checked"])
        _ITEMS.append((p["id"], label, desc, i))
    return _ITEMS or [("none", "No profiles", "", 0)]


class ManualTick(bpy.types.PropertyGroup):
    rule_id: StringProperty()
    done: BoolProperty(name="Done", description="You checked this by eye")


class Settings(bpy.types.PropertyGroup):
    scope: EnumProperty(
        name="Product",
        items=[("SELECTED", "Selected objects", "The selected objects are the product"),
               ("COLLECTION", "Active collection", "Everything in the active collection is the product"),
               ("SCENE", "Whole scene", "Everything in the scene is the product")],
        default="SELECTED")
    profile: EnumProperty(name="Store", items=_profile_items,
                          description="Which store's rules to check against")
    real_w: FloatProperty(name="Width", description="Real width in cm, left to right (optional)",
                          min=0.0, soft_max=1000.0, precision=1)
    real_d: FloatProperty(name="Depth", description="Real depth in cm, front to back (optional)",
                          min=0.0, soft_max=1000.0, precision=1)
    real_h: FloatProperty(name="Height", description="Real height in cm (optional)",
                          min=0.0, soft_max=1000.0, precision=1)
    show_passed: BoolProperty(name="Show passed", default=False)
    manual: CollectionProperty(type=ManualTick)

    def real_cm(self):
        vals = (self.real_w, self.real_d, self.real_h)
        return vals if all(v > 0 for v in vals) else None

    def tick(self, rule_id, create=False):
        for t in self.manual:
            if t.rule_id == rule_id:
                return t
        if create:
            t = self.manual.add()
            t.rule_id = rule_id
            return t
        return None


ManualTick.__name__ = f"{PREFIX}_ManualTick"
Settings.__name__ = f"{PREFIX}_Settings"
CLASSES = (ManualTick, Settings)


def settings(context):
    return getattr(context.scene, PROP)


def register():
    for c in CLASSES:
        bpy.utils.register_class(c)
    setattr(bpy.types.Scene, PROP, PointerProperty(type=Settings))


def unregister():
    delattr(bpy.types.Scene, PROP)
    for c in reversed(CLASSES):
        bpy.utils.unregister_class(c)
