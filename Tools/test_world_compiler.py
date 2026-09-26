#!/usr/bin/env python3
"""Offline tests for Tools/world_compiler.py (rung 1 of the compiled-world evidence ladder).

Run:  python Tools/test_world_compiler.py        (plain runner, no pytest needed)
      python -m pytest Tools/test_world_compiler.py -q
"""
from __future__ import annotations

import csv
import json
import math
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "Tools"))

import world_compiler as wc  # noqa: E402

RECIPE = ROOT / "recipes" / "morning_rainbow_bloom.v1.json"


def _compile(tmp: Path, recipe: Path = RECIPE) -> tuple[dict, Path]:
    manifest = wc.compile_recipe(recipe, out_root=tmp, write_envelope=False)
    return manifest, Path(manifest["out_dir"])


def _rows(path: Path) -> list[dict[str, str]]:
    with path.open(encoding="utf-8", newline="") as fh:
        return list(csv.DictReader(fh))


def test_recipe_validates():
    recipe, _ = wc.load_recipe(RECIPE)
    assert wc.validate_recipe(recipe) == []


def test_recipe_rejects_bad_band_count():
    recipe, _ = wc.load_recipe(RECIPE)
    recipe["field"]["band_count"] = 6
    errors = wc.validate_recipe(recipe)
    assert any("band_count" in e for e in errors)


def test_recipe_rejects_workstation_path():
    recipe, _ = wc.load_recipe(RECIPE)
    recipe["muse"]["brief"] = "C:/Users/someone/brief.md"
    assert any("workstation path" in e for e in wc.validate_recipe(recipe))


def test_bundle_matches_schema():
    with tempfile.TemporaryDirectory() as tmp:
        manifest, out = _compile(Path(tmp))
        disk = json.loads((out / "manifest.json").read_text(encoding="utf-8"))
        try:
            import jsonschema  # type: ignore

            schema = json.loads((ROOT / "specs" / "schemas" / "world_compiler_bundle.v1.schema.json").read_text(encoding="utf-8"))
            jsonschema.Draft202012Validator(schema).validate(disk)
        except ImportError:
            for key in ("schema", "compile_id", "stages", "bands", "tables", "counts", "ue_lane"):
                assert key in disk
        assert disk["status"] in ("PASS", "EXPECTED_FAIL")
        for name in ("points.csv", "fx_anchors.csv", "dressing_table.json", "signal_bindings.json", "identity.json", "manifest.json"):
            assert (out / name).exists(), name


def test_deterministic_two_runs_identical():
    with tempfile.TemporaryDirectory() as a, tempfile.TemporaryDirectory() as b:
        ma, oa = _compile(Path(a))
        mb, ob = _compile(Path(b))
        assert ma["manifest_sha256"] == mb["manifest_sha256"]
        for name in ("points.csv", "fx_anchors.csv", "dressing_table.json", "signal_bindings.json", "identity.json"):
            assert (oa / name).read_bytes() == (ob / name).read_bytes(), name


def test_seed_changes_output():
    recipe, _ = wc.load_recipe(RECIPE)
    recipe["world_seed"] = 3901
    with tempfile.TemporaryDirectory() as tmp:
        alt = Path(tmp) / "alt.json"
        alt.write_text(json.dumps(recipe), encoding="utf-8")
        m1, o1 = _compile(Path(tmp) / "a", alt)
        m2, o2 = _compile(Path(tmp) / "b")
        assert (o1 / "points.csv").read_bytes() != (o2 / "points.csv").read_bytes()


def test_band_counts_equal_manifest_and_columns_fixed():
    with tempfile.TemporaryDirectory() as tmp:
        manifest, out = _compile(Path(tmp))
        rows = _rows(out / "points.csv")
        assert list(rows[0].keys()) == wc.POINT_COLUMNS
        per_band = {}
        for r in rows:
            per_band[int(r["band"])] = per_band.get(int(r["band"]), 0) + 1
        for band in manifest["bands"]:
            assert per_band.get(band["band"], 0) == band["point_count"], band
            assert band["point_count"] > 0
        assert manifest["counts"]["points_total"] == len(rows)
        assert manifest["tables"]["points.csv"]["rows"] == len(rows)


