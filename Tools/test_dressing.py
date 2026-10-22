#!/usr/bin/env python3
"""Offline gate for the house dressing pipeline's DATA side. No engine required.

The Dash plan's delivery order (Docs/Research/DASH_MAGPIE_NATIVE_INTEGRATION_2026-08-31.md,
item 5) asks for `Tools/test_dressing.py`. This is it: a gate that runs in seconds on
any machine, with Unreal closed, and fails loudly when the dressing data and the
C++ that reads it drift apart.

What it proves:
  1. the catalogue seed parses, and every family has props;
  2. every family maps to a native gameplay tag that ACTUALLY EXISTS in the C++
     (the tag strings are read out of MelodiaDressingTags.cpp, not re-typed here);
  3. the catalogue generator is read-only: running it changes no tracked file;
  4. the three density textures exist, are 8-bit grayscale PNGs, and their bounds
     match the room volumes in the fill contract;
  5. the fill contract still says what it must: additive only, route excluded,
     one master, at most three species legible per frame.

What it does NOT prove: that anything compiles, that the PCG graphs run, or that a
prop ever lands in a room. Those need the engine and the walk.

Usage:
    python Tools/test_dressing.py
"""

from __future__ import annotations

import hashlib
import json
import pathlib
import re
import struct
import sys

REPO_ROOT = pathlib.Path(__file__).resolve().parents[1]
SEED_PATH = REPO_ROOT / "specs" / "p0" / "melusina_dressing_catalog.v1.json"
FILL_PATH = REPO_ROOT / "specs" / "p0" / "melusina_house_p0_fill.v1.json"
PIPELINE_PATH = REPO_ROOT / "specs" / "p0" / "melusina_room_dressing_pipeline.v1.json"
TAGS_CPP = REPO_ROOT / "Source" / "BS_GodFile" / "MelodiaIntegration" / "MelodiaDressingTags.cpp"
CATALOG_H = REPO_ROOT / "Source" / "BS_GodFile" / "MelodiaIntegration" / "MelodiaDressingCatalog.h"
GENERATOR = REPO_ROOT / "Tools" / "build_dressing_catalog_seed.py"
TEXTURE_DIR = REPO_ROOT / "Content" / "EnvSandbox" / "PCG" / "House" / "Textures"

# The artist vocabulary -> the native gameplay tag each family is keyed by.
# The tag STRINGS themselves are read out of the C++ below, so this table only
# holds the mapping, never the strings.
FAMILY_TO_NATIVE = {
    "Room_bedroom": "TAG_Room_Bedroom",
    "Room_landing": "TAG_Room_Landing",
    "Room_salon": "TAG_Room_Salon",
    "Room_any": "TAG_Room_Any",
}

failures: list[str] = []
checks = 0


def check(condition: bool, message: str) -> bool:
    global checks
    checks += 1
    if not condition:
        failures.append(message)
    return condition


def load_json(path: pathlib.Path) -> dict:
    with path.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def native_tag_strings() -> dict[str, str]:
    """Read {TAG_Var: "Tag.String"} out of the C++ that defines them."""
    text = TAGS_CPP.read_text(encoding="utf-8")
    found = dict(re.findall(r'UE_DEFINE_GAMEPLAY_TAG\((TAG_\w+),\s*"([^"]+)"\)', text))
    return found


def png_header(path: pathlib.Path) -> tuple[int, int, int, int]:
    """Return (width, height, bit_depth, colour_type) from a PNG's IHDR."""
    with path.open("rb") as handle:
        signature = handle.read(8)
        if signature != b"\x89PNG\r\n\x1a\n":
            raise ValueError("not a PNG")
        length = struct.unpack(">I", handle.read(4))[0]
        chunk = handle.read(4)
        if chunk != b"IHDR":
            raise ValueError("no IHDR")
        width, height, bit_depth, colour_type = struct.unpack(">IIBB", handle.read(10))
    return width, height, bit_depth, colour_type


