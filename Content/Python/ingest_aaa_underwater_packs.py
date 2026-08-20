"""Underwater + Kenney pack ingest → toon substrate pipeline.

Runs inside the editor (headless via UnrealEditor-Cmd, or live via editor_query):

  ingest_aaa_underwater_packs            # dry-run (default), all packs
  ingest_aaa_underwater_packs --pack atlantis --force
  ingest_aaa_underwater_packs --pack kenney --force
  ingest_aaa_underwater_packs --pack all --force

--force performs: source import (FBX/textures) → toon MI authoring under
M_Master_Toon_Universal → crosswalk JSON → material resolve.
--enable-oceanology-plugin edits the never-touch uproject (BOM preserved) — owner-gated.

Report: Saved/Audit/underwater_packs_ingest.json
"""
from __future__ import annotations

import json
import os
import re
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]
IMPORTS_ROOT = PROJECT_ROOT.parent / "Imports"
REPORT = PROJECT_ROOT / "Saved" / "Audit" / "underwater_packs_ingest.json"
UE_CMD = Path(r"C:\Program Files\Epic Games\UE_5.8\Engine\Binaries\Win64\UnrealEditor-Cmd.exe")
UPROJECT = PROJECT_ROOT / "BS_GodFile.uproject"

MASTER_UNIVERSAL = "/Game/EnvSandbox/Materials/Masters/M_Master_Toon_Universal"
MASTER_WATER_GRAND = "/Game/EnvSandbox/Materials/Masters/M_Water_Master_Grand_v10_Upgrade"
ATLANTIS_MESH_ROOT = "/Game/EnvSandbox/Meshes/Atlantis"
ATLANTIS_MI_ROOT = "/Game/EnvSandbox/Materials/Instances/Atlantis"
OCEANOLOGY_MI_ROOT = "/Game/EnvSandbox/Materials/Instances/Oceanology"
KENNEY_MESH_ROOT = "/Game/EnvSandbox/Meshes/Kenney"
KENNEY_MI_ROOT = "/Game/EnvSandbox/Materials/Instances/Kenney"
CROSSWALK_ATLANTIS = IMPORTS_ROOT / "KitBash3D_Atlantis" / "atlantis_toon.material_map.json"
CROSSWALK_OCEANOLOGY = IMPORTS_ROOT / "Oceanology" / "oceanology_toon.material_map.json"
CROSSWALK_KENNEY = IMPORTS_ROOT / "Kenney" / "kenney_toon.material_map.json"

SLOT_HINTS = {
    "albedo": ["albedo", "basecolor", "base_color", "diffuse", "col"],
    "normal": ["normal"],
    "orm": ["orm", "arm", "occlusion", "_ao", "rough_metal"],
    "roughness": ["roughness", "rough"],
    "metallic": ["metallic", "metal", "_mtl"],
    "height": ["height", "displacement", "disp"],
    "emissive": ["emissive", "glow", "emission", "luminous"],
    "opacity": ["opacity", "alpha", "mask"],
    "refraction": ["refraction"],
}

KENNEY_TEXTURE_ONLY_PACKS = ("pattern_pack", "pattern_pack_lines", "pattern_pack_extra", "retro_textures", "input_prompts")

