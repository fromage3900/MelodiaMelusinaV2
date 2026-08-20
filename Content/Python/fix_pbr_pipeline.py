"""PBR routing pipeline (2026-08-14) â€” resumable, chunked, audit-per-phase.

Phases (--phase):
  B   build pack texture catalog from Imports/, import needed textures (sRGB-correct)
  C   route + finish: LayerA activation, PBR mapping w/ tileable fallbacks, AvatarGarden/
      loose/library slot routing, BlingVol3 MIs. Chunked by props; resumes from state.
  D   dedupe: delete duplicate meshes (root vs StaticMeshes twin) and zero-referencer
      duplicate/orphan instances.
  E   verify: re-census bad slots + unfinished MIs; write full_pbr_sweep_2026-08-14.json.

State: Saved/Audit/pbr_pipeline_state.json (chunk cursors). Audits per phase.
Run through the live editor via Tools/editor_run.py (or direct run_python).
"""
from __future__ import annotations

import json
import re
import sys
import time
from pathlib import Path

import unreal

ROOT = Path(__file__).resolve().parents[2]
AUDIT = ROOT / "Saved" / "Audit"
STATE_FILE = AUDIT / "pbr_pipeline_state.json"
CATALOG_FILE = AUDIT / "pbr_texture_catalog.json"
IMPORTS_ENV = ROOT / "Imports" / "Environment"
ENV = "/Game/EnvSandbox/Meshes/Environment"
TEX_ROOT = "/Game/EnvSandbox/Textures/PackTextures"

MASTER = "/Game/EnvSandbox/Materials/Masters/M_Master_Toon_Universal"
PACK_TEX_DIRS = {
    "AvatarGarden": IMPORTS_ENV / "AvatarGarden_PolygonalMind" / "extracted" / "textures",
    "EnchantedForest": IMPORTS_ENV / "StylizedEnchantedForest" / "textures" / "crystaltextures",
    "CrystalCrossroads": IMPORTS_ENV / "CrystalCrossroads_PolygonalMind" / "extracted" / "Textures",
}

ROLE_SUFFIXES = [
    ("_ambientocclusion", "ao"), ("_ambient", "ao"), ("_ao", "ao"),
    ("_basecolor", "albedo"), ("_albedo", "albedo"), ("_color", "albedo"), ("_diffuse", "albedo"),
    ("_roughness", "roughness"), ("_rough", "roughness"),
    ("_metallic", "metallic"), ("_metal", "metallic"),
    ("_orm", "orm"), ("_arm", "orm"),
    ("_normal", "normal"), ("_normalmap", "normal"),
    ("_height", "height"), ("_displacement", "height"),
    ("_emissive", "emissive"), ("_emission", "emissive"),
    ("_mask", "mask"), ("_alpha", "mask"), ("_opacity", "mask"),
]
EXT = {".png", ".tif", ".tiff", ".jpg", ".jpeg", ".tga", ".bmp"}

ORGANIC = (
    "grass", "plant", "tree", "leaf", "flower", "bush", "crop", "rock", "stone", "cliff",
    "dirt", "moss", "log", "stump", "ground", "sand", "mushroom", "cactus", "fern",
    "wheat", "bamboo", "branch", "water", "river", "crystal", "lily", "bush", "hedge",
)


def now():
    return time.strftime("%Y-%m-%d %H:%M:%S")


def state() -> dict:
    if STATE_FILE.exists():
        try:
            return json.loads(STATE_FILE.read_text(encoding="utf-8"))
        except Exception:
            pass
    return {}


def save_state(s: dict):
    STATE_FILE.write_text(json.dumps(s, indent=2), encoding="utf-8")


def class_name(path: str) -> str:
    try:
        d = unreal.EditorAssetLibrary.find_asset_data(path)
        return str(d.asset_class_path.asset_name) if d and d.is_valid() else ""
    except Exception:
        return ""


def refs(package_name: str) -> list:
    opts = unreal.AssetRegistryDependencyOptions(
        include_hard_package_references=True, include_soft_package_references=True,
        include_searchable_names=False, include_hard_management_references=True,
        include_soft_management_references=True,
    )
    try:
        return sorted(unreal.AssetRegistryHelpers.get_asset_registry().get_referencers(package_name, opts) or [])
    except Exception:
        return []


def list_assets(root: str, recursive=True):
    return unreal.EditorAssetLibrary.list_assets(root, recursive=recursive, include_folder=False)


