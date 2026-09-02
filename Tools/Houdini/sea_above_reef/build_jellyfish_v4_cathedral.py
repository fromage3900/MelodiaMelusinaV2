"""THE JELLYFISH V4 — "CATHEDRAL": surreal architecture + cascading ribbons.

Builds on v3 SERAPH (tiers / halo / cilia / golden-angle arms — all kept) and adds:

  ARCHES (8, Fibonacci): flying-buttress arcs sweeping from the main-dome margin
    down-and-out to a lower outer ring — cathedral architecture at 190 m scale.
  SPIRE (1): a slender helix ribbon rising through the halo, 1.25 turns,
    tapering to a point — the impossible steeple.
  CASCADES (5, Fibonacci): fountain ribbons that fall in three stages with
    spreading "pools" at each plateau — ribbons that pour like tiered waterfalls
    and never touch the sea.
  DRAPES (21, Fibonacci): short curtain veils hanging between the cilia of the
    main margin, scalloped hems, gentle sway.

MATH CONTRACT (owner ask: "mathematically perfect, yet strange"):
  golden ratio radii, Fibonacci counts (8 arches / 5 cascades / 21 drapes /
  13 arms / 55 cilia / 21-13-8 lobes), golden-angle placement for arms and
  cascades. Architecture counts stay Fibonacci; arch spacing stays symmetric
  (buildings want axis), the living parts stay phyllotactic (life wants golden).

ENGINE CONTRACT (unchanged): same 4 pose names on every static part, uv.y
normalized arms (existing LUTs valid), v1/v2/v3 files untouched.

Outputs: jellyfish_mesh_v4_cathedral.json + manifest (same schema as v3).

Run (isolated console):
  & "C:\\Program Files\\Side Effects Software\\Houdini 22.0.368\\bin\\hython.exe" ^
      Tools/Houdini/sea_above_reef/build_jellyfish_v4_cathedral.py
"""

import json
import math
import sys
from pathlib import Path

import hou

sys.path.insert(0, str(Path(__file__).resolve().parent))
from build_jellyfish import _cook_report, _dump_geo  # noqa: E402
import build_jellyfish_v3_seraph as v3  # noqa: E402

PROJECT_ROOT = Path(__file__).resolve().parents[3]
OUT_DIR = PROJECT_ROOT / "Saved" / "Audit" / "sea_above" / "meshes"

SEED_V4 = 20260829
PHI = v3.PHI
GOLDEN_ANGLE = v3.GOLDEN_ANGLE

# v3 geometry constants (imported where possible)
BELL_R = v3.BELL_R
TIER_RADII = v3.TIER_RADII
TIER_LOBES = v3.TIER_LOBES
TIER_SEG = v3.TIER_SEG
TIER_RINGS = v3.TIER_RINGS
HALO_R = v3.HALO_R
HALO_SEG = v3.HALO_SEG
CILIA_COUNT = v3.CILIA_COUNT
CILIA_LEN = v3.CILIA_LEN
N_ARMS = v3.N_ARMS
ARM_LENGTH = v3.ARM_LENGTH
ARM_ROWS, ARM_COLS, ARM_WIDTH = v3.ARM_ROWS, v3.ARM_COLS, v3.ARM_WIDTH

# v4 additions
N_ARCHES = 8                    # Fibonacci
ARCH_SEG, ARCH_COLS = 96, 5
ARCH_DROP = BELL_R * 0.9        # how far below the margin the buttress lands
N_CASCADES = 5                  # Fibonacci
CASC_ROWS, CASC_COLS = 300, 7
CASC_LENGTH = 520.0             # total drop across three stages
CASC_WIDTH = 9.0
N_DRAPES = 21                   # Fibonacci
DRAPE_ROWS, DRAPE_COLS = 90, 3
DRAPE_LEN = 26.0
SPIRE_SEG = 160
SPIRE_HEIGHT = BELL_R * 0.55
SPIRE_TURNS = 1.25

