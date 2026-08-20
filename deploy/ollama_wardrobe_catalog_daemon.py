"""Wardrobe/cosmetic concept catalog daemon (Horizon-3 shelf-stocking).
Output: Imports/Data/Cosmetics/*.json  ·  Stop: deploy/OLLAMA_WARDROBE_STOP or deploy/STOP_ALL
Schema anchors: EMelodiaSpellElement palette moods, entitlement content packs, Heart/Swirl tokens.
"""
from __future__ import annotations
import json, random, re, time, urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "Imports" / "Data" / "Cosmetics"
STOPS = [ROOT / "deploy" / "OLLAMA_WARDROBE_STOP", ROOT / "deploy" / "STOP_ALL"]
LOG = ROOT / "deploy" / "ollama_wardrobe.log"
MODEL, API, CAP = "qwen2.5-coder:7b", "http://127.0.0.1:11434/api/generate", 40
SLOTS = ["dress", "hat", "gloves", "shawl", "trail", "hair_charm"]
RARITY = ["Common", "Common", "Refined", "Refined", "Couture", "Grandmaster"]
PACKS = ["Core", "Core", "Core", "Pack_MoonlitSonata", "Pack_GildedOverture"]
ELEMENTS = ["Forte", "Tide", "Gale", "Stone", "Radiant", "Umbral", "Arcane"]

def log(m):
    line = f"[{time.strftime('%H:%M:%S')}] {m}"
    print(line, flush=True); LOG.open("a", encoding="utf-8").write(line + "\n")

def ollama(prompt):
    body = json.dumps({"model": MODEL, "prompt": prompt, "stream": False,
                       "options": {"temperature": 1.0, "num_predict": 700}}).encode()
    try:
        req = urllib.request.Request(API, data=body, headers={"Content-Type": "application/json"})
        with urllib.request.urlopen(req, timeout=300) as r:
            return json.loads(r.read())["response"]
    except Exception as e:
        log(f"ollama error: {e}"); time.sleep(10); return ""

def main():
    OUT.mkdir(parents=True, exist_ok=True)
    ids = {p.stem for p in OUT.glob("*.json")}
    log(f"start (cap {CAP}, have {len(ids)})")
    while not any(s.exists() for s in STOPS) and len(ids) < CAP:
        slot, rarity, pack, element = random.choice(SLOTS), random.choice(RARITY), random.choice(PACKS), random.choice(ELEMENTS)
        prompt = f"""Design ONE cosmetic for Melusina, heroine of a dark-fairytale-sweet rhythm JRPG (Infinity Nikki-style dress-up desire, sheet-music magic, filigree + sparkle). Slot: {slot}. Rarity: {rarity}. Element mood: {element} (Forte=brassy, Tide=watery, Gale=wind, Stone=earthen, Radiant=light, Umbral=shadow, Arcane=starry).
Output ONLY JSON: {{"id": "Cos_{slot.title()}_<PascalName>", "display_name": "...", "slot": "{slot}", "rarity": "{rarity}", "element_mood": "{element}", "content_pack_id": "{pack}", "token_cost": {{"heart": int 1-12, "swirl": int 0-6}}, "palette": ["#RRGGBB","#RRGGBB","#RRGGBB"], "flavor": "one sentence, <=16 words", "material_notes": "one phrase referencing toon-master or SDF material family treatments (iridescence, gilded filigree, stained glass, aurora band...)"}}
Higher rarity = higher token cost. No markdown."""
        m = re.search(r"\{.*\}", ollama(prompt), re.DOTALL)
        try:
            data = json.loads(m.group(0)) if m else None
        except json.JSONDecodeError:
            data = None
        if not data or "id" not in data or data["id"] in ids:
            log("rejected"); continue
        data["content_pack_id"] = pack if data.get("content_pack_id") not in PACKS else data["content_pack_id"]
        data["schema"] = "MelodiaCosmetic-draft-v1"
        (OUT / f"{data['id']}.json").write_text(json.dumps(data, indent=2), encoding="utf-8")
        ids.add(data["id"]); log(f"written: {data['id']} ({rarity} {slot}, {pack})")
        time.sleep(4)
    log("exit")

if __name__ == "__main__":
    main()