def tileable_fallback(role: str) -> str:
    """Resolve a project tileable by role (cached)."""
    s = state()
    cache = s.setdefault("tileables", {})
    if role in cache:
        return cache[role]
    frag = {
        "albedo": "ZenTrim_Base4K_BaseColor",
        "normal": "ZenTrim_Base4K_Normal",
        "roughness": "ZenTrim_Base4K_Roughness",
        "metallic": "ZenTrim_Base4K_Metallic",
        "orm": "landscape_grass_orm",
        "ao": "landscapegrayscale_AmbientOcclusion",
    }[role]
    found = ""
    for root in ("/Game/EnvSandbox/Textures_Shared", "/Game/Melodia/_PROJECT/04_Materials/Textures/Tileables"):
        if not unreal.EditorAssetLibrary.does_directory_exist(root):
            continue
        for p in list_assets(root):
            stem = p.rsplit("/", 1)[-1].split(".")[0]
            if stem == frag:
                found = p
                break
        if found:
            break
    cache[role] = found
    save_state(s)
    return found


def pack_for_prop(prop: str) -> str:
    """Find which import pack a prop stem came from (by model filename)."""
    s = state()
    cache = s.setdefault("prop_packs", {})
    if prop in cache:
        return cache[prop]
    hit = ""
    for pack_dir in sorted(IMPORTS_ENV.iterdir()):
        if not pack_dir.is_dir():
            continue
        for ext in (".glb", ".fbx", ".obj"):
            if (pack_dir / "extracted" / "Models").exists():
                for p in (pack_dir / "extracted" / "Models").rglob(f"*{prop}*{ext}"):
                    hit = pack_dir.name
                    break
            if hit:
                break
        if hit:
            break
    cache[prop] = hit
    save_state(s)
    return hit


# ---------------------------------------------------------------- Phase B
def phase_b():
    catalog = {}
    imported_any = False
    for pack, tex_dir in PACK_TEX_DIRS.items():
        sets = {}
        if not tex_dir.exists():
            continue
        for f in sorted(tex_dir.rglob("*")):
            if not f.is_file() or f.suffix.lower() not in EXT:
                continue
            low = f.stem.lower()
            role = None
            for suffix, r in ROLE_SUFFIXES:
                if low.endswith(suffix):
                    role = r
                    break
            if role in (None, "mask"):
                continue
            set_name = f.stem[:-len([s for s, _ in ROLE_SUFFIXES if low.endswith(s)][0])] if role else f.stem
            sets.setdefault(set_name, {})[role] = str(f)
        catalog[pack] = sets
        # import
        dest_dir = f"{TEX_ROOT}/{pack}"
        unreal.EditorAssetLibrary.make_directory(dest_dir)
        srgb_roles = {"albedo", "emissive", "height"}
        for set_name, roles in sets.items():
            for role, src in roles.items():
                stem = f"{set_name}_{role}".replace(" ", "_")
                dest = f"{dest_dir}/{stem}"
                if unreal.EditorAssetLibrary.does_asset_exist(dest):
                    continue
                task = unreal.AssetImportTask()
                task.set_editor_property("automated", True)
                task.set_editor_property("filename", src)
                task.set_editor_property("destination_path", dest_dir)
                task.set_editor_property("destination_name", stem)
                task.set_editor_property("replace_existing", False)
                task.set_editor_property("save", False)
                unreal.AssetToolsHelpers.get_asset_tools().import_asset_tasks([task])
                tex = unreal.load_asset(dest)
                if tex:
                    try:
                        tex.set_editor_property("srgb", role in srgb_roles)
                    except Exception:
                        pass
                    unreal.EditorAssetLibrary.save_loaded_asset(tex, only_if_is_dirty=False)
                    imported_any = True
    CATALOG_FILE.write_text(json.dumps({"generated": now(), "catalog": catalog}, indent=2, default=str), encoding="utf-8")
    print(f"PHASE_B: catalog packs={list(catalog)} sets={sum(len(v) for v in catalog.values())} imported={imported_any}")


def catalog() -> dict:
    if not CATALOG_FILE.exists():
        return {}
    try:
        return json.loads(CATALOG_FILE.read_text(encoding="utf-8")).get("catalog", {})
    except Exception:
        return {}


