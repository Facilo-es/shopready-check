# SPDX-License-Identifier: GPL-3.0-or-later
"""One line in the results list."""
from dataclasses import dataclass, field

ORDER = {"fail": 0, "warn": 1, "manual": 2, "pass": 3, "info": 4}


@dataclass
class Result:
    rule_id: str
    status: str                 # fail, warn, manual, pass, info
    name: str = ""              # English rule name (translated at draw time)
    measured: str = ""          # already formatted, translated
    limit: str = ""
    message: str = ""           # English template, translated with args
    args: dict = field(default_factory=dict)
    why: str = ""
    source: str = ""
    select: dict = field(default_factory=dict)   # {"objects": [...]} or {"faces": {obj: [idx]}}
    fix: str = ""               # fix kind that can solve it, if any
