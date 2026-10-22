#!/usr/bin/env python3
"""Derive the dressing-catalog seed from the artist's own house state.

Why this exists
---------------
`UMelodiaDressingSubsystem::GetDressingCatalogPath()` reserves
`/Game/MelodiaIntegration/Config/DA_MelodiaDressingCatalog` and the Dash plan
(`Docs/Research/DASH_MAGPIE_NATIVE_INTEGRATION_2026-08-31.md`) names that
DataAsset as the key -> hero-prop-set catalogue. It does not exist yet, and it
cannot be authored by hand: the correct content is *the props the artist
already placed*, keyed by the gameplay-tag family the artist already used
(`Room_bedroom`, `Prop_SM_Desk`, ...).

So the content is derived, not invented. This script joins two records that
already exist and emits the catalogue content as a spec:

  * `specs/p0/melusina_house_p0_dressing_state.json` - the artist's live state
    (97 placements: label, room, prop, mesh, tags, transform).
  * `Saved/Audit/house_level_audit.json` - the read-only level audit, which
    carries the material instance assigned to each placed actor.

Output: `specs/p0/melusina_dressing_catalog.v1.json`.

This script only reads. It never touches Content, never opens the editor and
never mutates the map. Running it again after the artist adds props regenerates
the seed; it never overwrites the artist's work.

Usage:
    python Tools/build_dressing_catalog_seed.py [--out <path>]
"""

from __future__ import annotations

import argparse
import collections
import json
import pathlib
import sys

REPO_ROOT = pathlib.Path(__file__).resolve().parents[1]
STATE_PATH = REPO_ROOT / "specs" / "p0" / "melusina_house_p0_dressing_state.json"
AUDIT_PATH = REPO_ROOT / "Saved" / "Audit" / "house_level_audit.json"
DEFAULT_OUT = REPO_ROOT / "specs" / "p0" / "melusina_dressing_catalog.v1.json"

# Layer tags the dressing pass understands. Derived from the census layers
# (base / enchanted_interiors) plus the functional interactables.
LAYER_OF_KIND = {
    "dressing": "base",
    "functional": "functional",
}


def _load(path: pathlib.Path) -> dict:
    if not path.exists():
        raise SystemExit(f"missing input: {path}")
    with path.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def _materials_by_label(audit: dict) -> dict[str, list[str]]:
    out: dict[str, list[str]] = {}
    for row in audit.get("dressing_detail", []) or []:
        label = row.get("label")
        if label:
            out[label] = list(row.get("materials") or [])
    return out


def _layer_for(actor: dict, materials: list[str]) -> str:
    """ECI props come from the Enchanted Interiors pack; everything else is base."""
    if any("/EnchantedInteriors/" in m for m in materials):
        return "enchanted_interiors"
    return LAYER_OF_KIND.get(actor.get("kind"), "base")


