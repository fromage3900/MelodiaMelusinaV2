"""Diagnostic probe: dump PCGSelfPruningSettings property names and valid enum values.

Run in-editor:
  py Content/Python/pcg_probe_settings.py

Outputs to Saved/Audit/pcg_probe_self_pruning.json

Purpose: wire_scatter_chain() uses set_editor_property("pruning_type", 0)
inside a try/except, which may silently no-op if "pruning_type" isn't the
correct property name on this engine build (UE 5.8).
This probe discovers the actual property names so the fix can be precise.

Known issue from build_universal_rock_scatter.py (2026-07-02):
  - unreal.PCGSelfPruningType.LARGEST_TO_SMALLEST doesn't exist
  - 'pruning_type' property name may be incorrect
  - Real values may be LARGE_TO_SMALL / SMALL_TO_LARGE / etc.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path


def probe_pcg_self_pruning() -> dict:
    import unreal

    result: dict = {
        "class_found": False,
        "class_name": "PCGSelfPruningSettings",
        "properties": {},
        "enum_values": {},
        "candidate_property_names_tested": [],
        "recommended_fix": "",
    }

    cls = getattr(unreal, "PCGSelfPruningSettings", None)
    if cls is None:
        result["error"] = "PCGSelfPruningSettings class not found in unreal module"
        return result

    result["class_found"] = True
    result["class_path"] = str(cls)

    # Create a default instance to probe
    try:
        instance = cls()
    except Exception as e:
        result["error"] = f"Failed to instantiate PCGSelfPruningSettings: {e}"
        return result

    settings_obj = None
    for attr_name in dir(instance):
        if attr_name.startswith("_"):
            continue
        try:
            val = getattr(instance, attr_name, None)
            result["properties"][attr_name] = {
                "type": type(val).__name__,
                "value": str(val) if not callable(val) else "<callable>",
            }
        except Exception:
            result["properties"][attr_name] = {"type": "error", "value": "<read failed>"}

    # Test candidate set_editor_property names
    candidate_names = [
        "pruning_type",
        "pruning_type_enum",
        "self_pruning_type",
        "type",
        "mode",
        "pruning_mode",
        "b_largest_to_smallest",
        "b_enabled",
    ]

    for name in candidate_names:
        try:
            instance.set_editor_property(name, 0)
            result["candidate_property_names_tested"].append({"name": name, "result": "ok"})
        except Exception as e:
            result["candidate_property_names_tested"].append(
                {"name": name, "result": str(e)[:200]}
            )

    # Probe PCGSelfPruningType enum if it exists
    enum_cls = getattr(unreal, "PCGSelfPruningType", None)
    if enum_cls:
        for attr_name in dir(enum_cls):
            if attr_name.startswith("_"):
                continue
            try:
                val = getattr(enum_cls, attr_name)
                if isinstance(val, int):
                    result["enum_values"][attr_name] = val
            except Exception:
                pass
    else:
        # Try alternative enum class names
        for enum_name in ["EPCGSelfPruningType", "PCGSelfPruning"]:
            e = getattr(unreal, enum_name, None)
            if e:
                result["enum_values"][f"from_{enum_name}"] = {}
                for attr_name in dir(e):
                    if attr_name.startswith("_"):
                        continue
                    try:
                        val = getattr(e, attr_name)
                        if isinstance(val, int):
                            result["enum_values"][f"from_{enum_name}"][attr_name] = val
                    except Exception:
                        pass

    # Generate recommended fix
    working_names = [
        c["name"] for c in result["candidate_property_names_tested"] if c["result"] == "ok"
    ]
    if working_names:
        result["recommended_fix"] = (
            f"Use prune_s.set_editor_property('{working_names[0]}', ...) "
            f"instead of 'pruning_type'"
        )
    else:
        result["recommended_fix"] = (
            "No candidate property names accepted. PCGSelfPruningSettings "
            "may use different API on this engine build. Consider omitting "
            "the property set and relying on defaults."
        )

    return result


def main() -> int:
    result = probe_pcg_self_pruning()

    audit_dir = Path(unreal.Paths.project_saved_dir()) / "Audit"
    audit_dir.mkdir(parents=True, exist_ok=True)
    out_path = audit_dir / "pcg_probe_self_pruning.json"

    with open(str(out_path), "w") as f:
        json.dump(result, f, indent=2, default=str)

    unreal.log(f"[PCGProbe] Wrote {out_path}")
    print(json.dumps(result, indent=2, default=str))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