EXTRA_DEFS = r"""
def arch():
    # flying buttress: quadratic bezier from main-dome margin down-and-out
    ARC = __ARCH_INDEX__
    N = __N_ARCHES__
    a = ARC / N * 2.0 * math.pi
    ca, sa = math.cos(a), math.sin(a)
    r0 = __R0__; y0 = __Y0__
    r1 = __R1__; y1 = y0 - __DROP__
    P0 = V(r0 * ca, y0, r0 * sa)
    P2 = V(r1 * ca, y1, r1 * sa)
    mid_r = (r0 + r1) * 0.5 + 18.0
    P1 = V(mid_r * ca, (y0 + y1) * 0.5 + 26.0, mid_r * sa)
    ROWS, COLS = __ARCH_SEG__, __ARCH_COLS__
    W = 2.6
    rows = []
    for i in range(ROWS + 1):
        t = i / ROWS
        pos = (P0 * (1 - t) ** 2) + (P1 * (2 * t * (1 - t))) + (P2 * t * t)
        tan = ((P1 - P0) * (1 - t) + (P2 - P1) * t).normalized()
        up = V(0, 1, 0)
        if abs(tan.dot(up)) > 0.95:
            up = V(1, 0, 0)
        x1 = tan.cross(up).normalized()
        y1v = tan.cross(x1).normalized()
        row = []
        for k in range(COLS + 1):
            u = k / COLS - 0.5
            off = x1 * (W * u) + y1v * (W * 0.35 * u * u * 4.0 - W * 0.35)
            p = geo.createPoint()
            p.setPosition(pos + off)
            p.setAttribValue(geo.findPointAttrib("uv"), (u + 0.5, t))
            row.append(p)
        rows.append(row)
    for i in range(ROWS):
        for k in range(COLS):
            f = geo.createPolygon()
            for q in (rows[i][k], rows[i][k + 1], rows[i + 1][k + 1], rows[i + 1][k]):
                f.addVertex(q)

def spire():
    # slender helix through the halo, tapering to a point
    ROWS, COLS = __SPIRE_SEG__, 5
    H = __SPIRE_HEIGHT__; TURNS = __SPIRE_TURNS__
    R0 = __R0__ * 0.16
    rows = []
    for i in range(ROWS + 1):
        s = i / ROWS
        ang = s * 2.0 * math.pi * TURNS
        rr = R0 * (1.0 - 0.72 * s) * (1.0 + 0.05 * math.sin(ang * 3.0))
        y = __Y0__ + s * H
        cx, sz = math.cos(ang), math.sin(ang)
        tan = V(-sz, H / (2.0 * math.pi * TURNS * max(rr, 1.0)), cx).normalized()
        up = V(0, 1, 0)
        x1 = tan.cross(up).normalized()
        y1v = tan.cross(x1).normalized()
        w = 2.2 * (1.0 - 0.85 * s)
        row = []
        for k in range(COLS + 1):
            u = k / COLS - 0.5
            off = x1 * (w * u) + y1v * (w * 0.5 * u * u * 4.0 - w * 0.5)
            p = geo.createPoint()
            p.setPosition(V(rr * cx, y, rr * sz) + off)
            p.setAttribValue(geo.findPointAttrib("uv"), (u + 0.5, s))
            row.append(p)
        rows.append(row)
    for i in range(ROWS):
        for k in range(COLS):
            f = geo.createPolygon()
            for q in (rows[i][k], rows[i][k + 1], rows[i + 1][k + 1], rows[i + 1][k]):
                f.addVertex(q)

def cascade():
    # three-stage fountain ribbon: fall, pool (spread), fall, pool, fall
    CIDX = __CASCADE_INDEX__
    N = __N_CASCADES__
    a = CIDX * __GOLDEN_ANGLE__ + 0.35
    ca, sa = math.cos(a), math.sin(a)
    R = __R0__
    LEN = __CASC_LENGTH__
    W = __CASC_WIDTH__
    ROWS, COLS = __CASC_ROWS__, __CASC_COLS__
    rng2 = random.Random(SEED + 700 + CIDX)
    ph = rng2.uniform(0, 6.28)
    rows = []
    for i in range(ROWS + 1):
        s = i / ROWS
        stage = min(2, int(s * 3.0))
        ts = s * 3.0 - stage
        y = -LEN * (stage + ts) / 3.0
        rr = R * 0.94 + LEN * 0.10 * (stage + ts) + 4.0 * ts * (1 - ts) * 3.0
        spread = 1.0 + 0.9 * math.exp(-((ts - 0.5) ** 2) / 0.02)
        w = W * spread * (1.0 - 0.25 * stage)
        sway = math.sin(a * 2.0 + s * 6.0 + ph) * LEN * 0.04 * s
        x = rr * ca + sway * math.cos(a + 1.57)
        z = rr * sa + sway * math.sin(a + 1.57)
        rows.append((x, y, z, w, s, a))
    grid = []
    for (x, y, z, w, s, aa) in rows:
        row = []
        for k in range(COLS + 1):
            u = k / COLS - 0.5
            cup = (u * u * 4.0 - 1.0) * w * 0.08
            p = geo.createPoint()
            p.setPosition(V(x + w * u * math.cos(aa + 1.57),
                            y,
                            z + w * u * math.sin(aa + 1.57)) + V(0, cup, 0))
            p.setAttribValue(geo.findPointAttrib("uv"), (u + 0.5, s))
            row.append(p)
        grid.append(row)
    for i in range(ROWS):
        for k in range(COLS):
            f = geo.createPolygon()
            for q in (grid[i][k], grid[i][k + 1], grid[i + 1][k + 1], grid[i + 1][k]):
                f.addVertex(q)

def drape():
    # short curtain between cilia, scalloped hem, gentle sway
    DIDX = __DRAPE_INDEX__
    N = __N_DRAPES__
    a = DIDX / N * 2.0 * math.pi
    R = __R0__
    LEN = __DRAPE_LEN__
    ROWS, COLS = __DRAPE_ROWS__, __DRAPE_COLS__
    rng2 = random.Random(SEED + 800 + DIDX)
    ph = rng2.uniform(0, 6.28)
    rows = []
    for i in range(ROWS + 1):
        s = i / ROWS
        rr = R * (0.985 - 0.03 * s)
        sway = math.sin(a * 2.0 + s * 3.0 + ph) * LEN * 0.10 * s
        y = -s * LEN
        scallop = 1.0 - 0.22 * math.sin(s * math.pi) ** 2
        rows.append((rr * math.cos(a) + sway * math.cos(a + 1.57),
                     y,
                     rr * math.sin(a) + sway * math.sin(a + 1.57),
                     3.4 * scallop, s, a))
    grid = []
    for (x, y, z, w, s, aa) in rows:
        row = []
        for k in range(COLS + 1):
            u = k / COLS - 0.5
            p = geo.createPoint()
            p.setPosition(V(x + w * u * math.cos(aa + 1.57), y,
                            z + w * u * math.sin(aa + 1.57)))
            p.setAttribValue(geo.findPointAttrib("uv"), (u + 0.5, s))
            row.append(p)
        grid.append(row)
    for i in range(ROWS):
        for k in range(COLS):
            f = geo.createPolygon()
            for q in (grid[i][k], grid[i][k + 1], grid[i + 1][k + 1], grid[i + 1][k]):
                f.addVertex(q)
"""

