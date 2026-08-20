"""Gumroad/FAB listing copy daemon (Horizon-1 revenue support). Cap 8 drafts.
Output: Docs/Gumroad/Drafts/*.md  ·  Stop: deploy/OLLAMA_GUMROAD_STOP or deploy/STOP_ALL
SKU facts sourced from Docs/MONETIZATION_GEOMETRY_FIX_EXPORT_2026-07-12.md (do not invent contents).
"""
from __future__ import annotations
import argparse, json, os, random, sys, time, urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "Docs" / "Gumroad" / "Drafts"
STOPS = [ROOT / "deploy" / "OLLAMA_GUMROAD_STOP", ROOT / "deploy" / "STOP_ALL"]
LOG = ROOT / "deploy" / "ollama_gumroad.log"
DEFAULT_API = os.environ.get("OLLAMA_API", "http://127.0.0.1:11434/api/generate")
DEFAULT_TAGS_API = os.environ.get("OLLAMA_TAGS_API", "http://127.0.0.1:11434/api/tags")
DEFAULT_CAP = 8
PREFERRED_MODELS = [
    "qwen2.5-coder:7b",
    "deepseek-r1:14b",
    "qwen2.5-coder:14b",
    "deepseek-r1:7b",
    "deepseek-coder:6.7b",
    "qwen3.8-27b:latest",
    "hermes3:latest",
]

SKUS = [
    ("SKU1_OrnamentKitbash", "Ornament Kitbash — 15 gothic ornament meshes for stylized/toon scenes (arches, trims, filigree panels), FBX, game-ready kitbash set"),
    ("SKU1b_MusicalOrnamentKitbash", "Musical Ornament Kitbash — 10 musical ornament meshes incl. 3 Melody Token medallions, FBX, stylized/toon"),
    ("SKU2_SDFMathArtMaterials_FAB", "SDF Math-Art Toon Materials for UE5 — 61 procedural raymarched masters: Klein bottle, Mobius strip, Mandelbulb, Menger sponge, Penrose staircase, Julia set, gothic rose windows, parallax facades; no textures needed, pure material math"),
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
    env_model = os.environ.get("OLLAMA_GUMROAD_MODEL") or os.environ.get("OLLAMA_MODEL")
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
    log(f"[DRY-RUN] Validating gumroad copy daemon setup (model={model}, out={OUT})")
    sample_key, sample_facts = SKUS[0]
    log(f"[DRY-RUN] SKU template OK for: {sample_key} ({sample_facts[:60]}...)")
    log(f"[DRY-RUN] Dry run validation successful. Exiting with code 0.")
    return 0

def main():
    parser = argparse.ArgumentParser(description="Ollama Gumroad Copy Daemon")
    parser.add_argument("--dry-run", "--mock", action="store_true", dest="dry_run", help="Validate local setup and exit cleanly")
    parser.add_argument("--model", default=None, help="Override Ollama model tag")
    parser.add_argument("--cap", type=int, default=DEFAULT_CAP, help="Maximum drafts to generate")
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
        key, facts = random.choice(SKUS)
        prompt = f"""Write a marketplace listing draft for a 3D asset product. FACTS (do not invent beyond these): {facts}.
Sections: 1) Title (<=60 chars, benefit-led). 2) Hook paragraph (2-3 sentences, who it's for). 3) Bullet list of contents/benefits (from facts only). 4) 'Perfect for' one-liner. 5) SCREENSHOT SHOT-LIST: 6 numbered, specific beauty-shot compositions a UE artist could stage. Tone: confident indie-dev, zero hype-slop words (no 'unleash', 'elevate', 'stunning'). Plain markdown."""
        body = json.dumps({"model": model, "prompt": prompt, "stream": False,
                           "options": {"temperature": 0.8, "num_predict": 800}}).encode()
        try:
            req = urllib.request.Request(DEFAULT_API, data=body, headers={"Content-Type": "application/json"})
            with urllib.request.urlopen(req, timeout=300) as r:
                text = json.loads(r.read())["response"].strip()
        except Exception as e:
            log(f"ollama error: {e}"); time.sleep(10); continue
        if len(text) < 200:
            log("rejected"); continue
        i += 1
        fname = f"{key}_draft{i}.md"
        (OUT / fname).write_text(text + "\n", encoding="utf-8")
        log(f"written: {fname}")
        time.sleep(5)
    log("exit")

if __name__ == "__main__":
    main()