def test_points_lie_in_their_band_ring():
    recipe, _ = wc.load_recipe(RECIPE)
    ax, ay, _ = recipe["place"]["anchor_cm"]
    jitter = recipe["field"]["radial_jitter_cm"]
    with tempfile.TemporaryDirectory() as tmp:
        manifest, out = _compile(Path(tmp))
        rings = {b["band"]: (b["inner_radius_cm"], b["outer_radius_cm"]) for b in manifest["bands"]}
        for r in _rows(out / "points.csv"):
            d = math.hypot(float(r["x"]) - ax, float(r["y"]) - ay)
            lo, hi = rings[int(r["band"])]
            assert lo - jitter - 0.01 <= d <= hi + jitter + 0.01, (r["point_id"], d, lo, hi)


def test_clearance_masks_respected_for_points_and_anchors():
    recipe, _ = wc.load_recipe(RECIPE)
    clearance = wc.Clearance.from_recipe(recipe)
    with tempfile.TemporaryDirectory() as tmp:
        manifest, out = _compile(Path(tmp))
        for r in _rows(out / "points.csv"):
            assert clearance.blocked(float(r["x"]), float(r["y"])) is None, r["point_id"]
        for r in _rows(out / "fx_anchors.csv"):
            assert clearance.blocked(float(r["x"]), float(r["y"])) is None, r["anchor_id"]
        assert manifest["counts"]["points_removed_by_clearance"] > 0  # the wake path crosses the field


def test_attribute_ranges():
    recipe, _ = wc.load_recipe(RECIPE)
    with tempfile.TemporaryDirectory() as tmp:
        manifest, out = _compile(Path(tmp))
        for r in _rows(out / "points.csv"):
            for col in ("hue_seed", "wind_phase", "wind_response", "sparkle_response", "hero_weight", "Resonance"):
                v = float(r[col])
                assert 0.0 <= v <= 1.0, (col, v)
            assert 0.0 <= float(r["yaw"]) < 360.0
            species = {s["species_id"]: s for s in recipe["species"]}[r["species_id"]]
            s_lo, s_hi = species.get("scale_range", recipe["field"]["scale_range"])
            assert s_lo * 0.85 <= float(r["scale"]) <= s_hi * 1.0 + 1e-6, (r["species_id"], r["scale"])
            assert int(r["EcologyClass"]) in (0, 1, 2)
            assert int(r["MaterialVariant"]) == int(r["band"])
            meshes = species.get("meshes") or [species["mesh"]]
            assert r["mesh"].split(".")[0] in meshes  # mesh follows variant_id
            assert int(r["variant_id"]) < int(species.get("variants", len(meshes)))
            # no two columns may differ only by case (FName is case-insensitive in UE)
            lowered = [c.lower() for c in wc.POINT_COLUMNS]
            assert len(set(lowered)) == len(lowered)


def test_fx_anchor_contract():
    recipe, _ = wc.load_recipe(RECIPE)
    with tempfile.TemporaryDirectory() as tmp:
        manifest, out = _compile(Path(tmp))
        rows = _rows(out / "fx_anchors.csv")
        assert list(rows[0].keys()) == wc.FX_COLUMNS
        kinds = {}
        for r in rows:
            kinds[r["fx_kind"]] = kinds.get(r["fx_kind"], 0) + 1
            assert 300 <= float(r["bounds_cm"]) <= 500
            assert r["system"].startswith("/Game/Melodia/VFX/NS_Morning_")
            if r["fx_kind"] in ("petal", "pollen"):
                assert r["material_instance"].endswith(f"_B{r['band']}")
        bands = recipe["field"]["band_count"]
        assert kinds["petal"] == bands * recipe["fx"]["anchors_per_band"]["petal"]
        assert kinds["pollen"] == bands * recipe["fx"]["anchors_per_band"]["pollen"]
        assert kinds["mist"] == recipe["fx"]["mist_anchors"]
        assert kinds["windfront"] == recipe["fx"]["windfront_anchors"]
        assert 10 <= len(rows) <= 20


