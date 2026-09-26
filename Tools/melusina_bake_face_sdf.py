"""
Headless Blender 5.2 tool: bake an anime-style face shadow threshold SDF map
for Melusina from the staged FBX export.

Run:
  "C:/Program Files/Blender Foundation/Blender 5.2/blender.exe" -b --factory-startup ^
      --python C:/EnvironmentPortfolio/BS_GodFile/Tools/melusina_bake_face_sdf.py

Hard constraints (see task): only touches the staged FBX, never opens/saves any
.blend under harp_bow_pipeline, never touches UE/Config/Content/git. Writes only
under Saved/Staging/MelusinaFaceSDF/.

Method (standard Genshin/anime-style face-shadow threshold map):
  1. Import FBX into an empty scene.
  2. Isolate head/face verts (vertex-group name match, else height heuristic).
  3. Build a "spherized" normal per face-vert: blend the real vertex normal
     toward the outward direction from a head-centered ellipsoid center, to
     suppress high-frequency noise from the nose/eyes/mouth (this is the
     standard trick to keep the shadow band smooth across the cheek).
  4. For N angles around the head's up axis (0..90 degrees, front to side,
     mirrored for symmetry), compute a light direction in the head's local
     frame and a binary lit/shadow mask per face vert: lit if
     dot(spherized_normal, light_dir) > 0.
  5. Rasterize each vert's mask into its face-UV (UV1 if present, else UV0)
     texel via nearest/point assignment from the mesh's UV layout, accumulate
     into a per-texel "first angle at which the texel goes into shadow" =
     the threshold value. Store as a monotonic 0..1 gradient, mirror
     left/right by averaging with the horizontally-flipped copy (UV-space
     mirror around U=0.5), write to 16-bit grayscale PNG.
  6. Also write a contact-sheet PNG (mask thumbnails at several angles) and a
     JSON report.

Pure numpy (mesh data pulled via bpy/bmesh); no Cycles baking needed.
"""

import bpy
import bmesh
import json
import math
import os
import sys

import numpy as np

# ---------------------------------------------------------------------------
# Config
# ---------------------------------------------------------------------------

FBX_PATH = "C:/EnvironmentPortfolio/BS_GodFile/Saved/Staging/MelusinaExport_20260925/SK_Melusina_V2_Body.fbx"
OUT_DIR = "C:/EnvironmentPortfolio/BS_GodFile/Saved/Staging/MelusinaFaceSDF"
OUT_PNG = os.path.join(OUT_DIR, "T_Melusina_FaceSDF.png")
OUT_CONTACT = os.path.join(OUT_DIR, "T_Melusina_FaceSDF_contact.png")
OUT_JSON = os.path.join(OUT_DIR, "T_Melusina_FaceSDF_report.json")

TEX_RES = 1024          # output resolution
N_ANGLES = 32            # light-angle steps, 0..90 degrees
ANGLE_MAX_DEG = 90.0
DILATE_PX = 4            # texel dilation to fill unwritten gaps (padding)
HEAD_VGROUP_HINTS = (
    "head", "face", "org-face", "org-head", "forehead", "cheek", "nose",
    "lip", "jaw", "chin", "brow", "lid", "eye", "temple",
)
HEAD_VGROUP_EXCLUDE = ("eyelash",)


def log(msg):
    print(f"[face_sdf] {msg}")
    sys.stdout.flush()


# ---------------------------------------------------------------------------
# Import
# ---------------------------------------------------------------------------

def import_fbx(path):
    bpy.ops.import_scene.fbx(filepath=path)
    meshes = [o for o in bpy.context.scene.objects if o.type == "MESH"]
    if not meshes:
        raise RuntimeError("No mesh objects found after FBX import")
    # pick the mesh with the most vertices (the body mesh)
    meshes.sort(key=lambda o: len(o.data.vertices), reverse=True)
    return meshes[0]


# ---------------------------------------------------------------------------
# Head/face vertex isolation
# ---------------------------------------------------------------------------

def find_head_vertex_indices(obj):
    """Return (indices, method_str). Try vertex groups skinned to head/face
    bones first; fall back to a height-based heuristic."""
    mesh = obj.data
    vg_hits = []
    for vg in obj.vertex_groups:
        name_lc = vg.name.lower()
        if any(h in name_lc for h in HEAD_VGROUP_HINTS) and not any(x in name_lc for x in HEAD_VGROUP_EXCLUDE):
            vg_hits.append(vg)

    if vg_hits:
        vg_indices = {vg.index for vg in vg_hits}
        idxs = []
        for v in mesh.vertices:
            for g in v.groups:
                if g.group in vg_indices and g.weight > 0.25:
                    idxs.append(v.index)
                    break
        if len(idxs) > 200:
            return np.array(idxs, dtype=np.int64), f"vertex_groups:{sorted(vg.name for vg in vg_hits)}"
        log(f"vertex group match too small ({len(idxs)}) - falling back to height heuristic")

    # Height heuristic: verts above a Z threshold derived from the bounding box.
    # Use the top ~22% of the mesh's Z extent as "head" (neck cut).
    zs = np.array([v.co.z for v in mesh.vertices], dtype=np.float64)
    z_min, z_max = zs.min(), zs.max()
    cut = z_min + 0.80 * (z_max - z_min)
    idxs = np.nonzero(zs > cut)[0]
    return idxs, f"height_heuristic:z>{cut:.4f} (range {z_min:.4f}..{z_max:.4f})"


