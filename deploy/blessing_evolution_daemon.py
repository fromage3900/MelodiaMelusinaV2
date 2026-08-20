#!/usr/bin/env python
"""Blessing Evolution Daemon - Processes blessing evolution requests via Ollama.

Reads from Saved/AgentMemory/blessing_evolution_queue.json and generates
new blessing/curse pairs based on existing patterns in roguelike.py.

Usage:
    python blessing_evolution_daemon.py [--once]  # Process once, or continuously
"""
from __future__ import annotations

import json
import sys
import time
import subprocess
from pathlib import Path
from datetime import datetime
from typing import Optional

PROJECT_ROOT = Path(__file__).resolve().parent.parent
AGENT_MEMORY_DIR = PROJECT_ROOT / "Saved" / "AgentMemory"
BLESSINGS_FILE = PROJECT_ROOT / "Content" / "Python" / "gmm" / "game" / "roguelike.py"
ROOM_MODS_FILE = PROJECT_ROOT / "Content" / "Melodia" / "DataStuctures" / "DT_MelodySlime_RoomMods.json"
EVOLUTION_QUEUE = AGENT_MEMORY_DIR / "blessing_evolution_queue.json"
EVOLUTION_LOG = AGENT_MEMORY_DIR / "blessing_evolution_log.json"

# OpenAI configuration (cloud API)
OPENAI_API_KEY = None  # Will use OPENAI_API_KEY env var
DEFAULT_MODEL = "gpt-4"  # Cloud model
# Fallback Ollama config (only used if OpenAI unavailable)
OLLAMA_HOST = "http://127.0.0.1:11434"
OLLAMA_MODEL = "qwen2.5-coder:7b"

# Element types for blessing focus
ELEMENTS = ["Forte", "Tide", "Gale", "Stone", "Radiant", "Umbral", "Arcane"]

# Effect types from the game system
EFFECT_TYPES = ["starting_mana", "max_sp", "element_unlock", "passive", "perfect_window_bonus", "combo_persistence"]


def load_existing_patterns() -> dict:
    """Load existing blessing patterns to maintain consistency."""
    patterns = {
        "effect_types_used": set(),
        "elements_mentioned": [],
        "typical_values": {"token_cost": 50},
    }
    
    # Parse roguelike.py BLESSINGS dict
    if BLESSINGS_FILE.exists():
        content = BLESSINGS_FILE.read_text()
        # Extract effect types used
        for et in EFFECT_TYPES:
            if et in content:
                patterns["effect_types_used"].add(et)
        
        # Extract elements
        for el in ELEMENTS:
            if el in content:
                patterns["elements_mentioned"].append(el)
    
    return patterns


def generate_blessing_prompt(target_count: int, element_focus: str | None) -> str:
    """Create prompt for Ollama to generate new blessings."""
    patterns = load_existing_patterns()
    
    element_hint = f" focused on {element_focus} element" if element_focus else ""
    
    prompt = f"""Generate {target_count} new roguelike blessings for Melodia game{element_hint}.

Each blessing must be a JSON object with these fields:
- blessing_id: "RoomMod_<UniqueName>" (camel case, no spaces)
- display_name: "Pretty Name"
- description: "Mechanical effect description (like existing blessings)"
- token_cost: 50 (consistent with other blessings)
- effect_type: one of {EFFECT_TYPES}
- effect_value: number or 0.0
- effect_str: element name or ""
- curse: "Curse Name"
- curse_effect: "What the curse does"

Follow these patterns from existing blessings:
- Descriptions start with mechanical effects like "HP +10%" or "Rhythm timing window +20%"
- Curses are thematically opposite (discord, silence, weakness)
- Flavor text is poetic but optional

Return ONLY a JSON array of blessing objects, no extra text.

Example format:
[
  {{
    "blessing_id": "RoomMod_NewHarmony",
    "display_name": "New Harmony",
    "description": "HP +15% during boss fights",
    "token_cost": 50,
    "effect_type": "starting_mana",
    "effect_value": 15.0,
    "effect_str": "",
    "curse": "Discordant Weakness",
    "curse_effect": "HP -5% per missed note"
  }}
]
"""
    return prompt


def call_openai(prompt: str, model: str = DEFAULT_MODEL) -> dict:
    """Call OpenAI API to generate content."""
    import os
    api_key = os.environ.get("OPENAI_API_KEY", OPENAI_API_KEY)
    if not api_key:
        return {"status": "error", "message": "OPENAI_API_KEY not set"}
    
    try:
        import requests
        response = requests.post(
            "https://api.openai.com/v1/chat/completions",
            headers={
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json",
            },
            json={
                "model": model,
                "messages": [{"role": "user", "content": prompt}],
                "max_tokens": 1000,
            },
            timeout=60,
        )
        if response.status_code == 200:
            data = response.json()
            content = data.get("choices", [{}])[0].get("message", {}).get("content", "")
            return {"status": "success", "response": content}
        return {"status": "error", "message": f"HTTP {response.status_code}: {response.text}"}
    except Exception as e:
        return {"status": "error", "message": str(e)}


