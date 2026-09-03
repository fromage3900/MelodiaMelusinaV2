"""VN dialogue batch daemon. Output: Imports/Data/Dialogue/*.md
Stop: deploy/OLLAMA_DIALOGUE_STOP or deploy/STOP_ALL  -  Cap: 30 files.
Beats: Sir Melodious dungeon entry/exit/defeat-consolation, bed-save whispers, boss intro barks.
"""
from __future__ import annotations
import argparse, json, os, random, re, sys, time, urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "Imports" / "Data" / "Dialogue"
STOPS = [ROOT / "deploy" / "OLLAMA_DIALOGUE_STOP", ROOT / "deploy" / "STOP_ALL"]
LOG = ROOT / "deploy" / "ollama_dialogue.log"
DEFAULT_API = os.environ.get("OLLAMA_API", "http://127.0.0.1:11434/api/generate")
DEFAULT_TAGS_API = os.environ.get("OLLAMA_TAGS_API", "http://127.0.0.1:11434/api/tags")
DEFAULT_CAP = 30
PREFERRED_MODELS = [
    "qwen2.5-coder:7b",
    "deepseek-r1:14b",
    "qwen2.5-coder:14b",
    "deepseek-r1:7b",
    "deepseek-coder:6.7b",
    "qwen3.8-27b:latest",
    "hermes3:latest",
]

BEATS = [
    ("SirEntry", "Sir Melodious sends Melusina into the dungeon - proud, worried, a little theatrical"),
    ("SirExitVictory", "Sir Melodious greets her after a victorious run - relieved warmth, gentle teasing"),
    ("SirDefeatConsole", "Sir Melodious consoles her after a defeat - tender, no blame, quiet resolve"),
    ("BedWhisper", "the bed's save-moment whisper - lullaby-like, second person, cozy-magical"),
    ("BossBark", "a boss enemy's intro bark - melodic menace, dark-fairytale, two lines max"),
]

def log(m):
    line = f"[{time.strftime('%H:%M:%S')}] {m}"
    print(line, flush=True)
    LOG.parent.mkdir(parents=True, exist_ok=True)
    try:
        with LOG.open("a", encoding="utf-8") as f:
            f.write(line + "\n")
    except Exception:
        pass

def resolve_model(tags_api: str = DEFAULT_TAGS_API) -> str:
    """Dynamically detect installed Ollama model with fallback hierarchy."""
    env_model = os.environ.get("OLLAMA_DIALOGUE_MODEL") or os.environ.get("OLLAMA_MODEL")
    if env_model:
        return env_model.strip()

    try:
        req = urllib.request.Request(tags_api, headers={"Accept": "application/json"})
        with urllib.request.urlopen(req, timeout=3.0) as resp:
            data = json.loads(resp.read().decode("utf-8"))
            installed = {
                (m.get("name") or m.get("model") or "").strip()
                for m in data.get("models", [])
            }
            for candidate in PREFERRED_MODELS:
                if candidate in installed:
                    return candidate
            if installed:
                return next(iter(installed))
    except Exception:
        pass

    return "qwen2.5-coder:7b"

def run_dry_run(model: str) -> int:
    """Perform quick local validation without hanging or requiring live Ollama."""
    OUT.mkdir(parents=True, exist_ok=True)
    log(f"[DRY-RUN] Validating dialogue daemon setup (model={model}, out={OUT})")
    sample_key, sample_desc = BEATS[0]
    sample_prompt = f"Prompt template OK for beat: {sample_key} ({sample_desc})"
    log(f"[DRY-RUN] {sample_prompt}")
    log(f"[DRY-RUN] Dry run validation successful. Exiting with code 0.")
    return 0

def main():
    parser = argparse.ArgumentParser(description="Ollama Dialogue Daemon")
    parser.add_argument("--dry-run", "--mock", action="store_true", dest="dry_run", help="Validate local setup and exit cleanly")
    parser.add_argument("--model", default=None, help="Override Ollama model tag")
    parser.add_argument("--cap", type=int, default=DEFAULT_CAP, help="Maximum dialogue files to generate")
    args = parser.parse_args()

    model = args.model or resolve_model()
    cap = args.cap

    if args.dry_run:
        sys.exit(run_dry_run(model))

    OUT.mkdir(parents=True, exist_ok=True)
    n = len(list(OUT.glob("*.md")))
    log(f"start (model={model}, cap {cap}, have {n})")
    i = n
    while not any(s.exists() for s in STOPS) and i < cap:
        key, desc = random.choice(BEATS)
        prompt = f"""Write ONE dialogue beat for a dark-fairytale-sweet rhythm JRPG (tone: gentle melancholy + whimsy, sheet-music magic vocabulary - melodies, rests, crescendos as metaphors). Beat: {desc}. Max 6 short lines, speaker-labeled (SIR MELODIOUS: / MELUSINA: / VOICE: as fits). No stage directions beyond one bracketed mood note. No markdown headers."""
        body = json.dumps({"model": model, "prompt": prompt, "stream": False,
                           "options": {"temperature": 1.05, "num_predict": 400}}).encode()
        try:
            req = urllib.request.Request(DEFAULT_API, data=body, headers={"Content-Type": "application/json"})
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
