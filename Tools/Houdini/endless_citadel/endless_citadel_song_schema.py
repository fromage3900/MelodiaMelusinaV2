"""A1 - The song becomes architecture.

Consumes the authoritative resonant-phrase voxel table
(Saved/Audit/resonant_world_phrase_128bpm.json, 192 voxels) and derives the
Endless Escher Citadel's architecture schema deterministically:

  time -> spiral position (torus: TURNS full rotations, returns at the seam)
  pitch -> height (halls rise with the melody; register drives tower height)
  velocity/energy -> scale + ornament density (loud notes = ornate halls)
  voice/timbre -> module variant (choir nave / piano hall / reed passage)
  material_id -> resonant marble vs dissonant obsidian
  pitch_class -> aurora hue index (Phrygian degrees -> 7-stop dream palette)
  beat/measure -> tower cadence + wing grouping (8 wings = 8 phrases)

seed = world_seed (3900) xor phrase_id hash. The citadel IS the song.
Output: Saved/Audit/endless_citadel/song_schema.json

Run:  python Tools/Houdini/endless_citadel/endless_citadel_song_schema.py
"""
import hashlib
import json
import math
from pathlib import Path

ROOT = Path(r"C:\EnvironmentPortfolio\BS_GodFile")
PHRASE_JSON = ROOT / "Saved" / "Audit" / "resonant_world_phrase_128bpm.json"
OUT = ROOT / "Saved" / "Audit" / "endless_citadel"
OUT.mkdir(parents=True, exist_ok=True)

TURNS = 3
WINGS = 8

# Aurora dream palette stops (violet->pink->peach->gold->teal->blue->lilac)
AURORA = [
    (0.55, 0.34, 0.85), (0.95, 0.55, 0.78), (1.00, 0.80, 0.65),
    (0.98, 0.90, 0.60), (0.50, 0.85, 0.80), (0.40, 0.60, 0.95),
    (0.72, 0.52, 0.92),
]


def smooth01(x):
    x = max(0.0, min(1.0, x))
    return x * x * (3.0 - 2.0 * x)


def main():
    data = json.loads(PHRASE_JSON.read_text(encoding="utf-8"))
    voxels = data["voxels"]
    world = data.get("world", {})
    src = data.get("source", {})
    phrase_id = src.get("phrase_id", "unknown")
    world_seed = int(world.get("world_seed", 3900))
    bpm = float(world.get("bpm", 128))
    root_note = world.get("root_note", "C")
    mode = world.get("mode_name", "Phrygian Ember")

    seed = world_seed ^ int(hashlib.md5(phrase_id.encode()).hexdigest()[:8], 16)
    max_tick = max(v["onset_tick"] for v in voxels) or 1

    points = []
    for v in voxels:
        t_norm = v["onset_tick"] / max_tick
        st = smooth01(t_norm)
        angle = TURNS * 2.0 * math.pi * st
        r = 14.0 + 6.0 * t_norm + 2.2 * math.sin(TURNS * 2.0 * math.pi * t_norm)
        z = 1.0 + (v["pitch"] - 48) * 0.42 + 3.2 * t_norm
        beat = v["onset_tick"] // 96
        measure = v["onset_tick"] // 384
        wing = measure % WINGS
        hue = AURORA[v["pitch_class"] % len(AURORA)]
        ornate = v["velocity"] / 127.0
        points.append({
            "cell_id": v["cell_id"],
            "x": round(r * math.cos(angle), 3),
            "y": round(r * math.sin(angle), 3),
            "z": round(z, 3),
            "t": round(t_norm, 4),
            "angle": round(angle, 4),
            "radius": round(r, 3),
            "pitch": v["pitch"],
            "pitch_class": v["pitch_class"],
            "scale_degree": v.get("scale_degree"),
            "velocity": v["velocity"],
            "energy": v.get("energy", 0),
            "voice": v.get("voice", "harmony"),
            "timbre": v.get("timbre", "marble"),
            "material": v.get("material_id", "resonant_note"),
            "beat": beat,
            "measure": measure,
            "wing": wing,
            "hue_r": round(hue[0], 3),
            "hue_g": round(hue[1], 3),
            "hue_b": round(hue[2], 3),
            "ornate": round(ornate, 3),
        })

    # melody contour for the roofline spline (resample 256)
    contour_pts = sorted(points, key=lambda p: p["t"])
    contour = [[p["t"], p["pitch"]] for p in contour_pts]

    # phrase table (per wing): start tick, note count, avg pitch, avg energy
    phrases = []
    for w in range(WINGS):
        wp = [p for p in points if p["wing"] == w]
        if not wp:
            continue
        phrases.append({
            "wing": w,
            "note_count": len(wp),
            "start_tick": min(p["onset"] for p in [
                {"onset": v["onset_tick"]} for v in voxels]) if False else wp[0]["t"],
            "avg_pitch": round(sum(p["pitch"] for p in wp) / len(wp), 1),
            "avg_energy": round(sum(p["energy"] for p in wp) / len(wp), 1),
        })

    schema = {
        "schema": "melodia.endless_citadel_song_schema.v1",
        "seed": seed,
        "song": {
            "midi": src.get("midi_file_name"),
            "phrase_id": phrase_id,
            "bpm": bpm,
            "root_note": root_note,
            "mode": mode,
            "turns": TURNS,
            "wings": WINGS,
            "note_count": len(points),
        },
        "mapping": {
            "time_to_spiral": "onset_tick/max -> smoothstep -> TURNS rotations (torus)",
            "pitch_to_height": "z = 1 + (pitch-48)*0.42 + 3.2*t",
            "velocity_to_ornate": "ornate = velocity/127",
            "material": "resonant_note=marble, dissonant_note=obsidian",
            "pitch_class_to_hue": "Phrygian degree -> aurora stop",
            "wing": "measure % 8",
        },
        "voxels": points,
        "contour": contour,
        "phrases": phrases,
    }
    out_path = OUT / "song_schema.json"
    out_path.write_text(json.dumps(schema, indent=2) + "\n", encoding="utf-8")
    print(f"[citadel-song] {len(points)} voxels -> {out_path}")
    print(f"[citadel-song] seed={seed} turns={TURNS} wings={WINGS} bpm={bpm} mode={mode}")
    print("[citadel-song] DONE")


if __name__ == "__main__":
    main()