# Night Reel — Nikki Polish Iteration Queue (cron loop state file)

**Rules for every tick:** headless Blender 5.2 ONLY (`blender --factory-startup -b <blend> -P <script>`),
NEVER connect to port 9876 (owner's GUI session), never save outside
`Saved/Portfolio/wave_violin/`, one iteration per tick, update THIS file first.
Blend: `C:/EnvironmentPortfolio/BS_GodFile/Saved/Portfolio/wave_violin/ME_WaveViolin.blend`
Scripts dir: `C:/EnvironmentPortfolio/BS_GodFile/Tools/wave_violin/`
Reports: `.../render_out/pXX_report.json` + plate `pXX_<tag>.png`
After each: `git -C C:/EnvironmentPortfolio/BS_GodFile add -f Tools/wave_violin/ Saved/Portfolio/wave_violin/render_out/pXX_report.json` + commit `feat(waveviolin): pXX <title>` (never bare `add`; never clean/checkout).

**Done so far:** p00-p08 pipeline ✓, p09-p13 refine ✓, p14-p17 Nikki shader arc ✓
(current: gems 8/10, belly pattern 6/10, deploy plate ~7/10, exposure repaired,
ShaderNodeMix RGBA-socket fix landed).

## Queue (pick highest OPEN; mark DONE with commit hash)
| # | Iter | State | Notes |
|---|---|---|---|
| p18 | F-holes: bake Chladni Emissive INTO vent material as texture-driven glow (not flat emission) — Emissive map from Copernicus set, constant ramp multiplied | OPEN | Nikki doctrine: pattern glow, not lamp glow |
| p19 | Belly roughness variance: wood-grain fbm into ORM green (0.5-0.75 range) so cel ramp picks up fabric-of-wood | OPEN | |
| p20 | Ribbons: add subtle Chladni BC texture along length (world-space mapping so it doesn't slide) | OPEN | |
| p21 | Turntable: 8-frame 360° deploy-pose mini-animation, render loop PNGs (P6 prototype pattern from EEVEE plan) | OPEN | |
| p22 | Contact shadow: shadow-catcher ground + tighter key angle (review: fluffy contact) | OPEN | |
| p23 | String anisotropy: sheen tint cool per-string, slight radius variance (1-4 gauge) | OPEN | |
| p24 | Palette harmony pass: pull deploy plate, sample mean colors vs Shorewake dusk palette tokens; nudge lamp values | OPEN | |
| p25 | Outline weight audit: inverted hull missing on new parts (f-holes, scroll, beads) — decide per-part, apply GN_InvertedHull pattern from WaveHarp | OPEN | |
| p26 | Final hero plate: poster composition per P4 sheet pattern (3/4 + macro + deploy contact) | OPEN | |

**Stop condition:** queue empty or p-score >= 9/10 from vision review twice → write FINAL.md, mark loop done.
**Vision check every 3rd tick** using the vision tool on the newest plate; record score in table below.

## Tick log
| Time | Iter | Commit | Score/Notes |
|---|---|---|---|
| 2026-09-07 ~19:00 | setup | — | queue created by interactive session |
