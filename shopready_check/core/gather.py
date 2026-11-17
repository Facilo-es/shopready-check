# SPDX-License-Identifier: GPL-3.0-or-later
"""Read the product from the Blender scene into a Model.

Works on evaluated meshes (modifiers applied in memory, scene untouched) and
reports bounds in glTF axes: Blender (x, y, z) is glTF (x, z, -y).
"""
import os

import bpy
import numpy as np

from .model import ImageInfo, MaterialInfo, MeshInfo, Model

UV_EPS = 1e-4
AREA_EPS = 1e-12
PROCEDURAL = {
    "TEX_NOISE", "TEX_VORONOI", "TEX_WAVE", "TEX_MUSGRAVE", "TEX_MAGIC", "TEX_BRICK",
    "TEX_CHECKER", "TEX_GRADIENT", "TEX_WHITE_NOISE", "TEX_SKY", "TEX_POINTDENSITY",
    "TEX_GABOR", "VALTORGB", "BUMP", "AMBIENT_OCCLUSION", "WIREFRAME", "BEVEL",
}


# ---------------------------------------------------------------- scope

def scope_objects(context, scope, collection=None):
    if scope == "SELECTED":
        return list(context.selected_objects)
    if scope == "COLLECTION":
        coll = collection or context.view_layer.active_layer_collection.collection
        return list(coll.all_objects)
    return list(context.scene.objects)


# ---------------------------------------------------------------- meshes

def _arr(seq, attr, n, width=1, dtype=np.float64):
    a = np.empty(n * width, dtype=dtype)
    if n:
        seq.foreach_get(attr, a)
    return a.reshape(-1, width) if width > 1 else a


def _uv_overlap(uv, tri_loops, tri_face, grid):
    """Rasterise UV triangles into a grid; return (cells hit by 2+ faces, faces)."""
    t = uv[tri_loops]                      # (T, 3, 2)
    n = grid
    lo = t.min(axis=1)
    hi = t.max(axis=1)
    i0 = np.clip(np.ceil(lo[:, 0] * n - 0.5), 0, n).astype(np.int64)
    i1 = np.clip(np.floor(hi[:, 0] * n - 0.5), -1, n - 1).astype(np.int64)
    j0 = np.clip(np.ceil(lo[:, 1] * n - 0.5), 0, n).astype(np.int64)
    j1 = np.clip(np.floor(hi[:, 1] * n - 0.5), -1, n - 1).astype(np.int64)
    nx = np.maximum(i1 - i0 + 1, 0)
    ny = np.maximum(j1 - j0 + 1, 0)
    cnt = nx * ny
    total = int(cnt.sum())
    if total == 0:
        return 0, []
    if total > 30_000_000:   # absurd UVs; give up quietly (warn-level rule)
        return 0, []
    tri = np.repeat(np.arange(len(t)), cnt)
    off = np.arange(total) - np.repeat(np.cumsum(cnt) - cnt, cnt)
    ix = i0[tri] + off % nx[tri]
    iy = j0[tri] + off // nx[tri]
    px = (ix + 0.5) / n
    py = (iy + 0.5) / n
    a, b, c = t[tri, 0], t[tri, 1], t[tri, 2]

    def edge(p, q):
        return (q[:, 0] - p[:, 0]) * (py - p[:, 1]) - (q[:, 1] - p[:, 1]) * (px - p[:, 0])
    d1, d2, d3 = edge(a, b), edge(b, c), edge(c, a)
    inside = ((d1 >= 0) & (d2 >= 0) & (d3 >= 0)) | ((d1 <= 0) & (d2 <= 0) & (d3 <= 0))
    area = np.abs(d1 + d2 + d3)
    inside &= area > 0
    cell = (iy * n + ix)[inside]
    face = tri_face[tri][inside]
    if not len(cell):
        return 0, []
    pairs = np.unique(cell * (int(face.max()) + 1) + face)
    pcell = pairs // (int(face.max()) + 1)
    pface = pairs % (int(face.max()) + 1)
    cells, counts = np.unique(pcell, return_counts=True)
    bad = cells[counts > 1]
    faces = np.unique(pface[np.isin(pcell, bad)])
    return int(len(bad)), faces.tolist()


