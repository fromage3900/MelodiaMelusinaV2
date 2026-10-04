"""Material Instance Widget UI Panel & In-Editor Inspector.

Provides an organized, column-aware UI panel for inspecting, clamping, and tuning
Material Instances derived from Melodia's master materials:
  - M_Master_Toon_Universal
  - M_Master_Toon_Landscape_HeightBlend
  - M_Master_Nikki
  - M_Master_Nikki_Landscape

Features:
  - Categorizes all parameters into canonical columns per master_column_scheme.py
  - Enforces physical / artistic slider bounds from master_material_clamping_engine.py
  - Detects active overrides vs master defaults
  - Integrates with envui command registry and LevelEditor menu
  - Supports live parameter updates in-editor and browser-based lookdev launch
"""
from __future__ import annotations

import json
import logging
import os
import sys
import webbrowser
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

PYTHON_DIR = Path(__file__).resolve().parent
if str(PYTHON_DIR) not in sys.path:
    sys.path.insert(0, str(PYTHON_DIR))

import master_column_scheme as scheme
import master_material_clamping_engine as clamping

logger = logging.getLogger("MaterialInstanceWidget")
PROJECT_ROOT = Path(__file__).resolve().parents[2]
WEB_PANEL_HTML = PROJECT_ROOT.parent / "teamwork_projects" / "material_instance_widget_panel" / "index.html"


def _safe_unreal():
    try:
        import unreal  # type: ignore
        return unreal
    except ImportError:
        return None


@dataclass
class ParameterViewItem:
    name: str
    param_type: str  # "scalar", "vector", "texture", "switch"
    value: Any
    is_overridden: bool
    group: str
    sort_priority: int
    slider_min: Optional[float] = None
    slider_max: Optional[float] = None
    description: Optional[str] = None


@dataclass
class InstanceInspectorState:
    instance_name: str
    instance_path: str
    parent_master: str
    total_parameters: int
    override_count: int
    groups: Dict[str, List[Dict[str, Any]]]
    generated_at: str