def call_ollama_fallback(prompt: str, model: str = OLLAMA_MODEL) -> dict:
    """Call Ollama API as fallback if OpenAI unavailable."""
    try:
        import requests
        response = requests.post(
            f"{OLLAMA_HOST}/api/generate",
            json={
                "model": model,
                "prompt": prompt,
                "stream": False,
            },
            timeout=60,
        )
        if response.status_code == 200:
            data = response.json()
            return {"status": "success", "response": data.get("response", "")}
        return {"status": "error", "message": f"HTTP {response.status_code}"}
    except Exception as e:
        # Fallback to subprocess if requests not available
        try:
            result = subprocess.run(
                ["ollama", "run", model],
                input=prompt,
                capture_output=True,
                text=True,
                timeout=120,
            )
            if result.returncode == 0:
                return {"status": "success", "response": result.stdout}
            return {"status": "error", "message": result.stderr}
        except Exception as e2:
            return {"status": "error", "message": str(e2)}


def call_ai(prompt: str, model: str = None) -> dict:
    """Call AI - prefers OpenAI (cloud), falls back to Ollama (local)."""
    if model is None:
        model = DEFAULT_MODEL
    
    # Try OpenAI first (cloud)
    openai_result = call_openai(prompt, model)
    if openai_result.get("status") == "success":
        return {"status": "success", "source": "openai", "response": openai_result.get("response")}
    
    # Log that we're falling back
    print(f"[BlessingEvolution] OpenAI failed ({openai_result.get('message')}), falling back to Ollama")
    
    # Fallback to Ollama
    ollama_result = call_ollama_fallback(prompt, model)
    if ollama_result.get("status") == "success":
        return {"status": "success", "source": "ollama", "response": ollama_result.get("response")}
    
    return {"status": "error", "message": f"Both OpenAI and Ollama failed. OpenAI: {openai_result.get('message')}, Ollama: {ollama_result.get('message')}"}


def process_evolution_request(request: dict) -> dict:
    """Process a single evolution request."""
    target_count = request.get("target_count", 5)
    element_focus = request.get("element_focus")
    
    prompt = generate_blessing_prompt(target_count, element_focus)
    ai_result = call_ai(prompt)
    
    if ai_result.get("status") != "success":
        return {"status": "error", "message": ai_result.get("message", "AI call failed")}
    
    # Parse the generated blessings
    try:
        blessings = json.loads(ai_result.get("response", "[]"))
    except json.JSONDecodeError:
        # Try to extract JSON from response
        response_text = ai_result.get("response", "")
        # Find JSON array in response
        start = response_text.find("[")
        end = response_text.rfind("]") + 1
        if start >= 0 and end > start:
            blessings = json.loads(response_text[start:end])
        else:
            return {"status": "error", "message": "Could not parse blessing JSON from response"}
    
    # Log the evolution
    evolution_entry = {
        "timestamp": datetime.now().isoformat(),
        "request": request,
        "generated_count": len(blessings),
        "blessings": blessings,
    }
    
    log = []
    if EVOLUTION_LOG.exists():
        log = json.loads(EVOLUTION_LOG.read_text())
    log.append(evolution_entry)
    EVOLUTION_LOG.write_text(json.dumps(log[-50:], indent=2))  # Keep last 50
    
    return {
        "status": "success",
        "generated_count": len(blessings),
        "blessings": blessings,
    }


def main(once: bool = False):
    """Main daemon loop."""
    AGENT_MEMORY_DIR.mkdir(parents=True, exist_ok=True)
    
    print(f"[BlessingEvolution] Daemon starting... checking {EVOLUTION_QUEUE}")
    
    while True:
        try:
            if EVOLUTION_QUEUE.exists():
                queue = json.loads(EVOLUTION_QUEUE.read_text())
                
                if queue:
                    # Process first request
                    request = queue.pop(0)
                    print(f"[BlessingEvolution] Processing request: {request}")
                    
                    result = process_evolution_request(request)
                    print(f"[BlessingEvolution] Result: {result.get('status')}")
                    
                    # Save remaining queue
                    if queue:
                        EVOLUTION_QUEUE.write_text(json.dumps(queue, indent=2))
                    else:
                        EVOLUTION_QUEUE.unlink()  # Remove empty queue
                else:
                    EVOLUTION_QUEUE.unlink() if EVOLUTION_QUEUE.exists() else None
            else:
                print(f"[BlessingEvolution] No queue file, sleeping...")
        
        except Exception as e:
            print(f"[BlessingEvolution] Error: {e}")
        
        if once:
            break
        
        time.sleep(10)  # Check every 10 seconds


if __name__ == "__main__":
    once_mode = "--once" in sys.argv
    main(once=once_mode)
