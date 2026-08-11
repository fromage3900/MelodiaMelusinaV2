#!/usr/bin/env python3
"""
NL→Blueprint Generator: Natural Language → T3D Blueprint Injection.

Describes what you want in English, and this tool:
1. Reads the current graph state via Monolith
2. Sends description + context to an LLM (Qwen3:8b locally or DeepSeek via OpenRouter)
3. LLM generates a build_blueprint_from_spec JSON
4. Injects it into the Blueprint in ONE transaction via Monolith
5. Compiles and verifies

Usage:
    python nl_to_blueprint.py \\
        --bp "/Game/.../BP_BattleController" \\
        --prompt "Wire RecordInputNow to SubmitRatedInput after the skill selection"
    python nl_to_blueprint.py --bp "BP_BattleUI" --prompt "Swap MelodiaNoteHighway Image for WBP_MelodiaRhythmHighway"
"""

import json, sys, os, re, subprocess, urllib.request, urllib.parse
from pathlib import Path

MONOLITH_URL = "http://127.0.0.1:9316/mcp"
OLLAMA_URL = "http://127.0.0.1:11434/api/generate"

# Available node types for build_blueprint_from_spec
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

def monolith(action, args=None):
    """Call Monolith MCP tool."""
    body = {
        "jsonrpc": "2.0", "id": 1,
        "method": "tools/call",
        "params": {"name": action, "arguments": args or {}}
    }
    req = urllib.request.Request(
        MONOLITH_URL,
        data=json.dumps(body).encode(),
        headers={"Content-Type": "application/json"}
    )
    try:
        resp = urllib.request.urlopen(req, timeout=30)
        data = json.loads(resp.read().decode())
        content = data.get("result", {}).get("content", [{}])
        if content:
            text = content[0].get("text", "")
            try:
                return json.loads(text)
            except:
                return text
        return None
    except Exception as e:
        return {"error": str(e)}

def get_bp_graph(asset_path):
    """Get the current graph state of a Blueprint."""
    result = monolith("blueprint_query", {
        "action": "export_graph",
        "asset_path": asset_path
    })
    return result

def get_bp_variables(asset_path):
    """Get variables from a Blueprint."""
    result = monolith("blueprint_query", {
        "action": "get_variables",
        "asset_path": asset_path,
        "include_bind_widgets": True
    })
    return result

def get_bp_components(asset_path):
    """Get components from a Blueprint."""
    result = monolith("blueprint_query", {
        "action": "get_components",
        "asset_path": asset_path
    })
    return result

def ask_qwen(prompt, system_prompt=None):
    """Ask Qwen3:8b via Ollama."""
    payload = {
        "model": "qwen3:8b",
        "prompt": prompt,
        "stream": False,
        "options": {"temperature": 0.2, "num_predict": 4096}
    }
    if system_prompt:
        payload["system"] = system_prompt
    
    req = urllib.request.Request(
        OLLAMA_URL,
        data=json.dumps(payload).encode(),
        headers={"Content-Type": "application/json"}
    )
    try:
        resp = urllib.request.urlopen(req, timeout=60)
        data = json.loads(resp.read().decode())
        return data.get("response", "")
    except Exception as e:
        return f"Error: {e}"

def ask_deepseek(prompt, system_prompt=None):
    """Ask DeepSeek V4 via OpenRouter."""
    key = os.environ.get("OPENROUTER_API_KEY", "")
    if not key:
        print("WARNING: OPENROUTER_API_KEY is not set; DeepSeek requests will fail with auth errors.")
    payload = {
        "model": "deepseek/deepseek-v4",
        "messages": [
            {"role": "system", "content": system_prompt or "You are a UE 5.8 Blueprint expert."},
            {"role": "user", "content": prompt}
        ],
        "temperature": 0.2,
        "max_tokens": 4096
    }
    req = urllib.request.Request(
        "https://openrouter.ai/api/v1/chat/completions",
        data=json.dumps(payload).encode(),
        headers={
            "Content-Type": "application/json",
            "Authorization": f"Bearer {key}"
        }
    )
    try:
        resp = urllib.request.urlopen(req, timeout=120)
        data = json.loads(resp.read().decode())
        return data["choices"][0]["message"]["content"]
    except Exception as e:
        return f"Error: {e}"

def build_system_prompt(asset_path, graph_data, variables_data):
    """Build the system prompt with context about the Blueprint."""
    prompt = f"""You are a UE 5.8 Blueprint graph expert. Your task is to generate a JSON spec for Monolith's build_blueprint_from_spec tool.

TARGET: {asset_path}

AVAILABLE NODE TYPES (use type field):
{json.dumps(NODE_TYPES, indent=2)}

AVAILABLE FUNCTION CLASSES (use function_class for CallFunction nodes):
{json.dumps(FUNCTION_CLASSES, indent=2)}

CURRENT GRAPH SUMMARY:
The graph has been exported. Study the existing nodes and connections to understand what's already wired.

VARIABLES AVAILABLE:
{json.dumps(variables_data, indent=2) if isinstance(variables_data, dict) else str(variables_data)[:2000]}

OUTPUT FORMAT:
You MUST output ONLY valid JSON matching this schema:
{{
    "nodes": [
        {{"id": "N_<unique_name>", "type": "CallFunction|VariableGet|VariableSet|CustomEvent|etc", "function_name": "...", "function_class": "...", "position": [x, y]}}
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
2. Use unique IDs starting with "N_"
3. Positions should be [x, y] with x incrementing by ~300 per node
4. For CallFunction nodes, function_class must be one of the available FUNCTION_CLASSES
5. For VariableGet/VariableSet nodes, use the variable names from the graph
6. For DynamicCast nodes, use target_class for the class to cast to
7. Connections use source and target node IDs with pin names:
   - Exec output pins are ALWAYS "then" (NOT "ReturnValue")
   - Exec input pins are ALWAYS "execute" (NOT "then")
   - Object/struct output pins are "ReturnValue"
   - Object/struct input pins are "self" for function targets, or specific pin names
   - Boolean outputs from branches are "Condition"
8. The graph may have existing nodes - ADD to them, don't replace
"""
    return prompt