PACK_DEFS = {
    "atlantis": {
        "staging": IMPORTS_ROOT / "KitBash3D_Atlantis" / "Split",
        "mesh_root": ATLANTIS_MESH_ROOT,
        "mi_root": ATLANTIS_MI_ROOT,
        "crosswalk": CROSSWALK_ATLANTIS,
        "label": "KitBash3D Atlantis",
        "split_meshes": True,
        "texture_sets_from_name": True,
        "set_prefix": "KB3D_ATL_",
        "channel_suffixes": ("basecolor", "metallic", "normal", "roughness", "height", "emissive", "opacity", "refraction", "refraction.inverted"),
        "water_sets": {"WaterClean"},
        "water_master": MASTER_WATER_GRAND,
    },
    "oceanology": {
        "staging": IMPORTS_ROOT / "Oceanology",
        "mesh_root": "/Game/Oceanology",
        "mi_root": OCEANOLOGY_MI_ROOT,
        "crosswalk": CROSSWALK_OCEANOLOGY,
        "label": "Oceanology NextGen",
        "split_meshes": False,
        "texture_sets_from_name": False,
    },
    "kenney_kit": {
        "staging": IMPORTS_ROOT / "Kenney" / "kenney_retro-fantasy-kit" / "Models" / "FBX format",
        "mesh_root": f"{KENNEY_MESH_ROOT}/RetroFantasyKit",
        "mi_root": f"{KENNEY_MI_ROOT}/RetroFantasyKit",
        "crosswalk": CROSSWALK_KENNEY,
        "label": "Kenney Retro Fantasy Kit",
        "split_meshes": False,
        "texture_sets_from_name": False,
        "mtl_dir": IMPORTS_ROOT / "Kenney" / "kenney_retro-fantasy-kit" / "Models" / "OBJ format",
        "obj_dir": IMPORTS_ROOT / "Kenney" / "kenney_retro-fantasy-kit" / "Models" / "OBJ format",
        "texture_root": "/Game/EnvSandbox/Textures/Kenney/RetroFantasyKit",
    },
    "pattern_pack": {
        "staging": IMPORTS_ROOT / "Kenney" / "kenney_pattern-pack" / "PNG",
        "label": "Kenney Pattern Pack",
        "texture_root": "/Game/EnvSandbox/Textures/Kenney/PatternPack",
        "texture_only": True,
    },
    "pattern_pack_lines": {
        "staging": IMPORTS_ROOT / "Kenney" / "kenney_pattern-pack-lines" / "PNG",
        "label": "Kenney Pattern Pack Lines",
        "texture_root": "/Game/EnvSandbox/Textures/Kenney/PatternPackLines",
        "texture_only": True,
    },
    "pattern_pack_extra": {
        "staging": IMPORTS_ROOT / "Kenney" / "kenney_pattern-pack-extra" / "PNG",
        "label": "Kenney Pattern Pack Extra",
        "texture_root": "/Game/EnvSandbox/Textures/Kenney/PatternPackExtra",
        "texture_only": True,
    },
    "retro_textures": {
        "staging": IMPORTS_ROOT / "Kenney" / "kenney_retro-textures-fantasy" / "PNG",
        "label": "Kenney Retro Textures Fantasy",
        "texture_root": "/Game/EnvSandbox/Textures/Kenney/RetroTexturesFantasy",
        "texture_only": True,
    },
    "input_prompts": {
        "staging": IMPORTS_ROOT / "Kenney" / "kenney_input-prompts_1_5",
        "label": "Kenney Input Prompts 1.5",
        "texture_root": "/Game/EnvSandbox/Textures/Kenney/InputPrompts",
        "texture_only": True,
        "png_glob": "**/*.png",
    },
}


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


# ═══════════════════════════════════════════════════════════════════════
# Staging scan
# ═══════════════════════════════════════════════════════════════════════

def scan_staging(pack_key: str) -> dict:
    cfg = PACK_DEFS[pack_key]
    staging = cfg["staging"]
    result = {
        "pack": pack_key,
        "label": cfg["label"],
        "staging": str(staging),
        "exists": staging.is_dir(),
        "fbx": [],
        "textures": [],
        "mtl": [],
        "archives": [],
        "plugin_folder": None,
        "notes": [],
    }
    if not staging.is_dir():
        result["notes"].append("NOT STAGED YET")
        return result

    for f in staging.rglob("*"):
        if f.is_file():
            ext = f.suffix.lower()
            if ext == ".fbx":
                result["fbx"].append(str(f))
            elif ext in (".png", ".jpg", ".jpeg", ".tga", ".tif", ".tiff", ".exr"):
                result["textures"].append(str(f))
            elif ext == ".zip":
                result["archives"].append(str(f))
    if cfg.get("mtl_dir") and cfg["mtl_dir"].is_dir():
        result["mtl"] = [str(f) for f in cfg["mtl_dir"].rglob("*.mtl")]

    plugin_hits = list((PROJECT_ROOT / "Plugins").glob("*Ocean*")) if pack_key == "oceanology" else []
    if plugin_hits:
        result["plugin_folder"] = str(plugin_hits[0])
    return result


