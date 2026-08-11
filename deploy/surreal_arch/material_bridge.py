"""Material Bridge ΓÇö Blender material slot Γåö Unreal material instance crosswalk.

Solves the #1 friction point in the BlenderΓåÆUnreal pipeline:
  - Browse known UE material instances from Blender
  - Auto-map Blender material names to UE paths via fuzzy matching
  - Persist crosswalk as .material_map.json  
  - Auto-embed correct UE paths during LiveLink export

Integrates with:
  - Live Bridge dashboard (live_bridge.py) ΓÇö shares the N-panel
  - surreal_world/export.py ΓÇö ROLE_UE_HINTS + STYLE_ROLE_OVERRIDES
  - UE Monolith MCP (port 9316) ΓÇö live material catalog queries
  - LiveLink (port 9876) ΓÇö material paths embedded in scene exports
"""

from __future__ import annotations

import json
import os
import re
from difflib import SequenceMatcher
from pathlib import Path

import bpy
from bpy.props import (
    BoolProperty, CollectionProperty, EnumProperty,
    FloatProperty, IntProperty, PointerProperty, StringProperty,
)
from bpy.types import Panel, Operator, PropertyGroup

from ..branding import N_PANEL_CATEGORY


# ΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉ
# Known UE material catalog ΓÇö seed from export.py + common patterns
# ΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉ

DEFAULT_UE_CATALOG: list[dict] = [
    # Stylized environment materials
    {"path": "/Game/EnvSandbox/Materials/Instances/Environment/Stylized/MI_Show_StoneCliff",
     "tags": ["stone", "cliff", "rock", "organic", "stylized"], "role": "large"},
    {"path": "/Game/EnvSandbox/Materials/Instances/Environment/Stylized/MI_Show_Default",
     "tags": ["default", "generic", "base", "stylized"], "role": "medium"},
    {"path": "/Game/EnvSandbox/Materials/Instances/Environment/Stylized/MI_Show_ContactRimHero",
     "tags": ["hero", "rim", "edge", "contact", "stylized"], "role": "hero"},
    {"path": "/Game/EnvSandbox/Materials/Instances/Environment/Stylized/MI_Trimsheet_HeavyWear",
     "tags": ["trim", "wear", "damage", "edge", "stylized"], "role": "wall"},
    {"path": "/Game/EnvSandbox/Materials/Instances/Environment/Stylized/MI_Trimsheet_Arch",
     "tags": ["trim", "arch", "curve", "stylized"], "role": "arch"},
    # Zen / Japanese
    {"path": "/Game/EnvSandbox/Materials/Instances/Environment/Zen/MI_Zen_Karesansui",
     "tags": ["zen", "gravel", "sand", "garden"], "role": "sacred"},
    {"path": "/Game/EnvSandbox/Materials/Instances/Environment/Zen/MI_Zen_ToriiVermillion",
     "tags": ["zen", "torii", "red", "vermilion", "wood"], "role": "gate"},
    {"path": "/Game/EnvSandbox/Materials/Instances/Environment/Zen/MI_Zen_HondenSanctum",
     "tags": ["zen", "temple", "sanctum", "dark", "wood"], "role": "sacred"},
    {"path": "/Game/EnvSandbox/Materials/Instances/Environment/Zen/MI_Zen_MossGarden",
     "tags": ["zen", "moss", "green", "organic", "garden"], "role": "large"},
    {"path": "/Game/EnvSandbox/Materials/Instances/Environment/Zen/MI_Zen_SakuraDrift",
     "tags": ["zen", "sakura", "pink", "petal", "spring"], "role": "monument"},
    # Character materials
    {"path": "/Game/EnvSandbox/Materials/Instances/Melusina/MI_Melusina_Body",
     "tags": ["melusina", "body", "skin", "character"], "role": "character"},
    {"path": "/Game/EnvSandbox/Materials/Instances/Melusina/MI_Melusina_Cloth",
     "tags": ["melusina", "cloth", "fabric", "dress"], "role": "character"},
    {"path": "/Game/EnvSandbox/Materials/Instances/Melusina/MI_Melusina_Hair",
     "tags": ["melusina", "hair", "strand", "anime"], "role": "character"},
    {"path": "/Game/EnvSandbox/Materials/Instances/Melusina/MI_Melusina_Eyes",
     "tags": ["melusina", "eyes", "iris", "character"], "role": "character"},
    # Props / Ornaments
    {"path": "/Game/EnvSandbox/Materials/Instances/Ornaments/MI_Ornament_Gold",
     "tags": ["gold", "ornament", "metal", "decorative"], "role": "ornament"},
    {"path": "/Game/EnvSandbox/Materials/Instances/Ornaments/MI_Ornament_Stone",
     "tags": ["stone", "ornament", "rock", "decorative"], "role": "ornament"},
    {"path": "/Game/EnvSandbox/Materials/Instances/Ornaments/MI_Ornament_Iron",
     "tags": ["iron", "metal", "dark", "ornament"], "role": "ornament"},
    # VFX / Special
    {"path": "/Game/EnvSandbox/Materials/Instances/VFX/MI_VFX_GoldGlow",
     "tags": ["vfx", "gold", "glow", "particle", "magic"], "role": "vfx"},
    {"path": "/Game/EnvSandbox/Materials/Instances/VFX/MI_VFX_Starlight",
     "tags": ["vfx", "star", "light", "glow", "magic"], "role": "vfx"},
    {"path": "/Game/EnvSandbox/Materials/Instances/VFX/MI_VFX_Celestial_Aura",
     "tags": ["vfx", "aura", "celestial", "magic", "particle"], "role": "vfx"},
    # Zundamon character materials
    {"path": "/Game/Melodia/Characters/Zundamon/MI_Zundamon_Body",
     "tags": ["zundamon", "body", "skin", "character", "anime"], "role": "character"},
    {"path": "/Game/Melodia/Characters/Zundamon/MI_Zundamon_Cloth",
     "tags": ["zundamon", "cloth", "fabric", "character", "anime"], "role": "character"},
    {"path": "/Game/Melodia/Characters/Zundamon/MI_Zundamon_Hair",
     "tags": ["zundamon", "hair", "green", "character", "anime"], "role": "character"},
    {"path": "/Game/Melodia/Characters/Zundamon/MI_Zundamon_Head",
     "tags": ["zundamon", "head", "face", "character", "anime"], "role": "character"},
    {"path": "/Game/Melodia/Characters/Zundamon/MI_Zundamon_Eye",
     "tags": ["zundamon", "eye", "iris", "character", "anime"], "role": "character"},
]


# ΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉ
# Data model ΓÇö material crosswalk
# ΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉ

class MATB_CrosswalkEntry(PropertyGroup):
    """One crosswalk entry: Blender material slot ΓåÆ UE material path."""
    blender_slot: StringProperty(name="Blender Slot")
    blender_material: StringProperty(name="Blender Material")
    ue_path: StringProperty(
        name="UE Material Path",
        description="Full Unreal material instance path, e.g. /Game/EnvSandbox/Materials/...",
    )
    auto_matched: BoolProperty(name="Auto Matched", default=False)
    confidence: FloatProperty(name="Confidence", default=0.0, min=0.0, max=1.0)


class MATB_Settings(PropertyGroup):
    """Material bridge settings persisted on the scene."""
    entries: CollectionProperty(type=MATB_CrosswalkEntry)
    active_entry_index: IntProperty(default=0)
    catalog_filter: StringProperty(
        name="Filter",
        default="",
        description="Filter UE material catalog by name, tag, or path",
        options={"TEXTEDIT_UPDATE"},
    )
    expand_catalog: BoolProperty(name="Expand Catalog", default=True)
    expand_slots: BoolProperty(name="Expand Slots", default=True)
    expand_crosswalk: BoolProperty(name="Expand Crosswalk", default=True)
    auto_crosswalk_enabled: BoolProperty(
        name="Auto Crosswalk",
        default=True,
        description="Auto-map Blender material names to UE paths on export",
    )


# ΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉ
# Crosswalk engine ΓÇö fuzzy matching + persistence
# ΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉ

def _fuzzy_match(name: str, candidates: list[dict]) -> tuple[dict | None, float]:
    """Fuzzy-match a Blender material name against the UE catalog."""
    best, best_score = None, 0.0
    name_lower = name.lower().replace("_", " ").replace(".", " ").strip()

    for entry in candidates:
        path = entry["path"].lower()
        path_stem = Path(path).stem.lower().replace("_", " ").replace("mi_", "").replace("mi ", "")

        # Direct substring match
        if name_lower in path_stem or path_stem in name_lower:
            score = 0.85
            if score > best_score:
                best, best_score = entry, score
            continue

        # Word-level overlap
        name_words = set(name_lower.split())
        path_words = set(path_stem.split())
        overlap = len(name_words & path_words)
        if overlap > 0:
            score = 0.4 + 0.2 * overlap
            if score > best_score:
                best, best_score = entry, score
            continue

        # Sequence similarity
        sim = SequenceMatcher(None, name_lower, path_stem).ratio()
        if sim > best_score:
            best, best_score = entry, sim

    return best, best_score