def test_signal_stage_reports_wind_lanes():
    recipe, _ = wc.load_recipe(RECIPE)
    bindings, stage = wc.stage_signal(recipe)
    lanes = {c["lane"] for c in bindings["lane_checks"]}
    assert {"Cymatic_WindDirX", "Cymatic_WindDirY", "Cymatic_WindStrength", "WindDirX", "WindDirY", "WindStrength"} <= lanes
    assert stage["status"] in ("PASS", "SKIPPED")  # SKIPPED only when the MPC uasset is an LFS pointer


def test_no_unreal_import_in_compiler():
    import ast

    tree = ast.parse((ROOT / "Tools" / "world_compiler.py").read_text(encoding="utf-8"))
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            assert all(a.name.split(".")[0] != "unreal" for a in node.names)
        elif isinstance(node, ast.ImportFrom):
            assert (node.module or "").split(".")[0] != "unreal"


def test_retired_rainbow_scripts_are_gone():
    leftovers = sorted(p.name for p in (ROOT / "Content" / "Python").glob("rainbow_*.py"))
    assert leftovers == [], f"retire into Tools/world_compiler.py: {leftovers}"



def test_structures_absent_emits_no_structure_tables():
    recipe = json.loads(RECIPE.read_text(encoding="utf-8"))
    recipe.pop("structures", None)
    with tempfile.TemporaryDirectory() as td:
        path = Path(td) / "no_structures.v1.json"
        path.write_text(json.dumps(recipe), encoding="utf-8")
        manifest, out = _compile(Path(td), path)
    assert "structures" not in manifest["stages"]
    assert not any(name.startswith("structure") for name in manifest["tables"])
    assert "structures" not in manifest["ue_lane"]


def test_structures_mandala_slots_and_curves():
    recipe = json.loads(RECIPE.read_text(encoding="utf-8"))
    st = recipe["structures"]
    with tempfile.TemporaryDirectory() as td:
        manifest, out = _compile(Path(td))
        slots = _rows(out / "structure_slots.csv")
        curves = _rows(out / "structure_curves.csv")
        bake = json.loads((out / "structures_bake.json").read_text(encoding="utf-8"))
    assert manifest["stages"]["structures"]["status"] == "PASS"
    assert len(slots) == sum(r.get("count", st["layout"]["order"]) for r in st["layout"]["rings"])
    cx, cy, cz = st["layout"]["center_cm"]
    for row in slots:
        ring = st["layout"]["rings"][int(row["ring"])]
        r = math.hypot(float(row["x"]) - cx, float(row["y"]) - cy)
        assert abs(r - ring["radius_cm"]) < 0.01, row["slot_uid"]
        assert row["builder_id"].startswith(("MEL_", "NT"))
    for decor in st["decor"]:
        pts = [c for c in curves if c["curve_id"].startswith(decor["decor_id"])]
        assert pts, decor["decor_id"]
        if decor["curve"]["kind"] == "phyllotaxis":
            assert len(pts) == decor["curve"]["count"]
        if decor["curve"]["kind"] == "catenary":
            chain = [c for c in pts if c["curve_id"] == decor["decor_id"] + "_0"]
            top = cz + decor["curve"]["attach_height_cm"]
            assert abs(float(chain[0]["z"]) - top) < 0.01 and abs(float(chain[-1]["z"]) - top) < 0.01
            assert min(float(c["z"]) for c in chain) < top - 1.0
    assert set(bake["slots"]) == set(st["slots"])

