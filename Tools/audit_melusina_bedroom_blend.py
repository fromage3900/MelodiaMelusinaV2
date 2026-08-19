"""Read-only Blender audit for the Melusina bedroom source scene.

Run with Blender in factory-startup mode so local add-ons do not affect the audit:
blender --factory-startup --background <scene.blend> --python audit_melusina_bedroom_blend.py
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import bpy


OUTPUT = Path(r"G:\EnvironmentPortfolio\BS_GodFile\Saved\Audit\melusina_bedroom_blend_audit.json")
INCLUDED_TYPES = {"MESH", "EMPTY", "LIGHT", "CAMERA"}


def vector(value):
    return [round(component, 3) for component in value]


def main() -> None:
    arguments = sys.argv[sys.argv.index("--") + 1 :] if "--" in sys.argv else []
    source_blend = arguments[0] if arguments else bpy.data.filepath
    if not source_blend:
        raise RuntimeError("Pass the bedroom .blend path after --")

    # Appending data into a factory-startup session is read-only with respect to the
    # source file and avoids its load handlers/add-on state.
    with bpy.data.libraries.load(source_blend, link=False) as (data_from, data_to):
        data_to.objects = data_from.objects

    objects = []
    for obj in bpy.context.scene.objects:
        if obj.type not in INCLUDED_TYPES:
            continue
        data = obj.data
        objects.append(
            {
                "name": obj.name,
                "type": obj.type,
                "collections": sorted(collection.name for collection in obj.users_collection),
                "location": vector(obj.location),
                "dimensions": vector(obj.dimensions),
                "materials": [material.name if material else None for material in getattr(data, "materials", [])],
                "modifiers": [
                    {"name": modifier.name, "type": modifier.type, "enabled_viewport": modifier.show_viewport, "enabled_render": modifier.show_render}
                    for modifier in obj.modifiers
                ],
                "hidden_viewport": obj.hide_viewport,
                "hidden_render": obj.hide_render,
            }
        )

    report = {
        "source_blend": source_blend,
        "collection_names": sorted(collection.name for collection in bpy.data.collections),
        "object_count": len(objects),
        "objects": sorted(objects, key=lambda item: (item["type"], item["name"])),
    }
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT.write_text(json.dumps(report, indent=2), encoding="utf-8")
    print(f"BEDROOM_AUDIT_WRITTEN={OUTPUT}")
    print(f"BEDROOM_OBJECT_COUNT={report['object_count']}")


if __name__ == "__main__":
    main()