def build() -> dict:
    state = _load(STATE_PATH)
    audit = _load(AUDIT_PATH)
    materials = _materials_by_label(audit)

    families: dict[str, dict] = {}
    for actor in state.get("actors", []):
        room = actor.get("room") or "unassigned"
        prop = actor.get("prop") or "unassigned"
        family_tag = f"Room_{room}"
        prop_tag = f"Prop_{prop}"
        actor_materials = materials.get(actor.get("label", ""), [])
        layer = _layer_for(actor, actor_materials)

        family = families.setdefault(
            family_tag,
            {
                "family": family_tag,
                "room": room,
                "description": "",
                "props": [],
            },
        )
        prop_entry = next(
            (p for p in family["props"] if p["prop_tag"] == prop_tag), None
        )
        if prop_entry is None:
            prop_entry = {
                "prop_tag": prop_tag,
                "mesh": actor.get("mesh", ""),
                "materials": actor_materials,
                "count": 0,
                "layer": layer,
                "kind": actor.get("kind", "dressing"),
                "placements": [],
            }
            family["props"].append(prop_entry)
        prop_entry["count"] += 1
        if len(prop_entry["materials"]) < len(actor_materials):
            prop_entry["materials"] = actor_materials
        if layer == "enchanted_interiors" and prop_entry["layer"] == "base":
            prop_entry["layer"] = layer
        prop_entry["placements"].append(
            {
                "label": actor.get("label", ""),
                "location": actor.get("location", [0, 0, 0]),
                "rotation": actor.get("rotation", [0, 0, 0]),
            }
        )

    for family in families.values():
        family["props"].sort(key=lambda p: p["prop_tag"])
        family["prop_count"] = len(family["props"])
        family["placement_count"] = sum(p["count"] for p in family["props"])
        for prop in family["props"]:
            prop["placements"].sort(key=lambda p: p["label"])

    family_list = sorted(families.values(), key=lambda f: f["family"])
    total_props = sum(f["prop_count"] for f in family_list)
    total_placements = sum(f["placement_count"] for f in family_list)

    return {
        "contract_id": "melodia.p0.melusina_dressing_catalog.v1",
        "kind": "dressing_catalog_seed",
        "schema_version": "1.0",
        "package": {
            "package_id": "package.melusina_dressing_catalog",
            "display_name": "Melodia dressing catalogue - seed content",
            "content_kind": "dressing_catalog_seed",
            "status": "seed_content_ready_asset_pending",
        },
        "purpose": (
            "The content of DA_MelodiaDressingCatalog, derived from the props the "
            "artist already placed, keyed by the gameplay-tag family the artist "
            "already used. This is the catalogue the art pass (Dash role) reads: "
            "family tag -> hero prop set, so a dressing pass places existing "
            "library assets instead of inventing a new authority."
        ),
        "authority": {
            "source_of_truth": (
                "the map itself (/Game/Melodia/Levels/Opening/L_MelusinaHouse_P0). "
                "This file is its reproducible record, never a competing one."
            ),
            "generator": "Tools/build_dressing_catalog_seed.py",
            "inputs": [
                "specs/p0/melusina_house_p0_dressing_state.json",
                "Saved/Audit/house_level_audit.json",
            ],
            "target_asset": "/Game/MelodiaIntegration/Config/DA_MelodiaDressingCatalog",
            "asset_path_reserved_by": (
                "UMelodiaDressingSubsystem::GetDressingCatalogPath() "
                "(Source/BS_GodFile/MelodiaIntegration/MelodiaDressingSubsystem.cpp)"
            ),
            "guardrail": (
                "read-only derivation: the generator never touches Content, never "
                "opens the editor and never moves an actor."
            ),
        },
        "tag_vocabulary": {
            "family_tag": (
                "Room_<room> - the gameplay-tag family the catalogue is keyed by. "
                "One family per room: a dressing pass asks for a room, not a mesh."
            ),
            "prop_tag": "Prop_<mesh leaf name> - one hero prop inside a family.",
            "layer": {
                "base": "the Magician's Library architecture and furniture.",
                "enchanted_interiors": (
                    "Kitbash3D Enchanted Interiors props, converted onto "
                    "M_Master_Toon_Universal on 2026-10-21."
                ),
                "functional": "hand-placed interactables that carry the gameplay.",
            },
        },
        "totals": {
            "families": len(family_list),
            "props": total_props,
            "placements": total_placements,
        },
        "families": family_list,
        "rules": [
            "a family is a room, not a mesh list - the art pass asks for a room and "
            "gets that room's hero props",
            "a prop keeps its mesh and its material instance exactly as placed; the "
            "catalogue never re-points a prop at a different master",
            "a placement is recorded so the catalogue can be reconciled against the "
            "map, not so the map can be overwritten from the catalogue",
            "the catalogue is the fill layer's source of truth for WHICH props exist; "
            "the fill contract (specs/p0/melusina_house_p0_fill.v1.json) is the "
            "source of truth for WHERE and HOW MANY of them are placed",
            "no gameplay tag is invented here: the families use the tags the artist "
            "already set on the actors",
        ],
        "not_yet_true": [
            "the DataAsset itself does not exist - there is no UMelodiaDressingCatalog "
            "class, so this content cannot yet be loaded by the subsystem",
            "UMelodiaDressingSubsystem::DressHeroClutter is a scaffold: it logs and "
            "returns true, it does not place anything",
            "no family has been validated by an actual dressing pass - the catalogue "
            "records what exists, not what looks right",
        ],
    }


def main(argv: list[str]) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", default=str(DEFAULT_OUT))
    args = parser.parse_args(argv)

    payload = build()
    out_path = pathlib.Path(args.out)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    with out_path.open("w", encoding="utf-8") as handle:
        json.dump(payload, handle, indent=2, ensure_ascii=False)
        handle.write("\n")

    totals = payload["totals"]
    print(
        f"wrote {out_path} - {totals['families']} families, "
        f"{totals['props']} props, {totals['placements']} placements"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