def inject_spec(asset_path, spec, graph_name="EventGraph"):
    """Inject the generated spec into the Blueprint."""
    params = {
        "asset_path": asset_path,
        "graph_name": graph_name,
        "auto_compile": True
    }
    
    if spec.get("nodes"):
        params["nodes"] = spec["nodes"]
    if spec.get("connections"):
        params["connections"] = spec["connections"]
    if spec.get("pin_defaults"):
        params["pin_defaults"] = spec["pin_defaults"]
    
    result = monolith("blueprint_query", {
        "action": "build_blueprint_from_spec",
        **params
    })
    
    return result

def verify_result(asset_path):
    """Verify the Blueprint compiles clean."""
    result = monolith("blueprint_query", {
        "action": "compile_blueprint",
        "asset_path": asset_path
    })
    return result

def extract_json(text):
    """Extract JSON from LLM response (handles markdown fences)."""
    # Try to find JSON between ``` fences
    json_match = re.search(r'```(?:json)?\s*([\s\S]*?)```', text)
    if json_match:
        text = json_match.group(1)
    
    # Try to find a JSON object
    json_match = re.search(r'\{[\s\S]*\}', text)
    if json_match:
        try:
            return json.loads(json_match.group(0))
        except:
            pass
    
    # Try parsing whole text
    try:
        return json.loads(text)
    except:
        return None


def main():
    import argparse
    parser = argparse.ArgumentParser(description="NL→Blueprint Generator")
    parser.add_argument("--bp", required=True, help="Blueprint asset path (e.g. /Game/.../BP_BattleController)")
    parser.add_argument("--prompt", required=True, help="Natural language description of what to wire")
    parser.add_argument("--model", default="qwen", choices=["qwen", "deepseek"], help="LLM to use")
    parser.add_argument("--dry-run", action="store_true", help="Print the generated spec without injecting")
    args = parser.parse_args()
    
    print(f"=== NL→Blueprint Generator ===")
    print(f"Target: {args.bp}")
    print(f"Prompt: {args.prompt}")
    print(f"Model: {args.model}")
    
    # Step 1: Read current graph state
    print("\n[1/4] Reading current graph state...")
    graph_data = get_bp_graph(args.bp)
    variables_data = get_bp_variables(args.bp)
    
    graph_summary = "No graph data available"
    if isinstance(graph_data, dict):
        nodes = graph_data.get("nodes", [])
        graph_summary = f"Graph has {len(nodes)} nodes"
    
    print(f"  {graph_summary}")
    
    # Step 2: Build system prompt with context
    print("\n[2/4] Building context and querying LLM...")
    system_prompt = build_system_prompt(args.bp, graph_data, variables_data)
    
    user_prompt = f"""Given the Blueprint at {args.bp}, generate a build_blueprint_from_spec JSON to:

{args.prompt}

Study the existing nodes carefully. Only add nodes that don't already exist.
For function calls, ALWAYS use a function_class from the provided list.
If you need a cast node, use type "DynamicCast" with target_class.
If a subsystem Get node already exists, reuse it — don't create a duplicate.

Output ONLY the JSON spec."""
    
    if args.model == "qwen":
        response = ask_qwen(user_prompt, system_prompt)
    else:
        response = ask_deepseek(user_prompt, system_prompt)
    
    print(f"  LLM response length: {len(response)} chars")
    
    # Step 3: Parse JSON from LLM response
    print("\n[3/4] Parsing generated spec...")
    spec = extract_json(response)
    
    if not spec:
        print("  ERROR: Could not parse JSON from LLM response")
        print(f"  Raw response (first 500 chars): {response[:500]}")
        return 1
    
    nodes_count = len(spec.get("nodes", []))
    connections_count = len(spec.get("connections", []))
    print(f"  Generated: {nodes_count} nodes, {connections_count} connections")
    
    if args.dry_run:
        print(f"\n[DRY RUN] Generated spec:")
        print(json.dumps(spec, indent=2))
        return 0
    
    # Step 4: Inject
    print("\n[4/4] Injecting into Blueprint...")
    result = inject_spec(args.bp, spec)
    
    if isinstance(result, dict):
        success = result.get("success", False)
        if success:
            summary = result.get("summary", {})
            print(f"  ✅ SUCCESS")
            print(f"  Nodes created: {summary.get('nodes_created', 0)}")
            print(f"  Connections made: {summary.get('connections_made', 0)}")
            errors = result.get("details", [])
            if errors:
                for e in errors:
                    print(f"  ⚠ {e.get('error', '')}")
        else:
            print(f"  ❌ FAILED")
            print(json.dumps(result, indent=2)[:1000])
    else:
        print(f"  Result: {str(result)[:500]}")
    
    # Step 5: Verify
    print("\nVerifying compile...")
    verify = verify_result(args.bp)
    if isinstance(verify, dict):
        status = verify.get("status", "?")
        errors = verify.get("error_count", 0)
        print(f"  Compile: {status}, errors: {errors}")
    
    print("\n=== DONE ===")
    return 0

if __name__ == "__main__":
    sys.exit(main())
