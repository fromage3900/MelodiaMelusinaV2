"""MIDI World-Gen Daemon — scan, generate, render, ledger.

Runs on a schedule (Hermes cron). For each new or changed MIDI file:
  1. Build walkable heightfields for all 5 presets (serpentine + spiral)
  2. Instance dressing + props via terrain_dressing
  3. Render a proof PNG per preset through Blender headless
  4. Append results to the daemon ledger
  5. Regenerate the portfolio SVG banner from latest metrics

Idempotent: the ledger tracks (midi_path, preset, mtime). Already-processed
skips are not re-rendered unless the MIDI file changes on disk.

Run:
  python -B Tools/midi_worldgen_daemon.py
"""

import os
import sys
import json
import time
import math
import subprocess

REPO = r"C:\EnvironmentPortfolio\BS_GodFile"
ADDON = os.path.join(REPO, "Tools", "BlenderAddons", "melodia_studio")
OUT_DIR = r"G:\EnvironmentPortfolio\BS_GodFile\Saved\Audit\midi_worldgen_daemon"
LEDGER = os.path.join(OUT_DIR, "ledger.json")
BLENDER = r"C:\Program Files\Blender Foundation\Blender 5.2\blender.exe"

for p in (ADDON, os.path.join(REPO, "Tools", "BlenderAddons", "resonant_world_studio")):
    if p not in sys.path:
        sys.path.insert(0, p)

import walkable_world as ww
import terrain_dressing as td

PRESETS = ["walkable_valley", "walkable_highlands", "walkable_plaza",
           "walkable_canyon", "walkable_spiral_arena"]


def load_ledger():
    if os.path.exists(LEDGER):
        with open(LEDGER, encoding="utf-8") as f:
            return json.load(f)
    return {"runs": [], "entries": []}


def save_ledger(ledger):
    os.makedirs(OUT_DIR, exist_ok=True)
    with open(LEDGER, "w", encoding="utf-8") as f:
        json.dump(ledger, f, indent=2)


def midi_files():
    roots = [
        os.path.join(REPO, "Content", "MelodiaIntegration", "MIDI"),
        os.path.join(REPO, "Imports", "Audio"),
    ]
    found, seen = [], set()
    for root in roots:
        if not os.path.isdir(root):
            continue
        for dirpath, _d, files in os.walk(root):
            for fn in files:
                if not fn.lower().endswith((".mid", ".midi")):
                    continue
                full = os.path.join(dirpath, fn)
                key = os.path.normcase(full)
                if key in seen:
                    continue
                seen.add(key)
                found.append(full)
    return sorted(found)


def file_fingerprint(path):
    st = os.stat(path)
    return "%s:%d:%d" % (path, st.st_mtime, st.st_size)


def already_processed(ledger, midi_path, preset):
    fp = file_fingerprint(midi_path)
    for entry in ledger.get("entries", []):
        if entry.get("midi") == midi_path and entry.get("preset") == preset:
            if entry.get("fingerprint") == fp:
                return True
    return False


def build_field(midi_path, preset_id):
    mv = ww.load_voxel_module()
    tracks, tpb = mv.parse_midi(midi_path)
    if not tracks:
        return None, None, None
    preset = ww.WALKABLE_PRESETS.get(preset_id)
    if preset is None:
        return None, None, None
    notes = list(tracks[0])
    stem, ext = os.path.splitext(midi_path)
    bg = stem + "_beatgrid" + ext
    if os.path.exists(bg):
        b_tracks, b_tpb = mv.parse_midi(bg)
        if b_tracks and b_tpb:
            scale = float(tpb) / float(b_tpb)
            notes.extend((int(n[0] * scale), n[1] + 36, n[2]) for n in b_tracks[0])
            notes.sort()
    field, _gw = ww.build_heightfield(
        notes, preset["cells_per_beat"], preset["height_scale"],
        preset["plateau_radius"], tpb, preset.get("fold", "serpentine"))
    field = ww.limit_slope(ww.fill_gaps(field), preset["max_slope"],
                           preset["smooth_passes"])
    metrics = ww.walkability(field, preset["max_slope"])
    metrics["largest_region"] = ww.largest_connected_region(field, preset["max_slope"])
    metrics["largest_region_fraction"] = round(
        metrics["largest_region"] / float(max(1, metrics["cells"])), 3)
    return field, preset, metrics