# ═══════════════════════════════════════════════════════════════════════
# Master slot discovery (reflection, not hardcoded names)
# ═══════════════════════════════════════════════════════════════════════

def discover_texture_slots(master_path: str = MASTER_UNIVERSAL) -> dict:
    """Return {slot_name_lower: full_parameter_name} for a material master."""
    try:
        import unreal
    except ImportError:
        return {}
    mat = unreal.EditorAssetLibrary.load_asset(master_path)
    if not mat:
        return {}
    slots = {}
    try:
        for pv in mat.get_editor_property("texture_parameter_values"):
            name = str(pv.get_editor_property("parameter_name"))
            slots[name.lower()] = name
    except Exception:
        pass
    return slots


def pick_slot(texture_path: str, slots: dict) -> str | None:
    base = Path(texture_path).stem.lower()
    for slot_name, full_name in slots.items():
        for hints in SLOT_HINTS.values():
            if any(h in base for h in hints) and any(h in slot_name for h in hints):
                return full_name
    return None


# ═══════════════════════════════════════════════════════════════════════
# Texture import (texture-only packs + kit texture roots)
# ═══════════════════════════════════════════════════════════════════════

def import_texture_file(tex_path: str, dest_root: str) -> str | None:
    """Import a single PNG/JPG as a texture asset under dest_root (no overwrite)."""
    import unreal

    stem = Path(tex_path).stem
    dest = f"{dest_root}/{stem}"
    if unreal.EditorAssetLibrary.does_asset_exist(dest):
        return dest
    if not unreal.EditorAssetLibrary.does_directory_exist(dest_root):
        unreal.EditorAssetLibrary.make_directory(dest_root)

    task = unreal.AssetImportTask()
    task.set_editor_property("filename", tex_path)
    task.set_editor_property("destination_path", dest_root)
    task.set_editor_property("replace_existing", False)
    task.set_editor_property("automated", True)
    task.set_editor_property("save", True)
    try:
        unreal.AssetToolsHelpers.get_asset_tools().import_asset_tasks([task])
    except Exception as exc:
        unreal.log_error(f"[UnderwaterIngest] texture import failed {tex_path}: {exc}")
        return None
    if unreal.EditorAssetLibrary.does_asset_exist(dest):
        return dest
    imported = [r for r in task.get_editor_property("imported_object_paths") if r]
    return imported[0] if imported else None


# ═══════════════════════════════════════════════════════════════════════
# MI creation (toon substrate pipeline)
# ═══════════════════════════════════════════════════════════════════════

def build_toon_instance(mat_name: str, textures: list[str], mi_root: str, slots: dict,
                        parent_override: str | None = None) -> str | None:
    """Create a MaterialInstanceConstant wired to textures under the given parent."""
    import unreal

    safe = re.sub(r"[^A-Za-z0-9_]", "_", mat_name)
    mi_path = f"{mi_root}/MI_{safe}"
    if unreal.EditorAssetLibrary.does_asset_exist(mi_path):
        return mi_path

    if not unreal.EditorAssetLibrary.does_directory_exist(mi_root):
        unreal.EditorAssetLibrary.make_directory(mi_root)

    factory = unreal.MaterialInstanceConstantFactoryNew()
    tools = unreal.AssetToolsHelpers.get_asset_tools()
    mi = tools.create_asset(f"MI_{safe}", mi_root, unreal.MaterialInstanceConstant, factory)
    if not mi:
        return None
    parent = unreal.EditorAssetLibrary.load_asset(parent_override or MASTER_UNIVERSAL)
    if not parent:
        unreal.log_error(f"[UnderwaterIngest] parent missing: {parent_override or MASTER_UNIVERSAL}")
        return None
    mi.set_editor_property("parent", parent)

    tex_params = []
    wired = 0
    for tex_path in textures:
        slot = pick_slot(tex_path, slots)
        if not slot:
            continue
        tex = unreal.EditorAssetLibrary.load_asset(tex_path)
        if not tex:
            continue
        tex_params.append(unreal.MaterialTextureParameterValue(parameter_name=slot, parameter_value=tex))
        wired += 1

    if tex_params:
        mi.set_editor_property("texture_parameter_values", tex_params)

    try:
        unreal.MaterialEditingLibrary.update_material_instance(mi)
    except Exception:
        pass
    unreal.EditorAssetLibrary.save_loaded_asset(mi)
    unreal.log(f"[UnderwaterIngest] MI {mi_path} (wired {wired} textures)")
    return mi_path


