"""THE JELLYFISH V3 — "SERAPH": tiered, angelic, feminine, horrifying.

Deep-sea cathedral above the reef. Design contract with the owner ask:
  - surreal TIERS (three stacked veil tiers, floating)
  - LOBES everywhere, but MATHEMATICALLY PERFECT: tier radii step by the
    golden ratio (phi = 1.618), lobe counts are Fibonacci (21 / 13 / 8),
    arms are placed on the golden angle (137.507 deg phyllotaxis), and the
    cilia crown has 55 filaments (Fibonacci).
  - ANGELIC: a detached halo ring above the crown tier.
  - FEMININE: ogee dome profile (fuller, softer silhouette), graceful thin
    long arms.
  - HORRIFYING: 190 m bell, 13 x 640 m arms, and a 55-filament cilia fringe
    (the Atolla "burglar alarm" crown, scaled to a nightmare).

ENGINE CONTRACT (unchanged from v1/v2 — do not break):
  - same 4 pose names (Neutral / PulseContract / PulseExpand / SurrealLurch)
    generated from one code path per mesh; every static mesh (tiers, halo,
    cilia) carries the pose set; topology identical across poses per mesh.
  - arm uv.y normalized along length -> existing T_Jelly_ArmLogic_LUT /
    T_Jelly_Biolum_LUT drive v3 arms unchanged.
  - v1/v2 files untouched; new output names.

Outputs (Saved/Audit/sea_above/meshes/):
  jellyfish_mesh_v3_seraph.json + jellyfish_mesh_v3_seraph_manifest.json

Run (isolated console):
  & "C:\\Program Files\\Side Effects Software\\Houdini 22.0.368\\bin\\hython.exe" ^
      Tools/Houdini/sea_above_reef/build_jellyfish_v3_seraph.py
"""

import json
import math
from pathlib import Path

import hou

sys_path = Path(__file__).resolve().parent
import sys
sys.path.insert(0, str(sys_path))
from build_jellyfish import _cook_report, _dump_geo  # noqa: E402

PROJECT_ROOT = Path(__file__).resolve().parents[3]
OUT_DIR = PROJECT_ROOT / "Saved" / "Audit" / "sea_above" / "meshes"

SEED_V3 = 20260829
PHI = (1.0 + math.sqrt(5.0)) / 2.0
GOLDEN_ANGLE = math.radians(137.50776405003785)

BELL_R = 95.0                    # main dome radius -> 190 m diameter
TIER_RADII = [BELL_R, BELL_R / PHI, BELL_R / (PHI * PHI)]   # 95 / 58.7 / 36.3
TIER_LOBES = [21, 13, 8]         # Fibonacci
TIER_SEG = [168, 128, 96]
TIER_RINGS = [26, 20, 16]
HALO_R = TIER_RADII[2] * 1.12
HALO_SEG = 144
CILIA_COUNT = 55                 # Fibonacci
CILIA_LEN = 14.0
N_ARMS = 13                      # Fibonacci
ARM_LENGTH = 640.0
ARM_ROWS, ARM_COLS, ARM_WIDTH = 360, 7, 5.0   # thinner, longer (feminine)

