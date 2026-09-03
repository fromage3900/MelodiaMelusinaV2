#!/usr/bin/env python3
"""
NL->Blueprint Generator: Natural Language -> T3D Blueprint patch spec.

Describes what you want in English, and this tool:
1. Reads the current graph state via Monolith.
2. Sends description + context to a locally-installed LLM (deepseek-r1:14b
   or qwen2.5-coder:7b via Ollama; OpenRouter DeepSeek as a remote fallback).
3. The LLM generates a patch spec (nodes/connections/pin_defaults).
4. The spec is validated, then handed to `t3d_safe_wire.safe_wire()`, which
   enforces the full mandatory verification loop (export/fingerprint/
   validate/mutate/compile/assert/fingerprint/save/re-export) and writes the
   evidence manifest under `Saved/T3D/`.

This tool is a spec AUTHOR, not its own injector -- `t3d_safe_wire.py` is the
one place that verification loop is enforced, and this file must not
reimplement or bypass it.

Usage:
    python nl_to_blueprint.py \\
        --bp "/Game/.../BP_BattleController" \\
        --prompt "Wire RecordInputNow to SubmitRatedInput after the skill selection" \\
        --expected-fingerprint <hash>
    python nl_to_blueprint.py --bp "BP_BattleUI" --prompt "..." --dry-run
"""
from __future__ import annotations

import json
import argparse
import os
import re
import sys
import uuid
import urllib.error
import urllib.request
from pathlib import Path

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

from mcp_client import monolith  # noqa: E402
from t3d_safe_wire import find_duplicate_spec_ids, safe_wire  # noqa: E402

OLLAMA_URL = os.environ.get("OLLAMA_URL", "http://127.0.0.1:11434/api/generate")

# `ollama list` on this machine has deepseek-r1:14b and qwen2.5-coder:7b only
# (2026-08-13). qwen3:8b, the old default, is not installed and every run
# with the default model silently failed against a nonexistent model.
LOCAL_MODELS = {
    "deepseek-r1": "deepseek-r1:14b",
    "qwen-coder": "qwen2.5-coder:7b",
}
DEFAULT_LOCAL_MODEL = "deepseek-r1"

# Available node types for the patch spec (same vocabulary
# build_blueprint_from_spec / validate_nodes_t3d / inject_nodes_t3d accept).
NODE_TYPES = [
    "CallFunction", "VariableGet", "VariableSet", "CustomEvent",
    "Branch", "Sequence", "MacroInstance", "SpawnActorFromClass",
    "DynamicCast", "Self", "Return", "MakeStruct", "BreakStruct",
    "SwitchOnEnum", "SwitchOnInt", "SwitchOnString", "FormatText",
    "MakeArray", "Select", "ComponentBoundEvent", "AddDelegate",
    "RemoveDelegate", "ClearDelegate", "CallDelegate"
]

# Common function class paths
FUNCTION_CLASSES = {
    "MelodiaRhythmCombatSubsystem": "/Script/BS_GodFile.MelodiaRhythmCombatSubsystem",
    "MelodiaNarrativeSubsystem": "/Script/BS_GodFile.MelodiaNarrativeSubsystem",
    "MelodiaTokenWalletSubsystem": "/Script/MelodiaCore.MelodiaTokenWalletSubsystem",
    "MelodiaInputContextSubsystem": "/Script/BS_GodFile.MelodiaInputContextSubsystem",
    "MelodiaExternalJRPGBridgeSubsystem": "/Script/BS_GodFile.MelodiaExternalJRPGBridgeSubsystem",
    "MelodiaJRPGPresentationRhythmComponent": "/Script/BS_GodFile.MelodiaJRPGPresentationRhythmComponent",
    "MelodiaAudioReactivePresentationSubsystem": "/Script/BS_GodFile.MelodiaAudioReactivePresentationSubsystem",
    "MelodiaMusicClockSubsystem": "/Script/BS_GodFile.MelodiaMusicClockSubsystem",
    "GameplayStatics": "/Script/Engine.GameplayStatics",
    "KismetSystemLibrary": "/Script/Engine.KismetSystemLibrary",
    "WidgetBlueprintLibrary": "/Script/UMG.WidgetBlueprintLibrary",
    "WidgetLayoutLibrary": "/Script/UMG.WidgetLayoutLibrary",
}