# ═══════════════════════════════════════════════════════════════════════
# FBX import (no-overwrite guarded; optional per-node split)
# ═══════════════════════════════════════════════════════════════════════

def make_fbx_task(fbx_path: str, mesh_root: str, split_meshes: bool):
    """Build an AssetImportTask wired to FbxImportUI/FbxFactory. Returns (task, mode)
    where mode tells the report how the split was configured:
    'per-node' | 'options-unsupported' | 'combined'."""
    import unreal

    task = unreal.AssetImportTask()
    task.set_editor_property("filename", fbx_path)
    task.set_editor_property("destination_path", mesh_root)
    task.set_editor_property("replace_existing", False)
    task.set_editor_property("automated", True)
    task.set_editor_property("save", True)
    task.set_editor_property("factory", unreal.FbxFactory())

    ui = unreal.FbxImportUI()
    ui.set_editor_property("import_materials", False)
    ui.set_editor_property("import_textures", False)
    ui.set_editor_property("import_as_skeletal", False)
    ui.set_editor_property("automated_import_should_detect_type", True)
    task.set_editor_property("options", ui)

    smd = None
    try:
        smd = ui.get_editor_property("static_mesh_import_data")
    except Exception:
        pass

    if smd:
        # Reduce peak import memory: skip Nanite build + collision gen (can be
        # re-enabled per-mesh later; meshes stay editable).
        for prop, val in (("build_nanite", False), ("auto_generate_collision", False)):
            try:
                smd.set_editor_property(prop, val)
            except Exception:
                pass

    if not split_meshes:
        return task, "combined"

    try:
        smd.set_editor_property("combine_meshes", False)
        return task, "per-node"
    except Exception as exc:
        unreal.log_warning(
            f"[UnderwaterIngest] split requested but FbxStaticMeshImportData.combine_meshes "
            f"unavailable ({exc}) — result will be a combined mesh; use the Atlantis.blend fallback."
        )
        return task, "options-unsupported"


def import_fbx_mesh(fbx_path: str, mesh_root: str, split_meshes: bool) -> tuple:
    """Import one FBX. Returns (imported_paths, mode)."""
    import unreal

    asset_name = Path(fbx_path).stem
    dest = f"{mesh_root}/{asset_name}"
    if unreal.EditorAssetLibrary.does_asset_exist(dest):
        unreal.log_warning(f"[UnderwaterIngest] SKIP (exists): {dest}")
        return [], "exists"

    if not unreal.EditorAssetLibrary.does_directory_exist(mesh_root):
        unreal.EditorAssetLibrary.make_directory(mesh_root)

    task, mode = make_fbx_task(fbx_path, mesh_root, split_meshes)
    tools = unreal.AssetToolsHelpers.get_asset_tools()
    tools.import_asset_tasks([task])
    imported = [r for r in task.get_editor_property("imported_object_paths") if r]
    unreal.log(f"[UnderwaterIngest] Imported {fbx_path} mode={mode} → {len(imported)} objects")
    return imported, mode


# ═══════════════════════════════════════════════════════════════════════
# Texture set grouping
# ═══════════════════════════════════════════════════════════════════════

