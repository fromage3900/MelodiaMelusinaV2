"""Draft-data validator loop (no LLM needed for structural checks; deterministic).
Lints Imports/Data/**/*.json against draft schemas; writes Imports/Data/VALIDATION.md
plus a quarantine LIST (never moves/deletes). Re-runs when the file census changes.
Stop: deploy/OLLAMA_VALIDATOR_STOP or deploy/STOP_ALL.
"""
from __future__ import annotations
import json, time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "Imports" / "Data"
STOPS = [ROOT / "deploy" / "OLLAMA_VALIDATOR_STOP", ROOT / "deploy" / "STOP_ALL"]
LOG = ROOT / "deploy" / "ollama_validator.log"
ELEMENTS = {"Forte", "Tide", "Gale", "Stone", "Radiant", "Umbral", "Arcane"}
PACKS = {"Core", "Pack_MoonlitSonata", "Pack_GildedOverture"}

def log(m):
    line = f"[{time.strftime('%H:%M:%S')}] {m}"
    print(line, flush=True); LOG.open("a", encoding="utf-8").write(line + "\n")

def check(path: Path) -> list[str]:
    errs = []
    try:
        d = json.loads(path.read_text(encoding="utf-8"))
    except Exception as e:
        return [f"unparseable JSON: {e}"]
    schema = d.get("schema", "")
    if schema.startswith("FMelodiaEnemyDef"):
        s = d.get("stats", {})
        if d.get("element") not in ELEMENTS: errs.append(f"bad element {d.get('element')}")
        if not 50 <= s.get("max_hp", 0) <= 2000: errs.append(f"max_hp out of band: {s.get('max_hp')}")
        if not 5 <= s.get("base_damage", 0) <= 120: errs.append(f"base_damage out of band")
        if not isinstance(d.get("intents"), list) or not d["intents"]: errs.append("missing intents")
    elif schema.startswith("FMelodiaChartNote"):
        notes = d.get("notes", [])
        if len(notes) < 6: errs.append("fewer than 6 notes")
        last = -1.0
        for n in notes:
            if not (isinstance(n.get("lane"), int) and 0 <= n["lane"] <= 3): errs.append(f"bad lane {n.get('lane')}"); break
            if n.get("beat", -1) < last: errs.append("beats not ascending"); break
            last = n.get("beat", last)
    elif schema.startswith("MelodiaCosmetic"):
        if d.get("content_pack_id") not in PACKS: errs.append(f"bad pack {d.get('content_pack_id')}")
        tc = d.get("token_cost", {})
        if not (isinstance(tc.get("heart"), int) and 0 <= tc["heart"] <= 20): errs.append("bad heart cost")
        if d.get("slot") not in {"dress", "hat", "gloves", "shawl", "trail", "hair_charm"}: errs.append(f"bad slot")
    elif schema.startswith("RoomModifier"):
        if "blessing" not in d or "curse" not in d: errs.append("missing blessing/curse pair")
    else:
        errs.append(f"unknown schema '{schema}'")
    return errs

def census() -> tuple:
    return tuple(sorted(str(p) for p in DATA.rglob("*.json")))

def run_pass():
    files = [Path(p) for p in census()]
    bad = {}
    for f in files:
        errs = check(f)
        if errs:
            bad[f] = errs
    lines = [f"# Imports/Data Validation - {time.strftime('%Y-%m-%d %H:%M')}",
             f"\nScanned: {len(files)} - Passed: {len(files) - len(bad)} - Flagged: {len(bad)}\n"]
    if bad:
        lines.append("## Quarantine candidates (review + fix or discard - NOT auto-moved)\n")
        for f, errs in sorted(bad.items()):
            lines.append(f"- `{f.relative_to(ROOT)}` - " + "; ".join(errs))
    (DATA / "VALIDATION.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
    log(f"pass done: {len(files)} scanned, {len(bad)} flagged")

def main():
    DATA.mkdir(parents=True, exist_ok=True)
    log("validator start")
    last = None
    while not any(s.exists() for s in STOPS):
        cur = census()
        if cur != last:
            run_pass(); last = cur
        time.sleep(30)
    log("exit")

if __name__ == "__main__":
    main()
