#!/usr/bin/env python3
"""
T3D Animation Blueprint Injector - automates AnimBP, BlendSpace, and
IK Retargeter operations via Monolith MCP's editor_query:run_python and
blueprint_query:build_blueprint_from_spec.

This is a companion to t3d_blueprint_injector.py focused on AnimBP-specific
modifications (state machines, blend space samples, blend weights, variables)
that require the in-editor Unreal Python API rather than generic node wiring.

Usage:
    injector = T3DAnimBlueprintInjector()
    injector.set_blendspace_sample("BS_MyBlend", 0, "A_Idle", 0.0)
    injector.set_anim_blueprint_variable("ABP_MyChar", "Speed", 0.0)
"""

import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from mcp_client import monolith


class T3DAnimBlueprintInjector:
    """Automate AnimBP / BlendSpace / IK Rig operations via Monolith MCP."""

    def _run_unreal_python(self, script, timeout=60):
        """Execute a Python script inside the Unreal Editor via editor_query:run_python."""
        result = monolith("editor_query", {
            "action": "run_python",
            "script": script,
        }, timeout=timeout)
        if result.startswith("ERROR:"):
            raise RuntimeError(f"editor_query:run_python failed: {result}")
        return result

    def _resolve_asset_path(self, path):
        """Normalise an asset path - strip .AssetName suffix if present, ensure /Game/ prefix."""
        path = path.replace("\\", "/")
        if "." in path:
            path = path.rsplit(".", 1)[0]
        if not path.startswith("/Game/"):
            path = "/Game/" + path.lstrip("/")
        return path

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def set_blendspace_sample(self, blendspace_path, sample_index, animation_path, speed, timeout=30):
        """Set a sample in a BlendSpace: replace animation + speed at given index."""
        bs_path = self._resolve_asset_path(blendspace_path)
        anim_path = self._resolve_asset_path(animation_path)
        script = f"""
import unreal
bs = unreal.load_asset("{bs_path}")
if bs is None:
    raise RuntimeError("BlendSpace not found: {bs_path}")
samples = bs.get_editor_property("sample_interps")
if {sample_index} >= len(samples):
    raise RuntimeError("Sample index {sample_index} out of range ({{0}} samples)".format(len(samples)))
anim = unreal.load_asset("{anim_path}")
if anim is None:
    raise RuntimeError("Animation not found: {anim_path}")
sample = samples[{sample_index}]
sample.set_editor_property("animation", anim)
sv = sample.get_editor_property("sample_value")
if isinstance(sv, (list, tuple)) and len(sv) > 0:
    sv[0] = {speed}
    sample.set_editor_property("sample_value", sv)
else:
    sample.set_editor_property("sample_value", [{speed}])
unreal.EditorAssetLibrary.save_loaded_asset(bs)
print("OK: blendspace sample {sample_index} set to {anim_path} @ speed={speed}")
"""
        return self._run_unreal_python(script, timeout=timeout)

    def add_state_machine_transition(self, anim_bp_path, state_machine_name, from_state, to_state, rule, timeout=30):
        """Add a transition rule between two states in an AnimBP state machine.

        NOTE: State-machine graph editing in Unreal Python has limited API
        surface. This method tries several approaches:
        1. Direct AnimGraph traversal + AddTransition Node creation
        2. Unreal.EditorAnimUtils helper
        Falls back to reporting the spec so build_blueprint_from_spec can handle it.
        """
        abp_path = self._resolve_asset_path(anim_bp_path)
        script = f"""
import unreal
anim_bp = unreal.load_asset("{abp_path}")
if anim_bp is None:
    raise RuntimeError("AnimBP not found: {abp_path}")
anim_graph = anim_bp.get_animation_blueprint_graph()
if anim_graph is None:
    raise RuntimeError("No AnimGraph found on {abp_path}")
sm_nodes = [n for n in anim_graph.nodes if n.get_name() == "{state_machine_name}"]
if not sm_nodes:
    names = [n.get_name() for n in anim_graph.nodes]
    raise RuntimeError("State machine '{state_machine_name}' not found. Nodes: {{}}".format(names))
sm_node = sm_nodes[0]
# Attempt to add transition via editor utils
try:
    trans = unreal.AnimationStateMachineLibrary.add_transition(
        sm_node, "{from_state}", "{to_state}", "{rule}"
    )
    print("OK: transition added {{from}} -> {{to}}".format(from="{from_state}", to="{to_state}"))
except Exception as e:
    print("WARN: Direct transition API failed: {{}}".format(e))
    print("FALLBACK: Export graph spec and use build_blueprint_from_spec instead")
    print("  from_state={from_state}  to_state={to_state}  rule=\"{rule}\"")
unreal.EditorAssetLibrary.save_loaded_asset(anim_bp)
"""
        return self._run_unreal_python(script, timeout=timeout)

    def set_blend_weights(self, anim_bp_path, node_path, weights, timeout=30):
        """Set per-bone blend weights on a LayeredBoneBlend or similar node in an AnimBP."""
        abp_path = self._resolve_asset_path(anim_bp_path)
        weights_json = json.dumps(weights)
        script = f"""
import unreal
anim_bp = unreal.load_asset("{abp_path}")
if anim_bp is None:
    raise RuntimeError("AnimBP not found: {abp_path}")
anim_graph = anim_bp.get_animation_blueprint_graph()
targets = [n for n in anim_graph.nodes if n.get_name() == "{node_path}"]
if not targets:
    names = [n.get_name() for n in anim_graph.nodes]
    raise RuntimeError("Node '{node_path}' not found. Nodes: {{}}".format(names))
node = targets[0]
try:
    node.set_editor_property("blend_weights", {weights_json})
    print("OK: blend weights set on {{}}".format("{node_path}"))
except Exception as e:
    try:
        node.set_editor_property("blend_weights", [{weights_json}])
        print("OK: blend weights set (nested) on {{}}".format("{node_path}"))
    except Exception as e2:
        raise RuntimeError("Could not set blend weights: {{}} / {{}}".format(e, e2))
unreal.EditorAssetLibrary.save_loaded_asset(anim_bp)
"""
        return self._run_unreal_python(script, timeout=timeout)

    def retarget_animation_sequence(self, sequence_path, source_ik_rig, target_ik_rig, timeout=60):
        """Trigger IK retarget of an animation sequence using the specified IK rigs.

        Uses the UE5.8 IKRetargeter API via editor Python.
        Requires an existing IKRetargeter asset (path derived from convention
        or provided explicitly).
        """
        seq_path = self._resolve_asset_path(sequence_path)
        src_rig = self._resolve_asset_path(source_ik_rig)
        tgt_rig = self._resolve_asset_path(target_ik_rig)
        script = f"""
import unreal
seq = unreal.load_asset("{seq_path}")
if seq is None:
    raise RuntimeError("Sequence not found: {seq_path}")
src = unreal.load_asset("{src_rig}")
if src is None:
    raise RuntimeError("Source IK Rig not found: {src_rig}")
tgt = unreal.load_asset("{tgt_rig}")
if tgt is None:
    raise RuntimeError("Target IK Rig not found: {tgt_rig}")
# Construct retargeter path from convention
rtg_path = "{seq_path}".rsplit("/", 1)[0] + "/RTG_" + "{seq_path}".rsplit("/", 1)[-1]
retargeter = unreal.load_asset(rtg_path)
if retargeter is None:
    # Try creating via AssetTools
    try:
        asset_tools = unreal.AssetToolsHelpers.get_asset_tools()
        retargeter = asset_tools.create_asset(
            "RTG_" + "{seq_path}".rsplit("/", 1)[-1],
            "{seq_path}".rsplit("/", 1)[0],
            unreal.IKRetargeter,
            unreal.IKRetargetFactory()
        )
        print("Created new IKRetargeter at {{}}".format(rtg_path))
    except Exception as ce:
        raise RuntimeError(
            "No IKRetargeter found at {{}} and auto-creation failed: {{}}".format(rtg_path, ce)
        )
retargeter.set_editor_property("source_ik_rig", src)
retargeter.set_editor_property("target_ik_rig", tgt)
# Run retarget via editor chain
try:
    processor = unreal.IKRetargetProcessor()
    processor.set_retargeter(retargeter)
    result = processor.run_retarget(seq)
    unreal.EditorAssetLibrary.save_loaded_asset(result)
    print("OK: retargeted {{seq}} -> {{result}}".format(seq="{seq_path}", result=result.get_path_name()))
except Exception as re:
    print("WARN: Runtime retarget failed: {{}}".format(re))
    print("INFO: Retargeter configured with source/target rigs ready for manual run in editor.")
unreal.EditorAssetLibrary.save_loaded_asset(retargeter)
"""
        return self._run_unreal_python(script, timeout=timeout)

    def set_anim_blueprint_variable(self, anim_bp_path, var_name, value, timeout=30):
        """Set a default variable value on an Animation Blueprint."""
        abp_path = self._resolve_asset_path(anim_bp_path)
        if isinstance(value, str):
            value_repr = f'"{value}"'
        elif isinstance(value, bool):
            value_repr = "true" if value else "false"
        else:
            value_repr = str(value)
        script = f"""
import unreal
anim_bp = unreal.load_asset("{abp_path}")
if anim_bp is None:
    raise RuntimeError("AnimBP not found: {abp_path}")
bp_obj = unreal.load_object(name="{abp_path}_C", outer=anim_bp)
if bp_obj is None:
    bp_obj = anim_bp
try:
    prop = bp_obj.get_editor_property("{var_name}")
    print("Current {{var_name}} = {{}}".format(prop))
except Exception:
    print("WARN: Cannot read property {{var_name}} on AnimBP")
try:
    bp_obj.set_editor_property("{var_name}", {value_repr})
    print("OK: set {{var_name}} = {value_repr}")
except Exception as e:
    print("WARN: Could not set {{var_name}} directly: {{}}".format(e))
    print("HINT: Use blueprint_query:build_blueprint_from_spec to wire a Set node")
unreal.EditorAssetLibrary.save_loaded_asset(anim_bp)
"""
        return self._run_unreal_python(script, timeout=timeout)

    def apply_blendspace_preset(self, preset_path, timeout=30):
        """Load a blendspace preset JSON and apply all samples."""
        with open(preset_path, "r") as f:
            preset = json.load(f)
        bs_path = preset["blendspace_path"]
        results = []
        for sample in preset["samples"]:
            r = self.set_blendspace_sample(
                bs_path,
                sample["index"],
                sample["animation"],
                sample["speed"],
                timeout=timeout,
            )
            results.append({"sample": sample["index"], "result": r})
        return results

    def apply_anim_var_preset(self, preset_path, timeout=30):
        """Load an anim variable preset JSON and set all variables."""
        with open(preset_path, "r") as f:
            preset = json.load(f)
        abp_path = preset["asset_path"]
        results = []
        for var_name, var_info in preset["variables"].items():
            r = self.set_anim_blueprint_variable(
                abp_path, var_name, var_info["default"], timeout=timeout,
            )
            results.append({"variable": var_name, "result": r})
        return results


