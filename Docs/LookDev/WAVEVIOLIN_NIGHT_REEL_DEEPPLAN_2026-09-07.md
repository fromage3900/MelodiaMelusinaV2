# ME_WaveViolin — "Night Reel" · Deep Plan (2026-09-07, 6-8h lane)

**Board provenance:** `Docs/Art/VISUAL_REFERENCE_INDEX.md` → `_github_deploy/generated/assets/props/violin_komikaze_*` (violin plate, CANONICAL COMMITTED IMAGE family) + `Imports/Audio/StringInstruments_Aoneko/extracted/violin.fbx` (shape reference).
**Siblings:** follows `harp_bow_pipeline` conventions exactly (ME_WaveHarp Rev01→05 cadence).
**Live-file safety:** ALL work headless (`blender -b`), NEVER the GUI session on 9876. The owner's open `ME_WaveHarp_Rev05_BakeUV.blend` is unsaved and untouchable.

## Design brief (from the board, carried to the weapon)
- **Silhouette:** hourglass bouts → twin-blade waist; scroll → spiral pommel; fingerboard → spine rail; bridge → central socket hub; tailpiece → counterweight; f-holes → resonance vents (glow lanes); 4 strings → energy lines with faint emissive.
- **Hybrid twist (violin ⇄ reel):** body splits at the waist into two symmetric "reel blades" that sweep back like a bow's recurves; the scroll unfurls into a crank. Transformation rig = driver+shape-key pattern proven on WaveHarp (no armature, no parallel authority).
- **Palette "Night Reel":** amber rosewood body, pale brass fittings, pearl pegs, twilight-violet ribbons (continuity w/ Day-2), Chladni nodal emissive = warm candle-gold.
- **Music-is-visible:** eigen-mode Chladni on the belly plate at the four open-string frequencies (G-D-A-E: 196/294/440/587 Hz → nearest (m,n) per `chladni_eigen.py`).

## Phases (each ends in a PNG + JSON evidence row)
| # | Phase | Deliverable | Time | Unattended? |
|---|---|---|---|---|
| p00 | Stage bootstrap | `ME_WaveViolin_v00_Stage.blend`: collections, sockets, EEVEE 64spp 1400², 3-band toon dusk world, 3-light rig, Cel group appended from disk | 30m | YES |
| p01 | Blockout | primitive silhouette pass + 2 plates (front/deploy) + tri census | 45m | YES |
| p02 | Hero body | bezier bouts real curve, f-holes as cut-curves, bevel purfling; UV-smart; bake-UV | 90m | YES (owner eyes on shapes after) |
| p03 | Transformation | split-waist deployment: shape keys `Reel_Deploy` + master control drivers + 4 sockets; 3 poses rendered | 90m | YES |
| p04 | Cymatics | eigen Height/Normal (brass→rosewood recipe) on belly plate, vent glow ramps, macro render | 60m | YES |
| p05 | Ribbons + beads | 2 curve ribbons on scroll+tailpiece sockets (cloth dielectric — lessons: hue rot 0.20, linked-BaseColor trap), bead chain along waist (instance-on-curve) | 90m | YES |
| p06 | Editorial drape | XPBD single-shell veil settle → shape key `Drape_Editorial`; poster composition | 60m | PARTIAL — if XPBD headless stalls, author fallback pose |
| p07 | Polish audit | art-review checklist: framing, contact shadow, blown/dead check, hue sanity, ORM noncolor, tri budget <80k, outline consistency; contact sheet | 45m | YES |
| p08 | Export prep | `Export` collection + ME_BakeUV + sidecar JSON; UE intake manifest `/Game/EnvSandbox/Meshes/Environment/waveviolin` naming `SM_MEWaveViolin` | 30m | YES |

**Acceptance:** p07 contact sheet + `pipeline_report.json` with per-phase status; owner viewport = final truth.
**Guardrails:** no GUI-session writes; no saves outside the lane folder; git = docs+scripts only (renders to `Saved/Portfolio/` allowlist); never `clean`/`checkout -- .`.

**Runner:** `run_phases.sh` executes p00→p08 sequentially headless, logging `pipeline.log`; phases idempotent (skip if output PNG exists).
