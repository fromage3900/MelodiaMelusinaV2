"""Ollama slice-content daemon - generates review-ready JSON game data for the
20-min vertical slice. Follows the project's loop conventions (STOP file + pid).

Scope (per AI_ORCHESTRATION_HANDOFFS_2026-07-17.md, HANDOFF 4 - nothing new invented):
  1. MelodySlime RNG variants  -> Imports/Data/EnemyVariants/   (mirrors FMelodiaEnemyDef)
  2. Skill charts              -> Imports/Data/Charts/          (mirrors FMelodiaChartNote)
  3. Room modifier pairs       -> Imports/Data/RoomMods/        (roguelike blessing/curse)

Never writes into Content/. Output is drafts for human + coordinator review.

Run:   python deploy/ollama_slice_content_daemon.py
Stop:  create deploy/OLLAMA_SLICE_STOP  (checked between generations)
Log:   deploy/ollama_slice_content.log
"""
from __future__ import annotations

import json
import random
import re
import time
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "Imports" / "Data"
STOP = ROOT / "deploy" / "OLLAMA_SLICE_STOP"
LOG = ROOT / "deploy" / "ollama_slice_content.log"
PID = ROOT / "deploy" / "OLLAMA_SLICE_LOOP.pid"
MODEL = "qwen2.5-coder:7b"
API = "http://127.0.0.1:11434/api/generate"

# Real project constants - DO NOT let the model invent these.
ELEMENTS = ["Forte", "Tide", "Gale", "Stone", "Radiant", "Umbral", "Arcane"]
# Baseline from the shipped MelodySlime family (BP_MelodySlime / demo enemy bands):
SLIME_BASE = {"max_hp": 300.0, "base_damage": 15.0, "speed": 80, "toughness": 60.0, "bpm": 128.0}
CAPS = {"EnemyVariants": 48, "Charts": 24, "RoomMods": 20}


def log(msg: str) -> None:
    line = f"[{time.strftime('%H:%M:%S')}] {msg}"
    print(line, flush=True)
    with LOG.open("a", encoding="utf-8") as f:
        f.write(line + "\n")


def ollama(prompt: str, retries: int = 3) -> str:
    body = json.dumps({"model": MODEL, "prompt": prompt, "stream": False,
                       "options": {"temperature": 0.95, "num_predict": 900}}).encode()
    for attempt in range(retries):
        try:
            req = urllib.request.Request(API, data=body, headers={"Content-Type": "application/json"})
            with urllib.request.urlopen(req, timeout=300) as r:
                return json.loads(r.read())["response"]
        except Exception as exc:  # noqa: BLE001 - daemon must survive transient ollama hiccups
            log(f"ollama error (attempt {attempt + 1}): {exc}")
            time.sleep(10)
    return ""


def extract_json(text: str) -> dict | None:
    m = re.search(r"\{.*\}", text, re.DOTALL)
    if not m:
        return None
    try:
        return json.loads(m.group(0))
    except json.JSONDecodeError:
        return None


def count_existing(folder: Path) -> int:
    return len(list(folder.glob("*.json"))) if folder.exists() else 0


def gen_enemy_variant(existing_ids: set[str]) -> None:
    element = random.choice(ELEMENTS)
    tier = random.choice(["Lesser", "Common", "Common", "Greater", "Crowned"])
    scale = {"Lesser": 0.6, "Common": 1.0, "Greater": 1.6, "Crowned": 2.4}[tier]
    prompt = f"""You are naming and flavoring an enemy variant for a whimsical dark-fairytale rhythm JRPG (tone: Infinity Nikki whimsy meets sheet-music magic). The base creature is the MelodySlime: a bouncing blob of living melody.
Produce ONE JSON object, nothing else, with EXACTLY these keys:
{{"id": "Slime<PascalCaseName>", "display_name": "...", "element": "{element}", "tier": "{tier}", "flavor": "one sentence, <=18 words", "color_hint": "#RRGGBB fitting the element", "intents": [{{"name": "...", "damage_mult": 0.8-1.5}}, {{"name": "...", "damage_mult": 0.8-1.5}}], "mesh_note": "one-phrase visual variation of the slime body"}}
Element {element} flavor guide: Forte=brassy/bold, Tide=watery, Gale=wind, Stone=earthen, Radiant=light, Umbral=shadow, Arcane=starry. Intent names are musical attack names (e.g. "Off-Key Splash"). No markdown."""
    data = extract_json(ollama(prompt))
    if not data or "id" not in data or data["id"] in existing_ids:
        log("enemy variant: rejected (bad json or dup id)")
        return
    if data.get("element") not in ELEMENTS:
        data["element"] = element
    # Deterministic stats: RNG banded off the real MelodySlime baseline, not model-invented.
    rng = random.Random(data["id"])
    data["stats"] = {
        "max_hp": round(SLIME_BASE["max_hp"] * scale * rng.uniform(0.85, 1.15), 0),
        "base_damage": round(SLIME_BASE["base_damage"] * scale * rng.uniform(0.85, 1.15), 1),
        "speed": int(SLIME_BASE["speed"] * rng.uniform(0.8, 1.25)),
        "toughness": round(SLIME_BASE["toughness"] * scale * rng.uniform(0.8, 1.2), 0),
        "bpm": random.choice([112.0, 120.0, 128.0, 128.0, 136.0, 144.0]),
    }
    data["base_creature"] = "BP_MelodySlime"
    data["schema"] = "FMelodiaEnemyDef-draft-v1"
    folder = OUT / "EnemyVariants"
    folder.mkdir(parents=True, exist_ok=True)
    (folder / f"{data['id']}.json").write_text(json.dumps(data, indent=2), encoding="utf-8")
    existing_ids.add(data["id"])
    log(f"enemy variant written: {data['id']} ({element} {tier})")