def get_bp_graph(asset_path: str, graph_name: str = "EventGraph"):
    result = monolith("blueprint_query", {
        "action": "export_graph", "asset_path": asset_path, "graph_name": graph_name,
    })
    if isinstance(result, str):
        if result.startswith("ERROR:"):
            return None
        try:
            return json.loads(result)
        except json.JSONDecodeError:
            return result
    return result


def get_bp_variables(asset_path: str):
    result = monolith("blueprint_query", {
        "action": "get_variables", "asset_path": asset_path, "include_bind_widgets": True,
    })
    if isinstance(result, str):
        if result.startswith("ERROR:"):
            return None
        try:
            return json.loads(result)
        except json.JSONDecodeError:
            return result
    return result


def ask_local(prompt: str, system_prompt: str | None, model_key: str) -> str:
    """Ask a locally-installed Ollama model."""
    model = LOCAL_MODELS.get(model_key, LOCAL_MODELS[DEFAULT_LOCAL_MODEL])
    payload = {
        "model": model,
        "prompt": prompt,
        "stream": False,
        "options": {"temperature": 0.2, "num_predict": 4096},
    }
    if system_prompt:
        payload["system"] = system_prompt

    req = urllib.request.Request(
        OLLAMA_URL,
        data=json.dumps(payload).encode(),
        headers={"Content-Type": "application/json"},
    )
    try:
        with urllib.request.urlopen(req, timeout=120) as resp:
            data = json.loads(resp.read().decode())
        return data.get("response", "")
    except (urllib.error.URLError, OSError, json.JSONDecodeError) as e:
        return f"Error: {e}"


def ask_deepseek_remote(prompt: str, system_prompt: str | None = None) -> str:
    """Ask DeepSeek via OpenRouter (remote fallback when no local model fits)."""
    key = os.environ.get("OPENROUTER_API_KEY", "")
    if not key:
        return "Error: OPENROUTER_API_KEY is not set"
    payload = {
        "model": "deepseek/deepseek-v3",
        "messages": [
            {"role": "system", "content": system_prompt or "You are a UE 5.8 Blueprint expert."},
            {"role": "user", "content": prompt},
        ],
        "temperature": 0.2,
        "max_tokens": 4096,
    }
    req = urllib.request.Request(
        "https://openrouter.ai/api/v1/chat/completions",
        data=json.dumps(payload).encode(),
        headers={"Content-Type": "application/json", "Authorization": f"Bearer {key}"},
    )
    try:
        with urllib.request.urlopen(req, timeout=120) as resp:
            data = json.loads(resp.read().decode())
        return data["choices"][0]["message"]["content"]
    except (urllib.error.URLError, OSError, json.JSONDecodeError, KeyError, IndexError) as e:
        return f"Error: {e}"


def build_system_prompt(asset_path: str, graph_data, variables_data) -> str:
    graph_summary = "No graph data available"
    if isinstance(graph_data, dict):
        nodes = graph_data.get("nodes", [])
        graph_summary = f"Graph has {len(nodes)} nodes: " + ", ".join(
            f"{n.get('id', '?')}({n.get('type', '?')})" for n in nodes[:40]
        )

    return f"""You are a UE 5.8 Blueprint graph expert. Your task is to generate a JSON
patch spec for a T3D wiring pipeline that will validate and inject it in one
transaction.

TARGET: {asset_path}

AVAILABLE NODE TYPES (use type field):
{json.dumps(NODE_TYPES, indent=2)}

AVAILABLE FUNCTION CLASSES (use target_class for CallFunction nodes):
{json.dumps(FUNCTION_CLASSES, indent=2)}

CURRENT GRAPH:
{graph_summary}

VARIABLES AVAILABLE:
{json.dumps(variables_data, indent=2) if isinstance(variables_data, dict) else str(variables_data)[:2000]}

OUTPUT FORMAT:
You MUST output ONLY valid JSON matching this schema:
{{
    "nodes": [
        {{"id": "N_<unique_name>", "type": "CallFunction|VariableGet|VariableSet|CustomEvent|etc",
          "function_name": "...", "target_class": "...", "position": [x, y]}}
    ],
    "connections": [
        {{"source": "N_<id>", "source_pin": "then|ReturnValue|etc", "target": "N_<id>", "target_pin": "execute|self|etc"}}
    ],
    "pin_defaults": [
        {{"node_id": "N_<id>", "pin_name": "...", "value": "..."}}
    ]
}}

RULES:
1. Only output the JSON. No explanation, no markdown.
2. Use unique IDs starting with "N_". Every node id in "nodes" must be unique
   within this spec -- a duplicate id is rejected before injection.
3. Positions should be [x, y] with x incrementing by ~300 per node.
4. For CallFunction nodes, use "target_class" (NOT "function_class") with a
   path from the AVAILABLE FUNCTION CLASSES list.
5. For VariableGet/VariableSet nodes, use the variable names from the graph.
6. For DynamicCast nodes, use target_class for the class to cast to.
7. Connections use source and target node IDs with pin names:
   - Exec output pins are ALWAYS "then" (NOT "ReturnValue")
   - Exec input pins are ALWAYS "execute" (NOT "then")
   - Object/struct output pins are "ReturnValue"
   - Object/struct input pins are "self" for function targets, or specific pin names
   - Boolean outputs from branches are "Condition"
8. The graph may have existing nodes - ADD to them, don't replace.
"""


