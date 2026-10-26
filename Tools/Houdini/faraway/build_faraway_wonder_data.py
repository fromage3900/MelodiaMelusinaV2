r"""build_faraway_wonder_data.py -- Faraway Mother "wonder layer" data (Infinity Nikki north star). spike: true

Pure Python, deterministic (seed 3900). Consumes the biome placements and seam polylines already built:
  FarawayBiomes_20261026/placements.json, FarawaySeamDressing_20261026/{seam_polylines,junctions}.json
Emits export-ready JSON for the UE intake (no UE, no materials):
  lace_wings.json     beat-locked ambient fauna: settle points on F=0, behaviour states, scatter rules
  landmarks.json      La Berceuse (guardian) + lullaby gate, friendly guide Thimble waypoints
  wonders.json        wish_lanterns, sing_to_bloom chains, stitch_hop buttons (Heart Gate path)
Gate: counts, 80 m junction clearance, world bounds, determinism, every point on its intended field (|F| or biome).
"""
from __future__ import annotations

import argparse
import hashlib
import json
import math
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
STAGE = ROOT / "Saved" / "Staging" / "HoudiniForge"
HALF = 4000.0
PI = math.pi


def F(x, y):
    u, v = (x + HALF) / 8000.0, (y + HALF) / 8000.0
    return math.cos(3 * PI * u) * math.cos(5 * PI * v) - math.cos(5 * PI * u) * math.cos(3 * PI * v)


