# SPDX-License-Identifier: GPL-3.0-or-later
from . import base, kind


@kind("manual")
def manual(ctx, rule):
    return [base(rule, "manual", message=rule.get("why", ""))]