def mesh_info(ob, me, grid=256):
    info = MeshInfo(name=ob.name)
    nv, nf, nl = len(me.vertices), len(me.polygons), len(me.loops)
    info.faces = nf
    if nf == 0:
        return info, _arr(me.vertices, "co", nv, 3)
    co = _arr(me.vertices, "co", nv, 3)
    ltot = _arr(me.polygons, "loop_total", nf, dtype=np.int64)
    lstart = _arr(me.polygons, "loop_start", nf, dtype=np.int64)
    area = _arr(me.polygons, "area", nf)
    lvert = _arr(me.loops, "vertex_index", nl, dtype=np.int64)
    ledge = _arr(me.loops, "edge_index", nl, dtype=np.int64)

    info.tris = int((ltot - 2).clip(min=0).sum())
    info.ngons = np.nonzero(ltot > 4)[0].tolist()
    info.degenerate = np.nonzero(area <= AREA_EPS)[0].tolist()

    # edges: manifold means exactly two faces per edge
    ne = len(me.edges)
    use = np.bincount(ledge, minlength=ne)
    bad_edges = (use != 2) & (use > 0)
    info.nonmanifold_edges = int(bad_edges.sum())
    loop_face = np.repeat(np.arange(nf), ltot)
    if info.nonmanifold_edges:
        info.nonmanifold_faces = np.unique(loop_face[bad_edges[ledge]]).tolist()

    # winding: the two loops on a shared edge must run in opposite directions
    pos = np.arange(nl) - np.repeat(lstart, ltot)
    nxt = np.repeat(lstart, ltot) + (pos + 1) % np.repeat(ltot, ltot)
    start = lvert
    twin = use[ledge] == 2
    idx = np.nonzero(twin)[0]
    order = idx[np.argsort(ledge[idx], kind="stable")]
    first, second = order[0::2], order[1::2]
    same = start[first] == start[second]
    info.inconsistent_edges = int(same.sum())

    me.calc_loop_triangles()
    nt = len(me.loop_triangles)
    tv = _arr(me.loop_triangles, "vertices", nt, 3, np.int64)
    if info.nonmanifold_edges == 0 and info.inconsistent_edges == 0 and nt:
        v0, v1, v2 = co[tv[:, 0]], co[tv[:, 1]], co[tv[:, 2]]
        vol = np.einsum("ij,ij->i", v0, np.cross(v1, v2)).sum() / 6.0
        info.flipped = bool(vol < 0)

    info.uv_layers = len(me.uv_layers)
    uvl = me.uv_layers.active
    if uvl is not None and nl:
        uv = _arr(uvl.data, "uv", nl, 2)
        outside = ((uv < -UV_EPS) | (uv > 1 + UV_EPS)).any(axis=1)
        if outside.any():
            info.uv_out = np.unique(loop_face[outside]).tolist()
        tl = _arr(me.loop_triangles, "loops", nt, 3, np.int64)
        tf = _arr(me.loop_triangles, "polygon_index", nt, dtype=np.int64)
        info.uv_overlap_cells, info.uv_overlap_faces = _uv_overlap(uv, tl, tf, grid)
    return info, co


# ---------------------------------------------------------------- materials

def _upstream(node, seen=None):
    """All nodes feeding into node (inclusive), following links backwards."""
    seen = seen if seen is not None else set()
    if node is None or node in seen:
        return seen
    seen.add(node)
    for sock in node.inputs:
        for link in sock.links:
            if link.is_valid and not link.is_muted:
                _upstream(link.from_node, seen)
    return seen


def _images_into(sock):
    out = []
    if sock is None:
        return out
    for link in sock.links:
        for n in _upstream(link.from_node):
            if n.type == "TEX_IMAGE" and n.image:
                out.append(n.image)
    return out


def _inp(node, *names):
    for name in names:
        s = node.inputs.get(name)
        if s is not None:
            return s
    return None


