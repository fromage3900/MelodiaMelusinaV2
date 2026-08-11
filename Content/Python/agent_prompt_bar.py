"""UE Agent Prompt Bar - Natural language input for agent delegation.

Provides a smart prompt interface in Unreal Editor that:
- Accepts natural language commands like "Make this wall more gothic"
- Routes to appropriate agent via bridge
- Shows responses in editor

Candidate Owner Agent: World Integration Agent (WIA)
"""
import json
from datetime import datetime
from pathlib import Path

# Handle both UE and standalone contexts
try:
    import unreal
except ImportError:
    unreal = None

AGENT_MEMORY_DIR = Path(__file__).resolve().parent.parent / "Saved" / "AgentMemory"


def parse_natural_language(prompt: str) -> dict:
    """Parse natural language into intent/action/payload."""
    prompt_lower = prompt.lower()
    
    # Geometry patterns
    if any(kw in prompt_lower for kw in ["wall", "arch", "building", "structure", "mesh", "geometry", "zen", "gothic", "cathedral"]):
        if "list" in prompt_lower or "show" in prompt_lower:
            return {"intent": "geometry", "action": "list_genomes", "payload": {}}
        if "spawn" in prompt_lower or "create" in prompt_lower:
            # Extract genome type
            genome_map = {
                "zen": "ZEN_SHRINE_AXIS",
                "gothic": "GOTHIC_CATHEDRAL",
                "baroque": "BAROQUE_SPAWN",
            }
            for key, genome in genome_map.items():
                if key in prompt_lower:
                    return {"intent": "geometry", "action": "spawn_graph", "payload": {"genome_id": genome}}
        if "random" in prompt_lower or "mutate" in prompt_lower:
            return {"intent": "geometry", "action": "randomize_dna", "payload": {}}
        return {"intent": "geometry", "action": "apply_genome", "payload": {"genome_id": "ZEN_SHRINE_AXIS"}}
    
    # Material patterns
    if any(kw in prompt_lower for kw in ["material", "shader", "texture", "toon", "substrate"]):
        if "build" in prompt_lower or "create" in prompt_lower:
            return {"intent": "material", "action": "build_universal", "payload": {}}
        if "list" in prompt_lower:
            return {"intent": "material", "action": "list_masters", "payload": {}}
        return {"intent": "material", "action": "apply_toon_preset", "payload": {}}
    
    # Placement/PCG patterns
    if any(kw in prompt_lower for kw in ["spawn", "place", "scatter", "grass", "tree", "flower", "pcg", "sakura", "zen shrine"]):
        if "sakura" in prompt_lower:
            return {"intent": "placement", "action": "build_sakura", "payload": {}}
        if "zen" in prompt_lower:
            return {"intent": "placement", "action": "build_zen", "payload": {}}
        if "status" in prompt_lower:
            return {"intent": "placement", "action": "status", "payload": {}}
        return {"intent": "placement", "action": "build_universal", "payload": {}}
    
    # Blessing patterns
    if any(kw in prompt_lower for kw in ["blessing", "curse", "evolution", "meta", "upgrade"]):
        element_focus = None
        for el in ["forte", "tide", "gale", "stone", "radiant", "umbral", "arcane"]:
            if el in prompt_lower:
                element_focus = el.capitalize()
                break
        
        target_count = 5
        import re
        match = re.search(r"(\d+)", prompt_lower)
        if match:
            target_count = int(match.group(1))
        
        return {"intent": "blessing", "action": "evolve", "payload": {"target_count": target_count, "element_focus": element_focus}}
    
    # Audit patterns
    if any(kw in prompt_lower for kw in ["audit", "health", "verify", "check", "status"]):
        return {"intent": "audit", "action": "run_health", "payload": {}}
    
    # Default: try to understand
    return {"intent": "integration", "action": "sync_blender", "payload": {}}


def queue_agent_request(intent: str, action: str, payload: dict) -> dict:
    """Queue a request for the agent bridge to process."""
    AGENT_MEMORY_DIR.mkdir(parents=True, exist_ok=True)
    
    # Get timestamp - works in both UE and standalone
    if unreal and hasattr(unreal, 'StringLibrary'):
        timestamp = unreal.StringLibrary.get_current_date()
    else:
        timestamp = datetime.now().isoformat()
    
    request = {
        "timestamp": timestamp,
        "intent": intent,
        "action": action,
        "payload": payload,
    }
    
    queue_file = AGENT_MEMORY_DIR / "prompt_queue.json"
    queue = []
    if queue_file.exists():
        try:
            queue = json.loads(queue_file.read_text())
        except Exception:
            pass
    
    queue.append(request)
    queue_file.write_text(json.dumps(queue, indent=2))
    
    return {"status": "queued", "request": request}


def process_prompt_bar(prompt: str) -> None:
    """Main entry point - parse and queue a natural language prompt."""
    parsed = parse_natural_language(prompt)
    
    # Log to editor
    unreal.log("[PromptBar] Processing: " + prompt)
    unreal.log(f"[PromptBar] → Intent: {parsed['intent']}, Action: {parsed['action']}")
    
    # Queue for bridge processing
    result = queue_agent_request(parsed["intent"], parsed["action"], parsed["payload"])
    unreal.log(f"[PromptBar] Status: {result['status']}")


def spawn_prompt_bar_widget() -> None:
    """Register prompt bar in UE editor (would need Slate implementation for full UI)."""
    unreal.log("[PromptBar] Natural Language Agent Interface Ready")
    unreal.log("[PromptBar] Examples:")
    unreal.log("  - 'Spawn zen shrine geometry'")
    unreal.log("  - 'Build sakura PCG scattered'")
    unreal.log("  - 'Generate 5 forte blessings'")
    unreal.log("  - 'Check agent status'")


# For testing outside UE
if __name__ == "__main__":
    test_prompts = [
        "Spawn zen shrine geometry",
        "Generate 5 forte blessings",
        "Check agent status",
        "Build sakura PCG scattered",
    ]
    
    for prompt in test_prompts:
        result = parse_natural_language(prompt)
        print("'{}' -> {}".format(prompt, result))