def pack_set_for(prop: str, slot_name: str = "") -> dict:
    """Best texture set for a prop/slot: exact prop name, slot-name prefix, shared digit token."""
    cat = catalog()
    pack = pack_for_prop(prop)
    if pack not in cat:
        return {}
    sets = cat[pack]
    cands = [c for c in (prop, slot_name) if c]
    for c in cands:
        c_tokens = set(re.findall(r"\d+", c.lower()))
        c_first = c.lower().split("_")[0]
        for set_name in sets:
            s_low = set_name.lower()
            s_tokens = set(re.findall(r"\d+", s_low))
            if (s_low.startswith(c_first) or c.lower().startswith(s_low)
                    or (c_tokens and c_tokens & s_tokens)):
                return sets[set_name]
    return {}


# ---------------------------------------------------------------- Phase C
def create_mi(parent_path: str, asset_path: str):
    """Create a MaterialInstanceConstant via the AssetTools factory (UE 5.8-safe)."""
    factory = unreal.MaterialInstanceConstantFactoryNew()
    name = asset_path.rsplit("/", 1)[-1].split(".")[0]
    folder = asset_path.rsplit("/", 1)[0]
    a = unreal.AssetToolsHelpers.get_asset_tools().create_asset(
        name, folder, unreal.MaterialInstanceConstant, factory
    )
    if a:
        try:
            a.set_editor_property("parent", unreal.load_asset(parent_path))
        except Exception:
            pass
    return a


def activate_layer_a(mic: unreal.MaterialInstanceConstant, s) -> dict:
    """Explicit LayerA activation: bLayerA_Active, LayerA_TextureWeight, TextureWeight."""
    lib = unreal.MaterialEditingLibrary
    parent = mic.parent
    if not parent:
        return {}
    try:
        scalars = {str(x) for x in lib.get_scalar_parameter_names(parent)}
        switches = {str(x) for x in lib.get_static_switch_parameter_names(parent)}
    except Exception:
        return {}
    setv = {}
    if "TextureWeight" in scalars:
        lib.set_material_instance_scalar_parameter_value(mic, "TextureWeight", 1.0)
        setv["TextureWeight"] = 1.0
    if "LayerA_TextureWeight" in scalars:
        lib.set_material_instance_scalar_parameter_value(mic, "LayerA_TextureWeight", 1.0)
        setv["LayerA_TextureWeight"] = 1.0
    if "bLayerA_Active" in switches:
        lib.set_material_instance_static_switch_parameter_value(mic, "bLayerA_Active", True)
        setv["bLayerA_Active"] = True
    return setv


def route_textures(mic: unreal.MaterialInstanceConstant, prop: str, slot_name: str) -> dict:
    """PBR route (universal-master MIs only): pack set > colormap > tileable fallback. BaseTint kept."""
    lib = unreal.MaterialEditingLibrary
    parent = mic.parent
    if not parent or parent.get_path_name() != MASTER:
        return {}
    try:
        tex_params = {str(x) for x in lib.get_texture_parameter_names(parent)}
    except Exception:
        tex_params = set()
    routed = {}
    set_ = pack_set_for(prop, slot_name)

    def put(param, role):
        if param not in tex_params:
            return
        tex = None
        src = set_.get(role)
        if src:
            stem = Path(src).stem
            tex = unreal.load_asset(f"{TEX_ROOT}/{pack_for_prop(prop)}/{stem}")
        if not tex and role == "albedo":
            cm = f"/Game/EnvSandbox/Meshes/Environment/{prop}/Textures/colormap"
            if unreal.EditorAssetLibrary.does_asset_exist(cm):
                tex = unreal.load_asset(cm)
        if not tex:
            fb = tileable_fallback(role) if role in ("albedo", "normal", "roughness", "metallic", "ao", "orm") else ""
            if fb:
                tex = unreal.load_asset(fb)
        if tex:
            lib.set_material_instance_texture_parameter_value(mic, param, tex)
            routed[param] = tex.get_path_name()

    put("Albedo", "albedo")
    put("NormalMap", "normal")
    put("ORM", "orm")
    put("RoughnessMap", "roughness")
    put("MetallicMap", "metallic")
    if "HeightMap" in tex_params and set_.get("height"):
        put("HeightMap", "height")
    if "EmissiveMap" in tex_params and set_.get("emissive"):
        put("EmissiveMap", "emissive")
    return routed


