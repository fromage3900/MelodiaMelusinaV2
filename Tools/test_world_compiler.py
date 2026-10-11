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


def _parse_rotation(rot: str) -> dict[str, float]:
    vals: dict[str, float] = {}
    for part in rot.strip("()").split(","):
        k, v = part.split("=")
        vals[k] = float(v)
    return vals


def test_glitter_brightness_expands_mis():
    recipe = json.loads(RECIPE.read_text(encoding="utf-8"))
    assert wc.validate_recipe(recipe) == []
    with tempfile.TemporaryDirectory() as tmp:
        manifest, out = _compile(Path(tmp))
        lane = json.loads((out / "dressing_table.json").read_text(encoding="utf-8"))["glitter_lane"]
    steps = recipe["palette"]["glitter"]["brightness_steps"]
    assert len(lane["bands"]) == 7 * len(steps)
    names = [b["material_instance"] for b in lane["bands"]]
    assert len(set(names)) == len(names), "MI names must be unique"
    prefix = recipe["palette"]["glitter"]["mi_prefix"]
    for b in recipe["palette"]["bands"]:
        canon = f"{prefix}{b['label']}"
        assert canon in names, f"canonical MI preserved: {canon}"
    for b in lane["bands"]:
        base = next(t for t in recipe["palette"]["bands"] if t["label"] == b["label"])["tint"]
        for c, t in zip(base, b["tint"]):
            assert abs(t - min(4.0, c * b["brightness"])) < 1e-6, b["material_instance"]


def test_glitter_points_reference_forged_mis():
    with tempfile.TemporaryDirectory() as tmp:
        manifest, out = _compile(Path(tmp))
        lane = json.loads((out / "dressing_table.json").read_text(encoding="utf-8"))["glitter_lane"]
        forged = {b["material_instance"] for b in lane["bands"]}
        for r in _rows(out / "points.csv"):
            if r["species_id"].startswith("melody_glitter"):
                mat = r["material"].split(".")[0]
                assert mat in forged, (r["point_id"], mat)


def test_fairy_flat_lay_and_scale():
    recipe = json.loads(RECIPE.read_text(encoding="utf-8"))
    fairy = next(s for s in recipe["species"] if s["species_id"] == "melody_glitter_fairy")
    with tempfile.TemporaryDirectory() as tmp:
        manifest, out = _compile(Path(tmp))
        rows = [r for r in _rows(out / "points.csv") if r["species_id"] == "melody_glitter_fairy"]
    assert rows, "fairy species must emit points"
    lo, hi = fairy["scale_range"]
    for r in rows:
        assert lo * 0.85 <= float(r["scale"]) <= hi * 1.0 + 1e-6, (r["point_id"], r["scale"])
        pitch = _parse_rotation(r["Rotation"])["Pitch"]
        assert fairy["pitch_deg"] - fairy["pitch_jitter_deg"] - 1e-6 <= pitch <= fairy["pitch_deg"] + fairy["pitch_jitter_deg"] + 1e-6, (r["point_id"], pitch)


def test_trail_arcs_emit_marked_rows():
    recipe = json.loads(RECIPE.read_text(encoding="utf-8"))
    arcs = recipe["field"]["trail_arcs"]
    ax, ay, _ = recipe["place"]["anchor_cm"]
    clearance = wc.Clearance.from_recipe(recipe)
    with tempfile.TemporaryDirectory() as tmp:
        manifest, out = _compile(Path(tmp))
        rows = [r for r in _rows(out / "points.csv") if int(r["cluster_id"]) >= 900]
    assert rows, "trail arcs must emit rows"
    total = sum(a["count"] for a in arcs)
    assert len(rows) <= total, "trails only lose rows to ground/clearance"
    assert len(rows) >= total * 0.5, "trails must mostly survive"
    for r in rows:
        arc = arcs[int(r["cluster_id"]) - 900]
        assert r["species_id"] == arc["species_id"]
        d = math.hypot(float(r["x"]) - ax, float(r["y"]) - ay)
        assert abs(d - arc["radius_cm"]) <= arc["width_cm"] + 0.01, (r["point_id"], d)
        assert clearance.blocked(float(r["x"]), float(r["y"])) is None, r["point_id"]