CODE = r"""
import hou, math, random

node = hou.pwd()
geo = node.geometry()
if geo.findPointAttrib("uv") is None:
    geo.addAttrib(hou.attribType.Point, "uv", (0.0, 0.0))

V = hou.Vector3

def _rot(v, axis, ang):
    c = math.cos(ang); s = math.sin(ang)
    a = axis.normalized()
    return v * c + a.cross(v) * s + a * (a.dot(v) * (1.0 - c))

MODE = __MODE__
SEED = __SEED__
POSE = __POSE__
rng = random.Random(SEED + hash(MODE) % 1000)

PHI = (1.0 + math.sqrt(5.0)) / 2.0

def ogee(phi_n, h):
    # feminine dome profile: fuller shoulder, soft crown
    return h * (math.sin(phi_n * math.pi * 0.5) ** 0.8)

def tier_dome():
    # params: __R__ radius, __LOBES__, __SEG__, __RINGS__, __TIER_Y__, __DOME_H__
    R = __R__; LOBES = __LOBES__; SEG = __SEG__; RINGS = __RINGS__
    TIER_Y = __TIER_Y__; DOME_H = __DOME_H__
    rows = []
    for j in range(RINGS + 1):
        phi_n = j / RINGS
        phi = phi_n * (math.pi * 0.55)
        row = []
        for i in range(SEG):
            th = i / SEG * 2.0 * math.pi
            lobed = 1.0 + 0.06 * math.cos(th * LOBES) * (phi_n ** 1.5)
            rr = R * math.sin(phi) * lobed
            y = TIER_Y + ogee(phi_n, DOME_H)
            if POSE == "PulseContract":
                rr *= 0.86; y -= DOME_H * 0.14 * (phi_n ** 2)
            elif POSE == "PulseExpand":
                rr *= 1.10; y += DOME_H * 0.08 * (phi_n ** 2)
            elif POSE == "SurrealLurch":
                lurch = 0.5 + 0.5 * math.sin(th * 3.0 + 0.8)
                rr *= (0.76 + 0.30 * lurch)
                y += DOME_H * (0.10 * lurch - 0.05) * (phi_n ** 2)
            fold = 0.035 * math.sin(5.0 * th + 2.0) + 0.024 * math.sin(9.0 * th * (1 + 0.2 * math.sin(phi_n * 3.0)))
            rr *= (1.0 + fold * phi_n)
            p = geo.createPoint()
            p.setPosition(V(rr * math.cos(th), y, rr * math.sin(th)))
            p.setAttribValue(geo.findPointAttrib("uv"), (i / SEG, 1.0 - phi_n))
            row.append(p)
        rows.append(row)
    for j in range(RINGS):
        for i in range(SEG):
            f = geo.createPolygon()
            for q in (rows[j][i], rows[j][(i + 1) % SEG],
                      rows[j + 1][(i + 1) % SEG], rows[j + 1][i]):
                f.addVertex(q)

def halo_ring():
    # params: __R__, __SEG__, __TIER_Y__ — a detached angelic halo
    R = __R__; SEG = __SEG__; TIER_Y = __TIER_Y__
    rows = []
    for j in range(3):
        row = []
        rr = R * (1.0 + (j - 1) * 0.012)
        for i in range(SEG):
            th = i / SEG * 2.0 * math.pi
            y = TIER_Y + 0.35 * math.sin(th * 3.0) * (POSE == "SurrealLurch")
            p = geo.createPoint()
            p.setPosition(V(rr * math.cos(th), y, rr * math.sin(th)))
            p.setAttribValue(geo.findPointAttrib("uv"), (i / SEG, j / 2.0))
            row.append(p)
        rows.append(row)
    for j in range(2):
        for i in range(SEG):
            f = geo.createPolygon()
            for q in (rows[j][i], rows[j][(i + 1) % SEG],
                      rows[j + 1][(i + 1) % SEG], rows[j + 1][i]):
                f.addVertex(q)

def cilium():
    # params: __R__, __COUNT__, __LEN__, __TIER_Y__ — the cilia crown fringe
    R = __R__; COUNT = __COUNT__; LEN = __LEN__; TIER_Y = __TIER_Y__
    ROWS, COLS = 26, 3
    idx = __CIL_INDEX__
    rng2 = random.Random(SEED + 900 + idx)
    a0 = idx / COUNT * 2.0 * math.pi
    ph = rng2.uniform(0, 6.28)
    rows = []
    for i in range(ROWS + 1):
        s = i / ROWS
        rr = R * 0.985 - LEN * s * 0.12
        fall = -s * LEN
        sway = math.sin(a0 * 2.0 + s * 4.0 + ph) * LEN * 0.08 * s
        x = rr * math.cos(a0) + sway * math.cos(a0 + 1.57)
        z = rr * math.sin(a0) + sway * math.sin(a0 + 1.57)
        y = TIER_Y + fall
        if POSE == "PulseContract":
            y += LEN * 0.18 * s
        elif POSE == "PulseExpand":
            y -= LEN * 0.10 * s
        elif POSE == "SurrealLurch":
            sway *= 2.4
            x = rr * math.cos(a0) + sway * math.cos(a0 + 1.57)
            z = rr * math.sin(a0) + sway * math.sin(a0 + 1.57)
        rows.append((x, y, z, s))
    grid = []
    for (x, y, z, s) in rows:
        w = 0.9 * (1.0 - 0.55 * s)
        row = []
        for k in range(COLS + 1):
            u = k / COLS - 0.5
            p = geo.createPoint()
            p.setPosition(V(x + w * u * math.cos(a0 + 1.57),
                            y,
                            z + w * u * math.sin(a0 + 1.57)))
            p.setAttribValue(geo.findPointAttrib("uv"), (u + 0.5, s))
            row.append(p)
        grid.append(row)
    for i in range(ROWS):
        for k in range(COLS):
            f = geo.createPolygon()
            for q in (grid[i][k], grid[i][k + 1], grid[i + 1][k + 1], grid[i + 1][k]):
                f.addVertex(q)

def arm_phyllo():
    # golden-angle placed arm, double bifurcation, 1.5pi twist, stronger rise
    ARM_INDEX = __ARM_INDEX__
    N_ARMS = __N_ARMS__
    LENGTH = __LENGTH__
    ROWS, COLS = __ROWS__, __COLS__
    WIDTH = __WIDTH__
    R = __R__
    rng2 = random.Random(SEED + 500 + ARM_INDEX)
    a0 = ARM_INDEX * __GOLDEN_ANGLE__
    ph = rng2.uniform(0, 6.28)
    pts = []
    for i in range(ROWS + 1):
        s = i / ROWS
        r = 0.92 * R + LENGTH * s * 0.55 * (0.4 + 0.6 * s)
        fall = -math.sin(min(1.0, s * 1.6) * math.pi * 0.5) * LENGTH * 0.34
        rise = max(0.0, s - 0.55) ** 1.6 * LENGTH * 0.42
        spiral = math.sin(a0 * 3.0 + s * 5.0 + ph) * LENGTH * 0.05 * s
        x = r * math.cos(a0) + spiral * math.cos(a0 + 1.57)
        z = r * math.sin(a0) + spiral * math.sin(a0 + 1.57)
        y = fall + rise
        drift = 0.0
        for _bs in (0.5, 0.72):
            if s > _bs:
                drift += (1.0 if (int(_bs * 100) + ARM_INDEX) % 2 == 0 else -1.0) * (s - _bs) * 2.0 * LENGTH * 0.05
        x += drift * math.cos(a0 + 1.57)
        z += drift * math.sin(a0 + 1.57)
        pts.append(V(x, y, z))
    grid = []
    for i, pos in enumerate(pts):
        s = i / ROWS
        if i == 0:
            tan = pts[1] - pts[0]
        elif i == ROWS:
            tan = pts[-1] - pts[-2]
        else:
            tan = pts[i + 1] - pts[i - 1]
        tan = tan.normalized()
        up = V(0, 1, 0)
        if abs(tan.dot(up)) > 0.95:
            up = V(1, 0, 0)
        x1 = tan.cross(up).normalized()
        y1 = tan.cross(x1).normalized()
        twist = math.pi * 1.5 * s
        x2 = _rot(x1, tan, twist)
        y2 = _rot(y1, tan, twist)
        w = WIDTH * (0.3 + 0.7 * math.sin(math.pi * min(1.0, 0.12 + 0.88 * s))) \
            * (1.0 - 0.4 * s)
        row = []
        for k in range(COLS + 1):
            u = k / COLS - 0.5
            cup = (u * u * 4.0 - 1.0) * WIDTH * 0.10
            off = x2 * (w * u) + y2 * cup
            p = geo.createPoint()
            p.setPosition(pos + off)
            p.setAttribValue(geo.findPointAttrib("uv"), (u + 0.5, s))
            row.append(p)
        grid.append(row)
    for i in range(ROWS):
        for k in range(COLS):
            f = geo.createPolygon()
            for q in (grid[i][k], grid[i][k + 1], grid[i + 1][k + 1], grid[i + 1][k]):
                f.addVertex(q)

if MODE == "tier":
    tier_dome()
elif MODE == "halo":
    halo_ring()
elif MODE == "cilium":
    cilium()
else:
    arm_phyllo()
try:
    geo.computeVertexNormals()
except Exception:
    pass
"""