def extract_json(text: str) -> dict | None:
    """Extract JSON from LLM response (handles markdown fences and <think> blocks)."""
    text = re.sub(r"<think>[\s\S]*?</think>", "", text)

    json_match = re.search(r"```(?:json)?\s*([\s\S]*?)```", text)
    if json_match:
        text = json_match.group(1)

    json_match = re.search(r"\{[\s\S]*\}", text)
    if json_match:
        try:
            return json.loads(json_match.group(0))
        except json.JSONDecodeError:
            pass

    try:
        return json.loads(text)
    except json.JSONDecodeError:
        return None


def validate_spec_schema(spec: dict) -> list[str]:
    """Minimal structural check before anything touches Monolith.

    Not a substitute for validate_nodes_t3d (the live dry-run inside
    safe_wire) -- this only catches shapes the LLM is known to produce that
    would otherwise fail confusingly deep inside the pipeline: the
    function_class/target_class mix-up, missing ids, and node references
    from connections/pin_defaults that don't exist in this spec.
    """
    errors = []
    if not isinstance(spec, dict):
        return ["spec is not a JSON object"]

    nodes = spec.get("nodes", [])
    if not isinstance(nodes, list):
        errors.append("'nodes' must be a list")
        nodes = []

    node_ids: set[str] = set()
    for i, node in enumerate(nodes):
        if not isinstance(node, dict):
            errors.append(f"nodes[{i}] is not an object")
            continue
        if not node.get("id"):
            errors.append(f"nodes[{i}] is missing 'id'")
        if "function_class" in node:
            errors.append(
                f"nodes[{i}] ({node.get('id')}) uses 'function_class', which the injector "
                "does not read -- use 'target_class'"
            )
        if node.get("id"):
            node_ids.add(node["id"])

    dupes = find_duplicate_spec_ids(spec)
    if dupes:
        errors.append(f"duplicate node id(s) in spec: {dupes}")

    for i, conn in enumerate(spec.get("connections", [])):
        if not isinstance(conn, dict):
            errors.append(f"connections[{i}] is not an object")
            continue
        for key in ("source", "target"):
            ref = conn.get(key)
            if ref and ref not in node_ids:
                errors.append(f"connections[{i}].{key} references unknown node id '{ref}'")

    for i, pin in enumerate(spec.get("pin_defaults", [])):
        if not isinstance(pin, dict):
            errors.append(f"pin_defaults[{i}] is not an object")
            continue
        ref = pin.get("node_id")
        if ref and ref not in node_ids:
            errors.append(f"pin_defaults[{i}].node_id references unknown node id '{ref}'")

    return errors