def test_trail_rejects_unknown_species():
    recipe = json.loads(RECIPE.read_text(encoding="utf-8"))
    recipe["field"]["trail_arcs"] = [
        {"species_id": "nope_not_real", "angle_center_deg": 0.0, "span_deg": 10.0, "radius_cm": 500.0, "count": 3}
    ]
    assert any("trail_arcs" in e for e in wc.validate_recipe(recipe))


def test_absent_glitter_keys_legacy_output():
    recipe = json.loads(RECIPE.read_text(encoding="utf-8"))
    recipe["species"] = [s for s in recipe["species"] if s["species_id"] != "melody_glitter_fairy"]
    for s in recipe["species"]:
        s.pop("pitch_deg", None)
        s.pop("pitch_jitter_deg", None)
    recipe["field"].pop("trail_arcs", None)
    recipe["palette"]["glitter"].pop("brightness_steps", None)
    assert wc.validate_recipe(recipe) == []
    with tempfile.TemporaryDirectory() as tmp:
        path = Path(tmp) / "legacy_glitter.v1.json"
        path.write_text(json.dumps(recipe), encoding="utf-8")
        manifest, out = _compile(Path(tmp), path)
        lane = json.loads((out / "dressing_table.json").read_text(encoding="utf-8"))["glitter_lane"]
        rows = _rows(out / "points.csv")
    prefix = recipe["palette"]["glitter"]["mi_prefix"]
    assert len(lane["bands"]) == 7
    assert [b["material_instance"] for b in lane["bands"]] == [f"{prefix}{b['label']}" for b in recipe["palette"]["bands"]]
    assert not [r for r in rows if int(r["cluster_id"]) >= 900]
    for r in rows:
        assert _parse_rotation(r["Rotation"])["Pitch"] == 0.0, r["point_id"]


def test_wind_lane_covers_mesh_variants():
    recipe = json.loads(RECIPE.read_text(encoding="utf-8"))
    assert wc.validate_recipe(recipe) == []
    with tempfile.TemporaryDirectory() as tmp:
        manifest, out = _compile(Path(tmp))
        lane = json.loads((out / "dressing_table.json").read_text(encoding="utf-8"))["wind_lane"]
    names = [b["material_instance"] for b in lane["bands"]]
    assert len(names) == len(set(names)), "wind MI names must be unique"
    prefix = recipe["palette"]["wind"]["mi_prefix"]
    for b in recipe["palette"]["bands"]:
        assert f"{prefix}{b['label']}" in names, f"canonical wind MI preserved: {b['label']}"
    # Every suffixed mesh variant the points reference must have a forged twin
    # carrying the same tint + the lane response/overrides.
    for r_suffix in ("_Tall",):
        twins = [b for b in lane["bands"] if b["material_instance"].endswith(r_suffix)]
        assert len(twins) == len(recipe["palette"]["bands"]), r_suffix
        for t in twins:
            base = next(b for b in lane["bands"] if b["material_instance"] == t["material_instance"][: -len(r_suffix)])
            assert t["tint"] == base["tint"] and t["band"] == base["band"], t["material_instance"]
    assert lane["response"] == recipe["palette"]["wind"]["response"]
    assert lane["scalar_overrides"] == (recipe["palette"]["wind"].get("scalar_overrides") or {})


def test_wind_absent_suffixes_legacy_seven():
    recipe = json.loads(RECIPE.read_text(encoding="utf-8"))
    for s in recipe["species"]:
        s.pop("mesh_mi_suffixes", None)
    assert wc.validate_recipe(recipe) == []
    with tempfile.TemporaryDirectory() as tmp:
        path = Path(tmp) / "no_suffix.v1.json"
        path.write_text(json.dumps(recipe), encoding="utf-8")
        manifest, out = _compile(Path(tmp), path)
        lane = json.loads((out / "dressing_table.json").read_text(encoding="utf-8"))["wind_lane"]
    prefix = recipe["palette"]["wind"]["mi_prefix"]
    assert [b["material_instance"] for b in lane["bands"]] == [f"{prefix}{b['label']}" for b in recipe["palette"]["bands"]]