def sha256(path: pathlib.Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def test_seed_shape() -> None:
    seed = load_json(SEED_PATH)
    check(seed.get("kind") == "dressing_catalog_seed", "the seed is not a dressing_catalog_seed")
    families = seed.get("families", [])
    check(len(families) > 0, "the seed holds no families")
    for family in families:
        check(bool(family.get("family")), f"a family has no name: {family}")
        check(len(family.get("props", [])) > 0, f"family {family.get('family')} has no props")
        for prop in family.get("props", []):
            check(bool(prop.get("prop_tag")), f"a prop in {family.get('family')} has no prop_tag")
            check("mesh" in prop, f"prop {prop.get('prop_tag')} has no mesh field")
    totals = seed.get("totals", {})
    check(totals.get("placements") == sum(f["placement_count"] for f in families),
          "the seed's placement total does not match its families")


def test_family_tags_exist_in_cpp() -> None:
    tags = native_tag_strings()
    check(len(tags) >= 4, f"the C++ defines only {len(tags)} native tags")
    seed = load_json(SEED_PATH)
    for family in seed.get("families", []):
        artist_tag = family.get("family")
        variable = FAMILY_TO_NATIVE.get(artist_tag)
        if not check(variable is not None, f"family {artist_tag} has no native tag mapping"):
            continue
        check(variable in tags, f"the native tag {variable} is not defined in MelodiaDressingTags.cpp")
        if variable in tags:
            check(tags[variable].startswith("Melodia.Dressing."),
                  f"the native tag {variable} is '{tags[variable]}' - it is not in the Melodia.Dressing namespace")
    # The header must actually declare the catalogue class the subsystem loads.
    header = CATALOG_H.read_text(encoding="utf-8")
    check("class BS_GODFILE_API UMelodiaDressingCatalog : public UDataAsset" in header,
          "MelodiaDressingCatalog.h does not declare the UDataAsset")


def test_generator_is_read_only() -> None:
    """Run the generator into a scratch path and prove the tracked files do not move."""
    watched = [SEED_PATH, FILL_PATH, PIPELINE_PATH]
    before = {p: sha256(p) for p in watched if p.exists()}
    import tempfile

    with tempfile.TemporaryDirectory() as tmp:
        out = pathlib.Path(tmp) / "seed.json"
        import subprocess
        result = subprocess.run(
            [sys.executable, str(GENERATOR), "--out", str(out)],
            capture_output=True, text=True)
        check(result.returncode == 0, f"the catalogue generator failed: {result.stderr.strip()[:200]}")
        check(out.exists(), "the catalogue generator wrote no output")
        if out.exists():
            regenerated = load_json(out)
            live = load_json(SEED_PATH)
            check(regenerated.get("totals") == live.get("totals"),
                  "regenerating the catalogue changed its totals - the seed is stale")
    after = {p: sha256(p) for p in watched if p.exists()}
    check(before == after, "running the generator changed a tracked file - it is not read-only")


def test_density_textures() -> None:
    fill = load_json(FILL_PATH)
    density = fill.get("density_textures", {})
    check(density.get("status") == "DERIVED_FIRST_PASS_READY_TO_PAINT",
          "the fill contract does not record the derived density textures")
    for room in fill.get("rooms", {}):
        path = TEXTURE_DIR / f"dressing_heatmap_{room}.png"
        if not check(path.exists(), f"the density texture for {room} is missing: {path}"):
            continue
        width, height, bit_depth, colour_type = png_header(path)
        check(bit_depth == 8, f"{path.name} is {bit_depth}-bit, not 8-bit")
        check(colour_type == 0, f"{path.name} is colour type {colour_type}, not grayscale")
        volume = fill["rooms"][room]["volume"]
        xs = re.search(r"x\s*\[\s*(-?\d+(?:\.\d+)?)\s*,\s*(-?\d+(?:\.\d+)?)", volume)
        ys = re.search(r"y\s*\[\s*(-?\d+(?:\.\d+)?)\s*,\s*(-?\d+(?:\.\d+)?)", volume)
        if xs and ys:
            span_x = float(xs.group(2)) - float(xs.group(1))
            span_y = float(ys.group(2)) - float(ys.group(1))
            expected_w = int(round(span_x * 2))
            expected_h = int(round(span_y * 2))
            check(width == expected_w and height == expected_h,
                  f"{path.name} is {width}x{height}, but the room volume implies {expected_w}x{expected_h} at 0.5 m/px")


def test_fill_contract_rules() -> None:
    fill = load_json(FILL_PATH)
    rules = " ".join(fill.get("rules", [])).lower()
    for phrase in ("additive", "master_toon_universal"):
        check(phrase in rules, f"the fill contract no longer states the '{phrase}' rule")
    exclusions = " ".join(fill.get("exclusions", [])).lower()
    check("route" in exclusions, "the fill contract no longer excludes the route")
    check("medallion" in exclusions, "the fill contract no longer excludes the medallion footprint")
    species_total = sum(len(room.get("species", [])) for room in fill.get("rooms", {}).values())
    check(species_total == 9, f"the fill contract has {species_total} species rows, not 9")


def test_contracts_name_nodes_that_exist() -> None:
    """Every PCG node the contracts name must exist in the engine or the plugin.

    This is the gate that would have caught the PCGDensityData mistake: the fill
    contract named a class that does not exist in UE 5.8, and nobody would have
    found out until someone opened the editor and looked for it.
    """
    graph_spec = load_json(REPO_ROOT / "specs" / "p0" / "melusina_house_p0_fill_graphs.v1.json")
    kit_spec = load_json(REPO_ROOT / "specs" / "p0" / "melusina_room_kit.v1.json")

    # Collect the node names the contracts use.
    named: set[str] = set()
    for entry in graph_spec.get("node_chain", []):
        node = entry.get("node", "")
        for part in node.split(" / "):
            part = part.strip()
            if part:
                named.add(part)
    for entry in graph_spec.get("mechanism_correction", {}).get("true_now", []):
        for candidate in ("PCGExGetTextureData", "PCGExSampleTexture", "PCGExSelectorDensityWeighted", "PCGDensityFilter"):
            if candidate in entry:
                named.add(candidate)

    # Where to look: the engine's PCG plugin and this project's PCGExtendedToolkit.
    search_roots = [
        pathlib.Path(r"C:\Program Files\Epic Games\UE_5.8\Engine\Plugins\PCG\Source"),
        REPO_ROOT / "Plugins" / "PCGExtendedToolkit" / "Source",
    ]
    headers: list[str] = []
    for root in search_roots:
        if root.exists():
            headers.extend(str(p) for p in root.rglob("*.h"))

    for node in sorted(named):
        stem = node.split(".")[-1]
        found = any(pathlib.Path(h).stem == stem for h in headers)
        check(found, f"the fill contract names the node '{node}' but no {stem}.h exists in the PCG plugin or PCGExtendedToolkit")

    # The correction must still be recorded: the old, non-existent class must not
    # come back as if it were real.
    fill = load_json(FILL_PATH)
    mechanism = fill.get("pcg_graph", {}).get("density_mechanism", {})
    check(bool(mechanism), "the fill contract no longer records how the density actually works")
    # PCGDensityData may appear ONLY in a sentence that says it does not exist.
    live = {k: v for k, v in fill.get("pcg_graph", {}).items()
            if k not in ("density_mechanism", "mechanism_correction")}
    for key, value in live.items():
        blob = json.dumps(value)
        for match in re.finditer(r"PCGDensityData", blob):
            lead = blob[max(0, match.start() - 60):match.start()].lower()
            check(("no " in lead or "not " in lead),
                  f"the fill contract's pcg_graph.{key} uses PCGDensityData as if it existed")
    check("Alpha" in json.dumps(mechanism), "the ColorChannel=Alpha gotcha is no longer recorded")


def test_room_kit_contract() -> None:
    kit = load_json(REPO_ROOT / "specs" / "p0" / "melusina_room_kit.v1.json")
    children = " ".join(child.get("type", "") + child.get("name", "") for child in kit.get("children", []))
    check("CarrierSlot" in children, "the room kit has no carrier slot")
    check("FIXED CHILD" in children.upper(), "the room kit's carrier is not a fixed child (Jev, 2026-10-22)")
    meter = kit.get("meter", {})
    check(meter.get("module_m") == 0.6, "the room kit's module is not 0.6 m")
    check(meter.get("bay_m") == 2.4, "the room kit's bay is not 2.4 m")
    check(meter.get("bpm") == 128, "the room kit's tempo is not 128 BPM")
    frozen = kit.get("frozen_metrics", {})
    for key in ("pivot", "footprint", "transition"):
        check(key in frozen, f"the room kit does not freeze the '{key}' metric")
    check(bool(kit.get("story_tags")), "the room kit carries no story tags (Infold's 'fashion as narrative', 2026-10-22)")
    rules = " ".join(kit.get("placement_rules", []))
    check("never move" in rules or "never moves" in rules,
          "the room kit does not say that it may not move a hand-placed actor")


def main() -> int:
    print("=" * 68)
    print("DRESSING PIPELINE - OFFLINE DATA GATE (no engine)")
    print("=" * 68)
    for test in (test_seed_shape, test_family_tags_exist_in_cpp, test_generator_is_read_only,
                 test_density_textures, test_fill_contract_rules,
                 test_contracts_name_nodes_that_exist, test_room_kit_contract):
        name = test.__name__
        before = len(failures)
        try:
            test()
        except Exception as exc:  # a gate that crashes is a gate that failed
            failures.append(f"{name} raised {type(exc).__name__}: {exc}")
        status = "ok" if len(failures) == before else "FAIL"
        print(f"   {status:>4}  {name}")

    print(f"\n{checks - len(failures)}/{checks} checks passed")
    if failures:
        print("\nFAILURES:")
        for failure in failures:
            print(f"   - {failure}")
        return 1
    print("the dressing DATA is consistent with the C++ that reads it")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
