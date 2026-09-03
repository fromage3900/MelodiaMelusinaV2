"""Procedural ornamental/architectural mesh generator for world building.

Creates detailed architectural meshes using pure math (GeometryScript bake):
gothic tracery, rosettes, column capitals, crown molding, spiral stairs,
vaulted ribs, filigree panels, corbels, door arches, and quatrefoils.

Run in-editor:
  py Content/Python/generate_ornamental_meshes.py
  py Content/Python/generate_ornamental_meshes.py --all
  py Content/Python/generate_ornamental_meshes.py --run 1
"""
from __future__ import annotations

import json
import math
import sys
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Callable

PROJECT_ROOT = Path(__file__).resolve().parents[2]
ORNAMENT_DIR = "/Game/EnvSandbox/Meshes/Ornament"
AUDIT_PATH = PROJECT_ROOT / "Saved" / "Audit" / "ornamental_meshes.json"
MATH_DIR = "/Game/EnvSandbox/Meshes/MathStructures"

PHI = (1.0 + math.sqrt(5.0)) / 2.0
TAU = 2.0 * math.pi


@dataclass
class StructureSpec:
    key: str
    asset_name: str
    pillar: str
    description: str
    params: dict
    run_group: int = 1

    @property
    def asset_path(self) -> str:
        return f"{ORNAMENT_DIR}/{self.asset_name}"


BUILDERS: dict[str, Callable] = {}


def _register(key: str):
    def deco(fn):
        BUILDERS[key] = fn
        return fn
    return deco


# ═══════════════════════════════════════════════════════════════════════
# PURE MATH GENERATORS
# ═══════════════════════════════════════════════════════════════════════

def _tube_along_curve(curve: list[tuple], radius: float, ring_segments: int = 16):
    """Sweep a ring along a curve to produce tube vertices + triangles."""
    n = len(curve)
    verts = []
    tris = []
    for i in range(n):
        p = curve[i]
        p_next = curve[(i + 1) % n]
        tang = (p_next[0] - p[0], p_next[1] - p[1], p_next[2] - p[2])
        tl = math.sqrt(tang[0]**2 + tang[1]**2 + tang[2]**2)
        if tl < 1e-9: tang = (1, 0, 0); tl = 1
        tang = (tang[0]/tl, tang[1]/tl, tang[2]/tl)
        up = (0, 0, 1) if abs(tang[2]) < 0.9 else (1, 0, 0)
        nrm = (
            up[1]*tang[2] - up[2]*tang[1],
            up[2]*tang[0] - up[0]*tang[2],
            up[0]*tang[1] - up[1]*tang[0]
        )
        nl = math.sqrt(nrm[0]**2 + nrm[1]**2 + nrm[2]**2)
        nrm = (nrm[0]/nl, nrm[1]/nl, nrm[2]/nl)
        binorm = (
            tang[1]*nrm[2] - tang[2]*nrm[1],
            tang[2]*nrm[0] - tang[0]*nrm[2],
            tang[0]*nrm[1] - tang[1]*nrm[0]
        )
        for j in range(ring_segments):
            a = (TAU * j) / ring_segments
            ca, sa = math.cos(a), math.sin(a)
            v = (
                p[0] + radius * (ca * nrm[0] + sa * binorm[0]),
                p[1] + radius * (ca * nrm[1] + sa * binorm[1]),
                p[2] + radius * (ca * nrm[2] + sa * binorm[2])
            )
            verts.append(v)
    rs = ring_segments
    for i in range(n):
        for j in range(rs):
            a = i * rs + j
            b = i * rs + (j + 1) % rs
            c = ((i + 1) % n) * rs + (j + 1) % rs
            d = ((i + 1) % n) * rs + j
            tris.append((a, b, c))
            tris.append((a, c, d))
    return verts, tris


