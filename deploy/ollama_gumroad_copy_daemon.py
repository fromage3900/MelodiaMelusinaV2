"""Gumroad/FAB listing copy daemon (Horizon-1 revenue support). Cap 8 drafts.
Output: Docs/Gumroad/Drafts/*.md  ·  Stop: deploy/OLLAMA_GUMROAD_STOP or deploy/STOP_ALL
SKU facts sourced from Docs/MONETIZATION_GEOMETRY_FIX_EXPORT_2026-07-12.md (do not invent contents).
"""
from __future__ import annotations
import json, random, time, urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "Docs" / "Gumroad" / "Drafts"
STOPS = [ROOT / "deploy" / "OLLAMA_GUMROAD_STOP", ROOT / "deploy" / "STOP_ALL"]
LOG = ROOT / "deploy" / "ollama_gumroad.log"
MODEL, API, CAP = "llama3.1:8b", "http://127.0.0.1:11434/api/generate", 8
SKUS = [
    ("SKU1_OrnamentKitbash", "Ornament Kitbash — 15 gothic ornament meshes for stylized/toon scenes (arches, trims, filigree panels), FBX, game-ready kitbash set"),
    ("SKU1b_MusicalOrnamentKitbash", "Musical Ornament Kitbash — 10 musical ornament meshes incl. 3 Melody Token medallions, FBX, stylized/toon"),
    ("SKU2_SDFMathArtMaterials_FAB", "SDF Math-Art Toon Materials for UE5 — 61 procedural raymarched masters: Klein bottle, Mobius strip, Mandelbulb, Menger sponge, Penrose staircase, Julia set, gothic rose windows, parallax facades; no textures needed, pure material math"),
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
        key, facts = random.choice(SKUS)
        prompt = f"""Write a marketplace listing draft for a 3D asset product. FACTS (do not invent beyond these): {facts}.
Sections: 1) Title (<=60 chars, benefit-led). 2) Hook paragraph (2-3 sentences, who it's for). 3) Bullet list of contents/benefits (from facts only). 4) 'Perfect for' one-liner. 5) SCREENSHOT SHOT-LIST: 6 numbered, specific beauty-shot compositions a UE artist could stage. Tone: confident indie-dev, zero hype-slop words (no 'unleash', 'elevate', 'stunning'). Plain markdown."""
        body = json.dumps({"model": MODEL, "prompt": prompt, "stream": False,
                           "options": {"temperature": 0.8, "num_predict": 800}}).encode()
        try:
            req = urllib.request.Request(API, data=body, headers={"Content-Type": "application/json"})
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