CODE_V4 = v3.CODE.replace(
    "if MODE == \"tier\":",
    EXTRA_DEFS + "\n\nif MODE == \"tier\":"
).replace(
    "elif MODE == \"cilium\":\n    cilium()\nelse:\n    arm_phyllo()",
    "elif MODE == \"cilium\":\n    cilium()\n"
    "elif MODE == \"arch\":\n    arch()\n"
    "elif MODE == \"spire\":\n    spire()\n"
    "elif MODE == \"cascade\":\n    cascade()\n"
    "elif MODE == \"drape\":\n    drape()\n"
    "else:\n    arm_phyllo()"
)


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
    payload = {"schema": "melodia.jellyfish.v1", "variant": "v4_cathedral",
               "seed": SEED_V4, "scale": "metres; UE import x100",
               "static_parts": {}, "arms": []}

    pose_names = ["Neutral", "PulseContract", "PulseExpand", "SurrealLurch"]

    # ---- v3 static assembly (tiers/halo/cilia) rebuilt under the v4 seed ----
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
    # ---- v4 architecture ----
    margin_y = 0.0
    for ai in range(N_ARCHES):
        static_specs.append((f"arch_{ai:02d}", "arch",
                             dict(ARCH_INDEX=ai, N_ARCHES=N_ARCHES,
                                  R0=TIER_RADII[0] * 0.97, Y0=margin_y,
                                  R1=TIER_RADII[0] * 1.22, DROP=ARCH_DROP,
                                  ARCH_SEG=ARCH_SEG, ARCH_COLS=ARCH_COLS)))
    static_specs.append(("spire", "spire",
                         dict(SPIRE_SEG=SPIRE_SEG, SPIRE_HEIGHT=SPIRE_HEIGHT,
                              SPIRE_TURNS=SPIRE_TURNS, R0=BELL_R,
                              Y0=2 * BELL_R * 0.34 + BELL_R * 0.30 + 6.0)))
    for ci in range(N_CASCADES):
        static_specs.append((f"cascade_{ci:02d}", "cascade",
                             dict(CASCADE_INDEX=ci, N_CASCADES=N_CASCADES, R0=BELL_R,
                                  CASC_LENGTH=CASC_LENGTH, CASC_WIDTH=CASC_WIDTH,
                                  CASC_ROWS=CASC_ROWS, CASC_COLS=CASC_COLS,
                                  GOLDEN_ANGLE=GOLDEN_ANGLE)))
    for di in range(N_DRAPES):
        static_specs.append((f"drape_{di:02d}", "drape",
                             dict(DRAPE_INDEX=di, N_DRAPES=N_DRAPES, R0=BELL_R,
                                  DRAPE_LEN=DRAPE_LEN, DRAPE_ROWS=DRAPE_ROWS,
                                  DRAPE_COLS=DRAPE_COLS)))

    for part_name, mode, params in static_specs:
        data_by_pose = {}
        ok = True
        for pose in pose_names:
            for old in [n for n in obj.children() if n.name() == f"CATH_{part_name}"]:
                old.destroy()
            g = obj.createNode("geo", f"CATH_{part_name}", run_init_scripts=True)
            py = g.createNode("python", "gen")
            code = _inject(CODE_V4, MODE=mode, SEED=SEED_V4, POSE=pose, **params)
            code = _fix_seed(code, SEED_V4)
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
                print(f"[cath] WARNING: {part_name} pose {pose} topology mismatch!")
        payload["static_parts"][part_name] = {
            "mesh": base, "poses": poses_out, "kind": mode,
        }
        print(f"[cath] {part_name}: {len(base['points'])} pts ({len(base['faces'])} faces)")

    # ---- arms (v3 golden-angle phyllotaxis, unchanged recipe) ----
    for arm_i in range(N_ARMS):
        for old in [n for n in obj.children() if n.name() == f"CATH_ARM_{arm_i}"]:
            old.destroy()
        ga = obj.createNode("geo", f"CATH_ARM_{arm_i}", run_init_scripts=True)
        pya = ga.createNode("python", "gen_arm")
        ca = _inject(CODE_V4, MODE="arm", SEED=SEED_V4, POSE="Neutral", R=BELL_R,
                     ARM_INDEX=arm_i, N_ARMS=N_ARMS, LENGTH=ARM_LENGTH,
                     ROWS=ARM_ROWS, COLS=ARM_COLS, WIDTH=ARM_WIDTH,
                     GOLDEN_ANGLE=GOLDEN_ANGLE)
        ca = _fix_seed(ca, SEED_V4)
        pya.parm("python").set(ca)
        if not _cook_report(pya, f"arm:{arm_i}"):
            ga.destroy()
            continue
        payload["arms"].append(_dump_geo(pya.geometry()))
        print(f"[cath] arm {arm_i}: {len(payload['arms'][-1]['points'])} pts")
        ga.destroy()

    payload["meta"] = {
        "n_arms": N_ARMS, "arm_length_m": ARM_LENGTH,
        "bell_main_diameter_m": TIER_RADII[0] * 2,
        "architecture": {
            "arches_fibonacci": N_ARCHES,
            "spire_height_m": round(SPIRE_HEIGHT, 1),
            "cascades_fibonacci": N_CASCADES,
            "cascade_drop_m": CASC_LENGTH,
            "drapes_fibonacci": N_DRAPES,
        },
        "surreal_logic": ["flying-buttress arches on the main margin",
                          "helix spire through the halo",
                          "three-stage fountain cascades with spreading pools",
                          "scalloped drape curtains between cilia",
                          "all v3 math kept: golden-ratio tiers, Fibonacci lobes, "
                          "golden-angle arms, 55-filament crown"],
    }

    out = OUT_DIR / "jellyfish_mesh_v4_cathedral.json"
    out.write_text(json.dumps(payload, separators=(",", ":")), encoding="utf-8")
    print(f"[cath] wrote {out.name} ({out.stat().st_size} bytes)")

    manifest = {
        "schema": "melodia.sea_above_reef_meshes.v1",
        "kind": "jellyfish R6 v4 CATHEDRAL: v3 SERAPH + buttress arches, spire, "
                "cascading fountain ribbons, drape curtains",
        "variant": "v4_cathedral", "seed": SEED_V4,
        "hython": hou.applicationVersionString(),
        "mesh_json": str(out),
        "pose_names": pose_names,
        "engine_contract": "pose names + uv layout compatible with v1-v3 wiring; "
                           "LUTs remain valid (uv.y normalized)",
        "ue_import": {"scale": "100x (m -> cm)",
                      "static_parts": "skeletal (root bone) with 4 shape keys each",
                      "arms": "static Nanite; existing LUT recipe"},
        "entries": [{"name": "v4_cathedral", "json_bytes": out.stat().st_size}],
    }
    (OUT_DIR / "jellyfish_mesh_v4_cathedral_manifest.json").write_text(
        json.dumps(manifest, indent=2), encoding="utf-8")
    print("[cath] manifest -> jellyfish_mesh_v4_cathedral_manifest.json")


if __name__ == "__main__":
    main()