def _inject(code, **params):
    for key, value in params.items():
        code = code.replace(f"__{key}__", repr(value))
    return code


def _fix_seed(code, seed):
    return code.replace("random.Random(SEED + hash(MODE) % 1000)",
                        f"random.Random({seed} + hash(MODE) % 1000)")


def main():
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    obj = hou.node("/obj")
    payload = {"schema": "melodia.jellyfish.v1", "variant": "v3_seraph",
               "seed": SEED_V3, "scale": "metres; UE import x100",
               "static_parts": {}, "arms": []}

    # ---- static assembly (tiers + halo + cilia), each with the 4-pose set ----
    static_specs = []
    for ti, (R, LOBES, SEG, RINGS) in enumerate(zip(TIER_RADII, TIER_LOBES, TIER_SEG, TIER_RINGS)):
        static_specs.append((f"tier_{ti}", "tier",
                             dict(R=R, LOBES=LOBES, SEG=SEG, RINGS=RINGS,
                                  TIER_Y=ti * BELL_R * 0.34, DOME_H=BELL_R * 0.30)))
    static_specs.append(("halo", "halo",
                         dict(R=HALO_R, SEG=HALO_SEG, TIER_Y=2 * BELL_R * 0.34 + BELL_R * 0.30)))
    for ci in range(CILIA_COUNT):
        static_specs.append((f"cilium_{ci:02d}", "cilium",
                             dict(R=TIER_RADII[0], COUNT=CILIA_COUNT, LEN=CILIA_LEN,
                                  TIER_Y=0.0, CIL_INDEX=ci)))

    pose_names = ["Neutral", "PulseContract", "PulseExpand", "SurrealLurch"]
    for part_name, mode, params in static_specs:
        data_by_pose = {}
        ok = True
        for pose in pose_names:
            for old in [n for n in obj.children() if n.name() == f"SERAPH_{part_name}"]:
                old.destroy()
            g = obj.createNode("geo", f"SERAPH_{part_name}", run_init_scripts=True)
            py = g.createNode("python", "gen")
            code = _inject(CODE, MODE=mode, SEED=SEED_V3, POSE=pose,
                           GOLDEN_ANGLE=GOLDEN_ANGLE, **params)
            code = _fix_seed(code, SEED_V3)
            py.parm("python").set(code)
            if not _cook_report(py, f"{part_name}:{pose}"):
                ok = False
                g.destroy()
                break
            data_by_pose[pose] = _dump_geo(py.geometry())
            g.destroy()
        if not ok:
            continue
        base = data_by_pose["Neutral"]
        poses_out = {}
        for pose in pose_names[1:]:
            same = len(data_by_pose[pose]["points"]) == len(base["points"])
            poses_out[pose] = {"points": data_by_pose[pose]["points"],
                               "topology_matches": same}
            if not same:
                print(f"[seraph] WARNING: {part_name} pose {pose} topology mismatch!")
        payload["static_parts"][part_name] = {
            "mesh": base, "poses": poses_out,
            "kind": mode, "params": {k: v for k, v in params.items() if not isinstance(v, float)}
        }
        print(f"[seraph] {part_name}: {len(base['points'])} pts "
              f"({len(base['faces'])} faces), {len(pose_names)-1} pose deltas")

    # ---- arms: 13 golden-angle ribbons ----
    for arm_i in range(N_ARMS):
        for old in [n for n in obj.children() if n.name() == f"SERAPH_ARM_{arm_i}"]:
            old.destroy()
        ga = obj.createNode("geo", f"SERAPH_ARM_{arm_i}", run_init_scripts=True)
        pya = ga.createNode("python", "gen_arm")
        ca = _inject(CODE, MODE="arm", SEED=SEED_V3, POSE="Neutral", R=BELL_R,
                     ARM_INDEX=arm_i, N_ARMS=N_ARMS, LENGTH=ARM_LENGTH,
                     ROWS=ARM_ROWS, COLS=ARM_COLS, WIDTH=ARM_WIDTH,
                     GOLDEN_ANGLE=GOLDEN_ANGLE)
        ca = _fix_seed(ca, SEED_V3)
        pya.parm("python").set(ca)
        if not _cook_report(pya, f"arm:{arm_i}"):
            ga.destroy()
            continue
        payload["arms"].append(_dump_geo(pya.geometry()))
        print(f"[seraph] arm {arm_i}: {len(payload['arms'][-1]['points'])} pts")
        ga.destroy()

    payload["meta"] = {
        "n_arms": N_ARMS, "arm_length_m": ARM_LENGTH,
        "football_fields_per_arm": round(ARM_LENGTH / 91.44, 2),
        "bell_main_diameter_m": TIER_RADII[0] * 2,
        "tier_radii_m": [round(r, 2) for r in TIER_RADII],
        "tier_lobes_fibonacci": TIER_LOBES,
        "halo_radius_m": round(HALO_R, 2),
        "cilia_count_fibonacci": CILIA_COUNT,
        "arms_placement": "golden angle 137.507deg phyllotaxis",
        "surreal_logic": ["three floating veil tiers (golden-ratio radii)",
                          "Fibonacci lobe cascade 21/13/8",
                          "detached halo ring",
                          "55-filament cilia crown (deep-sea burglar alarm)",
                          "double bifurcation + 1.5pi twist + strong rise",
                          "LUT time-loop per jelly_surreal_lut.py (unchanged)"],
    }

    out = OUT_DIR / "jellyfish_mesh_v3_seraph.json"
    out.write_text(json.dumps(payload, separators=(",", ":")), encoding="utf-8")
    print(f"[seraph] wrote {out.name} ({out.stat().st_size} bytes)")

    manifest = {
        "schema": "melodia.sea_above_reef_meshes.v1",
        "kind": "jellyfish R6 v3 SERAPH: tiered angelic deep-sea cathedral",
        "variant": "v3_seraph", "seed": SEED_V3,
        "hython": hou.applicationVersionString(),
        "mesh_json": str(out),
        "pose_names": pose_names,
        "engine_contract": "pose names + uv layout compatible with v1/v2 wiring; "
                           "LUTs remain valid (uv.y normalized)",
        "ue_import": {"scale": "100x (m -> cm)",
                      "static_parts": "skeletal (root bone) with 4 shape keys each",
                      "arms": "static Nanite; existing LUT recipe"},
        "entries": [{"name": "v3_seraph", "json_bytes": out.stat().st_size}],
    }
    (OUT_DIR / "jellyfish_mesh_v3_seraph_manifest.json").write_text(
        json.dumps(manifest, indent=2), encoding="utf-8")
    print("[seraph] manifest -> jellyfish_mesh_v3_seraph_manifest.json")


if __name__ == "__main__":
    main()
