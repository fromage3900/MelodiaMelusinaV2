"""VN dialogue batch daemon. Output: Imports/Data/Dialogue/*.md
Stop: deploy/OLLAMA_DIALOGUE_STOP or deploy/STOP_ALL  ·  Cap: 30 files.
Beats: Sir Melodious dungeon entry/exit/defeat-consolation, bed-save whispers, boss intro barks.
"""
from __future__ import annotations
import json, random, re, time, urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "Imports" / "Data" / "Dialogue"
STOPS = [ROOT / "deploy" / "OLLAMA_DIALOGUE_STOP", ROOT / "deploy" / "STOP_ALL"]
LOG = ROOT / "deploy" / "ollama_dialogue.log"
MODEL, API, CAP = "llama3.1:8b", "http://127.0.0.1:11434/api/generate", 30
BEATS = [
    ("SirEntry", "Sir Melodious sends Melusina into the dungeon — proud, worried, a little theatrical"),
    ("SirExitVictory", "Sir Melodious greets her after a victorious run — relieved warmth, gentle teasing"),
    ("SirDefeatConsole", "Sir Melodious consoles her after a defeat — tender, no blame, quiet resolve"),
    ("BedWhisper", "the bed's save-moment whisper — lullaby-like, second person, cozy-magical"),
    ("BossBark", "a boss enemy's intro bark — melodic menace, dark-fairytale, two lines max"),
]

def log(m):
    line = f"[{time.strftime('%H:%M:%S')}] {m}"
    print(line, flush=True); LOG.open("a", encoding="utf-8").write(line + "\n")

def main():
    OUT.mkdir(parents=True, exist_ok=True)
    n = len(list(OUT.glob("*.md")))
    log(f"start (cap {CAP}, have {n})")
    i = n
    while not any(s.exists() for s in STOPS) and i < CAP:
        key, desc = random.choice(BEATS)
        prompt = f"""Write ONE dialogue beat for a dark-fairytale-sweet rhythm JRPG (tone: gentle melancholy + whimsy, sheet-music magic vocabulary — melodies, rests, crescendos as metaphors). Beat: {desc}. Max 6 short lines, speaker-labeled (SIR MELODIOUS: / MELUSINA: / VOICE: as fits). No stage directions beyond one bracketed mood note. No markdown headers."""
        body = json.dumps({"model": MODEL, "prompt": prompt, "stream": False,
                           "options": {"temperature": 1.05, "num_predict": 400}}).encode()
        try:
            req = urllib.request.Request(API, data=body, headers={"Content-Type": "application/json"})
            with urllib.request.urlopen(req, timeout=300) as r:
                text = json.loads(r.read())["response"].strip()
        except Exception as e:
            log(f"ollama error: {e}"); time.sleep(10); continue
        if len(text) < 40:
            log("rejected (too short)"); continue
        i += 1
        fname = f"{key}_{i:03d}.md"
        (OUT / fname).write_text(f"# {key} (draft {i})\n\n{text}\n", encoding="utf-8")
        log(f"written: {fname}")
        time.sleep(4)
    log("exit")

if __name__ == "__main__":
    main()
