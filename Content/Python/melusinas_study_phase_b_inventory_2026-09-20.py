# -*- coding: utf-8 -*-
"""Phase B — Melusinas Study Blender source inventory. READ-ONLY: never save the .blend."""
from __future__ import annotations
import json, hashlib, sys, traceback
from datetime import datetime, timezone
from pathlib import Path

REPO = Path(r"C:\EnvironmentPortfolio\BS_GodFile")
BLEND = REPO / "Saved" / "Audit" / "melusinas_study" / "recovery" / "Melusina_s_Study__from_027dce9b39a03bcdbaa79e647c9eb669a07c0de9.blend"
ALT = REPO / "Saved" / "MelusinasHouse" / "Melusina's_Study.blend"
AUDIT = REPO / "Saved" / "Audit" / "melusinas_study"
VOCAB = AUDIT / "builder_registry_vocab_audit.json"
OUT_INV = AUDIT / "blender_source_inventory.json"
OUT_MX = AUDIT / "gn_builder_matrix.json"
ADDON_PATH = REPO / "Tools" / "BlenderAddons" / "melodia_studio"

def main():
    import bpy
    from mathutils import Vector

    report = {
        "schema": "melodia.melusinas_study.blender_source_inventory.v1",
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "blend_path": None,
        "saved": False,
        "objects": [],
        "collections": [],
        "materials": [],
        "cameras": [],
        "lights": [],
        "gn_modifiers": [],
        "gn_groups": [],
        "registered_builder_mapping": {},
        "local_unregistered_groups": [],
        "linked_libraries": [],
        "missing_files": [],
        "notes": [],
        "errors": [],
    }

    src = BLEND if BLEND.exists() else ALT
    if not src.exists():
        report["errors"].append("blend_missing")
        OUT_INV.write_text(json.dumps(report, indent=2), encoding="utf-8")
        print("INV_ERR blend_missing")
        return 1
    report["blend_path"] = str(src)
    report["blend_bytes"] = src.stat().st_size
    report["blend_sha256"] = hashlib.sha256(src.read_bytes()).hexdigest()

    # Enable Melodia Studio addon from repo path
    try:
        import addon_utils
        sys.path.insert(0, str(ADDON_PATH.parent))
        # Prefer enabling by module if already installed
        enabled = False
        for mod in addon_utils.modules():
            name = getattr(mod, "__name__", "")
            if "melodia" in name.lower():
                addon_utils.enable(name, default_set=True, persistent=True)
                report["notes"].append(f"enabled_addon={name}")
                enabled = True
        if not enabled and ADDON_PATH.exists():
            # load as scripts path
            bpy.ops.preferences.addon_install(filepath=str(ADDON_PATH / "__init__.py")) if (ADDON_PATH / "__init__.py").exists() else None
            report["notes"].append(f"addon_path_present={ADDON_PATH.exists()}")
    except Exception as e:
        report["notes"].append(f"addon_enable:{e}")

    # Open blend (never save)
    bpy.ops.wm.open_mainfile(filepath=str(src))

    # Registry / vocab
    vocab = {}
    registered = set()
    if VOCAB.exists():
        vocab = json.loads(VOCAB.read_text(encoding="utf-8"))
        for b in vocab.get("builders") or []:
            if isinstance(b, dict):
                key = b.get("key") or b.get("name") or b.get("builder")
                if key and (b.get("present_and_registered") or b.get("registered") or b.get("status") == "ok"):
                    registered.add(key)
            elif isinstance(b, str):
                registered.add(b)
        # also summary keys
        for k, v in (vocab.get("builders") or {}).items() if isinstance(vocab.get("builders"), dict) else []:
            if isinstance(v, dict) and (v.get("present_and_registered") or v.get("in_baseline")):
                registered.add(k)

    # node groups
    groups = []
    for ng in bpy.data.node_groups:
        if ng.bl_idname != "GeometryNodeTree":
            continue
        entry = {
            "name": ng.name,
            "users": ng.users,
            "is_modifier": getattr(ng, "is_modifier", None),
            "nodes": len(ng.nodes) if hasattr(ng, "nodes") else None,
        }
        groups.append(entry)
    report["gn_groups"] = groups
    group_names = {g["name"] for g in groups}

    # objects
    for obj in bpy.data.objects:
        bb = None
        try:
            coords = [obj.matrix_world @ Vector(c) for c in obj.bound_box]
            xs = [c.x for c in coords]; ys = [c.y for c in coords]; zs = [c.z for c in coords]
            bb = {"min": [min(xs), min(ys), min(zs)], "max": [max(xs), max(ys), max(zs)]}
        except Exception:
            pass
        eval_verts = None
        try:
            deps = bpy.context.evaluated_depsgraph_get()
            ev = obj.evaluated_get(deps)
            mesh = ev.to_mesh()
            if mesh:
                eval_verts = len(mesh.vertices)
                ev.to_mesh_clear()
        except Exception:
            pass
        mods = []
        for m in obj.modifiers:
            md = {"name": m.name, "type": m.type}
            if m.type == "NODES":
                ng = getattr(m, "node_group", None)
                md["node_group"] = ng.name if ng else None
                report["gn_modifiers"].append({
                    "object": obj.name,
                    "modifier": m.name,
                    "node_group": ng.name if ng else None,
                    "show_viewport": m.show_viewport,
                    "show_render": m.show_render,
                })
            mods.append(md)
        custom = {}
        for k in obj.keys():
            if k.startswith("_"):
                continue
            try:
                custom[k] = str(obj[k])[:200]
            except Exception:
                custom[k] = "<err>"
        report["objects"].append({
            "name": obj.name,
            "type": obj.type,
            "location": list(obj.location),
            "rotation_euler": list(obj.rotation_euler),
            "scale": list(obj.scale),
            "modifiers": mods,
            "materials": [s.material.name if s.material else None for s in (obj.material_slots or [])],
            "eval_verts": eval_verts,
            "bounds_world": bb,
            "hide_viewport": obj.hide_viewport,
            "hide_render": obj.hide_render,
            "instance_type": getattr(obj, "instance_type", None),
            "custom_props": custom,
            "library": obj.library.filepath if obj.library else None,
        })

    for c in bpy.data.collections:
        report["collections"].append({
            "name": c.name,
            "objects": [o.name for o in c.objects],
            "children": [ch.name for ch in c.children],
            "hide_viewport": c.hide_viewport,
        })
    for mat in bpy.data.materials:
        report["materials"].append({"name": mat.name, "users": mat.users, "library": mat.library.filepath if mat.library else None})
    for cam in bpy.data.cameras:
        owners = [o.name for o in bpy.data.objects if o.type == "CAMERA" and o.data == cam]
        report["cameras"].append({"name": cam.name, "objects": owners})
    for light in bpy.data.lights:
        owners = [o.name for o in bpy.data.objects if o.type == "LIGHT" and o.data == light]
        report["lights"].append({"name": light.name, "type": light.type, "objects": owners})

    for lib in bpy.data.libraries:
        report["linked_libraries"].append({"name": lib.name, "filepath": lib.filepath})

    # missing files
    try:
        missing = []
        for img in bpy.data.images:
            if img.filepath and not Path(bpy.path.abspath(img.filepath)).exists() and not img.packed_file:
                missing.append({"type": "image", "name": img.name, "filepath": img.filepath})
        report["missing_files"] = missing
    except Exception as e:
        report["notes"].append(f"missing_scan:{e}")

    # builder mapping vs registered
    mapping = {}
    local_unreg = []
    for g in groups:
        name = g["name"]
        # strip common prefixes
        candidates = [name, name.replace("GN_", "MEL_"), name.replace("MEL_", "")]
        hit = None
        for c in candidates:
            if c in registered:
                hit = c
                break
        # fuzzy: any registered key contained
        if not hit:
            for r in registered:
                if r in name or name in r:
                    hit = r
                    break
        mapping[name] = {"registered_as": hit, "registered": bool(hit)}
        if not hit:
            local_unreg.append(name)
    report["registered_builder_mapping"] = mapping
    report["local_unregistered_groups"] = local_unreg
    report["counts"] = {
        "objects": len(report["objects"]),
        "collections": len(report["collections"]),
        "materials": len(report["materials"]),
        "cameras": len(report["cameras"]),
        "lights": len(report["lights"]),
        "gn_modifiers": len(report["gn_modifiers"]),
        "gn_groups": len(report["gn_groups"]),
    }

    # Handoff matrix
    matrix = {
        "schema": "melodia.melusinas_study.gn_builder_matrix.v1",
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "source_blend": str(src),
        "entries": [],
        "group_coverage": {},
        "notes": [
            "Handoff is intended assignment for Phase E; not an export yet.",
            "Player floor / primary circulation stay STATIC_MESH or greybox-legible.",
            "Repeated decor fields prefer PCG_SOURCE.",
        ],
    }
    used_groups = set()
    for obj in report["objects"]:
        gn_mods = [m for m in obj["modifiers"] if m["type"] == "NODES"]
        for m in gn_mods:
            gname = m.get("node_group")
            if gname:
                used_groups.add(gname)
        handoff = "STATIC_MESH"
        reason = "default structural/hero bake candidate"
        name_l = obj["name"].lower()
        gnames = [m.get("node_group") or "" for m in gn_mods]
        blob = " ".join(gnames + [obj["name"]]).lower()
        if obj["type"] in ("CAMERA", "LIGHT", "EMPTY") and not gn_mods:
            handoff = "REFERENCE_ONLY"
            reason = "camera/light/empty non-mesh"
        elif any(k in blob for k in ("bead", "star", "crystal", "note", "pearl", "scatter", "book", "flora", "nikki")):
            handoff = "PCG_SOURCE"
            reason = "repeated decor / field — points+species later"
        elif any(k in blob for k in ("escher", "penrose", "mobius", "hyperbolic", "waterfall", "belvedere")):
            handoff = "STATIC_MESH"
            reason = "Escher hero / framed sightline — bake for UE"
        elif any(k in blob for k in ("roof", "wall", "floor", "shell", "room", "slab", "opening", "window", "door")):
            handoff = "STATIC_MESH"
            reason = "structural shell/opening"
        elif obj.get("eval_verts") and obj["eval_verts"] > 200000:
            handoff = "KEEP_PROCEDURAL_BLENDER"
            reason = f"heavy eval_verts={obj['eval_verts']} — review before bake"
        elif not gn_mods and obj["type"] == "MESH":
            handoff = "STATIC_MESH"
            reason = "plain mesh"
        elif gn_mods and not any(mapping.get(g, {}).get("registered") for g in gnames if g):
            # unregistered GN
            if obj.get("eval_verts") is None:
                handoff = "REJECT_BROKEN"
                reason = "GN with no eval mesh / unregistered"
            else:
                handoff = "KEEP_PROCEDURAL_BLENDER"
                reason = "local/unregistered GN — keep in Blender until mapped"
        matrix["entries"].append({
            "object": obj["name"],
            "type": obj["type"],
            "gn_groups": gnames,
            "eval_verts": obj.get("eval_verts"),
            "handoff": handoff,
            "reason": reason,
        })

    for g in groups:
        matrix["group_coverage"][g["name"]] = {
            "used_on_objects": sum(1 for e in matrix["entries"] if g["name"] in (e.get("gn_groups") or [])),
            "registered": mapping.get(g["name"], {}).get("registered"),
            "registered_as": mapping.get(g["name"], {}).get("registered_as"),
        }
    # account for every Study GN group
    for g in groups:
        if g["name"] not in matrix["group_coverage"]:
            matrix["group_coverage"][g["name"]] = {"used_on_objects": 0, "registered": False}

    OUT_INV.write_text(json.dumps(report, indent=2, default=str), encoding="utf-8")
    OUT_MX.write_text(json.dumps(matrix, indent=2, default=str), encoding="utf-8")
    print("INV_OK", json.dumps({
        "inventory": str(OUT_INV),
        "matrix": str(OUT_MX),
        "counts": report["counts"],
        "gn_groups": len(groups),
        "saved": False,
    }))
    return 0

if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception:
        err = {"error": traceback.format_exc()}
        AUDIT.mkdir(parents=True, exist_ok=True)
        (AUDIT / "blender_source_inventory_ERROR.json").write_text(json.dumps(err, indent=2), encoding="utf-8")
        print("INV_ERR")
        traceback.print_exc()
        raise SystemExit(1)
