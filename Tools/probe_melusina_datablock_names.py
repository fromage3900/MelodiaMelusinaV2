"""Print lightweight Blender datablock names without mesh evaluation."""

from __future__ import annotations

import json
from pathlib import Path
import bpy


def main() -> int:
    report = {
        "stage": bpy.data.filepath,
        "collections": list(bpy.data.collections.keys()),
        "libraries": [lib.filepath for lib in bpy.data.libraries],
        "object_name_count": len(bpy.data.objects),
        "object_names_matching": [
            name
            for name in bpy.data.objects.keys()
            if any(token in name.lower() for token in ("melusina", "shirt", "skirt", "boot", "dress", "shawl", "sleeve", "glove", "access"))
        ],
    }
    path = Path("Saved/Audit/melusina_v2_datablock_names.json")
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(report, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