def _get_ue_catalog() -> list[dict]:
    """Get the full UE material catalog (default + user-extended)."""
    catalog = list(DEFAULT_UE_CATALOG)
    # Load user-extended catalog if present
    ext_path = _catalog_path()
    if os.path.isfile(ext_path):
        try:
            extra = json.loads(Path(ext_path).read_text(encoding="utf-8"))
            if isinstance(extra, list):
                catalog.extend(extra)
        except Exception:
            pass
    return catalog


def _catalog_path() -> str:
    """Resolve the material catalog JSON path."""
    base = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    return os.path.join(base, "uerial_catalog.json")


def _crosswalk_path() -> str:
    """Resolve the material crosswalk JSON path."""
    blend_path = bpy.data.filepath
    if blend_path:
        return os.path.splitext(blend_path)[0] + ".material_map.json"
    base = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    return os.path.join(base, "default.material_map.json")


def auto_crosswalk_object(obj) -> dict[str, str]:
    """Run auto-crosswalk on all material slots of an object.

    Returns {blender_material_name: ue_path}.
    """
    if obj is None or not hasattr(obj, "material_slots"):
        return {}
    catalog = _get_ue_catalog()
    mapping: dict[str, str] = {}
    for slot in obj.material_slots:
        if slot.material is None:
            continue
        mat_name = slot.material.name
        match, score = _fuzzy_match(mat_name, catalog)
        if match and score >= 0.3:
            mapping[mat_name] = match["path"]
    return mapping


def save_crosswalk(mapping: dict[str, str]) -> str:
    """Persist crosswalk to .material_map.json beside the .blend."""
    path = _crosswalk_path()
    # Load existing, merge
    existing: dict[str, str] = {}
    if os.path.isfile(path):
        try:
            existing = json.loads(Path(path).read_text(encoding="utf-8"))
        except Exception:
            pass
    existing.update(mapping)
    Path(path).write_text(
        json.dumps(existing, indent=2, sort_keys=True), encoding="utf-8"
    )
    return path


def load_crosswalk() -> dict[str, str]:
    """Load persisted crosswalk from .material_map.json."""
    path = _crosswalk_path()
    if os.path.isfile(path):
        try:
            return json.loads(Path(path).read_text(encoding="utf-8"))
        except Exception:
            pass
    return {}


def get_ue_path_for_material(mat_name: str) -> str:
    """Resolve a Blender material name to a UE path using saved crosswalk."""
    cw = load_crosswalk()
    return cw.get(mat_name, "")


# ΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉ
# Operators
# ΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉ

class MATB_OT_scan_slots(Operator):
    """Scan material slots on the active object and populate crosswalk."""

    bl_idname = "matb.scan_slots"
    bl_label = "Scan Material Slots"
    bl_options = {"REGISTER", "UNDO"}

    @classmethod
    def poll(cls, context):
        return context.active_object is not None

    def execute(self, context):
        obj = context.active_object
        settings = context.scene.matb_bridge
        settings.entries.clear()

        if not hasattr(obj, "material_slots") or not obj.material_slots:
            self.report({"WARNING"}, "No material slots on active object")
            return {"CANCELLED"}

        # Run auto-crosswalk
        auto_map = auto_crosswalk_object(obj)

        for i, slot in enumerate(obj.material_slots):
            entry = settings.entries.add()
            entry.blender_slot = slot.name
            entry.blender_material = slot.material.name if slot.material else "(none)"

            if auto_crosswalk_enabled := settings.auto_crosswalk_enabled:
                ue_path = auto_map.get(slot.material.name if slot.material else "", "")
                if ue_path:
                    entry.ue_path = ue_path
                    entry.auto_matched = True
                    entry.confidence = 0.85

            settings.active_entry_index = 0

        self.report(
            {"INFO"},
            f"Scanned {len(obj.material_slots)} slots, "
            f"{len(auto_map)} auto-matched",
        )
        return {"FINISHED"}


