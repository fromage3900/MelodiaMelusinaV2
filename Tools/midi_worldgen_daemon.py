"""MIDI World-Gen Daemon - scan, generate, render, ledger.

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

import contextlib
import hashlib
import json
import os
import subprocess
import sys
import tempfile
import time

from worldgen_tooling_contracts import daemon_run_passes, sha256_file

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.normpath(os.path.join(HERE, ".."))
ADDON = os.path.join(REPO, "Tools", "BlenderAddons", "melodia_studio")
OUT_DIR = os.environ.get(
    "MELODIA_WORLDGEN_OUT",
    os.path.join(REPO, "Saved", "Audit", "midi_worldgen_daemon"),
)
LEDGER = os.path.join(OUT_DIR, "ledger.json")
LOCK_FILE = os.path.join(OUT_DIR, ".daemon.lock")
BLENDER = os.environ.get(
    "MELODIA_BLENDER_EXE",
    os.path.join(
        os.environ.get("ProgramFiles", r"C:\Program Files"),
        "Blender Foundation",
        "Blender 5.2",
        "blender.exe",
    ),
)

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
    temp_path = LEDGER + ".%d.tmp" % os.getpid()
    try:
        with open(temp_path, "w", encoding="utf-8") as f:
            json.dump(ledger, f, indent=2)
            f.flush()
            os.fsync(f.fileno())
        os.replace(temp_path, LEDGER)
    finally:
        if os.path.exists(temp_path):
            os.remove(temp_path)


@contextlib.contextmanager
def single_instance():
    """Hold a process-lifetime lock so scheduled runs cannot overlap."""
    os.makedirs(OUT_DIR, exist_ok=True)
    handle = open(LOCK_FILE, "a+b")
    if os.path.getsize(LOCK_FILE) == 0:
        handle.write(b"0")
        handle.flush()
    handle.seek(0)
    try:
        if os.name == "nt":
            import msvcrt
            msvcrt.locking(handle.fileno(), msvcrt.LK_NBLCK, 1)
        else:
            import fcntl
            fcntl.flock(handle.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
    except OSError as exc:
        handle.close()
        raise RuntimeError("another MIDI world-gen daemon is active") from exc
    try:
        yield
    finally:
        handle.seek(0)
        if os.name == "nt":
            import msvcrt
            msvcrt.locking(handle.fileno(), msvcrt.LK_UNLCK, 1)
        else:
            import fcntl
            fcntl.flock(handle.fileno(), fcntl.LOCK_UN)
        handle.close()


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
                if os.path.splitext(fn)[0].lower().endswith("_beatgrid"):
                    continue
                full = os.path.join(dirpath, fn)
                key = os.path.normcase(full)
                if key in seen:
                    continue
                seen.add(key)
                found.append(full)
    return sorted(found)


def file_fingerprint(path):
    digest = hashlib.sha256()
    with open(path, "rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return "sha256:%s" % digest.hexdigest()


def already_processed(ledger, midi_path, preset):
    fp = file_fingerprint(midi_path)
    for entry in ledger.get("entries", []):
        if entry.get("midi") == midi_path and entry.get("preset") == preset:
            if (
                entry.get("fingerprint") == fp
                and entry.get("render")
                and os.path.exists(entry["render"])
            ):
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
    if not os.path.isfile(BLENDER):
        print("[daemon] Blender executable not found: %s" % BLENDER, flush=True)
        return None

    temp_root = os.path.join(os.environ.get("LOCALAPPDATA", REPO), "Temp")
    os.makedirs(temp_root, exist_ok=True)
    obj_handle = tempfile.NamedTemporaryFile(
        prefix="melodia_worldgen_", suffix=".obj", dir=temp_root, delete=False
    )
    tmp_obj = obj_handle.name
    obj_handle.close()
    try:
        mv = ww.load_voxel_module()
        voxels = ww.field_to_voxels(field, mv)
        mv.export_obj(voxels, tmp_obj, name="DaemonWorld")
    except Exception as e:
        print("[daemon] Export failed for %s / %s: %s" % (
            os.path.basename(midi_path), preset_id, e), flush=True)
        if os.path.exists(tmp_obj):
            os.remove(tmp_obj)
        return None

    # Write an isolated job file and pass it explicitly to the Blender process.
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
        "out": os.path.join(
            OUT_DIR,
            "renders",
            "%s__%s.png" % (os.path.splitext(os.path.basename(midi_path))[0], preset_id),
        ),
        "props": json_props,
        "camera": {"azimuth": -38, "elevation": 26, "lens": 40, "dist_mult": 1.3},
    }
    job_handle = tempfile.NamedTemporaryFile(
        mode="w",
        prefix="melodia_worldgen_",
        suffix=".json",
        dir=temp_root,
        delete=False,
        encoding="utf-8",
    )
    job_path = job_handle.name
    with job_handle as f:
        json.dump(job, f, indent=2)

    # Call Blender
    wrapper = os.path.join(REPO, "Tools", "_daemon_render_wrapper.py")
    child_env = os.environ.copy()
    child_env["MELODIA_WORLDGEN_JOB"] = job_path
    child_env["MELODIA_WORLDGEN_ALLOWED_TEMP"] = temp_root
    child_env["MELODIA_WORLDGEN_ALLOWED_OUT"] = OUT_DIR
    try:
        result = subprocess.run(
            [BLENDER, "--background", "--factory-startup", "--python", wrapper],
            capture_output=True,
            text=True,
            timeout=300,
            env=child_env,
        )
    finally:
        for temp_path in (job_path, tmp_obj):
            if os.path.exists(temp_path):
                os.remove(temp_path)

    if result.returncode != 0:
        print("[daemon] Blender render failed for %s / %s:\n%s" % (
            os.path.basename(midi_path), preset_id,
            result.stderr[-500:]), flush=True)
        return None

    return job["out"] if os.path.exists(job["out"]) else None


def regenerate_banner(_ledger):
    """Regenerate the portfolio SVG from latest metrics."""
    banner_script = os.path.join(REPO, "Tools", "gen_resonant_banner.py")
    if os.path.exists(banner_script):
        child_env = os.environ.copy()
        child_env["MELODIA_BANNER_OUT_DIR"] = os.path.join(OUT_DIR, "banner")
        result = subprocess.run(
            [sys.executable, "-B", banner_script],
            cwd=REPO,
            capture_output=True,
            text=True,
            env=child_env,
            timeout=120,
        )
        if result.returncode != 0:
            print("[daemon] Banner generation failed:\n%s" % result.stderr[-500:])
            return False
        return True
    return False


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
                if render_path is None:
                    run["errors"] += 1
                    continue

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
                    "render_sha256": sha256_file(render_path),
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

    if not regenerate_banner(ledger):
        run["errors"] += 1

    run["finished"] = time.strftime("%Y-%m-%d %H:%M:%S")
    run["verdict"] = (
        "PASS" if daemon_run_passes(run, len(PRESETS)) else "FAIL"
    )
    ledger.setdefault("runs", []).append(run)
    save_ledger(ledger)

    print("[daemon] Run complete: %d processed, %d skipped, %d errors" % (
        run["processed"], run["skipped"], run["errors"]), flush=True)
    print("[daemon] Ledger: %s" % LEDGER, flush=True)
    return run


if __name__ == "__main__":
    code = 0
    try:
        with single_instance():
            run = main()
        code = 0 if run.get("verdict") == "PASS" else 1
    except Exception:
        import traceback
        traceback.print_exc()
        code = 1
    finally:
        sys.stdout.flush()
        os._exit(code)