def phase_c(chunk: int, chunk_size: int):
    st = state()
    done = set(st.get("c_done", []))
    lib = unreal.MaterialEditingLibrary

    # C1: fix every MI under EnvSandbox meshes + Library (exclude pack MIs to be deleted)
    all_mis = []
    for root in (ENV, "/Game/EnvSandbox/Library/Migrated", "/Game/Library/Migrated"):
        if unreal.EditorAssetLibrary.does_directory_exist(root):
            all_mis += [p for p in list_assets(root) if class_name(p) == "MaterialInstanceConstant"]
    remaining = [p for p in all_mis if p not in done]
    if chunk < 0:
        batch = remaining
    else:
        batch = remaining[chunk * chunk_size:(chunk + 1) * chunk_size]
    rows = []
    for idx, p in enumerate(batch):
        mic = unreal.load_asset(p)
        if not isinstance(mic, unreal.MaterialInstanceConstant):
            done.add(p)
            continue
        parts = p.split("/")
        prop = ""
        for i, part in enumerate(parts):
            if part == "Environment" and i + 1 < len(parts):
                prop = parts[i + 1]
                break
        act = activate_layer_a(mic, None)
        routed = route_textures(mic, prop, "") if "/Library/" not in p else {}
        if act or routed:
            unreal.EditorAssetLibrary.save_loaded_asset(mic, only_if_is_dirty=False)
            rows.append({"path": p, "activated": act, "routed": routed})
        done.add(p)
        if idx % 25 == 0:
            st["c_done"] = sorted(done)
            save_state(st)
    st["c_done"] = sorted(done)
    save_state(st)
    print(f"PHASE_C1 chunk={chunk}: processed={len(batch)} changed={len(rows)} total_done={len(done)}/{len(all_mis)}")

    # C2: route bad mesh slots (AvatarGarden MI creation, prop routing, Library explicit, loose)
    if chunk == 0:
        bad = []
        for root in (ENV, "/Game/EnvSandbox/Library/Migrated", "/Game/Library/Migrated"):
            if not unreal.EditorAssetLibrary.does_directory_exist(root):
                continue
            for p in list_assets(root):
                if class_name(p) not in ("StaticMesh", "SkeletalMesh"):
                    continue
                a = unreal.load_asset(p)
                mats = getattr(a, "static_materials", None) or getattr(a, "materials", None) or []
                for i, s in enumerate(mats):
                    mat = getattr(s, "material_interface", None)
                    mp = mat.get_path_name() if mat else "NONE"
                    if mp == "NONE" or "WorldGridMaterial" in mp or "MI_Universal_" in mp or "/ImportedPacks/MI_Env" in mp:
                        bad.append((p, i, str(getattr(s, "material_slot_name", ""))))
        slot_rows = []
        for p, i, slot_name in bad:
            parts = p.split("/")
            stem = parts[-1].split(".")[0]
            prop_dir = "/".join(parts[:-1])
            target = None
            if "/Library/" in p and "/Game/EnvSandbox/" not in p:
                # explicit fallback to EnvSandbox migrated copy MI
                rel = p.split("/Library/", 1)[1]
                env_twin = f"/Game/EnvSandbox/Library/{rel}"
                env_mi = f"{env_twin}/{stem}"
                if unreal.EditorAssetLibrary.does_asset_exist(env_mi):
                    target = env_mi
                else:
                    folder = env_twin
                    if unreal.EditorAssetLibrary.does_directory_exist(folder):
                        for c in list_assets(folder, recursive=False):
                            if c.rsplit("/", 1)[-1].startswith(("MI_", "M_")):
                                target = c
                                break
            elif f"{prop_dir}/{stem}" != prop_dir:
                mats_dir = f"{prop_dir}/Materials"
                if unreal.EditorAssetLibrary.does_directory_exist(mats_dir):
                    cand = f"{mats_dir}/{slot_name}"
                    if unreal.EditorAssetLibrary.does_asset_exist(cand):
                        target = cand
                    else:
                        ms = [c for c in list_assets(mats_dir, recursive=False) if class_name(c) == "MaterialInstanceConstant"]
                        if len(ms) == 1:
                            target = ms[0]
            if not target and stem.endswith("_Art") and "Environment/" in p:
                # AvatarGarden: create MI from pack set (dedupe per set)
                mic_dir = f"{ENV}/AvatarGarden/Materials"
                unreal.EditorAssetLibrary.make_directory(mic_dir)
                set_ = pack_set_for(stem, slot_name)
                mi_name = f"MI_{stem.split('_')[0]}" if set_ else f"MI_{stem}"
                cand = f"{mic_dir}/{mi_name}"
                if not unreal.EditorAssetLibrary.does_asset_exist(cand):
                    parent = unreal.load_asset(MASTER)
                    mic = create_mi(MASTER, cand)
                    if mic:
                        for k, v in activate_layer_a(mic, None).items():
                            pass
                        for k, v in route_textures(mic, stem, slot_name).items():
                            pass
                        unreal.EditorAssetLibrary.save_loaded_asset(mic, only_if_is_dirty=False)
                if unreal.EditorAssetLibrary.does_asset_exist(cand):
                    target = cand
            if not target:
                # loose mesh: per-mesh MI with tileables only
                mic_dir = f"{prop_dir}/_Loose"
                unreal.EditorAssetLibrary.make_directory(mic_dir)
                cand = f"{mic_dir}/MI_{stem}"
                if not unreal.EditorAssetLibrary.does_asset_exist(cand):
                    parent = unreal.load_asset(MASTER)
                    mic = create_mi(MASTER, cand)
                    if mic:
                        activate_layer_a(mic, None)
                        route_textures(mic, stem, slot_name)
                        unreal.EditorAssetLibrary.save_loaded_asset(mic, only_if_is_dirty=False)
                if unreal.EditorAssetLibrary.does_asset_exist(cand):
                    target = cand
            if target:
                a = unreal.load_asset(p)
                mats = getattr(a, "static_materials", None) or getattr(a, "materials", None) or []
                if i < len(mats):
                    if hasattr(a, "set_material"):
                        a.set_material(i, unreal.load_asset(target))
                    else:
                        mats[i].material_interface = unreal.load_asset(target)
                    unreal.EditorAssetLibrary.save_loaded_asset(a, only_if_is_dirty=False)
                slot_rows.append({"mesh": p, "slot": i, "slot_name": slot_name, "to": target})
        st["c_bad_done"] = True
        save_state(st)
        print(f"PHASE_C2: bad_slots={len(bad)} routed={len(slot_rows)}")

    # C3: BlingVol3 MIs (once)
    if chunk == 0 and not st.get("c_bling_done"):
        bling_rows = []
        for nn in range(1, 16):
            n = f"{nn:02d}"
            mic_dir = "/Game/EnvSandbox/Materials/Instances/BlingVol3"
            unreal.EditorAssetLibrary.make_directory(mic_dir)
            cand = f"{mic_dir}/MI_BlingVol3_{n}"
            if unreal.EditorAssetLibrary.does_asset_exist(cand):
                continue
            parent = unreal.load_asset(MASTER)
            mic = create_mi(MASTER, cand)
            if not mic:
                continue
            activate_layer_a(mic, None)
            tex_dir = "/Game/EnvSandbox/Textures/BlingVol3"
            for param, suffix in (("Albedo", "basecolor"), ("NormalMap", "normal"),
                                  ("RoughnessMap", "roughness"), ("MetallicMap", "metallic"),
                                  ("HeightMap", "height")):
                t = unreal.load_asset(f"{tex_dir}/bling_surface_vol3_{n}_{suffix}")
                if t:
                    lib.set_material_instance_texture_parameter_value(mic, param, t)
            unreal.EditorAssetLibrary.save_loaded_asset(mic, only_if_is_dirty=False)
            bling_rows.append(cand)
        st["c_bling_done"] = True
        save_state(st)
        print(f"PHASE_C3: bling MIs created={len(bling_rows)}")