def _val(sock, default=0.0):
    if sock is None:
        return default
    try:
        return sock.default_value
    except AttributeError:
        return default


def material_info(mat, images):
    info = MaterialInfo(name=mat.name)
    info.double_sided = not getattr(mat, "use_backface_culling", False)
    if not mat.use_nodes or mat.node_tree is None:
        info.principled = False
        return info
    nt = mat.node_tree
    out = next((n for n in nt.nodes if n.type == "OUTPUT_MATERIAL" and n.is_active_output), None)
    out = out or next((n for n in nt.nodes if n.type == "OUTPUT_MATERIAL"), None)
    surf = out.inputs.get("Surface") if out else None
    feeding = set()
    if surf is not None:
        for link in surf.links:
            feeding |= _upstream(link.from_node)
    bsdf = next((n for n in feeding if n.type == "BSDF_PRINCIPLED"), None)
    info.principled = bsdf is not None
    for n in sorted(feeding, key=lambda n: n.name):
        if n.type in PROCEDURAL:
            info.procedural.append(n.label or n.name)
        if n.type == "TEX_IMAGE" and n.image:
            img = n.image
            if img.name not in info.images:
                info.images.append(img.name)
            ii = images.setdefault(img.name, image_info(img))
            alpha_out = n.outputs.get("Alpha")
            if alpha_out is not None and alpha_out.is_linked:
                ii.alpha = True
        if n.type == "NORMAL_MAP":
            for img in _images_into(n.inputs.get("Color")):
                images.setdefault(img.name, image_info(img)).normal = True
    # occlusion from the glTF settings group, if the artist added one
    orm = []
    for n in nt.nodes:
        if n.type == "GROUP" and n.node_tree and "gltf" in n.node_tree.name.lower():
            occ = _images_into(n.inputs.get("Occlusion"))
            orm += occ
            # the exporter writes the occlusion map too, so it counts as one of the material's textures
            for img in occ:
                if img.name not in info.images:
                    info.images.append(img.name)
                images.setdefault(img.name, image_info(img))
    if bsdf is not None:
        orm += _images_into(_inp(bsdf, "Roughness")) + _images_into(_inp(bsdf, "Metallic"))
        info.orm_images = sorted({i.name for i in orm})
        info.extensions = predict_extensions(bsdf, feeding)
    return info


def predict_extensions(bsdf, feeding):
    """glTF extensions Blender's exporter will write for this material."""
    ext = set()

    def on(*names, default=0.0):
        s = _inp(bsdf, *names)
        return s is not None and (s.is_linked or abs(float(_val(s, default)) - default) > 1e-4)

    if on("Transmission Weight", "Transmission"):
        ext.add("KHR_materials_transmission")
    if on("Coat Weight", "Clearcoat"):
        ext.add("KHR_materials_clearcoat")
    if on("Sheen Weight", "Sheen"):
        ext.add("KHR_materials_sheen")
    if on("IOR", default=1.5):
        ext.add("KHR_materials_ior")
    if on("Anisotropic"):
        ext.add("KHR_materials_anisotropy")
    spec = _inp(bsdf, "Specular IOR Level")
    tint = _inp(bsdf, "Specular Tint")
    if (spec is not None and (spec.is_linked or abs(_val(spec, 0.5) - 0.5) > 1e-4)) or \
            (tint is not None and (tint.is_linked or min(tuple(_val(tint, (1, 1, 1, 1)))[:3]) < 0.999)):
        ext.add("KHR_materials_specular")
    es = _inp(bsdf, "Emission Strength")
    ec = _inp(bsdf, "Emission Color", "Emission")
    if es is not None and ec is not None and _val(es, 0) > 1.0 and \
            (ec.is_linked or max(tuple(_val(ec, (0, 0, 0, 1)))[:3]) > 0):
        ext.add("KHR_materials_emissive_strength")
    if any(n.type == "MAPPING" for n in feeding):
        ext.add("KHR_texture_transform")
    return sorted(ext)