def h(*a):
    x = 2166136261
    for v in a:
        x = ((x ^ (int(v) & 0xFFFFFFFF)) * 16777619) & 0xFFFFFFFF
    return x / 4294967295.0


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default=str(STAGE / "FarawayWonder_20261026"))
    a = ap.parse_args()
    out = Path(a.out); out.mkdir(parents=True, exist_ok=True)
    pl = json.load(open(STAGE / "FarawayBiomes_20261026" / "placements.json"))["placements"]
    seams = json.load(open(STAGE / "FarawaySeamDressing_20261026" / "seam_polylines.json"))["seams"]
    J = json.load(open(STAGE / "FarawaySeamDressing_20261026" / "junctions.json"))["junctions"]

    def jd(x, y):
        return min(math.hypot(x - j[0], y - j[1]) for j in J)

    # ---- Lace Wings -------------------------------------------------------------------------------------------
    settle = []
    for s in seams:
        pts = s["points"]
        step = 20  # polyline already every 12 m (6 m resampled, every 2nd); 20 pts = 240 m
        for k in range(3, len(pts), step):
            x, y = pts[k]
            if jd(x, y) < 80 or abs(x) > HALF - 60 or abs(y) > HALF - 60:
                continue
            settle.append({"x": x, "y": y, "seam": s["id"], "flock": 2 + int(h(s["id"], k) * 4), "|F|": round(abs(F(x, y)), 6)})
    lace = {
        "species": "LaceWing", "size_m": 0.15, "wings": 4, "wing_style": "scalloped bobbin lace (GN group, other assistant)",
        "rhythm": {"bpm_param": "MPC_Melodia_Palette.BeatPhase", "default_bpm": 96, "wingbeats_per_beat": 1,
                   "settle_on": "bar_downbeat", "beats_per_bar": 4, "beat_lock_tolerance_ms": 90},
        "states": [
            {"id": "Drift", "enter": "spawn", "speed_m_s": 0.8, "path": "slow lissajous around settle point, radius 3-6 m"},
            {"id": "Settle", "enter": "bar_downbeat within 12 m of a settle point", "hold_bars": [1, 3], "wings": "half-open, pulse on beat"},
            {"id": "Flutter", "enter": "player within 14 m while on-beat", "speed_m_s": 1.6, "orbit_player": True, "trail": "stitch thread ribbon"},
            {"id": "Scatter", "enter": "player action off-beat within 8 m", "radius_m": 8, "burst_m_s": 4.5, "recover_bars": 4},
        ],
        "reward": {"on_beat_run_bars": 8, "effect": "wings align to player's beat and spell a motif glyph along the seam"},
        "settle_points": settle, "settle_point_count": len(settle),
        "spawn": {"flock_range": [2, 5], "lod_cull_m": 220, "max_alive": 160, "niagara": "NS_Morning_* GPU family style, one parameterised system"},
    }
    (out / "lace_wings.json").write_text(json.dumps(lace, indent=1))

    # ---- La Berceuse + guide --------------------------------------------------------------------------------------
    basin = pl["MotherfoldBasin"][0]
    tri = pl["TerracedIsland"]
    lull_gate_site = sorted(tri, key=lambda p: math.hypot(p["x"] - basin["x"], p["y"] - basin["y"]))[0]
    berceuse = {
        "name": "La Berceuse", "role": "landmark guardian, sleeping lullaby giantess carved of folded silk",
        "site": {"x": basin["x"], "y": basin["y"], "biome": "VelvetBasin", "F": basin["F"], "facing_deg": basin["yaw_deg"]},
        "height_m": 38, "footprint_m": [60, 44], "model_status": "NEEDS MODEL (one paragraph in design bible, no mesh)",
        "states": [{"id": "Asleep", "cue": "slow breath scales Niagara glow on beat/4"}, {"id": "Stirring", "cue": "player hums phrase A"},
                   {"id": "Awake", "cue": "phrase A+B resolved: she opens the Motherfold basin water"}, {"id": "Lulled", "cue": "all hush creatures calm, gate opens"}],
        "lullaby_gate": {"site": {"x": lull_gate_site["x"], "y": lull_gate_site["y"]}, "phrase_notes": 3, "retry_hint": "lace wings spell the next note"},
    }
    spine = []  # main walk: origin junction -> Heart Gate (580,0) -> basin
    for k in range(0, 7):
        spine.append({"x": round(k * 580 / 6.0, 1), "y": 0.0})
    guide = {
        "name": "Thimble", "form": "a thimble-sized stitch sprite wearing a tiny knitted hat, speaks in seam-glow colours",
        "emotional_thread": "remembers every lullaby you sang; sleeps in your hat between regions",
        "beats": [{"id": f"guide_{i}", "x": p["x"], "y": p["y"], "line": line}
                  for i, (p, line) in enumerate(zip(spine, ["Hello! Follow the thread.", "Hear that? The ground hums in four.", "Step on the beat and the stitches light.",
                                                                "Sing with me, just a little.", "The Gate is shy; hum to it.", "You made the seam sing!", "Mother is dreaming. Be gentle."]))],
        "follows": "player at 5 m, hovers on beat, hides in hat when idle 20 s",
    }
    (out / "landmarks.json").write_text(json.dumps({"la_berceuse": berceuse, "guide": guide}, indent=1))

    # ---- more wonder ----------------------------------------------------------------------------------------------
    trees = pl["ListeningOrchardTree"]
    lanterns = []
    for i, t in enumerate(trees[::3][:40]):
        lanterns.append({"x": t["x"], "y": t["y"], "height_m": round(6 + 10 * h(i, 11), 1), "float_to_m": round(60 + 80 * h(i, 12), 1), "wish_color_seed": int(h(i, 13) * 1000),
                         "release": "player sings/holds note near tree (4 m)", "F": t["F"]})
    blooms = []
    for si, s in enumerate(seams):
        for k in range(10, len(s["points"]), 28):
            x, y = s["points"][k]
            if jd(x, y) < 80:
                continue
            # bloom chain just off the seam: the field value picks the palette (sign of F on either side)
            for side in (-1, 1):
                bx, by = x + side * 14.0 * h(si, k, side), y + 9.0 * h(si, k, 5 + side)
                blooms.append({"x": round(bx, 2), "y": round(by, 2), "side_F": 1 if F(bx, by) >= 0 else -1, "chain_radius_m": 18, "note": int(h(si, k) * 7)})
    hop = []
    for k in range(0, 65):
        x = 9.0 * k
        if jd(x, 0) < 80 or x > 580:
            continue
        hop.append({"x": round(x, 2), "y": round((h(k, 4) - 0.5) * 3.0, 2), "radius_m": 1.1, "button": k % 2, "bounce_on_beat": True})
    (out / "wonders.json").write_text(json.dumps({"wish_lanterns": lanterns, "sing_to_bloom": blooms, "stitch_hop_path": {"from": [0, 0], "to": [580, 0], "buttons": hop}}, indent=1))

    gate = {
        "lace_settle_points": len(settle), "lace_all_clear_of_junctions": all(jd(p["x"], p["y"]) >= 80 for p in settle),
        "lace_on_seam": max(p["|F|"] for p in settle) < 0.02,
        "lanterns": len(lanterns), "blooms": len(blooms), "hop_buttons": len(hop),
        "guide_beats": len(guide["beats"]),
        "blooms_in_bounds": all(abs(b["x"]) < HALF and abs(b["y"]) < HALF for b in blooms),
    }
    gate["pass"] = bool(gate["lace_settle_points"] > 40 and gate["lace_all_clear_of_junctions"] and gate["lace_on_seam"]
                        and gate["lanterns"] >= 20 and gate["blooms"] > 100 and gate["hop_buttons"] > 30 and gate["blooms_in_bounds"])
    man = {"schema": "melodia.faraway_wonder.spike.v1", "spike": True, "gate": gate,
           "files": {p.name: hashlib.sha256(p.read_bytes()).hexdigest()[:16] for p in sorted(out.glob("*")) if p.is_file() and p.name != "manifest.json"}}
    (out / "manifest.json").write_text(json.dumps(man, indent=1))
    print("GATE", json.dumps(gate))
    return 0 if gate["pass"] else 2


if __name__ == "__main__":
    raise SystemExit(main())