# ── 1. Gothic Rose Window ─────────────────────────────────────────────
@_register("RoseWindow_8Petal")
def _rose_window(spec) -> tuple:
    lobes = spec.params.get("lobes", 8)
    outer_r = spec.params.get("outer_r", 280.0)
    inner_r = spec.params.get("inner_r", 60.0)
    petal_r = spec.params.get("petal_r", 90.0)
    tube = spec.params.get("tube", 12.0)
    steps = spec.params.get("steps", 480)

    curve = []
    for i in range(steps):
        t = (TAU * i) / steps
        r_base = outer_r
        petal_angle = (t * lobes) % TAU
        if petal_angle > math.pi:
            petal_angle = TAU - petal_angle
        petal_offset = petal_r * (1.0 - petal_angle / math.pi) * 0.85
        r = inner_r + (outer_r - inner_r) * 0.3 + petal_offset
        ct, st = math.cos(t), math.sin(t)
        curve.append((ct * r, st * r, 0.0))
    return _tube_along_curve(curve, tube, 16)


# ── 2. Quatrefoil Arch ────────────────────────────────────────────────
@_register("Quatrefoil_Arch")
def _quatrefoil_arch(spec) -> tuple:
    width = spec.params.get("width", 400.0)
    height = spec.params.get("height", 600.0)
    tube = spec.params.get("tube", 14.0)
    steps = spec.params.get("steps", 360)
    lobes = spec.params.get("lobes", 4)

    curve = []
    for i in range(steps):
        t = (TAU * i) / steps
        lobe_angle = (t * lobes) % TAU
        # Gothic arch profile with lobed indentations
        arch_t = (i / steps)
        x = width * (arch_t - 0.5) * 2.0
        y = height * math.sin(math.pi * arch_t) * (0.6 + 0.4 * abs(math.cos(lobe_angle)))
        if y > 0:
            r = math.sqrt(x**2 + y**2)
            if r > 1:
                curve.append((x, y, 0.0))
    return _tube_along_curve(curve[:steps//2], tube, 12)


# ── 3. Spiral Staircase ───────────────────────────────────────────────
@_register("Spiral_Staircase")
def _spiral_stairs(spec) -> tuple:
    radius = spec.params.get("radius", 250.0)
    height_total = spec.params.get("height", 800.0)
    steps = spec.params.get("steps", 24)
    step_thick = spec.params.get("step_thick", 12.0)
    step_depth = spec.params.get("step_depth", 120.0)
    turns = spec.params.get("turns", 2.0)

    verts = []
    tris = []
    for i in range(steps):
        t = float(i) / steps
        angle = t * TAU * turns
        z = t * height_total
        ca, sa = math.cos(angle), math.sin(angle)
        inner = (ca * radius * 0.3, sa * radius * 0.3, z)
        outer = (ca * (radius + step_depth), sa * (radius + step_depth), z)
        # Create wedge step
        base = len(verts)
        half = step_thick / 2.0
        for dz in [-half, half]:
            for pt in [inner, outer]:
                verts.append((pt[0], pt[1], pt[2] + dz))
        # Triangles: bottom face
        tris.append((base, base+1, base+2)); tris.append((base, base+2, base+3))
        # Top face
        tris.append((base+4, base+6, base+5)); tris.append((base+4, base+7, base+6))

    return verts, tris


# ── 4. Gothic Tracery Panel ───────────────────────────────────────────
@_register("Gothic_Tracery")
def _gothic_tracery(spec) -> tuple:
    width = spec.params.get("width", 300.0)
    height = spec.params.get("height", 500.0)
    tube = spec.params.get("tube", 8.0)
    divisions = spec.params.get("divisions", 3)
    steps = spec.params.get("steps", 200)

    # Create interlaced gothic arch tracery
    verts = []
    tris = []
    base_v = 0
    for div in range(divisions):
        x_offset = (div - (divisions - 1) / 2.0) * (width / divisions)
        sub_width = width / divisions * 0.8
        sub_height = height * (0.7 + 0.3 * (div % 2))
        curve = []
        for i in range(steps):
            t = (i / steps)
            x = x_offset + sub_width * (t - 0.5) * 2.0
            y = sub_height * math.sin(math.pi * t) * 0.9
            if abs(x - x_offset) < sub_width / 2:
                curve.append((x, y, 0.0))
        if len(curve) > 3:
            v, t = _tube_along_curve(curve, tube, 10)
            for vt in v:
                verts.append(vt)
            for ti in t:
                tris.append((ti[0] + base_v, ti[1] + base_v, ti[2] + base_v))
            base_v += len(v)
    return verts, tris


# ── 5. Column Capital (Corinthian-style) ──────────────────────────────
@_register("Column_Capital")
def _column_capital(spec) -> tuple:
    radius = spec.params.get("radius", 100.0)
    height = spec.params.get("height", 180.0)
    lobes = spec.params.get("lobes", 16)
    steps = spec.params.get("steps", 40)
    ring_seg = spec.params.get("ring_seg", 24)

    verts = []
    tris = []
    base_v = 0
    # Create bell-shaped capital with flared lobes
    for layer in range(steps):
        t = layer / (steps - 1)
        z = t * height
        bell_r = radius * (1.0 + t * t * 1.5)  # Flare outward
        lobe_mod = 1.0 + 0.15 * math.sin(t * math.pi) * math.sin(lobes * t * TAU / 2)
        r = bell_r * lobe_mod
        for j in range(ring_seg):
            a = (TAU * j) / ring_seg
            verts.append((math.cos(a) * r, math.sin(a) * r, z))
    for layer in range(steps - 1):
        for j in range(ring_seg):
            a = layer * ring_seg + j
            b = layer * ring_seg + (j + 1) % ring_seg
            c = (layer + 1) * ring_seg + (j + 1) % ring_seg
            d = (layer + 1) * ring_seg + j
            tris.append((a, b, c)); tris.append((a, c, d))
    return verts, tris


# ── 6. Rosette Medallion ──────────────────────────────────────────────
@_register("Rosette_Medallion")
def _rosette_medallion(spec) -> tuple:
    radius = spec.params.get("radius", 200.0)
    petals = spec.params.get("petals", 12)
    tube = spec.params.get("tube", 6.0)
    detail = spec.params.get("detail", 360)

    curve = []
    for i in range(detail):
        t = (TAU * i) / detail
        petal_angle = (t * petals) % TAU
        petal_r = 1.0 + 0.25 * abs(math.cos(petal_angle * 3)) * (1.0 - abs(petal_angle - math.pi) / math.pi)
        r = radius * petal_r
        curve.append((math.cos(t) * r, math.sin(t) * r, 0.0))
    return _tube_along_curve(curve, tube, 12)


# ── 7. Vaulted Ceiling Ribs ───────────────────────────────────────────
@_register("Vault_Ribs")
def _vault_ribs(spec) -> tuple:
    """Crossing pointed vault ribs + apex ring (kitbash-safe, not a room)."""
    arch_length = spec.params.get("arch_length", 800.0)
    arch_height = spec.params.get("arch_height", 520.0)
    ribs = spec.params.get("ribs", 5)
    tube = spec.params.get("tube", 14.0)
    vault_width = spec.params.get("vault_width", 800.0)
    steps = spec.params.get("steps", 64)

    verts = []
    tris = []
    base_v = 0

    def _add_curve(curve):
        nonlocal base_v
        if len(curve) < 4:
            return
        v, t_ = _tube_along_curve(curve, tube, 10)
        for vt in v:
            verts.append(vt)
        for ti in t_:
            tris.append((ti[0] + base_v, ti[1] + base_v, ti[2] + base_v))
        base_v += len(v)

    # Longitudinal ribs
    for rib in range(ribs):
        x_offset = (rib - (ribs - 1) / 2.0) * (vault_width / max(ribs - 1, 1))
        curve = []
        for i in range(steps):
            t = i / (steps - 1)
            y = arch_length * (t - 0.5)
            z = arch_height * (math.sin(math.pi * t) ** 0.85)
            curve.append((x_offset, y, z))
        _add_curve(curve)

    # Transverse ribs
    for rib in range(ribs):
        y_offset = (rib - (ribs - 1) / 2.0) * (arch_length / max(ribs - 1, 1))
        curve = []
        for i in range(steps):
            t = i / (steps - 1)
            x = vault_width * (t - 0.5)
            z = arch_height * (math.sin(math.pi * t) ** 0.85)
            curve.append((x, y_offset, z))
        _add_curve(curve)

    # Diagonal accents
    for sgn in (-1.0, 1.0):
        curve = []
        for i in range(steps):
            t = i / (steps - 1)
            x = vault_width * 0.9 * (t - 0.5)
            y = sgn * arch_length * 0.9 * (t - 0.5)
            z = arch_height * (math.sin(math.pi * t) ** 0.9) * 1.02
            curve.append((x, y, z))
        _add_curve(curve)

    # Apex boss ring
    boss = []
    for i in range(48):
        a = (TAU * i) / 48
        rr = 60.0 + 12.0 * math.sin(a * 6)
        boss.append((math.cos(a) * rr, math.sin(a) * rr, arch_height + 8.0))
    _add_curve(boss)
    return verts, tris


# ── 8. Crown Molding Profile ──────────────────────────────────────────
@_register("Crown_Molding")
def _crown_molding(spec) -> tuple:
    """Ogee/cyma crown with scallop waves along the run."""
    length = spec.params.get("length", 500.0)
    depth = spec.params.get("depth", 90.0)
    profile_points = spec.params.get("profile_points", 16)
    detail = spec.params.get("detail", 56)

    verts = []
    tris = []
    profile = []
    for i in range(profile_points):
        t = i / (profile_points - 1)
        # Cyma-ish ease
        x = depth * (3 * t * t - 2 * t * t * t)
        z = depth * (0.55 * t + 0.18 * math.sin(t * math.pi))
        profile.append((x, z))
    for i in range(detail + 1):
        y = (i / detail - 0.5) * length
        wave = 1.0 + 0.06 * math.sin((i / detail) * math.pi * 7)
        for px, pz in profile:
            verts.append((px * wave, y, pz))
    for i in range(detail):
        for j in range(profile_points - 1):
            a = i * profile_points + j
            b = i * profile_points + j + 1
            c = (i + 1) * profile_points + j + 1
            d = (i + 1) * profile_points + j
            tris.append((a, b, c))
            tris.append((a, c, d))
    return verts, tris


# ── 9. Filigree Ring ──────────────────────────────────────────────────
@_register("Filigree_Ring")
def _filigree_ring(spec) -> tuple:
    radius = spec.params.get("radius", 300.0)
    tube = spec.params.get("tube", 5.0)
    waves = spec.params.get("waves", 24)
    amplitude = spec.params.get("amplitude", 30.0)
    detail = spec.params.get("detail", 720)

    curve = []
    for i in range(detail):
        t = (TAU * i) / detail
        wave_offset = amplitude * math.sin(t * waves)
        r = radius + wave_offset
        z = amplitude * 0.3 * math.cos(t * waves * 2)
        curve.append((math.cos(t) * r, math.sin(t) * r, z))
    return _tube_along_curve(curve, tube, 8)


# ── 10. Corbel Bracket ────────────────────────────────────────────────
@_register("Corbel_Bracket")
def _corbel_bracket(spec) -> tuple:
    width = spec.params.get("width", 100.0)
    height = spec.params.get("height", 200.0)
    depth = spec.params.get("depth", 150.0)
    detail = spec.params.get("detail", 30)

    verts = []
    tris = []
    # S-curve profile swept with width
    profile = []
    for i in range(detail):
        t = i / (detail - 1)
        x = depth * t
        z = height * (math.sin(t * math.pi * 0.5) * 0.8 + t * 0.2)
        profile.append((x, z))
    half_w = width / 2.0
    for i in range(len(profile)):
        px, pz = profile[i]
        verts.append((px, -half_w, pz))
        verts.append((px, half_w, pz))
    n = len(profile)
    for i in range(n - 1):
        a, b = i * 2, i * 2 + 1
        c, d = (i + 1) * 2, (i + 1) * 2 + 1
        tris.append((a, b, c)); tris.append((b, d, c))
    return verts, tris


# ── 11. Door Archway (Gothic) ─────────────────────────────────────────
@_register("Door_Archway")
def _door_archway(spec) -> tuple:
    width = spec.params.get("width", 300.0)
    height_pillar = spec.params.get("height_pillar", 400.0)
    arch_radius = spec.params.get("arch_radius", 150.0)
    tube = spec.params.get("tube", 15.0)
    detail = spec.params.get("detail", 200)

    verts = []
    tris = []
    base_v = 0
    # Left pillar
    left_curve = [( -width/2, y, 0) for y in [i/50.0*height_pillar for i in range(51)]]
    v, t_ = _tube_along_curve(left_curve, tube, 12)
    for vt in v: verts.append(vt)
    for ti in t_: tris.append((ti[0], ti[1], ti[2]))
    base_v += len(v)
    # Right pillar
    right_curve = [(width/2, y, 0) for y in [i/50.0*height_pillar for i in range(51)]]
    v, t_ = _tube_along_curve(right_curve, tube, 12)
    for vt in v: verts.append(vt)
    for ti in t_: tris.append((ti[0]+base_v, ti[1]+base_v, ti[2]+base_v))
    base_v += len(v)
    # Pointed arch
    arch_curve = []
    for i in range(detail):
        t = (i / (detail - 1) - 0.5) * 2.0  # -1 to 1
        x = width/2 * t
        r = arch_radius * 1.2
        if abs(t) < 0.95:
            y = height_pillar + r * math.sqrt(max(0, 1 - t*t)) * 0.85
            arch_curve.append((x, y, 0.0))
    if len(arch_curve) > 3:
        v, t_ = _tube_along_curve(arch_curve, tube, 12)
        for vt in v: verts.append(vt)
        for ti in t_: tris.append((ti[0]+base_v, ti[1]+base_v, ti[2]+base_v))
    return verts, tris


# ── 12. Torus Knot Ornament ───────────────────────────────────────────
@_register("TorusKnot_Ornament")
def _torus_knot_ornament(spec) -> tuple:
    p = spec.params.get("p", 3)
    q = spec.params.get("q", 2)
    R = spec.params.get("R", 200.0)
    r = spec.params.get("r", 50.0)
    tube = spec.params.get("tube", 8.0)
    samples = spec.params.get("samples", 360)

    curve = []
    for i in range(samples):
        t = (TAU * i) / samples
        x = (R + r * math.cos(q * t)) * math.cos(p * t)
        y = (R + r * math.cos(q * t)) * math.sin(p * t)
        z = r * math.sin(q * t)
        curve.append((x, y, z))
    return _tube_along_curve(curve, tube, 8)


# ── 13. Oculus Frame ──────────────────────────────────────────────────
@_register("Oculus_Frame")
def _oculus_frame(spec) -> tuple:
    radius = spec.params.get("radius", 250.0)
    tube = spec.params.get("tube", 15.0)
    petals = spec.params.get("petals", 16)
    detail = spec.params.get("detail", 480)

    curve = []
    for i in range(detail):
        t = (TAU * i) / detail
        petal_mod = 1.0 + 0.12 * abs(math.sin(petals * t / 2))
        r = radius * petal_mod
        z = radius * 0.08 * math.sin(petals * t)
        curve.append((math.cos(t) * r, math.sin(t) * r, z))
    return _tube_along_curve(curve, tube, 16)


# ── 14. Pendant Finial ────────────────────────────────────────────────
@_register("Pendant_Finial")
def _pendant_finial(spec) -> tuple:
    height = spec.params.get("height", 300.0)
    base_radius = spec.params.get("base_radius", 50.0)
    tip_radius = spec.params.get("tip_radius", 3.0)
    rings = spec.params.get("rings", 30)
    ring_seg = spec.params.get("ring_seg", 20)

    verts = []
    tris = []
    for layer in range(rings):
        t = layer / (rings - 1)
        z = t * height
        r = base_radius * (1.0 - t) ** 1.5 + tip_radius * t
        if layer % 5 == 0:
            r *= 1.25  # Decorative ridge
        for j in range(ring_seg):
            a = (TAU * j) / ring_seg
            verts.append((math.cos(a) * r, math.sin(a) * r, z))
    for layer in range(rings - 1):
        for j in range(ring_seg):
            a = layer * ring_seg + j
            b = layer * ring_seg + (j + 1) % ring_seg
            c = (layer + 1) * ring_seg + (j + 1) % ring_seg
            d = (layer + 1) * ring_seg + j
            tris.append((a, b, c)); tris.append((a, c, d))
    return verts, tris


# ── 15. Woven Ring ────────────────────────────────────────────────────
@_register("Woven_Ring")
def _woven_ring(spec) -> tuple:
    radius = spec.params.get("radius", 280.0)
    tube = spec.params.get("tube", 5.0)
    strands = spec.params.get("strands", 3)
    weave_freq = spec.params.get("weave_freq", 18)
    detail = spec.params.get("detail", 540)

    verts = []
    tris = []
    base_v = 0
    for strand in range(strands):
        phase = TAU * strand / strands
        curve = []
        for i in range(detail):
            t = (TAU * i) / detail
            a = t + phase
            r_offset = radius + tube * 3 * math.sin(weave_freq * t + phase)
            z_offset = tube * 2 * math.cos(weave_freq * t + phase)
            curve.append((math.cos(a) * r_offset, math.sin(a) * r_offset, z_offset))
        v, t_ = _tube_along_curve(curve, tube, 8)
        for vt in v: verts.append(vt)
        for ti in t_: tris.append((ti[0]+base_v, ti[1]+base_v, ti[2]+base_v))
        base_v += len(v)
    return verts, tris


# ═══════════════════════════════════════════════════════════════════════
# STRUCTURE SPECS
# ═══════════════════════════════════════════════════════════════════════

STRUCTURES: dict[str, StructureSpec] = {
    "RoseWindow_8Petal": StructureSpec("RoseWindow_8Petal", "SM_Orn_RoseWindow_8Petal", "SpaceCathedral",
        "Gothic rose window with 8 petal lobes", {"lobes": 8, "outer_r": 280.0, "inner_r": 60.0, "petal_r": 90.0, "tube": 12.0}, run_group=1),
    "Quatrefoil_Arch": StructureSpec("Quatrefoil_Arch", "SM_Orn_QuatrefoilArch", "BaroqueGrotto",
        "Gothic quatrefoil archway with lobed indentations", {"width": 400.0, "height": 600.0, "tube": 14.0, "lobes": 4}, run_group=1),
    "Spiral_Staircase": StructureSpec("Spiral_Staircase", "SM_Orn_SpiralStaircase", "SpaceCathedral",
        "Spiral staircase with 24 steps, 2 turns", {"radius": 250.0, "height": 800.0, "steps": 24, "step_depth": 120.0, "turns": 2.0}, run_group=1),
    "Gothic_Tracery": StructureSpec("Gothic_Tracery", "SM_Orn_GothicTracery", "SpaceCathedral",
        "Interlaced gothic tracery panel with 3 divisions", {"width": 300.0, "height": 500.0, "tube": 8.0, "divisions": 3}, run_group=1),
    "Column_Capital": StructureSpec("Column_Capital", "SM_Orn_ColumnCapital", "BaroqueGrotto",
        "Corinthian-style bell capital with flared lobes", {"radius": 100.0, "height": 180.0, "lobes": 16}, run_group=2),
    "Rosette_Medallion": StructureSpec("Rosette_Medallion", "SM_Orn_RosetteMedallion", "SpaceCathedral",
        "Circular rosette with 12 overlapping petals", {"radius": 200.0, "petals": 12, "tube": 6.0}, run_group=2),
    "Vault_Ribs": StructureSpec("Vault_Ribs", "SM_Orn_VaultRibs", "SpaceCathedral",
        "Gothic vaulted ceiling ribs with 6 arches", {"arch_length": 800.0, "arch_height": 500.0, "ribs": 6, "tube": 10.0, "vault_width": 600.0}, run_group=2),
    "Crown_Molding": StructureSpec("Crown_Molding", "SM_Orn_CrownMolding", "BaroqueGrotto",
        "Swept crown molding with compound profile curves", {"length": 400.0, "depth": 80.0, "profile_points": 12}, run_group=2),
    "Filigree_Ring": StructureSpec("Filigree_Ring", "SM_Orn_FiligreeRing", "BaroqueGrotto",
        "Decorative filigree ring with 24 wave modulations", {"radius": 300.0, "tube": 5.0, "waves": 24, "amplitude": 30.0}, run_group=3),
    "Corbel_Bracket": StructureSpec("Corbel_Bracket", "SM_Orn_CorbelBracket", "BaroqueGrotto",
        "S-curve corbel bracket for wall support", {"width": 100.0, "height": 200.0, "depth": 150.0}, run_group=3),
    "Door_Archway": StructureSpec("Door_Archway", "SM_Orn_DoorArchway", "BaroqueGrotto",
        "Gothic pointed arch door frame with pillars", {"width": 300.0, "height_pillar": 400.0, "arch_radius": 150.0, "tube": 15.0}, run_group=3),
    "TorusKnot_Ornament": StructureSpec("TorusKnot_Ornament", "SM_Orn_TorusKnot", "CosmicOrrery",
        "Small ornamental torus knot for surface decoration", {"p": 3, "q": 2, "R": 200.0, "r": 50.0, "tube": 8.0}, run_group=3),
    "Oculus_Frame": StructureSpec("Oculus_Frame", "SM_Orn_OculusFrame", "SpaceCathedral",
        "Circular oculus window frame with petal modulation", {"radius": 250.0, "tube": 15.0, "petals": 16}, run_group=4),
    "Pendant_Finial": StructureSpec("Pendant_Finial", "SM_Orn_PendantFinial", "BaroqueGrotto",
        "Hanging pendant finial with decorative ridges", {"height": 300.0, "base_radius": 50.0, "tip_radius": 3.0, "rings": 30}, run_group=4),
    "Woven_Ring": StructureSpec("Woven_Ring", "SM_Orn_WovenRing", "CosmicOrrery",
        "3-strand braided woven ring for orbital decoration", {"radius": 280.0, "tube": 5.0, "strands": 3, "weave_freq": 18}, run_group=4),
}


# ═══════════════════════════════════════════════════════════════════════
# BAKE ENGINE
# ═══════════════════════════════════════════════════════════════════════

def _ensure_dirs(unreal, *paths: str) -> None:
    for path in paths:
        if not unreal.EditorAssetLibrary.does_directory_exist(path):
            unreal.EditorAssetLibrary.make_directory(path)


def _mesh_basic_edit_api(unreal):
    """Resolve GeometryScript mesh edit module."""
    for name in dir(unreal):
        if "basicedit" not in name.lower():
            continue
        mod = getattr(unreal, name)
        if hasattr(mod, "append_buffers_to_mesh"):
            return mod
    for name in ("GeometryScript_MeshBasicEdit", "GeometryScript_MeshBasicEditFunctions", "GeometryScript_MeshEdits"):
        if hasattr(unreal, name):
            mod = getattr(unreal, name)
            if hasattr(mod, "append_buffers_to_mesh"):
                return mod
    raise AttributeError("GeometryScript append_buffers_to_mesh API not found")


def _finalize_static_mesh(unreal, dm, asset_path: str) -> dict:
    unreal.GeometryScript_Normals.recompute_normals(dm, unreal.GeometryScriptCalculateNormalsOptions())
    out = unreal.GeometryScriptCreateNewStaticMeshAssetOptions()
    unreal.GeometryScript_NewAssetUtils.create_new_static_mesh_asset_from_mesh(dm, asset_path, out)
    unreal.EditorAssetLibrary.save_asset(asset_path, only_if_is_dirty=False)
    return {"status": "created"}


def _bake_structure(spec: StructureSpec) -> dict:
    import unreal

    if spec.key not in BUILDERS:
        return {"key": spec.key, "status": "no_builder", "asset_path": spec.asset_path}

    path = f"{spec.asset_path}.{spec.asset_name}"
    if unreal.EditorAssetLibrary.does_asset_exist(path):
        return {"key": spec.key, "status": "exists", "asset_path": spec.asset_path}

    if not unreal.EditorAssetLibrary.does_directory_exist(ORNAMENT_DIR):
        unreal.EditorAssetLibrary.make_directory(ORNAMENT_DIR)

    builder = BUILDERS[spec.key]
    verts, tris = builder(spec)

    if not verts or not tris:
        return {"key": spec.key, "status": "empty", "asset_path": spec.asset_path}

    dm = unreal.new_object(unreal.DynamicMesh)
    gsb = _mesh_basic_edit_api(unreal)
    buffers = unreal.GeometryScriptSimpleMeshBuffers()
    buffers.vertices = [unreal.Vector(x, y, z) for x, y, z in verts]
    buffers.triangles = [unreal.IntVector(a, b, c) for a, b, c in tris]
    buffers.uv0 = [unreal.Vector2D(0.0, 0.0) for _ in verts]
    gsb.append_buffers_to_mesh(dm, buffers, 0, False)

    unreal.GeometryScript_Normals.recompute_normals(dm, unreal.GeometryScriptCalculateNormalsOptions())
    out = unreal.GeometryScriptCreateNewStaticMeshAssetOptions()
    unreal.GeometryScript_NewAssetUtils.create_new_static_mesh_asset_from_mesh(dm, spec.asset_path, out)
    unreal.EditorAssetLibrary.save_asset(spec.asset_path, only_if_is_dirty=False)

    return {
        "key": spec.key,
        "status": "created",
        "asset_path": spec.asset_path,
        "vertex_count": len(verts),
        "triangle_count": len(tris),
    }


def build_all(run_group: int | None = None) -> list[dict]:
    results = []
    for key, spec in STRUCTURES.items():
        if run_group is not None and spec.run_group != run_group:
            continue
        result = _bake_structure(spec)
        results.append(result)
        print(f"[Ornament] {result['status']}: {spec.asset_name} ({result.get('triangle_count', 0)} tris)")
    return results


def main() -> int:
    import unreal

    rg = None
    run_all = "--all" in sys.argv
    for i, arg in enumerate(sys.argv):
        if arg == "--run" and i + 1 < len(sys.argv):
            rg = int(sys.argv[i + 1])
    if run_all:
        rg = None

    unreal.log("=== Ornamental Mesh Generator ===")
    results = build_all(rg)

    report = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "run_group": rg,
        "results": results,
        "created": len([r for r in results if r["status"] == "created"]),
        "existed": len([r for r in results if r["status"] == "exists"]),
    }

    AUDIT_PATH.parent.mkdir(parents=True, exist_ok=True)
    AUDIT_PATH.write_text(json.dumps(report, indent=2, ensure_ascii=False, default=str), encoding="utf-8")

    unreal.EditorLoadingAndSavingUtils.save_dirty_packages(True, True)
    unreal.log(f"[Ornament] {report['created']} new, {report['existed']} existing -> {AUDIT_PATH}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