# ---------------------------------------------------------------------------
# CLI usage
# ---------------------------------------------------------------------------
CLI_HELP = """
T3DAnimBlueprintInjector - AnimBP automation library

Commands:
  set-blendspace-sample <path> <index> <anim_path> <speed>
  set-anim-var <abp_path> <var_name> <value>
  apply-blendspace-preset <preset_json_path>
  apply-var-preset <preset_json_path>
"""


def main_cli():
    import sys
    injector = T3DAnimBlueprintInjector()
    args = sys.argv[1:]
    if not args:
        print(CLI_HELP)
        return
    cmd = args[0]
    if cmd == "set-blendspace-sample" and len(args) >= 5:
        print(injector.set_blendspace_sample(args[1], int(args[2]), args[3], float(args[4])))
    elif cmd == "set-anim-var" and len(args) >= 4:
        val = args[3]
        try:
            val = json.loads(val)
        except json.JSONDecodeError:
            pass
        print(injector.set_anim_blueprint_variable(args[1], args[2], val))
    elif cmd == "apply-blendspace-preset" and len(args) >= 2:
        results = injector.apply_blendspace_preset(args[1])
        print(json.dumps(results, indent=2))
    elif cmd == "apply-var-preset" and len(args) >= 2:
        results = injector.apply_anim_var_preset(args[1])
        print(json.dumps(results, indent=2))
    else:
        print(f"Unknown command: {cmd}")
        print(CLI_HELP)


if __name__ == "__main__":
    main_cli()
