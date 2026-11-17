# SPDX-License-Identifier: GPL-3.0-or-later
"""Check 3D product models against store rules before you send them."""
from . import i18n
from .ui import ops, panels, props

_MODULES = [i18n, props, ops, panels]
try:
    from .ui import more
    _MODULES.append(more)
except ImportError:
    pass


def register():
    for m in _MODULES:
        m.register()


def unregister():
    for m in reversed(_MODULES):
        m.unregister()
