"""Export Resonant Wilds music (tempo, meter, key, chords, motif) for UE runtime use.

Writes Content/MelodiaIntegration/ResonantWorld/Music/:
    resonant_wilds_music.json   human/UE-readable (Python/DataTable import)
    resonant_wilds_music.npz    NumPy: per zone, chords[bar, 5] MIDI and motif[n] MIDI
Chord voicing mirrors js/audio.js: [root, 3rd, 5th, octave, 9th].
Run from repo root: python Prototypes/Web/MelodiaResonantWilds/tools/export_music_for_ue.py
"""
import json, subprocess
from pathlib import Path
import numpy as np

ROOT = Path(__file__).resolve().parents[4]
OUT = ROOT / "Content/MelodiaIntegration/ResonantWorld/Music"
raw = subprocess.check_output(["node", "--experimental-default-type=module", str(Path(__file__).with_name("dump_music.mjs"))], text=True)
zones, arrays = [], {}
for z in json.loads(raw):
    chords = np.array([[z["key"] + s, z["key"] + s + (4 if q == "maj" else 3), z["key"] + s + 7, z["key"] + s + 12, z["key"] + s + 14] for s, q in z["prog"]], dtype=np.int16)
    motif = np.array([z["key"] + 12 + d for d in z.get("motif") or []], dtype=np.int16)
    arrays[f"{z['id']}__chords"], arrays[f"{z['id']}__motif"] = chords, motif
    arrays[f"{z['id']}__info"] = np.array([z["bpm"] if z.get("bpm") else 0, z["meter"], z["key"]], dtype=np.float32)
    z["chords_midi"], z["motif_midi"] = chords.tolist(), motif.tolist()
    zones.append(z)
OUT.mkdir(parents=True, exist_ok=True)
(OUT / "resonant_wilds_music.json").write_text(json.dumps({"schema": "melodia.resonant_wilds_music.v1", "source": "Prototypes/Web/MelodiaResonantWilds/js/design.js", "voicing": "root,3rd,5th,octave,9th", "info_array": "bpm,meter,key", "zones": zones}, indent=1) + "\n")
np.savez(OUT / "resonant_wilds_music.npz", **arrays)
print(f"{len(zones)} zones -> {OUT.relative_to(ROOT)}")
