import json
from pathlib import Path

root = Path(__file__).resolve().parent
source = root / "p0_waist_pinned_closeout.json"
data = json.loads(source.read_text(encoding="utf-8"))
phases = {}
for phase in ("idle", "walk", "turn", "stop"):
    samples = [s for s in data["samples"] if s["phase"] == phase]
    skins = [s for s in data["skin"] if s["phase"] == phase]
    waist = [v for s in samples for v in s["waist_ring_deviation_cm"].values()]
    contacts = [v["vertical_clearance_cm"] for s in skins for v in s["contacts"].values() if "vertical_clearance_cm" in v]
    phases[phase] = {
        "samples": len(samples),
        "skin_samples": len(skins),
        "speed_max_cm_s": max((s["speed"] for s in samples), default=None),
        "knee_min_deg": min((v for s in samples for v in s["knees"].values()), default=None),
        "knee_max_deg": max((v for s in samples for v in s["knees"].values()), default=None),
        "waist_deviation_max_cm": max(waist, default=None),
        "boot_clearance_min_cm": min(contacts, default=None),
        "boot_clearance_max_cm": max(contacts, default=None),
    }
summary = {
    "source": source.name,
    "world": data["world"],
    "input_proof": data["input_proof"],
    "candidate_anim": data["candidate_anim"],
    "kawaii_enabled": data["kawaii_enabled"],
    "spawn_location_cm": data["samples"][0]["location"] if data["samples"] else None,
    "finished": data["finished"],
    "errors": data["errors"],
    "screens": data["screens"],
    "phases": phases,
    "proof_boundary": "Fresh P0 injected-movement/contact evidence; not physical-input, run/sprint, bend, restart/reload, packaged, or final visual acceptance."
}
(root / "p0_waist_pinned_summary.json").write_text(json.dumps(summary, indent=2), encoding="utf-8")
print(json.dumps(summary, indent=2))