def main() -> int:
    parser = argparse.ArgumentParser(description="NL->Blueprint patch spec generator")
    parser.add_argument("--bp", required=True, help="Blueprint asset path (e.g. /Game/.../BP_BattleController)")
    parser.add_argument("--graph", default="EventGraph", help="Graph name (default EventGraph)")
    parser.add_argument("--prompt", required=True, help="Natural language description of what to wire")
    parser.add_argument("--model", default=DEFAULT_LOCAL_MODEL,
                         choices=list(LOCAL_MODELS) + ["deepseek-remote"],
                         help="LLM to use (default: deepseek-r1, the installed local model)")
    parser.add_argument("--expected-fingerprint", required=True,
                         help="Required pre-edit fingerprint; forwarded to t3d_safe_wire")
    parser.add_argument("--dry-run", action="store_true",
                         help="Generate and validate the spec but do not inject it")
    args = parser.parse_args()

    print("=== NL->Blueprint Generator ===")
    print(f"Target: {args.bp}")
    print(f"Prompt: {args.prompt}")
    print(f"Model: {args.model}")

    print("\n[1/4] Reading current graph state...")
    graph_data = get_bp_graph(args.bp, args.graph)
    variables_data = get_bp_variables(args.bp)
    if graph_data is None:
        print("  WARNING: could not read graph state (editor unreachable or asset not found). "
              "Continuing with no context -- the LLM output will be lower quality and "
              "validation still runs before anything is injected.")

    print("\n[2/4] Building context and querying LLM...")
    system_prompt = build_system_prompt(args.bp, graph_data, variables_data)
    user_prompt = f"""Given the Blueprint at {args.bp}, generate a patch spec to:

{args.prompt}

Study the existing nodes carefully. Only add nodes that don't already exist.
For function calls, ALWAYS use a target_class from the provided list.
If you need a cast node, use type "DynamicCast" with target_class.
If a subsystem Get node already exists, reuse it -- don't create a duplicate.

Output ONLY the JSON spec."""

    if args.model == "deepseek-remote":
        response = ask_deepseek_remote(user_prompt, system_prompt)
    else:
        response = ask_local(user_prompt, system_prompt, args.model)

    print(f"  LLM response length: {len(response)} chars")
    if response.startswith("Error:"):
        print(f"  ERROR: {response}")
        return 1

    print("\n[3/4] Parsing and validating generated spec...")
    spec = extract_json(response)
    if not spec:
        print("  ERROR: Could not parse JSON from LLM response")
        print(f"  Raw response (first 500 chars): {response[:500]}")
        return 1

    schema_errors = validate_spec_schema(spec)
    if schema_errors:
        print("  ERROR: generated spec failed schema validation:")
        for e in schema_errors:
            print(f"    - {e}")
        return 1

    # The model proposes the graph delta; the transaction identity and pre-edit
    # revision belong to the caller, never to generated text. Populate the
    # request-owned contract before handing anything to safe_wire.
    generated_nodes = [node.get("id") for node in spec.get("nodes", []) if isinstance(node, dict) and node.get("id")]
    generated_connections = [conn for conn in spec.get("connections", []) if isinstance(conn, dict)]
    spec["request_id"] = f"nl-blueprint-{uuid.uuid4().hex}"
    spec["expected_before_fingerprint"] = args.expected_fingerprint
    spec["expected_postconditions"] = {
        "required_nodes": generated_nodes,
        "forbidden_nodes": [],
        "required_connections": generated_connections,
        "expected_delta": {
            "new_nodes": generated_nodes,
            "new_connections": generated_connections,
        },
        "compile_error_count": 0,
        "reexport_after_save": True,
    }
    spec["verification"] = {
        "compile_zero_errors": True,
        "assert_graph_match": True,
        "reexport_after_save": True,
    }

    nodes_count = len(spec.get("nodes", []))
    connections_count = len(spec.get("connections", []))
    print(f"  Generated: {nodes_count} nodes, {connections_count} connections (schema OK)")

    print("\n[4/4] Handing spec to t3d_safe_wire (export/fingerprint/validate"
          + ("" if args.dry_run else "/mutate/compile/assert/save") + ")...")
    ok, manifest, evidence_dir = safe_wire(
        args.bp, args.graph, spec, args.expected_fingerprint, dry_run=args.dry_run
    )

    print(f"\n=== {'DRY RUN OK' if (ok and args.dry_run) else ('COMMITTED' if ok else 'FAILED')} ===")
    print(f"Evidence: {evidence_dir}")
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
