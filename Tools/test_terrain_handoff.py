#!/usr/bin/env python3
"""Assertions for the unified terrain-handoff contract (melodia.terrain_handoff.v1).

Covers the three-lane convergence: midi_voxel / audio_gn_5_2 / gaea native
handoffs must convert to the unified schema and validate under the contract's
semantics (UE 5.8, target Mesh Terrain, 100 cm/m, classic_landscape_used false,
/Game/ namespace).

Runs against real lane artifacts when present (Docs/WorldGen/GAEA_SETUP_*.json
and Saved/AudioTerrain/*.audio_terrain_handoff.json), synthetic fixtures
otherwise.

    python Tools/test_terrain_handoff.py
"""
import glob
import importlib.util
import json
import os
import sys
import tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
PROJECT = os.path.dirname(HERE)
GAEA_DIR = os.path.join(PROJECT, "Docs", "WorldGen")
AUDIO_DIR = os.path.join(PROJECT, "Saved", "AudioTerrain")

_spec = importlib.util.spec_from_file_location(
    "terrain_handoff", os.path.join(HERE, "terrain_handoff.py"))
th = importlib.util.module_from_spec(_spec)
sys.modules["terrain_handoff"] = th
_spec.loader.exec_module(th)

FAILURES: list[str] = []
CHECKS = 0


def check(name: str, cond: bool, detail: str = ""):
    global CHECKS
    CHECKS += 1
    if not cond:
        FAILURES.append("%s %s" % (name, ("-- " + detail) if detail else ""))


def synthetic_midi_manifest() -> dict:
    return {
        "schema_version": "1.0",
        "kind": "melodia_mesh_terrain_handoff",
        "preset_id": "test_preset",
        "ue": {
            "engine": "5.8",
            "target": "Mesh Terrain",
            "import_scale_cm_per_meter": 100.0,
            "required_plugins": ["MeshPartition", "MeshTerrainMode",
                                 "PCGMeshPartitionInterop"],
            "classic_landscape_used": False,
            "recommended_content_path": "/Game/_PROJECT/ResonantWorld/Offline/test_preset",
        },
        "artifacts": {
            "heightfield": {"path": "Saved/Audit/hf.png", "format": "PNG_16bit"},
            "dressing_plan": {"path": "Saved/Audit/dressing.json", "format": "JSON"},
        },
        "validation": {"pixel_dimensions": {"width": 128, "height": 128}},
    }


def synthetic_gaea_setup() -> dict:
    return {
        "schema": "melodia.gaea_setup.v1",
        "setup_id": "test_setup",
        "status": "recipe_ready_reference_graph_validated_native_export_pending",
        "musical_binding": {"midi_preset": "glacial_fugue"},
        "source": {"provider": "QuadSpinner Gaea", "source_units": "meters",
                   "working_window_m": [8000.0, 6000.0]},
        "gaea_reference": {"path": "C:/Program Files/QuadSpinner/Gaea 2/Examples/x.terrain",
                           "gaea_version": "2.2.3.2"},
        "recipe": {"target_resolution": 4097, "output_extent_m": [4000.0, 4000.0],
                   "height_range_m": [0.0, 650.0]},
        "outputs": {"mesh_obj": "Saved/Audit/test.obj",
                    "heightfield_png16": "Saved/Audit/test_height.png",
                    "manifest": "Saved/Audit/handoff_manifest.json",
                    "export_status": "pending_native_gaea_export"},
        "ue5_8": {"target": "Mesh Terrain",
                  "content_namespace": "/Game/_PROJECT/Test",
                  "classic_landscape_used": False,
                  "mesh_terrain_import_scale_cm_per_m": 100.0},
        "evidence": {"native_gaea_export_verified": False},
        "gates": ["native_gaea_height_and_mask_export"],
    }


def test_gaea_lane(gaea_files: list[str]):
    synthetic = None
    if not gaea_files:
        synthetic = synthetic_gaea_setup()
    for path in gaea_files or ["<synthetic>"]:
        name = os.path.basename(path)
        doc = synthetic if path == "<synthetic>" else None
        if doc is None:
            try:
                with open(path, encoding="utf-8") as f:
                    doc = json.load(f)
            except Exception as exc:
                check("gaea:load %s" % name, False, repr(exc))
                continue
        check("gaea:detect %s" % name, th.detect_lane(doc) == "gaea",
              "lane=" + str(th.detect_lane(doc)))
        try:
            unified = th.from_gaea_setup(doc)
        except Exception as exc:
            check("gaea:convert %s" % name, False, repr(exc))
            continue
        report = th.validate_handoff(unified)
        check("gaea:validate %s" % name, report["ok"], "; ".join(report["errors"]))
        check("gaea:handoff_id %s" % name,
              str(unified.get("handoff_id")).startswith("gaea:"))
        check("gaea:scale %s" % name,
              unified["coordinate_system"]["unreal_scale_cm_per_meter"] == 100.0)
        check("gaea:namespace %s" % name,
              str(unified["ue5_8"]["content_namespace"]).startswith("/Game/"))
        check("gaea:no_classic_landscape %s" % name,
              unified["ue5_8"]["classic_landscape_used"] is False)


