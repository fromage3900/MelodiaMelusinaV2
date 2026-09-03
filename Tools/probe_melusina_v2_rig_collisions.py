"""Read-only report of ARP-to-contract bone-name collisions in v22."""

from __future__ import annotations

import json
from collections import defaultdict
from pathlib import Path
import bpy


PROJECT = Path(__file__).resolve().parents[1]


def main() -> int:
    mapping = json.loads((PROJECT / "specs/anim_presets/melusina_contract_bones.json").read_text(encoding="utf-8"))
    semantic = dict(mapping.get("semantic_map", {}))
    semantic.update(mapping.get("weight_group_map", {}))
    rig = bpy.data.objects.get("character_rig")
    destinations = defaultdict(list)
    source_meta = {}
    for bone in rig.data.bones:
        sanitized = bone.name.replace(".", "_")
        destinations[semantic.get(sanitized, sanitized)].append(bone.name)
        source_meta[bone.name] = {"use_deform": bool(bone.use_deform), "parent": bone.parent.name if bone.parent else None}
    collisions = {destination: sources for destination, sources in destinations.items() if len(sources) > 1}
    final_names = set()
    for destination, sources in destinations.items():
        deform_sources = [source for source in sources if rig.data.bones.get(source).use_deform]
        keep = deform_sources[0] if deform_sources else sources[0]
        if destination in mapping["bone_names"]:
            final_names.add(destination)
    report = {
        "schema": "melodia.melusina_v2_rig_collision_probe.v1",
        "stage": bpy.data.filepath,
        "source_bone_count": len(rig.data.bones),
        "collision_count": len(collisions),
        "collisions": collisions,
        "collision_metadata": {
            destination: {source: source_meta[source] for source in sources}
            for destination, sources in collisions.items()
        },
        "mapped_contract_names": sorted(final_names & set(mapping["bone_names"])),
        "missing_contract_names": sorted(set(mapping["bone_names"]) - final_names),
        "source_candidates_for_missing": {
            missing: [
                bone.name for bone in rig.data.bones
                if missing.lower().replace("_", "") in bone.name.lower().replace(".", "").replace("_", "")
            ][:24]
            for missing in sorted(set(mapping["bone_names"]) - final_names)
        },
        "source_candidate_metadata": {
            bone.name: {"use_deform": bool(bone.use_deform), "parent": bone.parent.name if bone.parent else None}
            for bone in rig.data.bones
            if any(token in bone.name.lower() for token in ("_ref.", "_rot.", "root.x", "root_master"))
        },
    }
    path = PROJECT / "Saved/Audit/melusina_v2_rig_collision_probe.json"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(report, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