# ---------------------------------------------------------------------------
# UV channel selection
# ---------------------------------------------------------------------------

def pick_uv_layer(mesh, head_idx_set):
    """Prefer UV channel index 1 (matches bFaceSDF_UV1 in the master
    material) but only if it actually has populated (non-degenerate) data
    over the face region in this export; some staged FBX exports carry a
    second UV channel that is present but left at (0,0) placeholder values.
    Falls back to whichever channel has the least degenerate coverage."""
    names = [uv.name for uv in mesh.uv_layers]
    if not names:
        raise RuntimeError("Mesh has no UV layers at all")

    def degenerate_fraction(uv_layer):
        total = 0
        zero = 0
        for p in mesh.polygons:
            for k in range(p.loop_total):
                loop = mesh.loops[p.loop_start + k]
                if loop.vertex_index in head_idx_set:
                    uv = uv_layer.data[p.loop_start + k].uv
                    total += 1
                    if abs(uv[0]) < 1e-6 and abs(uv[1]) < 1e-6:
                        zero += 1
        return (zero / total) if total else 1.0

    stats = [(i, degenerate_fraction(mesh.uv_layers[i])) for i in range(len(names))]
    stats_str = {names[i]: f"{frac:.3f} degenerate" for i, frac in stats}

    # prefer index 1 (UV1) unless it's mostly degenerate (>50%) and another
    # channel is clearly better
    if len(names) >= 2:
        idx1_frac = dict(stats)[1]
        if idx1_frac <= 0.5:
            return mesh.uv_layers[1], names, 1, stats_str
        best_idx, best_frac = min(stats, key=lambda t: t[1])
        return mesh.uv_layers[best_idx], names, best_idx, stats_str

    return mesh.uv_layers[0], names, 0, stats_str


# ---------------------------------------------------------------------------
# Spherized normals
# ---------------------------------------------------------------------------

def compute_spherized_normals(mesh, head_idx_set, head_center, head_radii):
    """Blend true vertex normal toward the outward ellipsoid direction to
    suppress nose/eye/mouth noise. Returns dict vert_idx -> normalized np.array(3)."""
    out = {}
    blend = 0.55  # how much to pull toward the ellipsoid normal (0=raw normal, 1=pure ellipsoid)
    for v in mesh.vertices:
        if v.index not in head_idx_set:
            continue
        co = np.array(v.co, dtype=np.float64)
        n = np.array(v.normal, dtype=np.float64)
        n_len = np.linalg.norm(n)
        if n_len > 1e-8:
            n = n / n_len
        # outward direction on the ellipsoid centered at head_center with
        # radii head_radii (elementwise-normalized offset)
        d = (co - head_center) / head_radii
        d_len = np.linalg.norm(d)
        ell_n = d / d_len if d_len > 1e-8 else n
        blended = (1.0 - blend) * n + blend * ell_n
        b_len = np.linalg.norm(blended)
        if b_len > 1e-8:
            blended = blended / b_len
        out[v.index] = blended
    return out


# ---------------------------------------------------------------------------
# Threshold bake
# ---------------------------------------------------------------------------