def test_audio_lane(audio_files: list[str]):
    synthetic = None
    if not audio_files:
        synthetic = {
            "schema": "melodia.audio_terrain_ue_handoff.v1",
            "source_audio": "P:/x/song.wav",
            "blend": "P:/x/song.blend",
            "coordinate_system": {"source": "Blender Z-up meters",
                                  "unreal_scale_cm_per_meter": 100.0},
            "tile_grid": {"x": 1, "y": 1, "tile_size_m": 256.0},
            "ue": {"engine": "5.8", "asset_kind": "StaticMesh",
                   "recommended_content_path": "/Game/Melodia/World/AudioTerrain",
                   "runtime_audio_authority": "MPC_Portfolio_Audio"},
            "artifacts": [{
                "object": "MEL_audio_spectrum_terrain_DREAMING_HIGHLANDS_T0_X00_Y00",
                "builder": "MEL_audio_spectrum_terrain", "preset": "DREAMING_HIGHLANDS",
                "sample_time": 0.0, "tile": {"x": 0, "y": 0, "size_m": 256.0},
                "world_origin_m": [0.0, 0.0, 0.0], "frequency_hz": [80.0, 9000.0],
                "named_attributes": ["audio_amplitude", "frequency_hz"],
            }],
        }
    for path in audio_files or ["<synthetic>"]:
        name = os.path.basename(path)
        data = synthetic if path == "<synthetic>" else None
        if data is None:
            with open(path, encoding="utf-8") as f:
                data = json.load(f)
        check("audio:detect %s" % name, th.detect_lane(data) == "audio_gn_5_2",
              "lane=" + str(th.detect_lane(data)))
        unified = th.from_audio_gn(data)
        report = th.validate_handoff(unified)
        check("audio:validate %s" % name, report["ok"], "; ".join(report["errors"]))
        check("audio:blend %s" % name, bool(unified["artifacts"]["blend"]))
        check("audio:ue_target %s" % name, unified["ue5_8"]["target"] == "Mesh Terrain")
        check("audio:origin %s" % name,
              len(unified["extent"]["world_origin_m"] or []) == 3)


def test_midi_lane():
    unified = th.from_midi_handoff(synthetic_midi_manifest())
    report = th.validate_handoff(unified)
    check("midi:validate", report["ok"], "; ".join(report["errors"]))
    check("midi:handoff_id", str(unified["handoff_id"]).startswith("midi_voxel:"))
    check("midi:heightfield_path", bool(unified["artifacts"]["heightfield_png16"]))
    check("midi:dressing_path", bool(unified["artifacts"]["dressing_plan"]))
    check("midi:no_classic_landscape", unified["ue5_8"]["classic_landscape_used"] is False)


def test_negative():
    unified = th.from_midi_handoff(synthetic_midi_manifest())
    bad_scale = json.loads(json.dumps(unified))
    bad_scale["coordinate_system"]["unreal_scale_cm_per_meter"] = 60.0
    report = th.validate_handoff(bad_scale)
    check("neg:bad_scale_rejected", not report["ok"]
          and any("unreal_scale_cm_per_meter" in e for e in report["errors"]))
    bad_classic = json.loads(json.dumps(unified))
    bad_classic["ue5_8"]["classic_landscape_used"] = True
    report = th.validate_handoff(bad_classic)
    check("neg:classic_landscape_rejected", not report["ok"])
    check("neg:unknown_schema_detected_none", th.detect_lane({"schema": "bogus"}) is None)
    raised = False
    try:
        th.convert_document({"schema": "bogus"})
    except ValueError:
        raised = True
    check("neg:unknown_schema_convert_raises", raised)


def test_emit_roundtrip(gaea_file: str | None):
    if gaea_file:
        with open(gaea_file, encoding="utf-8") as f:
            unified = th.from_gaea_setup(json.load(f))
    else:
        unified = th.from_midi_handoff(synthetic_midi_manifest())
    with tempfile.TemporaryDirectory() as tmp:
        out = os.path.join(tmp, "terrain_handoff.json")
        report = th.emit_unified(unified, out)
        check("emit:ok_report", report["ok"], "; ".join(report["errors"]))
        check("emit:file_written", os.path.isfile(out))
        with open(out, encoding="utf-8") as f:
            reloaded = json.load(f)
        check("emit:roundtrip_validates", th.validate_handoff(reloaded)["ok"])


def test_cli(audio_file: str | None):
    if not audio_file:
        return
    with tempfile.TemporaryDirectory() as tmp:
        rc = th.main(["convert", audio_file, "--out-dir", tmp])
        check("cli:convert_exit0", rc == 0)
        stem = os.path.basename(audio_file).rsplit(".audio_terrain_handoff", 1)[0]
        emitted = os.path.join(tmp, stem + ".terrain_handoff.json")
        check("cli:convert_emitted", os.path.isfile(emitted))
        rc = th.main(["validate", emitted, "--strict"])
        check("cli:validate_strict_exit0", rc == 0)


def main() -> int:
    gaea_files = sorted(glob.glob(os.path.join(GAEA_DIR, "GAEA_SETUP_*.json")))
    audio_files = sorted(glob.glob(os.path.join(AUDIO_DIR, "*.audio_terrain_handoff.json")))
    print("fixtures: gaea=%d audio=%d" % (len(gaea_files), len(audio_files)))

    test_gaea_lane(gaea_files)
    test_audio_lane(audio_files)
    test_midi_lane()
    test_negative()
    test_emit_roundtrip(gaea_files[0] if gaea_files else None)
    test_cli(audio_files[0] if audio_files else None)

    print("%d checks run, %d passed, %d failed" % (CHECKS, CHECKS - len(FAILURES),
                                                   len(FAILURES)))
    for message in FAILURES:
        print("FAIL " + message)
    return 1 if FAILURES else 0


if __name__ == "__main__":
    raise SystemExit(main())