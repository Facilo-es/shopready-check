# SPDX-License-Identifier: GPL-3.0-or-later
"""A plain snapshot of "the product": what the checks look at.

Built either from the Blender scene (gather_scene) or from an exported GLB
(glb.read_model). Fields that a source can't know stay None and the checks
for them are skipped.
"""
from dataclasses import dataclass, field


@dataclass
class MeshInfo:
    name: str
    tris: int = 0
    faces: int = 0
    ngons: list = field(default_factory=list)        # face indices
    degenerate: list = field(default_factory=list)
    nonmanifold_edges: int = 0
    nonmanifold_faces: list = field(default_factory=list)
    inconsistent_edges: int = 0
    flipped: bool = False
    uv_layers: int = 0
    uv_out: list = field(default_factory=list)
    uv_overlap_faces: list = field(default_factory=list)
    uv_overlap_cells: int = 0
    modifiers: list = field(default_factory=list)
    rotated: bool = False
    scaled: bool = False
    materials: list = field(default_factory=list)


@dataclass
class ImageInfo:
    name: str
    width: int = 0
    height: int = 0
    fmt: str = ""            # PNG, JPEG, ...
    alpha: bool = False      # alpha channel is used by a material
    normal: bool = False     # used as a normal map
    nbytes: int = 0
    data_uri: bool = False


@dataclass
class MaterialInfo:
    name: str
    principled: bool = True
    procedural: list = field(default_factory=list)   # node labels that won't export
    images: list = field(default_factory=list)
    orm_images: list = field(default_factory=list)   # distinct images feeding O, R, M
    double_sided: bool = False
    extensions: list = field(default_factory=list)


@dataclass
class Model:
    source: str = "scene"            # scene or glb
    fmt: str = "glb"
    meshes: list = field(default_factory=list)       # MeshInfo
    cameras: list = field(default_factory=list)
    lights: list = field(default_factory=list)
    empties: list = field(default_factory=list)
    animated: list = field(default_factory=list)
    materials: dict = field(default_factory=dict)    # name -> MaterialInfo
    images: dict = field(default_factory=dict)       # name -> ImageInfo
    extensions: list = field(default_factory=list)
    draco: bool = None
    bmin: tuple = None               # bounds in glTF axes (Y up), metres
    bmax: tuple = None
    file_bytes: int = None           # real size after export
    est_bytes: int = None            # estimate before export
    notes: list = field(default_factory=list)

    @property
    def tris(self):
        return sum(m.tris for m in self.meshes)

    @property
    def dims(self):
        """(width X, depth Z, height Y) in metres, glTF axes."""
        if self.bmin is None:
            return None
        return (self.bmax[0] - self.bmin[0], self.bmax[2] - self.bmin[2], self.bmax[1] - self.bmin[1])