# ---------------------------------------------------------------- Phase D
def phase_d():
    st = state()
    ea = unreal.EditorAssetLibrary
    deleted = []
    # D1: duplicate meshes â€” delete ROOT copy, keep StaticMeshes twin
    dupes = json.loads((AUDIT / "sweep_pbr_state.json").read_text(encoding="utf-8")).get("duplicate_candidates", {})
    for root_p, info in dupes.items():
        twin = info["twin"]
        if not ea.does_asset_exist(root_p) or not ea.does_asset_exist(twin):
            continue
        root_refs = refs(root_p.split(".")[0])
        twin_refs = refs(twin.split(".")[0])
        if root_refs and not twin_refs:
            victim, keep = twin, root_p
        else:
            victim, keep = root_p, twin
        if refs(victim.split(".")[0]):
            continue  # both referenced -> keep both (owner-call)
        if not ea.delete_asset(victim):
            continue
        deleted.append({"victim": victim, "keep": keep})
    # D2: duplicate/zero-ref instances â€” orphaned pack MIs + duplicate override MIs
    pack_mis = []
    imp_dir = "/Game/EnvSandbox/Materials/Instances/Environment/ImportedPacks"
    if ea.does_directory_exist(imp_dir):
        pack_mis = [p for p in list_assets(imp_dir) if class_name(p) == "MaterialInstanceConstant"]
    for p in pack_mis:
        if not refs(p.split(".")[0]):
            if ea.delete_asset(p):
                deleted.append({"victim": p, "keep": None, "reason": "orphan pack MI"})
    st["d_done"] = True
    save_state(st)
    report = {"generated": now(), "deleted": deleted, "count": len(deleted)}
    (AUDIT / "pbr_dedupe_2026-08-14.json").write_text(json.dumps(report, indent=2), encoding="utf-8")
    print(f"PHASE_D: deleted={len(deleted)}")