def group_textures_by_set(textures: list[str], prefix: str, suffixes: tuple) -> dict:
    """Group KB3D_ATL_<Set>_<channel> filenames into {set_name: [tex_paths]}."""
    groups: dict[str, list[str]] = {}
    for tex in textures:
        name = Path(tex).stem
        if prefix and name.startswith(prefix):
            name = name[len(prefix):]
        channel = None
        for suf in suffixes:
            if name.endswith(f"_{suf}"):
                channel = suf
                name = name[: -(len(suf) + 1)]
                break
        if channel is None:
            groups.setdefault(name, []).append(tex)
            continue
        groups.setdefault(name, []).append(tex)
    return groups


def parse_mtl_map(mtl_files: list[str]) -> dict:
    """Parse Kenney MTL files: {material_name: texture_filename} (diffuse only)."""
    mapping: dict[str, str] = {}
    for mtl in mtl_files:
        current = None
        try:
            with open(mtl, encoding="utf-8", errors="ignore") as f:
                for raw in f:
                    line = raw.strip()
                    if line.startswith("newmtl"):
                        current = line.split(None, 1)[1].strip() if len(line.split(None, 1)) > 1 else None
                    elif line.startswith("map_Kd") and current:
                        tex = line.split(None, 1)[1].strip().replace("\\", "/")
                        mapping[current] = Path(tex).name
        except Exception:
            continue
    return mapping


# ═══════════════════════════════════════════════════════════════════════
# Crosswalk
# ═══════════════════════════════════════════════════════════════════════

def write_crosswalk(pack_key: str, mapping: dict) -> None:
    import unreal

    cfg = PACK_DEFS[pack_key]
    cfg["crosswalk"].parent.mkdir(parents=True, exist_ok=True)
    cfg["crosswalk"].write_text(json.dumps(mapping, indent=2, sort_keys=True), encoding="utf-8")
    unreal.log(f"[UnderwaterIngest] Crosswalk {cfg['crosswalk']} ({len(mapping)} entries)")


# ═══════════════════════════════════════════════════════════════════════
# Oceanology plugin enablement (never-touch uproject, BOM preserved)
# ═══════════════════════════════════════════════════════════════════════

def enable_oceanology_plugin() -> dict:
    """Textually insert the Oceanology plugin entry into BS_GodFile.uproject."""
    raw = UPROJECT.read_bytes()
    has_bom = raw.startswith(b"\xef\xbb\xbf")
    text = raw.decode("utf-8-sig")
    if '"Name":  "Oceanology"' in text:
        return {"ok": True, "changed": False, "note": "already present"}

    anchor = '"Name":  "MIDIDevice",\n                        "Enabled":  true\n                    }\n                ]'
    if anchor not in text:
        return {"ok": False, "changed": False, "note": "anchor not found — do not hand-edit"}

    entry = (
        '"Name":  "MIDIDevice",\n'
        '                        "Enabled":  true\n'
        '                    },\n'
        '                    {\n'
        '                        "Name":  "Oceanology",\n'
        '                        "Enabled":  true\n'
        '                    }\n'
        '                ]'
    )
    UPROJECT.write_bytes(((("\ufeff" if has_bom else "") + text.replace(anchor, entry))).encode("utf-8-sig"))
    return {"ok": True, "changed": True, "note": "Oceanology enabled; closed-editor build required"}


# ═══════════════════════════════════════════════════════════════════════
# Orchestration
# ═══════════════════════════════════════════════════════════════════════