def test_beauty_absent_emits_no_beauty_tables():
    recipe = json.loads(RECIPE.read_text(encoding="utf-8"))
    recipe.pop("beauty", None)
    with tempfile.TemporaryDirectory() as td:
        path = Path(td) / "no_beauty.v1.json"
        path.write_text(json.dumps(recipe), encoding="utf-8")
        manifest, out = _compile(Path(td), path)
    assert "beauty" not in manifest["stages"]
    assert not any(name.startswith("beauty") for name in manifest["tables"])
    assert "beauty_feed" not in manifest["ue_lane"]


def test_beauty_canon_defaults_match_live_contract():
    assert wc.BEAUTY_CANON["sender_name"] == "UE_Beauty"
    assert wc.BEAUTY_CANON["render_target"] == "/Game/Melodia/Lookdev/RT_UE_Beauty"
    assert wc.BEAUTY_CANON["sender_bp"] == "/Game/Melodia/Lookdev/BP_UE_BeautySender"
    assert (wc.BEAUTY_CANON["width"], wc.BEAUTY_CANON["height"]) == (1920, 1080)
    assert wc.BEAUTY_CANON["capture_source"] == "SCS_FinalColorLDR"


def test_beauty_present_emits_feed():
    recipe = json.loads(RECIPE.read_text(encoding="utf-8"))
    recipe["beauty"] = {
        "sender_name": "UE_Beauty",
        "render_target": wc.BEAUTY_CANON["render_target"],
        "sender_bp": wc.BEAUTY_CANON["sender_bp"],
    }
    assert wc.validate_recipe(recipe) == []
    with tempfile.TemporaryDirectory() as td:
        path = Path(td) / "with_beauty.v1.json"
        path.write_text(json.dumps(recipe), encoding="utf-8")
        manifest, out = _compile(Path(td), path)
        stage = manifest["stages"]["beauty"]
        # FAIL only when the canon uassets are missing from this checkout's disk.
        assert stage["status"] in ("PASS", "FAIL")
        if stage["status"] == "FAIL":
            assert any("missing on disk" in e for e in stage["errors"])
        feed = json.loads((out / "beauty_feed.json").read_text(encoding="utf-8"))
        assert feed["schema"] == "melodia.beauty_feed.v1"
        assert feed["sender_name"] == "UE_Beauty"
        assert (feed["width"], feed["height"]) == (1920, 1080)
        assert manifest["ue_lane"]["beauty_feed"]["sender_name"] == "UE_Beauty"
        assert manifest["tables"]["beauty_feed.json"]["rows"] == 1


def test_beauty_rejects_second_sender_name():
    recipe = json.loads(RECIPE.read_text(encoding="utf-8"))
    recipe["beauty"] = {
        "sender_name": "UE_Beauty_2",
        "render_target": wc.BEAUTY_CANON["render_target"],
        "sender_bp": wc.BEAUTY_CANON["sender_bp"],
    }
    feed, stage = wc.stage_beauty(recipe)
    assert stage["status"] == "FAIL"
    assert any("UE_Beauty" in e for e in stage["errors"])


def test_beauty_rejects_bad_paths():
    recipe = json.loads(RECIPE.read_text(encoding="utf-8"))
    recipe["beauty"] = {"sender_name": "UE Beauty", "render_target": "RT_UE_Beauty", "sender_bp": ""}
    errors = wc.validate_recipe(recipe)
    assert any("sender_name" in e and "beauty" in e for e in errors)
    assert any("render_target" in e and "beauty" in e for e in errors)
    assert any("sender_bp" in e and "beauty" in e for e in errors)


if __name__ == "__main__":
    failures = 0
    for name, fn in sorted(globals().items()):
        if name.startswith("test_") and callable(fn):
            try:
                fn()
                print(f"PASS {name}")
            except AssertionError as exc:
                failures += 1
                print(f"FAIL {name}: {exc}")
            except Exception as exc:  # pragma: no cover
                failures += 1
                print(f"ERROR {name}: {type(exc).__name__}: {exc}")
    print(f"\n{'ALL PASS' if not failures else str(failures) + ' FAILED'}")
    raise SystemExit(1 if failures else 0)