# ---------------------------------------------------------------- Phase E
def phase_e():
    bad, unfinished = [], []
    ea = unreal.EditorAssetLibrary
    for root in (ENV, "/Game/EnvSandbox/Library/Migrated", "/Game/Library/Migrated"):
        if not ea.does_directory_exist(root):
            continue
        for p in list_assets(root):
            cls = class_name(p)
            if cls in ("StaticMesh", "SkeletalMesh"):
                a = unreal.load_asset(p)
                mats = getattr(a, "static_materials", None) or getattr(a, "materials", None) or []
                for i, s in enumerate(mats):
                    mat = getattr(s, "material_interface", None)
                    mp = mat.get_path_name() if mat else "NONE"
                    if mp == "NONE" or "WorldGridMaterial" in mp or "MI_Universal_" in mp or "/ImportedPacks/MI_Env" in mp:
                        bad.append({"path": p, "slot": i, "name": str(getattr(s, "material_slot_name", "")), "mat": mp})
            elif cls == "MaterialInstanceConstant" and "/Meshes/Environment/" in p and "/ImportedPacks/" not in p:
                mic = unreal.load_asset(p)
                if not mic or not mic.parent:
                    continue
                try:
                    sw = {str(x) for x in unreal.MaterialEditingLibrary.get_static_switch_parameter_names(mic.parent)}
                    sc = {str(x) for x in unreal.MaterialEditingLibrary.get_scalar_parameter_names(mic.parent)}
                except Exception:
                    continue
                if "bLayerA_Active" not in sw and "LayerA_TextureWeight" not in sc:
                    continue
                ok = True
                if "LayerA_TextureWeight" in sc:
                    v = unreal.MaterialEditingLibrary.get_material_instance_scalar_parameter_value(mic, "LayerA_TextureWeight")
                    if v != 1.0:
                        ok = False
                if not ok:
                    unfinished.append(p)
    report = {
        "generated": now(),
        "bad_slots": bad,
        "bad_slot_count": len(bad),
        "unfinished_mics": unfinished,
        "unfinished_mic_count": len(unfinished),
    }
    (AUDIT / "full_pbr_sweep_2026-08-14.json").write_text(json.dumps(report, indent=2), encoding="utf-8")
    print(f"PHASE_E: bad_slots={len(bad)} unfinished_mics={len(unfinished)}")


def main() -> int:
    argv = sys.argv[1:]
    phase = argv[argv.index("--phase") + 1] if "--phase" in argv else "B"
    chunk = int(argv[argv.index("--chunk") + 1]) if "--chunk" in argv else 0
    chunk_size = int(argv[argv.index("--chunk-size") + 1]) if "--chunk-size" in argv else 200
    print(f"PBR_PIPELINE: phase={phase} chunk={chunk} start={now()}", flush=True)
    if phase == "B":
        phase_b()
    elif phase == "C":
        phase_c(chunk, chunk_size)
    elif phase == "D":
        phase_d()
    elif phase == "E":
        phase_e()
    print(f"PBR_PIPELINE: phase={phase} chunk={chunk} done={now()}", flush=True)
    return 0


if __name__ == "__main__":
    time.sleep(5)
    sys.exit(main())