def run_pack(pack_key: str, dry_run: bool) -> dict:
    import unreal

    cfg = PACK_DEFS[pack_key]
    state = scan_staging(pack_key)
    report = {"pack": pack_key, "dry_run": dry_run, "staging": state, "steps": []}

    def step(name: str, fn) -> None:
        try:
            report["steps"].append({"step": name, "ok": True, "result": fn()})
        except Exception as exc:
            report["steps"].append({"step": name, "ok": False, "error": str(exc)})
            unreal.log_error(f"[UnderwaterIngest] {name} failed: {exc}")

    # ── texture-only packs ────────────────────────────────────────────
    if cfg.get("texture_only"):
        if dry_run:
            report["steps"].append({
                "step": "plan",
                "ok": True,
                "result": {
                    "png_found": len(state["textures"]),
                    "action": "import textures (PNG; SVG skipped — no UE SVG importer)",
                },
            })
            return report
        pngs = [t for t in state["textures"] if t.lower().endswith(".png")]
        if not pngs:
            # pattern/retro packs stage PNG directly; input-prompts stage at pack root
            base = cfg["staging"]
            glob_pat = cfg.get("png_glob", "**/*.png")
            pngs = [str(p) for p in base.rglob(glob_pat) if p.suffix.lower() == ".png"]

        def import_textures_only() -> dict:
            result = {"imported": [], "failed": []}
            for p in pngs:
                r = import_texture_file(p, cfg["texture_root"])
                if r:
                    result["imported"].append(r)
                else:
                    result["failed"].append(p)
            result["svg_skipped"] = len(state["textures"]) - len(pngs) if state["textures"] else 0
            return result

        step("import_textures", import_textures_only)
        return report

    # ── Oceanology early-out ──────────────────────────────────────────
    if pack_key == "oceanology" and not state["plugin_folder"] and not state["archives"] and not state["fbx"]:
        report["steps"].append({"step": "detect", "ok": True, "result": "DOWNLOAD IN PROGRESS — nothing to ingest yet"})
        return report

    if dry_run:
        report["steps"].append({
            "step": "plan",
            "ok": True,
            "result": {
                "fbx_ready": len(state["fbx"]),
                "textures_ready": len(state["textures"]),
                "action": f"run with --force to import and author {cfg['label']} MIs",
            },
        })
        return report

    slots = discover_texture_slots()
    report["master_slots"] = len(slots)

    # ── Kenney kit: import textures first, then FBX ───────────────────
    if pack_key == "kenney_kit":
        def kenney_textures() -> dict:
            result = {"imported": []}
            for tex in state["textures"]:
                if tex.lower().endswith(".png"):
                    r = import_texture_file(tex, cfg["texture_root"])
                    if r:
                        result["imported"].append(r)
            return result

        step("import_kit_textures", kenney_textures)

        def kenney_materials() -> int:
            mtl_map = parse_mtl_map(state["mtl"])
            by_texture: dict[str, list[str]] = {}
            for mat_name, tex_file in mtl_map.items():
                by_texture.setdefault(tex_file, []).append(mat_name)
            count = 0
            crosswalk: dict[str, str] = {}
            for tex_file, mat_names in by_texture.items():
                tex_asset = f"{cfg['texture_root']}/{Path(tex_file).stem}"
                if not unreal.EditorAssetLibrary.does_asset_exist(tex_asset):
                    continue
                mi_path = build_toon_instance(Path(tex_file).stem, [tex_asset], cfg["mi_root"], slots)
                if mi_path:
                    for mn in mat_names:
                        crosswalk[mn] = mi_path
                    count += 1
            write_crosswalk(pack_key, crosswalk)
            return count

        step("author_kit_toon_instances", kenney_materials)

        def kenney_import() -> dict:
            imported = []
            modes = set()
            for fbx in state["fbx"]:
                paths, mode = import_fbx_mesh(fbx, cfg["mesh_root"], False)
                imported.extend(paths)
                modes.add(mode)
            return {"imported": len(imported), "modes": sorted(modes)}

        step("import_kit_meshes", kenney_import)

        def kenney_assign() -> dict:
            """Assign crosswalk MIs to mesh slots using each OBJ's usemtl order."""
            import unreal
            from resolve_material_crosswalk import load_crosswalk

            cw = load_crosswalk(str(cfg["crosswalk"]))
            obj_dir = cfg.get("obj_dir")
            meshes_done = 0
            slots_done = 0
            unresolved: list[str] = []
            for fbx in state["fbx"]:
                stem = Path(fbx).stem
                mesh_path = f"{cfg['mesh_root']}/{stem}"
                sm = unreal.EditorAssetLibrary.load_asset(mesh_path)
                if not sm:
                    # multi-node FBX: UE names assets stem_NodeName — try known patterns
                    for cand in (f"{stem}_Group", f"{stem}_{stem}"):
                        cand_path = f"{cfg['mesh_root']}/{cand}"
                        if unreal.EditorAssetLibrary.does_asset_exist(cand_path):
                            sm = unreal.EditorAssetLibrary.load_asset(cand_path)
                            unreal.log_warning(f"[UnderwaterIngest] {stem}: resolved to {cand}")
                            break
                if not sm:
                    unresolved.append(f"{stem} (no mesh)")
                    continue
                # OBJ usemtl order → material names (dedup preserving order)
                mat_names: list[str] = []
                obj_file = obj_dir / f"{stem}.obj" if obj_dir else None
                if obj_file and obj_file.is_file():
                    with open(obj_file, encoding="utf-8", errors="ignore") as fh:
                        for raw in fh:
                            line = raw.strip()
                            if line.startswith("usemtl"):
                                m = line.split(None, 1)[1].strip() if len(line.split(None, 1)) > 1 else ""
                                if m and m not in mat_names:
                                    mat_names.append(m)
                if not mat_names:
                    unresolved.append(f"{stem} (no usemtl)")
                    continue
                slots = []
                for mn in mat_names:
                    mi_path = cw.get(mn) or f"{cfg['mi_root']}/MI_{mn}"
                    cands = [mi_path, f"{cfg['mi_root']}/{mn}"]
                    mi = None
                    for cand in cands:
                        if unreal.EditorAssetLibrary.does_asset_exist(cand):
                            mi = unreal.EditorAssetLibrary.load_asset(cand)
                            if mi:
                                mi_path = cand
                                break
                    if not mi:
                        unresolved.append(f"{stem}:{mn} (MI missing)")
                        continue
                    slots.append(unreal.StaticMaterial(material_slot_name=mn, material_interface=mi))
                if slots:
                    sm.set_editor_property("static_materials", slots)
                    unreal.EditorAssetLibrary.save_loaded_asset(sm)
                    meshes_done += 1
                    slots_done += len(slots)
            # reconcile crosswalk with actually-existing MI paths
            reconciled = {}
            for mn, mi_path in cw.items():
                if unreal.EditorAssetLibrary.does_asset_exist(mi_path):
                    reconciled[mn] = mi_path
                elif unreal.EditorAssetLibrary.does_asset_exist(f"{cfg['mi_root']}/{mn}"):
                    reconciled[mn] = f"{cfg['mi_root']}/{mn}"
            if reconciled != cw:
                write_crosswalk(pack_key, reconciled)
            return {"meshes_assigned": meshes_done, "slots_assigned": slots_done,
                    "unresolved": unresolved}

        step("assign_kit_materials", kenney_assign)
        return report

    # ── Atlantis / Oceanology ─────────────────────────────────────────
    if pack_key == "oceanology" and state["plugin_folder"]:
        sources = []
    else:
        sources = state["fbx"]

    modes = set()
    imported_meshes = []

    def mesh_exists_guard(fbx_path: str) -> bool:
        """Check if the imported mesh already exists at the destination."""
        import unreal
        asset_name = Path(fbx_path).stem
        dest = f"{cfg['mesh_root']}/{asset_name}"
        return unreal.EditorAssetLibrary.does_asset_exist(dest)

    def import_all_meshes() -> dict:
        all_exist = all(mesh_exists_guard(fbx) for fbx in sources)
        if all_exist:
            unreal.log_warning(
                f"[UnderwaterIngest] All {len(sources)} meshes already exist — "
                "skipping FBX import, proceeding to material authoring."
            )
            return {"imported": 0, "modes": [], "total_fbx": len(sources), "note": "meshes_skipped_exist"}
        skipped: list[str] = []
        for fbx in sources:
            if mesh_exists_guard(fbx):
                skipped.append(fbx)
                continue
            paths, mode = import_fbx_mesh(fbx, cfg["mesh_root"], cfg.get("split_meshes", False))
            imported_meshes.extend(paths)
            modes.add(mode)
        if skipped:
            unreal.log_warning(
                f"[UnderwaterIngest] Skipped {len(skipped)} existing meshes during import."
            )
        return {"imported": len(imported_meshes), "modes": sorted(modes),
                "total_fbx": len(sources), "note": f"skipped={len(skipped)}" if skipped else ""}

    step("import_meshes", import_all_meshes)

    crosswalk: dict[str, str] = {}

    def author_materials() -> int:
        if cfg.get("texture_sets_from_name"):
            groups = group_textures_by_set(state["textures"], cfg.get("set_prefix", ""), cfg.get("channel_suffixes", ()))
        else:
            groups = {}
            for tex in state["textures"]:
                groups.setdefault(Path(tex).parent.name, []).append(tex)
        count = 0
        for set_name, textures in groups.items():
            parent_override = None
            if cfg.get("water_sets") and set_name in cfg["water_sets"]:
                parent_override = cfg["water_master"]
            mi_path = build_toon_instance(set_name, textures, cfg["mi_root"], slots, parent_override)
            if mi_path:
                crosswalk[set_name] = mi_path
                count += 1
        return count

    step("author_toon_instances", author_materials)
    step("write_crosswalk", lambda: write_crosswalk(pack_key, crosswalk))

    if crosswalk:
        try:
            import resolve_material_crosswalk as resolver
            step("resolve_materials", lambda: resolver.resolve_all())
        except Exception as exc:
            report["steps"].append({"step": "resolve_materials", "ok": False, "error": str(exc)})

    return report