def bake_threshold_map(mesh, uv_layer, head_idx, normals, head_center, up_axis, right_axis):
    """For each face-loop touching a head vert, rasterize a small splat into
    UV space and accumulate per-angle lit masks -> per-texel threshold angle."""
    res = TEX_RES
    accum_sum = np.zeros((res, res), dtype=np.float64)
    accum_cnt = np.zeros((res, res), dtype=np.float64)

    head_idx_set = set(int(i) for i in head_idx)
    angles_deg = np.linspace(0.0, ANGLE_MAX_DEG, N_ANGLES)

    # Precompute light dirs (front -> side, in the head's local right/up/fwd frame)
    fwd_axis = np.cross(up_axis, right_axis)
    fwd_axis /= np.linalg.norm(fwd_axis)

    light_dirs = []
    for deg in angles_deg:
        rad = math.radians(deg)
        d = math.cos(rad) * fwd_axis + math.sin(rad) * right_axis
        d = d / np.linalg.norm(d)
        light_dirs.append(d)

    uv_data = uv_layer.data
    poly_loop_start = [p.loop_start for p in mesh.polygons]
    poly_loop_total = [p.loop_total for p in mesh.polygons]

    contact_masks = [np.zeros((res, res), dtype=np.float64) for _ in range(N_ANGLES)]
    contact_wt = [np.zeros((res, res), dtype=np.float64) for _ in range(N_ANGLES)]

    for p_i, poly in enumerate(mesh.polygons):
        loop_start = poly_loop_start[p_i]
        loop_total = poly_loop_total[p_i]
        vids = [mesh.loops[loop_start + k].vertex_index for k in range(loop_total)]
        if not any(vid in head_idx_set for vid in vids):
            continue
        for k in range(loop_total):
            vid = vids[k]
            if vid not in normals:
                continue
            uv = uv_data[loop_start + k].uv
            u, v = float(uv[0]), float(uv[1])
            if not (0.0 <= u <= 1.0 and 0.0 <= v <= 1.0):
                continue
            px = min(res - 1, max(0, int(u * res)))
            py = min(res - 1, max(0, int((1.0 - v) * res)))  # image row 0 = top

            n = normals[vid]
            # find first angle index where texel flips lit->shadow
            thresh_deg = ANGLE_MAX_DEG  # never goes into shadow within range -> fully lit
            for a_i, ld in enumerate(light_dirs):
                lit = np.dot(n, ld) > 0.0
                contact_masks[a_i][py, px] += 1.0 if lit else 0.0
                contact_wt[a_i][py, px] += 1.0
                if not lit:
                    thresh_deg = angles_deg[a_i]
                    break
            accum_sum[py, px] += thresh_deg
            accum_cnt[py, px] += 1.0

    return accum_sum, accum_cnt, contact_masks, contact_wt, angles_deg


def dilate_fill(value, weight, iterations):
    """Simple push-pull dilation to fill unwritten texels using neighbor avg."""
    filled = value.copy()
    has = weight > 0
    for _ in range(iterations):
        missing = ~has
        if not missing.any():
            break
        # 4-neighbor average of currently-known texels
        acc = np.zeros_like(filled)
        cnt = np.zeros_like(filled)
        for dy, dx in ((1, 0), (-1, 0), (0, 1), (0, -1)):
            shifted_val = np.roll(filled, (dy, dx), axis=(0, 1))
            shifted_has = np.roll(has, (dy, dx), axis=(0, 1))
            acc += np.where(shifted_has, shifted_val, 0.0)
            cnt += shifted_has.astype(np.float64)
        newly = missing & (cnt > 0)
        filled = np.where(newly, acc / np.maximum(cnt, 1.0), filled)
        has = has | newly
    return filled, has


