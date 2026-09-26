"""Floating iridescent crystals: procedural meshes + texture bakes.

Run with hython (Houdini 22+; needs numpy + Pillow). Textures are numpy/Pillow rather than
Copernicus because Apprentice licences watermark every COP render.

    hython Tools/Houdini/floating_crystals/build_floating_crystals.py [--out-dir DIR] [--seed N]

Writes, deterministically for a given seed:
  SM_FloatingCrystal_<Variant>.obj      Y-up, cm, pivot at the cluster core, flat facets, 0-1 UVs
                                        (U = around the facets, V = along each shard, base -> tip)
  T_FloatingCrystal_ThinFilmLUT.png     sRGB, 256^2. X = cos(view angle), Y top->bottom = film thickness 150-1100 nm.
                                        Two-beam thin-film interference (n_film 1.38 on n_crystal 1.56).
  T_FloatingCrystal_Masks.png           linear, 1024^2, tileable in U and V.
                                        R = film thickness (LUT Y), G = inclusions/cloud,
                                        B = fracture veins, A = emissive core glow.
  T_FloatingCrystal_Normal.png          linear, 1024^2, tileable, tangent-space facet micro-normals (DirectX Y-).
  T_FloatingCrystal_preview.png         contact sheet (textures + shaded mesh previews).
  floating_crystals_manifest.json       hashes, variants, and the UE material recipe.

Offline source-art tooling only; never imports Unreal.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import math
import random
from pathlib import Path

import hou
import numpy as np
from PIL import Image

ROOT = Path(__file__).resolve().parents[3]
DEFAULT_OUT = ROOT / "Saved" / "Audit" / "houdini_floating_crystals"

# name, hero shard count, satellite count, hero length (m)
VARIANTS = [
    ("Cluster_A", 6, 3, 2.6),
    ("Cluster_B", 4, 5, 2.0),
    ("Cluster_C", 8, 2, 3.2),
    ("Shard_A", 1, 0, 1.4),
    ("Shard_B", 1, 2, 0.9),
]

SIDES = 6

def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


# ---------------------------------------------------------------- geometry

def _basis(d):
    d = hou.Vector3(d).normalized()
    helper = hou.Vector3(0, 0, 1) if abs(d[1]) > 0.9 else hou.Vector3(0, 1, 0)
    a = d.cross(helper).normalized()
    b = d.cross(a).normalized()
    return a, b, d


def shard_tris(origin, direction, radius, length, tip, base_tip, twist):
    """Bipyramid-capped hexagonal prism. Returns [(p0,p1,p2),(uv0,uv1,uv2)] triangles."""
    a, b, d = _basis(direction)
    o = hou.Vector3(origin)

    def ring(z, r):
        pts = []
        for i in range(SIDES):
            ang = twist + 2 * math.pi * i / SIDES
            pts.append(o + a * (math.cos(ang) * r) + b * (math.sin(ang) * r) + d * z)
        return pts

    lo = ring(0.0, radius)
    hi = ring(length, radius * 0.82)
    apex = o + d * (length + tip)
    nadir = o - d * base_tip
    tris = []
    for i in range(SIDES):
        j = (i + 1) % SIDES
        u0, u1 = i / SIDES, (i + 1) / SIDES
        tris.append(((lo[i], lo[j], hi[j]), ((u0, 0.15), (u1, 0.15), (u1, 0.85))))
        tris.append(((lo[i], hi[j], hi[i]), ((u0, 0.15), (u1, 0.85), (u0, 0.85))))
        tris.append(((hi[i], hi[j], apex), ((u0, 0.85), (u1, 0.85), ((u0 + u1) / 2, 1.0))))
        tris.append(((lo[j], lo[i], nadir), ((u1, 0.15), (u0, 0.15), ((u0 + u1) / 2, 0.0))))
    return tris


def random_dir(rng, up_bias):
    while True:
        v = hou.Vector3(rng.uniform(-1, 1), rng.uniform(-1, 1), rng.uniform(-1, 1))
        if 0.05 < v.length() <= 1.0:
            v = v.normalized()
            v[1] = abs(v[1]) * up_bias + v[1] * (1 - up_bias)
            return v.normalized()


def build_variant(rng, heroes, satellites, hero_len):
    tris = []
    core_r = hero_len * 0.09
    for k in range(heroes):
        d = hou.Vector3(0, 1, 0) if k == 0 else random_dir(rng, 0.65)
        length = hero_len * (1.0 if k == 0 else rng.uniform(0.35, 0.75))
        radius = length * rng.uniform(0.11, 0.16)
        tris += shard_tris(d * (-core_r), d, radius, length, radius * rng.uniform(1.6, 2.6),
                           radius * rng.uniform(0.6, 1.2), rng.uniform(0, math.pi))
    for _ in range(satellites):
        d = random_dir(rng, 0.2)
        dist = hero_len * rng.uniform(0.55, 0.95)
        length = hero_len * rng.uniform(0.08, 0.18)
        radius = length * rng.uniform(0.18, 0.26)
        pos = random_dir(rng, 0.0) * dist + hou.Vector3(0, hero_len * 0.35, 0)
        tris += shard_tris(pos, d, radius, length, radius * 1.8, radius * 1.8, rng.uniform(0, math.pi))
    return tris


def export_obj(tris, path: Path):
    """Plain OBJ writer (Apprentice licences block FBX export). Y-up, centimetres, flat facet normals."""
    lines = [f"# {path.stem} - build_floating_crystals.py", f"o {path.stem}"]
    faces = []
    for (p0, p1, p2), uvs in tris:
        n = (p1 - p0).cross(p2 - p0).normalized()
        base = len(faces) * 3
        for p in (p0, p1, p2):
            lines.append("v %.4f %.4f %.4f" % (p[0] * 100.0, p[1] * 100.0, p[2] * 100.0))
        for uv in uvs:
            lines.append("vt %.5f %.5f" % uv)
        lines.append("vn %.5f %.5f %.5f" % tuple(n))
        faces.append((base, len(faces)))
    for base, fi in faces:
        a, b, c = base + 1, base + 2, base + 3
        lines.append(f"f {a}/{a}/{fi + 1} {b}/{b}/{fi + 1} {c}/{c}/{fi + 1}")
    path.write_text("\n".join(lines) + "\n", newline="\n")


# ---------------------------------------------------------------- textures (numpy)

def _smooth(t):
    t = np.clip(t, 0.0, 1.0)
    return t * t * (3.0 - 2.0 * t)


def _srgb(lin):
    lin = np.clip(lin, 0.0, 1.0)
    return np.where(lin <= 0.0031308, lin * 12.92, 1.055 * np.power(lin, 1.0 / 2.4) - 0.055)


def _u8(a):
    return np.round(np.clip(a, 0.0, 1.0) * 255.0).astype(np.uint8)


def thin_film_lut(res):
    """X = cos(view angle) 0->1, Y (top->bottom) = film thickness 150->1100 nm. Two-beam interference."""
    u = np.clip((np.arange(res) + 0.5) / res, 0.02, 1.0)[None, :]
    v = ((np.arange(res) + 0.5) / res)[:, None]
    d = 150.0 + 950.0 * v
    nf, ns = 1.38, 1.56
    cos_t = np.sqrt(np.maximum(0.0, 1.0 - ((1.0 - u * u) / (nf * nf))))
    r1 = (1.0 - nf) / (1.0 + nf)
    r2 = (nf - ns) / (nf + ns)
    rmax = (abs(r1) + abs(r2)) ** 2
    rmin = (abs(r1) - abs(r2)) ** 2
    col = np.zeros((res, res, 3))
    for c, lams in enumerate(((610.0, 640.0, 670.0), (510.0, 535.0, 560.0), (430.0, 455.0, 480.0))):
        for lam in lams:
            delta = 4.0 * math.pi * nf * d * cos_t / lam
            col[..., c] += (r1 * r1 + r2 * r2 + 2.0 * r1 * r2 * np.cos(delta) - rmin) / (rmax - rmin)
    col /= 3.0
    avg = col.mean(axis=2, keepdims=True)
    wash = (_smooth((v - 0.7) / 0.3) * 0.6)[..., None]
    col = col + (avg - col) * wash
    col *= (1.0 + 0.3 * (1.0 - u) ** 3)[..., None]
    return _u8(_srgb(col))


def cellular(res, cells, rng):
    """Periodic jittered-grid Worley noise: F1, F2 (cell units) and nearest cell id."""
    jit = rng.random((cells, cells, 2))
    x = (np.arange(res) + 0.5) / res * cells
    gx, gy = np.meshgrid(x, x)
    ix, iy = np.floor(gx).astype(int), np.floor(gy).astype(int)
    f1 = np.full(gx.shape, 9.0)
    f2 = np.full(gx.shape, 9.0)
    cid = np.zeros(gx.shape, dtype=int)
    for dy in (-1, 0, 1):
        for dx in (-1, 0, 1):
            cx, cy = ix + dx, iy + dy
            wx, wy = cx % cells, cy % cells
            dist = np.hypot(cx + jit[wy, wx, 0] - gx, cy + jit[wy, wx, 1] - gy)
            closer = dist < f1
            f2 = np.where(closer, f1, np.minimum(f2, dist))
            cid = np.where(closer, wy * cells + wx, cid)
            f1 = np.where(closer, dist, f1)
    return f1, f2, cid


def fractal(res, period, octaves, rng):
    """Periodic value-noise fBm, normalised to 0-1."""
    total = np.zeros((res, res))
    amp, norm = 1.0, 0.0
    for _ in range(octaves):
        lattice = rng.random((period, period))
        x = (np.arange(res) + 0.5) / res * period
        i0 = np.floor(x).astype(int)
        t = _smooth(x - i0)
        i1 = (i0 + 1) % period
        i0 %= period
        a = lattice[np.ix_(i0, i0)] * (1 - t)[None, :] + lattice[np.ix_(i0, i1)] * t[None, :]
        b = lattice[np.ix_(i1, i0)] * (1 - t)[None, :] + lattice[np.ix_(i1, i1)] * t[None, :]
        total += amp * (a * (1 - t)[:, None] + b * t[:, None])
        norm += amp
        amp *= 0.5
        period *= 2
    total /= norm
    return (total - total.min()) / (total.max() - total.min())


def bake_textures(out: Path, seed: int):
    rng = np.random.default_rng(seed)
    res = 1024

    f1, _, cid = cellular(res, 6, rng)
    facet_val = rng.random(36)[cid]
    swirl = fractal(res, 3, 6, rng)
    vf1, vf2, _ = cellular(res, 9, rng)
    border = (vf2 - vf1) * 0.5

    v = ((np.arange(res) + 0.5) / res)[:, None] * np.ones((1, res))
    thick = np.clip(0.2 + 0.6 * (0.5 * facet_val + 0.5 * swirl) - 0.1 * f1, 0.0, 1.0)
    incl = _smooth((swirl - 0.55) / 0.3)
    vein = 1.0 - _smooth(border / 0.035)
    glow = np.clip(np.exp(-((v - 0.5) / 0.28) ** 2) * 0.6 + vein * 0.5, 0.0, 1.0)
    masks = np.stack([thick, incl, vein, glow], axis=-1)

    mf1, _, mcid = cellular(res, 28, rng)
    height = rng.random(28 * 28)[mcid] * 0.6 + mf1 * 0.4
    strength = 6.0
    dx = (np.roll(height, -1, axis=1) - np.roll(height, 1, axis=1)) * strength
    dy = (np.roll(height, -1, axis=0) - np.roll(height, 1, axis=0)) * strength
    n = np.stack([-dx, -dy, np.ones_like(dx)], axis=-1)
    n /= np.linalg.norm(n, axis=-1, keepdims=True)

    paths = {
        "T_FloatingCrystal_ThinFilmLUT": out / "T_FloatingCrystal_ThinFilmLUT.png",
        "T_FloatingCrystal_Masks": out / "T_FloatingCrystal_Masks.png",
        "T_FloatingCrystal_Normal": out / "T_FloatingCrystal_Normal.png",
    }
    Image.fromarray(thin_film_lut(256), "RGB").save(paths["T_FloatingCrystal_ThinFilmLUT"])
    Image.fromarray(_u8(masks), "RGBA").save(paths["T_FloatingCrystal_Masks"])
    Image.fromarray(_u8(n * 0.5 + 0.5), "RGB").save(paths["T_FloatingCrystal_Normal"])
    return paths


# ---------------------------------------------------------------- preview

def preview(out: Path, textures, variant_tris):
    from PIL import ImageDraw

    tile = 384
    lut = Image.open(textures["T_FloatingCrystal_ThinFilmLUT"]).convert("RGB")
    masks = Image.open(textures["T_FloatingCrystal_Masks"]).convert("RGBA")
    sheet = Image.new("RGB", (tile * max(6, len(variant_tris)), tile * 2), (12, 12, 18))
    row0 = [lut, *[m.convert("RGB") for m in masks.split()],
            Image.open(textures["T_FloatingCrystal_Normal"]).convert("RGB")]
    for i, img in enumerate(row0):
        sheet.paste(img.resize((tile, tile)), (i * tile, 0))

    lut_px = lut.load()
    view = hou.Vector3(0.35, 0.25, 1.0).normalized()
    for i, tris in enumerate(variant_tris):
        canvas = Image.new("RGB", (tile, tile), (12, 12, 18))
        draw = ImageDraw.Draw(canvas)
        pts = [p for t, _ in tris for p in t]
        span = max(max(abs(p[0]) for p in pts), max(abs(p[1] - 0.3) for p in pts)) * 1.15
        for (p0, p1, p2), uvs in sorted(tris, key=lambda t: sum(p.dot(view) for p in t[0])):
            n = (p1 - p0).cross(p2 - p0).normalized()
            cos_v = abs(n.dot(view))
            thick = 0.5 + 0.35 * math.sin(7.0 * uvs[0][1] + 3.0 * uvs[0][0])
            c = lut_px[min(255, int(cos_v * 255)), min(255, int(thick * 255))]
            shade = 0.35 + 0.65 * cos_v
            fill = tuple(int(ch * shade) for ch in c)
            xy = [((p[0] / span) * tile / 2 + tile / 2, tile / 2 - ((p[1] - 0.3) / span) * tile / 2)
                  for p in (p0, p1, p2)]
            draw.polygon(xy, fill=fill)
        sheet.paste(canvas, (i * tile, tile))
    path = out / "T_FloatingCrystal_preview.png"
    sheet.save(path)
    return path


# ---------------------------------------------------------------- main

def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--out-dir", type=Path, default=DEFAULT_OUT)
    ap.add_argument("--seed", type=int, default=3900)
    args = ap.parse_args()
    out = args.out_dir.resolve()
    out.mkdir(parents=True, exist_ok=True)

    variants, variant_tris = [], []
    for idx, (name, heroes, sats, hero_len) in enumerate(VARIANTS):
        rng = random.Random(args.seed * 1000 + idx)
        tris = build_variant(rng, heroes, sats, hero_len)
        mesh = out / f"SM_FloatingCrystal_{name}.obj"
        export_obj(tris, mesh)
        variants.append({"name": mesh.stem, "path": mesh.name, "triangles": len(tris),
                         "hero_length_m": hero_len, "shards": heroes + sats})
        variant_tris.append(tris)

    textures = bake_textures(out, args.seed)
    prev = preview(out, textures, variant_tris)

    manifest = {
        "schema": "melodia.floating_crystals/v1",
        "generator": "Tools/Houdini/floating_crystals/build_floating_crystals.py",
        "runtime": f"hython/hou {hou.applicationVersionString()}",
        "seed": args.seed,
        "meshes": variants,
        "mesh_conventions": {"format": "OBJ (Apprentice licence blocks FBX)", "up": "Y (UE Interchange converts to Z-up on import)", "units": "cm (baked into vertex positions)",
                             "pivot": "cluster core", "uv": "U around facets, V along shard base->tip"},
        "textures": {k: {"path": v.name, "sha256": sha256(v)} for k, v in textures.items()},
        "texture_import": {
            "T_FloatingCrystal_ThinFilmLUT": "sRGB on, Clamp, no mips (TextureGroup UI or Mip Gen NoMipmaps)",
            "T_FloatingCrystal_Masks": "sRGB OFF, Compression Masks",
            "T_FloatingCrystal_Normal": "sRGB OFF, Compression Normalmap (already DirectX/UE convention; no green flip)",
        },
        "ue_material_recipe": {
            "name": "M_FloatingCrystal_Iridescent (Opaque, Default Lit; two-sided off)",
            "view_term": "u = saturate(dot(PixelNormalWS, CameraVectorWS))",
            "thin_film": "irid = ThinFilmLUT.Sample(float2(u, Masks.R + Time*FilmDrift))",
            "base_color": "lerp(DeepTint(0.02,0.03,0.08), irid, 0.35)",
            "roughness": "lerp(0.05, 0.35, Masks.G)",
            "specular": 0.8,
            "normal": "Normal texture",
            "emissive": "irid * (Masks.A * GlowStrength + pow(1-u, 4) * RimStrength)",
            "float_bob_wpo": "float3(0,0, sin(Time*BobSpeed + dot(ObjectPositionWS, 0.013)) * BobAmplitudeCm)",
            "params": {"GlowStrength": 4.0, "RimStrength": 6.0, "FilmDrift": 0.02,
                       "BobSpeed": 0.6, "BobAmplitudeCm": 25.0},
        },
        "preview": {"path": prev.name, "sha256": sha256(prev)},
        "note": "Source art only. WPO bob uses ObjectPositionWS so PCG/HISM instances get independent phase.",
    }
    for v in variants:
        v["sha256"] = sha256(out / v["path"])
    (out / "floating_crystals_manifest.json").write_text(json.dumps(manifest, indent=2, sort_keys=True))
    print(json.dumps({"out": out.as_posix(), "meshes": [v["name"] for v in variants],
                      "textures": list(textures)}, indent=2))


if __name__ == "__main__":
    main()