class MATB_OT_auto_crosswalk(Operator):
    """Auto-map all Blender materials to UE paths using fuzzy matching."""

    bl_idname = "matb.auto_crosswalk"
    bl_label = "Auto-Match All"
    bl_options = {"REGISTER", "UNDO"}

    def execute(self, context):
        settings = context.scene.matb_bridge
        obj = context.active_object

        if obj is None:
            self.report({"WARNING"}, "Select an object first")
            return {"CANCELLED"}

        auto_map = auto_crosswalk_object(obj)
        mapped_count = 0

        for entry in settings.entries:
            if entry.ue_path and entry.auto_matched:
                continue  # Already auto-matched
            ue_path = auto_map.get(entry.blender_material, "")
            if ue_path:
                entry.ue_path = ue_path
                entry.auto_matched = True
                entry.confidence = 0.85
                mapped_count += 1

        # Also do a global pass on all materials in the scene
        global_map: dict[str, str] = {}
        for mat in bpy.data.materials:
            if mat.name in auto_map:
                global_map[mat.name] = auto_map[mat.name]

        if global_map:
            save_crosswalk(global_map)

        self.report(
            {"INFO"},
            f"Auto-matched {mapped_count} slots, saved {len(global_map)} to crosswalk",
        )
        return {"FINISHED"}


class MATB_OT_save_crosswalk(Operator):
    """Persist the current crosswalk to .material_map.json."""

    bl_idname = "matb.save_crosswalk"
    bl_label = "Save Crosswalk"
    bl_options = {"REGISTER", "UNDO"}

    def execute(self, context):
        settings = context.scene.matb_bridge
        mapping: dict[str, str] = {}
        for entry in settings.entries:
            if entry.ue_path and entry.blender_material:
                mapping[entry.blender_material] = entry.ue_path

        if not mapping:
            self.report({"WARNING"}, "No mappings to save")
            return {"CANCELLED"}

        path = save_crosswalk(mapping)
        self.report({"INFO"}, f"Saved {len(mapping)} mappings to {os.path.basename(path)}")
        return {"FINISHED"}


class MATB_OT_load_crosswalk(Operator):
    """Load crosswalk from .material_map.json."""

    bl_idname = "matb.load_crosswalk"
    bl_label = "Load Crosswalk"
    bl_options = {"REGISTER", "UNDO"}

    def execute(self, context):
        cw = load_crosswalk()
        if not cw:
            self.report({"WARNING"}, "No saved crosswalk found")
            return {"CANCELLED"}

        settings = context.scene.matb_bridge
        for entry in settings.entries:
            if entry.blender_material in cw:
                entry.ue_path = cw[entry.blender_material]

        self.report({"INFO"}, f"Loaded {len(cw)} mappings")
        return {"FINISHED"}


class MATB_OT_apply_to_slot(Operator):
    """Apply a specific UE material path to the active crosswalk entry."""

    bl_idname = "matb.apply_to_slot"
    bl_label = "Apply UE Path"
    bl_options = {"REGISTER", "UNDO"}

    ue_path: StringProperty(name="UE Path")

    def execute(self, context):
        settings = context.scene.matb_bridge
        idx = settings.active_entry_index
        if 0 <= idx < len(settings.entries):
            settings.entries[idx].ue_path = self.ue_path
            settings.entries[idx].auto_matched = False
            self.report({"INFO"}, f"Applied {Path(self.ue_path).stem}")
        return {"FINISHED"}


class MATB_OT_clear_slot(Operator):
    """Clear the UE path for the active crosswalk entry."""

    bl_idname = "matb.clear_slot"
    bl_label = "Clear Mapping"
    bl_options = {"REGISTER", "UNDO"}

    def execute(self, context):
        settings = context.scene.matb_bridge
        idx = settings.active_entry_index
        if 0 <= idx < len(settings.entries):
            settings.entries[idx].ue_path = ""
            settings.entries[idx].auto_matched = False
        return {"FINISHED"}


# ΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉ
# Panel ΓÇö Material Bridge (nested under Live Bridge)
# ΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉ

class MATB_PT_material_bridge(Panel):
    """Material Bridge ΓÇö Blender Γåö Unreal material crosswalk."""

    bl_label = "Material Bridge"
    bl_idname = "MATB_PT_material_bridge"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_category = N_PANEL_CATEGORY
    bl_parent_id = "SURREAL_ARCH_PT_genome_carousel"
    bl_options = {"DEFAULT_CLOSED"}
    bl_order = 16

    @classmethod
    def poll(cls, context):
        return context.active_object is not None

    def draw(self, context):
        layout = self.layout
        settings = context.scene.matb_bridge
        obj = context.active_object

        # ΓöÇΓöÇ Object info ΓöÇΓöÇ
        row = layout.row(align=True)
        row.label(text=f"Object: {obj.name}", icon="OBJECT_DATA")
        slot_count = len(obj.material_slots) if hasattr(obj, "material_slots") else 0
        row.label(text=f"{slot_count} slots")

        # ΓöÇΓöÇ Scan + Auto buttons ΓöÇΓöÇ
        row = layout.row(align=True)
        row.operator("matb.scan_slots", text="Scan Slots", icon="VIEWZOOM")
        row.operator("matb.auto_crosswalk", text="Auto-Match", icon="AUTOMERGE_ON")
        row.prop(settings, "auto_crosswalk_enabled", text="",
                 icon="SETTINGS" if settings.auto_crosswalk_enabled else "PROP_OFF")

        # ΓöÇΓöÇ Crosswalk entries ΓöÇΓöÇ
        if settings.entries:
            self._draw_crosswalk(layout, context, settings)
        else:
            layout.label(text="No slots scanned. Click 'Scan Slots' above.", icon="INFO")

        # ΓöÇΓöÇ UE Catalog browser ΓöÇΓöÇ
        self._draw_catalog(layout, context, settings)

        # ΓöÇΓöÇ Save/Load ΓöÇΓöÇ
        layout.separator()
        row = layout.row(align=True)
        row.operator("matb.save_crosswalk", text="Save Map", icon="FILE_TICK")
        row.operator("matb.load_crosswalk", text="Load Map", icon="FILE_REFRESH")

    def _draw_crosswalk(self, layout, context, settings):
        """Draw the crosswalk table: slot ΓåÆ UE path."""
        box = layout.box()
        row = box.row(align=True)
        row.prop(settings, "expand_crosswalk", text="",
                 icon="DOWNARROW_HLT" if settings.expand_crosswalk else "RIGHTARROW",
                 emboss=False)
        row.label(text=f"Crosswalk ({len(settings.entries)} slots)", icon="MATERIAL")

        if not settings.expand_crosswalk:
            return

        for i, entry in enumerate(settings.entries):
            is_active = (i == settings.active_entry_index)
            sub = box.box() if is_active else box.column(align=True)

            row = sub.row(align=True)
            # Select button
            icon = "CHECKBOX_HLT" if entry.ue_path else "CHECKBOX_DEHLT"
            if not is_active:
                op = row.operator("matb.scan_slots", text="", icon=icon, emboss=False)
                # Can't set entry index easily ΓÇö use a simple label instead
            row.label(text=f"[{i}] {entry.blender_slot[:24]}", icon=icon)

            if entry.blender_material and entry.blender_material != "(none)":
                row.label(text=f"ΓåÆ {entry.blender_material[:20]}", icon="DOT")

            # Auto-match badge
            if entry.auto_matched:
                row.label(text="", icon="AUTOMERGE_ON")

            # UE path display
            if entry.ue_path:
                stem = Path(entry.ue_path).stem
                row.label(text=stem[:20], icon="CHECKBOX_HLT")
            else:
                row.label(text="(unmapped)", icon="CHECKBOX_DEHLT")

    def _draw_catalog(self, layout, context, settings):
        """Draw the UE material catalog browser."""
        box = layout.box()
        row = box.row(align=True)
        row.prop(settings, "expand_catalog", text="",
                 icon="DOWNARROW_HLT" if settings.expand_catalog else "RIGHTARROW",
                 emboss=False)
        row.label(text="UE Material Catalog", icon="ASSET_MANAGER")

        if not settings.expand_catalog:
            return

        # Search filter
        col = box.column(align=True)
        col.prop(settings, "catalog_filter", text="", icon="VIEWZOOM")

        # Catalog entries
        catalog = _get_ue_catalog()
        ft = settings.catalog_filter.lower()

        shown = 0
        for entry in catalog:
            path = entry["path"]
            if ft and ft not in path.lower() and not any(ft in t for t in entry.get("tags", [])):
                continue

            if shown >= 15:
                col.label(text=f"... {len(catalog) - 15} more (filter to narrow)", icon="DOT")
                break

            stem = Path(path).stem
            row = col.row(align=True)
            op = row.operator("matb.apply_to_slot", text=stem, icon="MATERIAL")
            op.ue_path = path

            # Tags
            tags = entry.get("tags", [])
            if tags:
                row.label(text=", ".join(tags[:2]), icon="OUTLINER_OB_FONT")

            shown += 1


# ΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉ
# Registration
# ΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉ

CLASSES = [
    MATB_CrosswalkEntry,
    MATB_Settings,
    MATB_OT_scan_slots,
    MATB_OT_auto_crosswalk,
    MATB_OT_save_crosswalk,
    MATB_OT_load_crosswalk,
    MATB_OT_apply_to_slot,
    MATB_OT_clear_slot,
    MATB_PT_material_bridge,
]


def register_props():
    bpy.types.Scene.matb_bridge = PointerProperty(type=MATB_Settings)


def unregister_props():
    try:
        del bpy.types.Scene.matb_bridge
    except AttributeError:
        pass