HARMONY = ROOT / "recipes" / "harmonic_planet_lydian_c.v1.json"


def test_harmony_deterministic_and_shaped():
    with tempfile.TemporaryDirectory() as a, tempfile.TemporaryDirectory() as b:
        m1, out1 = _compile(Path(a), HARMONY)
        m2, out2 = _compile(Path(b), HARMONY)
        assert m1["manifest_sha256"] == m2["manifest_sha256"]
        assert m1["stages"]["harmony"]["status"] == "PASS"
        meta = json.loads((out1 / "harmony.json").read_text(encoding="utf-8"))
        res = meta["resolution"]
        assert (out1 / "harmony_height.r16").stat().st_size == res * res * 2
        nodes = _rows(out1 / "harmony_nodes.csv")
        peaks = [n for n in nodes if n["kind"] == "peak"]
        valleys = [n for n in nodes if n["kind"] == "valley"]
        assert len(valleys) == 4 and len(peaks) == 5
        # rising arpeggio => rising peaks; valleys sit below the anchor plane
        heights = [float(p["height_cm"]) for p in peaks]
        assert heights == sorted(heights)
        assert sum(float(v["z"]) < 0 for v in valleys) >= 3
        edges = _rows(out1 / "harmony_edges.csv")
        ids = {n["node_id"] for n in nodes}
        assert all(e["start_node"] in ids and e["end_node"] in ids for e in edges)


def test_harmony_rejects_unknown_quality():
    recipe, _ = wc.load_recipe(HARMONY)
    recipe["harmony"]["progression"][0]["quality"] = "lydian_dominant"
    assert wc.validate_recipe(recipe)


def test_harmony_absent_emits_no_harmony_tables():
    with tempfile.TemporaryDirectory() as tmp:
        manifest, out = _compile(Path(tmp))
        assert "harmony" not in manifest["stages"]
        assert "harmony" not in manifest["ue_lane"]
        assert not any(p.name.startswith("harmony") for p in out.iterdir())


MEADOW = ROOT / "recipes" / "morning_meadow.v1.json"


def test_meadow_deterministic_on_soil_outside_clearance():
    recipe, _ = wc.load_recipe(MEADOW)
    ground = wc.load_ground_mask(recipe)
    clearance = wc.Clearance.from_recipe(recipe)
    with tempfile.TemporaryDirectory() as a, tempfile.TemporaryDirectory() as b:
        m1, out1 = _compile(Path(a), MEADOW)
        m2, _ = _compile(Path(b), MEADOW)
        assert m1["manifest_sha256"] == m2["manifest_sha256"]
        assert m1["stages"]["meadow"]["status"] == "PASS"
        rows = _rows(out1 / "meadow_points.csv")
        assert len(rows) > 1000
        names = {sp["species_id"] for sp in recipe["meadow"]["species"]}
        assert {r["species_id"] for r in rows} <= names
        for r in rows:
            x, y = float(r["x"]), float(r["y"])
            assert ground.ground_z(x, y) is not None, "grass off probed soil"
            assert clearance.blocked(x, y) is None, "grass inside a clearance zone"
        assert m1["ue_lane"]["meadow"]["field_sha256"]


def test_meadow_health_drives_species_and_density():
    recipe, _ = wc.load_recipe(MEADOW)
    with tempfile.TemporaryDirectory() as tmp:
        _, out = _compile(Path(tmp), MEADOW)
        rows = _rows(out / "meadow_points.csv")
        hi = [float(r["Resonance"]) for r in rows if r["species_id"] == "kikuyu_lush"]
        lo = [float(r["Resonance"]) for r in rows if r["species_id"] == "kikuyu_sparse"]
        assert hi and lo and sum(hi) / len(hi) > sum(lo) / len(lo)   # lush tufts sit in healthier cells