def main(argv: list[str] | None = None) -> int:
    if argv is None:
        argv = sys.argv[1:]
    env_args = os.environ.get("UNDERWATER_INGEST_ARGS")
    if env_args:
        try:
            argv = json.loads(env_args) or argv
        except Exception:
            pass
    with open(PROJECT_ROOT / "Saved" / "Audit" / "ingest_bootstrap.txt", "a", encoding="utf-8") as _b:
        _b.write(f"{_now()} argv={argv!r} env={bool(env_args)} unreal=")
        try:
            import unreal  # noqa: F401
            _b.write("YES\n")
        except ImportError:
            _b.write("NO\n")
    requested = [a for a in argv if a in PACK_DEFS]
    if "kenney" in argv:
        requested = [k for k in PACK_DEFS if k.startswith("kenney") or k in KENNEY_TEXTURE_ONLY_PACKS]
    packs = list(PACK_DEFS) if "all" in argv else (requested or list(PACK_DEFS))
    dry_run = "--force" not in argv
    enable_plugin = "--enable-oceanology-plugin" in argv

    try:
        import unreal  # noqa: F401
    except ImportError:
        if not UE_CMD.exists():
            print("ERROR: no UE_CMD and no live unreal module")
            return 1
        log = PROJECT_ROOT / "Saved" / "Logs" / "underwater_packs_ingest.log"
        cmd = [
            str(UE_CMD), str(UPROJECT),
            f"-ExecutePythonScript={(PROJECT_ROOT / 'Content/Python/ingest_aaa_underwater_packs.py').as_posix()}",
            "-stdout", "-unattended", "-nullrhi",
            "-DisablePlugins=Monolith", f"-log={log}",
        ]
        env = dict(os.environ)
        env["UNDERWATER_INGEST_ARGS"] = json.dumps(argv)
        return subprocess.run(cmd, cwd=str(PROJECT_ROOT), env=env).returncode

    report: dict = {"timestamp": _now(), "dry_run": dry_run, "packs": {}}
    if enable_plugin:
        report["oceanology_plugin_enable"] = enable_oceanology_plugin()
    for pk in packs:
        report["packs"][pk] = run_pack(pk, dry_run)

    REPORT.parent.mkdir(parents=True, exist_ok=True)
    REPORT.write_text(json.dumps(report, indent=2), encoding="utf-8")
    print(f"UNDERWATER_INGEST dry_run={dry_run} packs={packs} -> {REPORT}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())