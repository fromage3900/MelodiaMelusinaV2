"""Validate and flatten a Resonant PCG plan for the editor proof lane.

This is a pure-Python bridge for the current workspace state.  It verifies
that a generated plan can be handed to the existing scale-world PCG owner and
emits the exact hero inputs plus a compact summary of wardrobe and magic
passage metadata.  It intentionally does not import ``unreal`` or mutate a
map; the editor lane can consume this envelope when its single-editor control
surface is available.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any, Mapping

from resonant_world_pcg_adapter import (
    hero_graph_specs_from_resonant_plan,
    validate_resonant_pcg_plan,
)


HANDOFF_VERSION = "resonant_world_proof_handoff_v1"


def _read_json(path: str | Path) -> dict[str, Any]:
    target = Path(path)
    if not target.exists():
        raise FileNotFoundError(f"Resonant PCG plan not found: {target}")
    data = json.loads(target.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise ValueError("Resonant PCG plan root is not an object")
    return data


def build_proof_handoff(plan: Mapping[str, Any], *, source_path: str | Path | None = None) -> dict[str, Any]:
    errors = validate_resonant_pcg_plan(plan)
    if errors:
        raise ValueError(f"Resonant PCG plan is invalid: {errors}")
    hero_specs = hero_graph_specs_from_resonant_plan(plan)
    hero_inputs = []
    for label, graph, origin, spec in hero_specs:
        hero_inputs.append({
            "label": label,
            "graph": graph,
            "origin_cm": list(origin),
            "chunk": [spec.get("chunk_x"), spec.get("chunk_y")],
            "profile": spec.get("profile"),
            "tags": list(spec.get("tags", [])),
            "resonant_world": dict(spec.get("resonant_world", {})),
            "data_layers": list(spec.get("data_layers", [])),
            "hlod_layers": list(spec.get("hlod_layers", [])),
            "interactive_ownership": {
                "gameplay_data_layer": "DL_Musical_HeroGameplay",
                "exclude_from_hlod": True,
            },
        })
    wardrobe = dict(plan.get("wardrobe_voicing", {}))
    passage = dict(plan.get("magic_passage", {}))
    return {
        "format": "melodia_resonant_world_proof_handoff",
        "schema_version": 1,
        "handoff_version": HANDOFF_VERSION,
        "source_plan": str(source_path) if source_path else None,
        "world_seed": int(plan["world_seed"]),
        "proof_level": plan.get("proof_level"),
        "pcg_owner": "existing pcg_scale_world_pipeline + pcg_visual_chunk_builder",
        "graph_reuse": bool(plan.get("graph_reuse")),
        "hero_inputs": hero_inputs,
        "hero_input_count": len(hero_inputs),
        "static_spec_count": int(plan.get("static_spec_count", 0)),
        "chunk_count": int(plan.get("chunk_count", 0)),
        "movement_ids": sorted({str(chunk.get("movement_id")) for chunk in plan.get("chunks", [])}),
        "wardrobe_voicing": {
            "applied": bool(wardrobe),
            "request_id": wardrobe.get("request_id"),
            "archetype_id": wardrobe.get("archetype_id"),
            "does_not_grant_capability": wardrobe.get("does_not_grant_capability"),
        },
        "magic_passage": {
            "applied": bool(passage),
            "passage_id": passage.get("passage_id"),
            "world_verb": passage.get("world_verb"),
            "stage_count": passage.get("stage_count"),
            "does_not_write_save": passage.get("does_not_write_save"),
        },
        "editor_apply": {
            "required": True,
            "performed": False,
            "single_editor_only": True,
            "production_maps_touched": False,
        },
    }


def validate_proof_handoff(handoff: Mapping[str, Any]) -> list[str]:
    errors: list[str] = []
    if handoff.get("format") != "melodia_resonant_world_proof_handoff":
        errors.append("unexpected proof handoff format")
    if handoff.get("handoff_version") != HANDOFF_VERSION:
        errors.append("unexpected proof handoff version")
    if int(handoff.get("hero_input_count", 0)) != len(handoff.get("hero_inputs", [])):
        errors.append("hero_input_count does not match hero_inputs")
    if not handoff.get("graph_reuse"):
        errors.append("proof handoff must reuse existing graphs")
    for hero in handoff.get("hero_inputs", []):
        if not str(hero.get("graph", "")).startswith("/Game/"):
            errors.append(f"hero graph is not an explicit Unreal asset path: {hero.get('graph')}")
        if not hero.get("resonant_world", {}).get("movement_id"):
            errors.append(f"hero input is missing movement metadata: {hero.get('label')}")
    editor_apply = handoff.get("editor_apply", {})
    if editor_apply.get("performed") is not False:
        errors.append("pure proof handoff must not claim editor mutation")
    if editor_apply.get("production_maps_touched") is not False:
        errors.append("proof handoff must not touch production maps")
    return errors


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--plan", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    return parser.parse_args()


def main() -> int:
    args = _parse_args()
    handoff = build_proof_handoff(_read_json(args.plan), source_path=args.plan)
    handoff["validation_errors"] = validate_proof_handoff(handoff)
    handoff["ok"] = not handoff["validation_errors"]
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(handoff, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({
        "ok": handoff["ok"],
        "output": str(args.output),
        "hero_inputs": handoff["hero_input_count"],
        "static_specs": handoff["static_spec_count"],
        "production_maps_touched": handoff["editor_apply"]["production_maps_touched"],
        "errors": handoff["validation_errors"],
    }, indent=2))
    return 0 if handoff["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