def test_meadow_rejects_bad_species():
    recipe, _ = wc.load_recipe(MEADOW)
    recipe["meadow"]["species"][0].pop("material")
    assert any("material" in e for e in wc.validate_recipe(recipe))


def test_meadow_absent_emits_no_meadow_tables():
    with tempfile.TemporaryDirectory() as tmp:
        manifest, out = _compile(Path(tmp))
        assert "meadow" not in manifest["stages"] and "meadow" not in manifest["ue_lane"]
        assert not any(p.name.startswith("meadow") for p in out.iterdir())


ARCH = ROOT / "recipes" / "kaleido_archipelago.v1.json"


def test_archipelago_deterministic_and_melodic():
    recipe, _ = wc.load_recipe(ARCH)
    with tempfile.TemporaryDirectory() as a, tempfile.TemporaryDirectory() as b:
        m1, out1 = _compile(Path(a), ARCH)
        m2, _ = _compile(Path(b), ARCH)
        assert m1["manifest_sha256"] == m2["manifest_sha256"]
        assert m1["stages"]["archipelago"]["status"] == "PASS"
        rows = _rows(out1 / "archipelago.csv")
        assert len(rows) == recipe["archipelago"]["count"]
        assert float(rows[0]["radius_cm"]) == max(float(r["radius_cm"]) for r in rows)   # tonic = hero island
        assert {r["biome"] for r in rows} <= {"meadow", "grove", "crystal"}
        for r in rows[:-1]:
            assert float(r["bridge_len_cm"]) > 0 and int(r["next_island"]) == int(r["island_id"]) + 1
        assert rows[-1]["next_island"] == "-1"
        assert m1["ue_lane"]["archipelago"]["islands"] == len(rows)


def test_archipelago_rejects_bad_mode():
    recipe, _ = wc.load_recipe(ARCH)
    recipe["archipelago"]["mode"] = "not_a_mode"
    assert any("archipelago" in e and "mode" in e for e in wc.validate_recipe(recipe))


def test_archipelago_bridges_span_next_island_edges():
    recipe, _ = wc.load_recipe(ARCH)
    with tempfile.TemporaryDirectory() as tmp:
        m, out = _compile(Path(tmp), ARCH)
        isl = _rows(out / "archipelago.csv")
        br = _rows(out / "archipelago_bridges.csv")
        assert len(br) == len(isl) - 1 and m["ue_lane"]["archipelago"]["bridges"] == len(br)
        for b in br:
            a, n = isl[int(b["from_island"])], isl[int(b["to_island"])]
            assert abs(float(b["scale_x"]) * float(b["mesh_length_cm"]) - float(b["length_cm"])) < 0.002 * float(b["length_cm"])
            assert abs(float(b["z"]) - float(a["top_z_cm"])) < 0.5
            assert float(b["length_cm"]) > 0


def test_archipelago_without_bridge_emits_no_bridge_table():
    recipe, _ = wc.load_recipe(ARCH)
    recipe["archipelago"].pop("bridge")
    assert not wc.validate_recipe(recipe)


CHOIR = ROOT / "recipes" / "infinitescore_choir.v1.json"


def test_archipelago_set_pieces_and_visual_scale():
    recipe, _ = wc.load_recipe(CHOIR)
    with tempfile.TemporaryDirectory() as tmp:
        m, out = _compile(Path(tmp), CHOIR)
        isl = _rows(out / "archipelago.csv")
        sp = _rows(out / "archipelago_set_pieces.csv")
        assert len(sp) == len(recipe["archipelago"]["set_pieces"]) >= 1
        assert all(float(r["target_length_cm"]) > 0 and 0 <= int(r["island"]) < len(isl) for r in sp)
        assert float(isl[0]["scale"]) > 10.0     # pool scale ~6.8 x visual_scale_mult 2.5


def test_archipelago_absent_emits_no_tables():
    with tempfile.TemporaryDirectory() as tmp:
        manifest, out = _compile(Path(tmp))
        assert "archipelago" not in manifest["stages"] and "archipelago" not in manifest["ue_lane"]
        assert not (out / "archipelago.csv").exists()


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
