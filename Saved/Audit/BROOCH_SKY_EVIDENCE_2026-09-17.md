# Brooch v10 + Melusina Sky — session evidence summary (2026-09-17)

Committed alongside the lane files on `collab/laptop/brooch-sky-20260917`. The heavy artifacts
(harness scripts, renders, logs, .blend) stay local-only per repo policy; this file records the
numbers so the commit is self-contained.

## Bead-rim audit + fix (owner question: "why is the rim of beads at an angle?")

- Measured: the pave ring sat at constant radius (r 18.3-21.1 mm) but its height rode a ~25 deg
  tilted plane (z spread 21.4 mm; plane fit 18.3 deg about X and Y alike).
- Live A/B: sampler connected -> 21.4 mm spread; `Value` field unplugged -> 2.43 mm (level).
- Root cause: `SampleNearestSurface` fed a Position field in its `Value` slot returned positions
  from the wrong geometry context. Fix: downward `Raycast` (Hit Position -> SeparateXYZ -> Z+lift)
  for BOTH the pave ring and the gem sampler.
- After rebuild: pave z extent 21.41 -> **3.13 mm**; body 20.62 -> 3.34 mm; all 7 genomes 0.0% err.
- Row regularity: `Pave Jitter` (default 0.0) + `Pave Even` (default on) -> **80/80 distinct
  beads, angular gaps mean 4.500 / std 0.000 / CV 0.000, plane tilt 0.00 deg**, pave bbox
  44.53 x 44.53 (symmetric).

## Presentation rig + Melusina Sky v1-v3

- Rig: dark field, white + black reflection cards, soft key 26 W, hard gem point 8 W, AgX
  medium-high, EEVEE 96 spp + raytracing; bbox-framed front/tq/macro stills; toon outline off
  for stills.
- Sky: 37-node stack per carrier (world + PRES_Back card), layers L0 gradient / L1 horizon glow /
  L4 stars / L3 cloud band / L5 aurora / L6 grain / L7 strength trim; 12 dials; 8 variants;
  genome auto-select (`sky_for_genome`).
- Gates: cost **+0%** (117 s baseline vs 114-118 s with sky); reruns **pixel-identical** (0 of
  12.8M channels differ; PNG bytes differ on metadata only); zero texture nodes; 37 <= 60 nodes;
  headless clean; black-window reflection survives; zero-dial degrades to a flat field; all 8
  variant fronts hash-distinct.
- EEVEE 5.2 findings: stars render SHARP in the world background (no dome needed); the
  Is-Camera-Ray split WORKS in this build; no world-sun threshold property exists on `scene.eevee`.
- Bugs found + fixed in-pass: backdrop-card up-axis (rotated 90 deg about X -> local Z is
  horizontal; card carriers must read local Y); cloud colour invisible under the strength clamp
  (lifted by a base grey).

## Artifacts (local-only)

- Stills: `Saved/Audit/sky_editorial_dark_{front,tq,macro}.png`, `sky_variants_sheet.png`,
  `sky_only_{stars_clouds,clouds}.png`, `sky_exp_camray.png`, `pres_*.png` (pre-sky baseline).
- Harness: `Saved/Audit/v10_*.py`, `Saved/Audit/sky_*.py` (audit, surgery, verify, render loops).
- Logs: `Saved/Audit/sky_v{1,2,3}_run*.log`, `v10_*_build*.log`, `pres_baseline_run.log`.
- Build: `Saved/MelusinasHouse/FlowerBrooch.blend` (local-only) + `BUILD_REPORT_V10.txt`.