def render_proof(midi_path, preset_id, field, metrics, props, pstats):
    """Render a single proof image through Blender headless (subprocess)."""
    try:
        mv = ww.load_voxel_module()
        tmp_obj = os.path.join(os.environ.get("LOCALAPPDATA", REPO), "Temp",
                               "daemon_%s.obj" % preset_id)
        os.makedirs(os.path.dirname(tmp_obj), exist_ok=True)
        voxels = ww.field_to_voxels(field, mv)
        mv.export_obj(voxels, tmp_obj, name="DaemonWorld")
    except Exception as e:
        print("[daemon] Export failed for %s / %s: %s" % (
            os.path.basename(midi_path), preset_id, e), flush=True)
        return None

    # Write render job JSON to fixed path
    # Convert colour tuples to lists for JSON serialization
    json_props = []
    for p in props:
        jp = dict(p)
        jp["colour"] = list(jp["colour"])
        json_props.append(jp)
    job = {
        "obj": tmp_obj,
        "midi": midi_path,
        "preset": preset_id,
        "out": os.path.join(OUT_DIR, "renders",
                            "%s__%s.png" % (
                                os.path.basename(midi_path).replace(".mid", ""),
                                preset_id)),
        "props": json_props,
        "camera": {"azimuth": -38, "elevation": 26, "lens": 40, "dist_mult": 1.3},
    }
    job_path = os.path.join(os.environ.get("LOCALAPPDATA", REPO), "Temp",
                            "daemon_current_job.json")
    with open(job_path, "w", encoding="utf-8") as f:
        json.dump(job, f, indent=2)

    # Call Blender
    wrapper = os.path.join(REPO, "Tools", "_daemon_render_wrapper.py")
    result = subprocess.run(
        [BLENDER, "--background", "--factory-startup", "--python", wrapper],
        capture_output=True, text=True, timeout=300
    )

    if result.returncode != 0:
        print("[daemon] Blender render failed for %s / %s:\n%s" % (
            os.path.basename(midi_path), preset_id,
            result.stderr[-500:]), flush=True)

    return job["out"] if os.path.exists(job["out"]) else None


def regenerate_banner(ledger):
    """Regenerate the portfolio SVG from latest metrics."""
    banner_script = os.path.join(REPO, "Tools", "gen_resonant_banner.py")
    if os.path.exists(banner_script):
        subprocess.run([sys.executable, "-B", banner_script],
                       cwd=REPO, capture_output=True)


def main():
    os.makedirs(OUT_DIR, exist_ok=True)
    os.makedirs(os.path.join(OUT_DIR, "renders"), exist_ok=True)

    ledger = load_ledger()
    files = midi_files()
    run = {
        "started": time.strftime("%Y-%m-%d %H:%M:%S"),
        "midi_found": len(files),
        "processed": 0,
        "skipped": 0,
        "errors": 0,
    }

    print("[daemon] Found %d MIDI files" % len(files), flush=True)

    for midi_path in files:
        for preset_id in PRESETS:
            if already_processed(ledger, midi_path, preset_id):
                run["skipped"] += 1
                continue

            try:
                field, preset, metrics = build_field(midi_path, preset_id)
                if field is None:
                    run["errors"] += 1
                    continue

                # Generate dressing in pure Python (no bpy)
                props, pstats = td.plan_dressing(field, "crystalline")

                render_path = render_proof(midi_path, preset_id, field, metrics,
                                           props, pstats)

                entry = {
                    "midi": midi_path,
                    "preset": preset_id,
                    "fingerprint": file_fingerprint(midi_path),
                    "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
                    "metrics": {
                        "footprint": metrics["footprint"],
                        "aspect_ratio": metrics["aspect_ratio"],
                        "height_span": metrics["height_span"],
                        "walkable_fraction": metrics["walkable_fraction"],
                        "largest_region_fraction": metrics[
                            "largest_region_fraction"],
                        "cells": metrics["cells"],
                    },
                    "render": render_path,
                }
                ledger.setdefault("entries", []).append(entry)
                run["processed"] += 1
                print("[daemon] %s / %s -> %s" % (
                    os.path.basename(midi_path), preset_id,
                    render_path), flush=True)

            except Exception as exc:
                run["errors"] += 1
                print("[daemon] ERROR %s / %s: %s" % (
                    os.path.basename(midi_path), preset_id, exc), flush=True)

    run["finished"] = time.strftime("%Y-%m-%d %H:%M:%S")
    ledger.setdefault("runs", []).append(run)
    save_ledger(ledger)

    regenerate_banner(ledger)

    print("[daemon] Run complete: %d processed, %d skipped, %d errors" % (
        run["processed"], run["skipped"], run["errors"]), flush=True)
    print("[daemon] Ledger: %s" % LEDGER, flush=True)


if __name__ == "__main__":
    code = 0
    try:
        main()
    except Exception:
        import traceback
        traceback.print_exc()
        code = 1
    finally:
        sys.stdout.flush()
        os._exit(code)
