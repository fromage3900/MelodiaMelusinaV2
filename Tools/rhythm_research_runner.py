"""
Rhythm game research runner - queries local Ollama (Qwen) in a loop
and logs structured findings for overnight research sessions.
"""

import argparse
import json
import os
import time
from datetime import datetime
from pathlib import Path

import requests

PROMPTS = [
    "What are the best rhythm game accuracy scoring models? Compare timing windows, linear vs exponential scaling.",
    "How do rhythm games handle token/resource economies tied to note accuracy? Examples from Crypt of the NecroDancer, Hi-Fi Rush, Metal Hellsinger.",
    "Design patterns for grief/emotional modifiers in rhythm combat: how should grief affect gameplay mechanically?",
    "How should mana drain debuffs work in a rhythm RPG? Timing, counterplay, visual feedback.",
    "Best UE5 UMG patterns for real-time rhythm HUD: combo counters, resource bars, hit feedback animations.",
    "How do companion skill systems work in rhythm games? Persona, Kingdom Hearts, examples of skill chains.",
    "Token wallet economy design: how to balance generation rate vs consumption rate for 4 resource types.",
    "Scalar skill tiers in RPGs: how to make tier upgrades feel meaningful without breaking balance.",
    "Dungeon encounter design for rhythm RPGs: pacing, difficulty curves, grief hooks as narrative beats.",
    "What makes rhythm game combat feel satisfying? Input latency, visual/audio feedback, reward loops.",
]

OLLAMA_URL = "http://localhost:11434/api/chat"
SAVE_DIR = Path(__file__).resolve().parent.parent / "Saved" / "RhythmResearch"


def pick_model(override: str | None) -> str:
    if override:
        return override
    for model in ("qwen2.5-coder:7b", "qwen2.5-coder:14b"):
        try:
            r = requests.get("http://localhost:11434/api/tags", timeout=5)
            names = [m["name"] for m in r.json().get("models", [])]
            if model in names:
                return model
        except requests.RequestException:
            break
    return "qwen2.5-coder:7b"


def query_ollama(model: str, prompt: str, temperature: float, max_tokens: int = 600) -> str:
    payload = {
        "model": model,
        "messages": [
            {"role": "system", "content": "You are a game design researcher specializing in rhythm games and RPG systems."},
            {"role": "user", "content": prompt},
        ],
        "options": {"temperature": temperature, "num_predict": max_tokens},
        "stream": False,
    }
    try:
        r = requests.post(OLLAMA_URL, json=payload, timeout=300)
        r.raise_for_status()
        return r.json()["message"]["content"]
    except Exception as e:
        return f"[ERROR] {e}"


def run_iteration(model: str, temperature: float, iteration: int, md_file: Path, pairs: list):
    with open(md_file, "a", encoding="utf-8") as f:
        f.write(f"\n## Iteration {iteration} - temp={temperature:.2f}, model={model}\n\n")

    for i, prompt in enumerate(PROMPTS, 1):
        ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        print(f"  [{ts}] Prompt {i}/{len(PROMPTS)}...")
        response = query_ollama(model, prompt, temperature)
        with open(md_file, "a", encoding="utf-8") as f:
            f.write(f"### Prompt {i} ({ts})\n\n")
            f.write(f"**Q:** {prompt}\n\n")
            f.write(f"**A:** {response}\n\n---\n\n")
        pairs.append({"iteration": iteration, "prompt_index": i, "prompt": prompt, "response": response, "temperature": temperature, "timestamp": ts})


def main():
    parser = argparse.ArgumentParser(description="Rhythm game research runner")
    parser.add_argument("--iterations", type=int, default=1)
    parser.add_argument("--delay", type=int, default=60, help="Seconds between iterations")
    parser.add_argument("--model", type=str, default=None)
    args = parser.parse_args()

    SAVE_DIR.mkdir(parents=True, exist_ok=True)
    date_str = datetime.now().strftime("%Y-%m-%d")
    md_file = SAVE_DIR / f"rhythm_research_{date_str}.md"
    json_file = SAVE_DIR / f"rhythm_research_summary_{date_str}.json"

    model = pick_model(args.model)
    print(f"Model: {model} | Iterations: {args.iterations} | Delay: {args.delay}s")

    with open(md_file, "a", encoding="utf-8") as f:
        f.write(f"# Rhythm Game Research - {date_str}\n\n")

    all_pairs: list[dict] = []

    for it in range(1, args.iterations + 1):
        temp = min(0.7 + 0.05 * (it - 1), 0.95)
        print(f"\n=== Iteration {it}/{args.iterations} (temp={temp:.2f}) ===")
        run_iteration(model, temp, it, md_file, all_pairs)
        with open(json_file, "w", encoding="utf-8") as f:
            json.dump(all_pairs, f, indent=2, ensure_ascii=False)
        if it < args.iterations:
            print(f"Sleeping {args.delay}s before next iteration...")
            time.sleep(args.delay)

    print(f"\nDone. Output:\n  MD:   {md_file}\n  JSON: {json_file}")


if __name__ == "__main__":
    main()