def gen_chart(existing_ids: set[str]) -> None:
    element = random.choice(ELEMENTS)
    difficulty = random.choice([1, 1, 2, 2, 3])
    note_count = {1: 8, 2: 12, 3: 16}[difficulty]
    prompt = f"""Design ONE rhythm-game tap chart for a {element}-element skill in 4/4 at 128 BPM, difficulty {difficulty}/3.
Output ONLY a JSON object: {{"id": "Chart_{element}_<ShortName>", "skill_name": "...", "element": "{element}", "difficulty": {difficulty}, "notes": [{{"lane": 0-3, "beat": float, "pitch": 60-84}}]}}.
Exactly {note_count} notes. Beats ascend strictly, start at 0.0, end before {note_count * 0.75:.1f}. Difficulty 1 = mostly on-beats (x.0/x.5); 2 = some off-beats (x.25/x.75); 3 = syncopation + one short 16th-note burst. Lanes should travel musically (runs, echoes), pitch should contour like a melody. No markdown."""
    data = extract_json(ollama(prompt))
    if not data or "id" not in data or data["id"] in existing_ids or not isinstance(data.get("notes"), list):
        log("chart: rejected")
        return
    notes = [n for n in data["notes"]
             if isinstance(n, dict) and 0 <= n.get("lane", -1) <= 3 and isinstance(n.get("beat"), (int, float))]
    notes.sort(key=lambda n: n["beat"])
    if len(notes) < 6:
        log("chart: rejected (too few valid notes)")
        return
    data["notes"] = notes
    data["schema"] = "FMelodiaChartNote-draft-v1"
    folder = OUT / "Charts"
    folder.mkdir(parents=True, exist_ok=True)
    (folder / f"{data['id']}.json").write_text(json.dumps(data, indent=2), encoding="utf-8")
    existing_ids.add(data["id"])
    log(f"chart written: {data['id']} (d{difficulty}, {len(notes)} notes)")


def gen_room_mod(existing_ids: set[str]) -> None:
    prompt = """Create ONE paired roguelike room modifier for a whimsical sheet-music dungeon (Infinity Nikki whimsy, dark-fairytale-sweet). Output ONLY JSON:
{"id": "Mod<PascalCase>", "blessing": {"name": "...", "effect_text": "player-facing, <=14 words, references an existing stat: HP, SP, ultimate gauge, toughness damage, AV/speed, or rhythm timing window"}, "curse": {"name": "...", "effect_text": "same constraints, a real tradeoff"}, "flavor": "one sentence tying both together"}
No markdown, no invented mechanics beyond those listed stats."""
    data = extract_json(ollama(prompt))
    if not data or "id" not in data or data["id"] in existing_ids:
        log("room mod: rejected")
        return
    data["schema"] = "RoomModifier-draft-v1"
    folder = OUT / "RoomMods"
    folder.mkdir(parents=True, exist_ok=True)
    (folder / f"{data['id']}.json").write_text(json.dumps(data, indent=2), encoding="utf-8")
    existing_ids.add(data["id"])
    log(f"room mod written: {data['id']}")


def main() -> None:
    import os
    PID.write_text(str(os.getpid()), encoding="utf-8")
    log(f"daemon start (model={MODEL}, caps={CAPS})")
    ids = {p.stem for folder in ("EnemyVariants", "Charts", "RoomMods") for p in (OUT / folder).glob("*.json")}
    while not STOP.exists():
        counts = {k: count_existing(OUT / k) for k in CAPS}
        if all(counts[k] >= CAPS[k] for k in CAPS):
            log(f"all caps reached {counts} - daemon done")
            break
        # Weighted toward enemies (the slice-gating content), then charts, then mods.
        pool = (["enemy"] * 3 if counts["EnemyVariants"] < CAPS["EnemyVariants"] else []) \
             + (["chart"] * 2 if counts["Charts"] < CAPS["Charts"] else []) \
             + (["mod"] if counts["RoomMods"] < CAPS["RoomMods"] else [])
        kind = random.choice(pool)
        try:
            {"enemy": gen_enemy_variant, "chart": gen_chart, "mod": gen_room_mod}[kind](ids)
        except Exception as exc:  # noqa: BLE001
            log(f"generation error ({kind}): {exc}")
        time.sleep(4)
    log("daemon exit")
    PID.unlink(missing_ok=True)


if __name__ == "__main__":
    main()