def main():
    os.makedirs(OUT_DIR, exist_ok=True)

    # Clean factory scene
    bpy.ops.wm.read_factory_settings(use_empty=True)

    log(f"Importing FBX: {FBX_PATH}")
    obj = import_fbx(FBX_PATH)
    mesh = obj.data
    vert_count = len(mesh.vertices)
    log(f"Imported mesh '{obj.name}' with {vert_count} verts, {len(mesh.polygons)} polys")

    head_idx, method = find_head_vertex_indices(obj)
    log(f"Head isolation method: {method}; head vert count = {len(head_idx)}")
    if len(head_idx) < 50:
        raise RuntimeError(f"Head vertex isolation failed - only {len(head_idx)} verts found")

    head_idx_set_early = set(int(i) for i in head_idx)
    uv_layer, uv_names, uv_index, uv_stats = pick_uv_layer(mesh, head_idx_set_early)
    log(f"UV layers found: {uv_names}; degenerate coverage: {uv_stats}; using index {uv_index} ({uv_layer.name})")

    head_coords = np.array([mesh.vertices[i].co for i in head_idx], dtype=np.float64)
    head_center = head_coords.mean(axis=0)
    head_min = head_coords.min(axis=0)
    head_max = head_coords.max(axis=0)
    head_radii = np.maximum((head_max - head_min) / 2.0, 1e-4)
    log(f"Head center={head_center.tolist()} radii={head_radii.tolist()}")

    # Local frame: Blender Z-up. up_axis = world Z, right_axis = world X.
    # (Body is FBX-imported from UE; front-facing assumption documented below.)
    up_axis = np.array([0.0, 0.0, 1.0])
    right_axis = np.array([1.0, 0.0, 0.0])

    head_idx_set = set(int(i) for i in head_idx)
    normals = compute_spherized_normals(mesh, head_idx_set, head_center, head_radii)
    log(f"Computed spherized normals for {len(normals)} verts")

    accum_sum, accum_cnt, contact_masks, contact_wt, angles_deg = bake_threshold_map(
        mesh, uv_layer, head_idx, normals, head_center, up_axis, right_axis
    )

    has_data = accum_cnt > 0
    written_texels = int(has_data.sum())
    log(f"Directly written texels: {written_texels} / {TEX_RES*TEX_RES}")
    if written_texels < 200:
        raise RuntimeError("Too few texels written - UV channel or head isolation is wrong")

    raw = np.where(has_data, accum_sum / np.maximum(accum_cnt, 1.0), 0.0)
    filled, has = dilate_fill(raw, accum_cnt.copy(), iterations=64)

    # Normalize 0..90deg range -> 0..1
    norm = np.clip(filled / ANGLE_MAX_DEG, 0.0, 1.0)

    # Mirror left/right for symmetry: average with horizontally-flipped copy.
    mirrored = 0.5 * (norm + np.fliplr(norm))

    # Light gaussian-ish smoothing (box blur passes) to remove residual noise
    def box_blur(a, passes=2):
        b = a.copy()
        for _ in range(passes):
            b = (b
                 + np.roll(b, 1, axis=0) + np.roll(b, -1, axis=0)
                 + np.roll(b, 1, axis=1) + np.roll(b, -1, axis=1)) / 5.0
        return b

    smoothed = box_blur(mirrored, passes=2)

    val_min, val_max = float(smoothed.min()), float(smoothed.max())
    log(f"Final value range: {val_min:.4f} .. {val_max:.4f}")

    # ---- write 16-bit grayscale PNG via Blender image datablock ----
    img16 = bpy.data.images.new("T_Melusina_FaceSDF", width=TEX_RES, height=TEX_RES, alpha=False, float_buffer=True)
    px = np.zeros((TEX_RES, TEX_RES, 4), dtype=np.float64)
    g = smoothed  # already row0=top; Blender images are row0=bottom, flip
    g_flipped = np.flipud(g)
    px[:, :, 0] = g_flipped
    px[:, :, 1] = g_flipped
    px[:, :, 2] = g_flipped
    px[:, :, 3] = 1.0
    img16.pixels.foreach_set(px.astype(np.float32).ravel())
    img16.filepath_raw = OUT_PNG
    img16.file_format = "PNG"
    scene = bpy.context.scene
    scene.view_settings.view_transform = "Standard"
    img16.save_render(OUT_PNG, scene=scene) if False else img16.save()
    log(f"Wrote {OUT_PNG}")

    # ---- contact sheet: pick 8 evenly spaced angle masks ----
    n_show = 8
    show_idx = np.linspace(0, N_ANGLES - 1, n_show).astype(int)
    tile = TEX_RES // 4
    sheet = np.zeros((tile * 2, tile * 4), dtype=np.float64)
    for si, a_i in enumerate(show_idx):
        m = contact_masks[a_i]
        w = np.maximum(contact_wt[a_i], 1.0)
        frac = m / w
        frac_img = np.flipud(frac)
        # downsample nearest
        ys = (np.linspace(0, TEX_RES - 1, tile)).astype(int)
        xs = (np.linspace(0, TEX_RES - 1, tile)).astype(int)
        small = frac_img[np.ix_(ys, xs)]
        row = si // 4
        col = si % 4
        sheet[row * tile:(row + 1) * tile, col * tile:(col + 1) * tile] = small

    sheet_img = bpy.data.images.new("T_Melusina_FaceSDF_contact", width=sheet.shape[1], height=sheet.shape[0], alpha=False)
    spx = np.zeros((sheet.shape[0], sheet.shape[1], 4), dtype=np.float64)
    spx[:, :, 0] = sheet
    spx[:, :, 1] = sheet
    spx[:, :, 2] = sheet
    spx[:, :, 3] = 1.0
    sheet_img.pixels.foreach_set(spx.astype(np.float32).ravel())
    sheet_img.filepath_raw = OUT_CONTACT
    sheet_img.file_format = "PNG"
    sheet_img.save()
    log(f"Wrote {OUT_CONTACT}")

    report = {
        "fbx_source": FBX_PATH,
        "uv_layers_found": uv_names,
        "uv_layer_degenerate_coverage": uv_stats,
        "uv_channel_used_index": uv_index,
        "uv_channel_used_name": uv_layer.name,
        "vert_count_total": vert_count,
        "head_vert_count": int(len(head_idx)),
        "head_isolation_method": method,
        "angle_count": N_ANGLES,
        "angle_max_deg": ANGLE_MAX_DEG,
        "directly_written_texels": written_texels,
        "texture_resolution": TEX_RES,
        "value_range_final": [val_min, val_max],
        "output_png": OUT_PNG,
        "contact_sheet_png": OUT_CONTACT,
    }
    with open(OUT_JSON, "w") as f:
        json.dump(report, f, indent=2)
    log(f"Wrote {OUT_JSON}")

    log("Done.")


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        import traceback
        traceback.print_exc()
        sys.stdout.flush()
        os._exit(1)
    sys.stdout.flush()
    os._exit(0)