_MAGIC = ((b"\x89PNG", "PNG"), (b"\xff\xd8", "JPEG"), (b"RIFF", "WEBP"), (b"II*\x00", "TIFF"),
          (b"MM\x00*", "TIFF"), (b"#?RA", "HDR"), (b"v/1\x01", "OPEN_EXR"), (b"BM", "BMP"))


def _sniff(img):
    """The real format from the file's first bytes (file_format can be stale)."""
    head = b""
    try:
        if img.packed_file is not None:
            head = bytes(img.packed_file.data[:4])
        elif img.source == "FILE":
            path = bpy.path.abspath(img.filepath, library=img.library)
            if os.path.isfile(path):
                with open(path, "rb") as fh:
                    head = fh.read(4)
    except (OSError, TypeError):
        return ""
    return next((name for magic, name in _MAGIC if head.startswith(magic)), "")


def image_info(img):
    w, h = (int(img.size[0]), int(img.size[1]))
    nbytes = 0
    if img.packed_file is not None:
        nbytes = img.packed_file.size
    elif img.source == "FILE":
        path = bpy.path.abspath(img.filepath, library=img.library)
        if os.path.isfile(path):
            nbytes = os.path.getsize(path)
    fmt = _sniff(img) or img.file_format or ""
    if not nbytes:
        nbytes = int(w * h * (0.6 if fmt == "JPEG" else 1.6))
    return ImageInfo(name=img.name, width=w, height=h, fmt=fmt, nbytes=nbytes)


# ---------------------------------------------------------------- scene

def _animated(ob):
    ad = ob.animation_data
    if ad and (ad.action or len(ad.nla_tracks)):
        return True
    data = getattr(ob, "data", None)
    keys = getattr(data, "shape_keys", None)
    if keys and keys.animation_data and keys.animation_data.action:
        return True
    return False


def gather(objects, depsgraph, grid=256):
    """Build a Model from scene objects. Only meshes count for geometry."""
    model = Model(source="scene")
    lo = np.full(3, np.inf)
    hi = np.full(3, -np.inf)
    vbytes = 0
    for ob in objects:
        if _animated(ob):
            model.animated.append(ob.name)
        if ob.type == "CAMERA":
            model.cameras.append(ob.name)
            continue
        if ob.type == "LIGHT":
            model.lights.append(ob.name)
            continue
        if ob.type != "MESH":
            if ob.type == "EMPTY":
                model.empties.append(ob.name)
            continue
        ev = ob.evaluated_get(depsgraph)
        me = ev.to_mesh()
        try:
            info, co = mesh_info(ob, me, grid)
            if len(co):
                mw = np.array(ev.matrix_world)
                w = co @ mw[:3, :3].T + mw[:3, 3]
                lo = np.minimum(lo, w.min(axis=0))
                hi = np.maximum(hi, w.max(axis=0))
            vbytes += len(me.loops) * 32 + info.tris * 12
        finally:
            ev.to_mesh_clear()
        info.modifiers = [m.name for m in ob.modifiers if m.show_viewport or m.show_render]
        loc, rot, scale = ob.matrix_world.decompose()
        info.rotated = rot.angle > 1e-5 if hasattr(rot, "angle") else False
        info.scaled = any(abs(s - 1.0) > 1e-5 for s in scale)
        for slot in ob.material_slots:
            mat = slot.material
            if mat is None:
                continue
            if mat.name not in info.materials:
                info.materials.append(mat.name)
            if mat.name not in model.materials:
                model.materials[mat.name] = material_info(mat, model.images)
        model.meshes.append(info)
    if np.isfinite(lo).all():
        # Blender (x, y, z) -> glTF (x, z, -y)
        model.bmin = (float(lo[0]), float(lo[2]), float(-hi[1]))
        model.bmax = (float(hi[0]), float(hi[2]), float(-lo[1]))
    ext = set()
    for m in model.materials.values():
        ext.update(m.extensions)
    model.extensions = sorted(ext)
    model.est_bytes = vbytes + sum(i.nbytes for i in model.images.values()) + 4096
    return model