class MaterialInstanceWidgetPanel:
    """Core controller for Material Instance inspection and parameter tuning."""

    @staticmethod
    def get_selected_or_default_instance() -> str:
        """Retrieve current Content Browser selection or return hero default."""
        unreal = _safe_unreal()
        default_hero = "/Game/EnvSandbox/Materials/Instances/Showcase/MI_Show_NikkiHero"

        if unreal is not None:
            try:
                selected = unreal.EditorUtilityLibrary.get_selected_assets()
                for asset in selected:
                    if isinstance(asset, unreal.MaterialInstanceConstant):
                        return asset.get_path_name().split(".")[0]
            except Exception as e:
                logger.warning(f"Failed to read selected asset: {e}")

        return default_hero

    @staticmethod
    def inspect_instance(instance_path: Optional[str] = None) -> InstanceInspectorState:
        """Inspect a Material Instance, resolving values, clamps, and column groupings."""
        target_path = instance_path or MaterialInstanceWidgetPanel.get_selected_or_default_instance()
        inst_name = target_path.rsplit("/", 1)[-1].split(".")[0]

        unreal = _safe_unreal()
        parent_master = "M_Master_Toon_Universal"
        overridden_scalars: Dict[str, float] = {}
        overridden_vectors: Dict[str, List[float]] = {}
        overridden_switches: Dict[str, bool] = {}
        overridden_textures: Dict[str, str] = {}

        if unreal is not None and unreal.EditorAssetLibrary.does_asset_exist(target_path):
            mi_asset = unreal.EditorAssetLibrary.load_asset(target_path)
            if isinstance(mi_asset, unreal.MaterialInstanceConstant):
                # Detect Parent
                parent = mi_asset.get_editor_property("parent")
                if parent:
                    parent_master = parent.get_name()

                # Read active scalar parameter values
                try:
                    for s in unreal.MaterialEditingLibrary.get_scalar_parameter_names(mi_asset):
                        s_name = str(s)
                        val = unreal.MaterialEditingLibrary.get_material_instance_scalar_parameter_value(mi_asset, s)
                        overridden_scalars[s_name] = float(val) if val is not None else 0.0
                except Exception:
                    pass

                # Read active vector parameter values
                try:
                    for v in unreal.MaterialEditingLibrary.get_vector_parameter_names(mi_asset):
                        v_name = str(v)
                        lin_color = unreal.MaterialEditingLibrary.get_material_instance_vector_parameter_value(mi_asset, v)
                        if lin_color is not None:
                            overridden_vectors[v_name] = [lin_color.r, lin_color.g, lin_color.b, lin_color.a]
                except Exception:
                    pass

                # Read active static switches
                try:
                    for sw in unreal.MaterialEditingLibrary.get_static_switch_parameter_names(mi_asset):
                        sw_name = str(sw)
                        sw_val = unreal.MaterialEditingLibrary.get_material_instance_static_switch_parameter_value(mi_asset, sw)
                        overridden_switches[sw_name] = bool(sw_val) if sw_val is not None else False
                except Exception:
                    pass

                # Read active texture overrides
                try:
                    for t in unreal.MaterialEditingLibrary.get_texture_parameter_names(mi_asset):
                        t_name = str(t)
                        tex = unreal.MaterialEditingLibrary.get_material_instance_texture_parameter_value(mi_asset, t)
                        if tex is not None:
                            overridden_textures[t_name] = tex.get_name()
                except Exception:
                    pass

        # If not live in editor, resolve parent master from catalog audit
        if unreal is None:
            # Fallback heuristic
            if "Landscape" in inst_name:
                parent_master = "M_Master_Toon_Landscape_HeightBlend"
            elif "Nikki" in inst_name:
                parent_master = "M_Master_Nikki"
            else:
                parent_master = "M_Master_Toon_Universal"

        # Resolve Master Column Scheme & Grouping
        try:
            canonical_groups = scheme.groups_for(parent_master)
        except ValueError:
            canonical_groups = scheme.UNIVERSAL_GROUPS

        meta = scheme.build_meta(canonical_groups)
        groups_dict: Dict[str, List[Dict[str, Any]]] = {grp_label: [] for grp_label, _ in canonical_groups}
        groups_dict["99 | Miscellaneous"] = []

        # Populate scalar parameters with clamps
        total_params = 0
        override_count = 0

        # Load master parameter definitions from Saved/Audit if available
        master_audit_file = PROJECT_ROOT / "Saved" / "Audit" / "master_material_clamps_catalog.json"
        master_scalars = {}
        if master_audit_file.is_file():
            try:
                catalog = json.loads(master_audit_file.read_text(encoding="utf-8"))
                m_info = catalog.get("masters", {}).get(parent_master, {})
                master_scalars = m_info.get("parameters", {})
            except Exception:
                pass

        # Build view items
        for grp_label, pnames in canonical_groups:
            for pname in pnames:
                total_params += 1
                is_overridden = (
                    pname in overridden_scalars
                    or pname in overridden_vectors
                    or pname in overridden_switches
                    or pname in overridden_textures
                )
                if is_overridden:
                    override_count += 1

                # Determine parameter type and clamp
                clamp_info = master_scalars.get(pname) or asdict(clamping.resolve_clamp(pname))
                grp, prio = meta.get(pname, ("99 | Miscellaneous", 9900))

                val = None
                p_type = "scalar"
                if pname.startswith("b") or pname.startswith("bUse"):
                    p_type = "switch"
                    val = overridden_switches.get(pname, False)
                elif "Color" in pname or "Tint" in pname or "RampLow" in pname or "RampMid" in pname or "RampHigh" in pname:
                    p_type = "vector"
                    val = overridden_vectors.get(pname, [1.0, 1.0, 1.0, 1.0])
                elif "Map" in pname or pname in ("Albedo", "NormalMap", "ORM", "HeightMap", "StarMap"):
                    p_type = "texture"
                    val = overridden_textures.get(pname, "T_Default_White")
                else:
                    p_type = "scalar"
                    val = overridden_scalars.get(pname, (clamp_info.get("slider_min", 0.0) + clamp_info.get("slider_max", 1.0)) * 0.5)

                item = ParameterViewItem(
                    name=pname,
                    param_type=p_type,
                    value=val,
                    is_overridden=is_overridden,
                    group=grp,
                    sort_priority=prio,
                    slider_min=clamp_info.get("slider_min"),
                    slider_max=clamp_info.get("slider_max"),
                    description=clamp_info.get("description"),
                )
                target_grp = grp if grp in groups_dict else "99 | Miscellaneous"
                groups_dict[target_grp].append(asdict(item))

        # Prune empty groups
        active_groups = {k: v for k, v in groups_dict.items() if len(v) > 0}

        return InstanceInspectorState(
            instance_name=inst_name,
            instance_path=target_path,
            parent_master=parent_master,
            total_parameters=total_params,
            override_count=override_count,
            groups=active_groups,
            generated_at=datetime.now(timezone.utc).isoformat(),
        )

    @staticmethod
    def set_scalar_parameter(instance_path: str, param_name: str, value: float) -> Dict[str, Any]:
        """Set a clamped scalar parameter on an instance in-editor."""
        unreal = _safe_unreal()
        if unreal is None:
            return {"ok": False, "error": "Unreal Engine not running"}

        clamp = clamping.resolve_clamp(param_name)
        clamped_val = max(clamp.slider_min, min(clamp.slider_max, float(value)))

        eal = unreal.EditorAssetLibrary
        if not eal.does_asset_exist(instance_path):
            return {"ok": False, "error": f"Asset {instance_path} not found"}

        mi = eal.load_asset(instance_path)
        if not isinstance(mi, unreal.MaterialInstanceConstant):
            return {"ok": False, "error": f"{instance_path} is not a MaterialInstanceConstant"}

        mel = unreal.MaterialEditingLibrary
        mel.set_material_instance_scalar_parameter_value(mi, param_name, clamped_val)
        mel.update_material_instance(mi)
        eal.save_loaded_asset(mi, only_if_is_dirty=True)

        return {
            "ok": True,
            "instance": instance_path,
            "param": param_name,
            "value": clamped_val,
            "min": clamp.slider_min,
            "max": clamp.slider_max,
        }

    @staticmethod
    def launch_web_panel() -> Dict[str, Any]:
        """Launch the standalone interactive Lookdev & Material Instance Web Panel."""
        if not WEB_PANEL_HTML.is_file():
            # Build directory if needed
            WEB_PANEL_HTML.parent.mkdir(parents=True, exist_ok=True)

        _resolved = str(WEB_PANEL_HTML.resolve()).replace("\\", "/")
        url = f"file:///{_resolved}"
        webbrowser.open(url)
        return {"ok": True, "url": url}


def show_in_editor_dialog(instance_path: Optional[str] = None) -> None:
    """In-editor command to display instance status or launch the interactive panel."""
    unreal = _safe_unreal()
    state = MaterialInstanceWidgetPanel.inspect_instance(instance_path)

    msg = (
        f"Material Instance Widget: {state.instance_name}\n"
        f"Parent Master: {state.parent_master}\n"
        f"Total Parameters: {state.total_parameters}\n"
        f"Active Overrides: {state.override_count}\n"
        f"Canonical Column Groups: {len(state.groups)}\n\n"
        f"Actions:\n"
        f"• Launching Interactive Web Lookdev & Clamping Panel\n"
        f"• Parameters clamped to master safety bounds\n"
    )

    if unreal is not None:
        unreal.log(f"[MaterialInstanceWidget] {msg}")
        MaterialInstanceWidgetPanel.launch_web_panel()
    else:
        print(msg)


if __name__ == "__main__":
    st = MaterialInstanceWidgetPanel.inspect_instance()
    print(f"Inspected: {st.instance_name} (Parent: {st.parent_master}, Overrides: {st.override_count})")
    print(f"Groups mapped: {len(st.groups)}")
