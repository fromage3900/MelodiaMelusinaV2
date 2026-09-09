# Resonance Astrolabe — R0 Evidence Packet

**Issue:** #42  
**Branch:** `feature/resonance-astrolabe-r0`  
**Current evidence level:** `SOURCE BUILT`  
**Promotion target:** `LIVE PROVEN` for silhouette/scale only.

This packet is the first implementation pass, not another roadmap. It contains eight authored silhouette candidates and an executable coarse-blockout generator. No HDA, filigree, cymatic engraving, material work, or runtime response is allowed to become the next task until one candidate survives the current character hand and the real gameplay camera.

## Tracked evidence

- `astrolabe_silhouette_candidates_v001.svg` — 8-up black silhouette sheet.
- `astrolabe_silhouette_candidates.v1.json` — authored centimeter dimensions, motion intent, risks, and R0 gate.
- `Tools/Houdini/mara_elletra/instrument/build_astrolabe_r0_blockouts.py` — validates the contract and emits coarse centimeter-scale OBJ blockouts into ignored `_staging/resonance_astrolabe_r0/`.

Run from repo root:

```powershell
python Tools/Houdini/mara_elletra/instrument/build_astrolabe_r0_blockouts.py --check
python Tools/Houdini/mara_elletra/instrument/build_astrolabe_r0_blockouts.py --emit
```

## PC review gate

Start with **03 Eye Compass**, **06 Rose Window**, and **08 Broken Halo** because they best test the intended controlled asymmetry and survey-instrument read. If none survives, test the remaining five before redesigning.

The R0/R1 gate passes only when the evidence below exists from the current production character:

| Evidence | Required result | Status |
|---|---|---|
| authored-scale lineup | all 8 beside current character | PENDING PC |
| hand pose | 03 / 06 / 08 in the actual grip | PENDING PC |
| fixed gameplay camera | same camera/FOV for compared candidates | PENDING PC |
| silhouette read | family + head + grip + one asymmetry readable | PENDING PC |
| motion read | one major moving element understandable without VFX | PENDING PC |
| owner decision | one winner + one-line rejection reason for the rest | PENDING PC |

Capture names:

```text
R0_lineup_all8.png
R0_hand_03_eye_compass.png
R0_hand_06_rose_window.png
R0_hand_08_broken_halo.png
R0_gameplay_compare.png
R0_owner_decision.md
```

Do not mark this `LIVE PROVEN` from the SVG or generated OBJ files. Those prove source/build repeatability only.

## Next production action after PASS

Only after the owner selects a winner: build that candidate's guide curves, grip/resonator transforms and motion axes, then begin `HDA_MEL_Instrument_Frame_v001` / `RingStack_v001`. `MEL_CYM_001` comes after the structural blockout survives R1.
