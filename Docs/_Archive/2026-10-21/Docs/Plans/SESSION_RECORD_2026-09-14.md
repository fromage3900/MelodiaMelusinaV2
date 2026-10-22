# Session Record — 2026-09-14 (outline freeze + Melusina lookdev)

## Outline: from crazy jitter to still ink (COMMITTED 946f67d1)
- Studied Premium V6.2 + frozen V7.1 shaders line by line. V7.1 (Claude Opus 5,
  09-13) fixed the StencilAlpha-mask bug (styleIdx read raw from PPI_CustomStencil).
- Proven live blendable = MI_StorybookOutline_Frozen (binary actor scan).
- Sir Melodious wrote NO stencil (took default ink) → stencil 4 (hero ward), verified.
- MelodiaInk ambush: live MI had InkHatch=802.68 etc.; reset 4 params to master.
- Tried TAA (still crawled) and V7.2/V7.3 protos (superseded). FXAA (method 1)
  froze the ink live — Borderlands parallel holds (world ink needs jitter-free buffer).
- Persisted r.DefaultFeature.AntiAliasing=1 + verdict comment in DefaultEngine.ini.
- Shimmer-metric experiment: NEGATIVE (run variance swamps signal) — viewport-only proof.

## Melusina water/VFX (saved, uncommitted — gitignored, exceptions owed)
- BOUND trio verified parked DISABLED; parked-diagnostic ghost diagnosed (see skill).
- New: ImpactBurst + Mist MIs/systems/actors in Morning VFX/Morning (rates were 0!).
- Burst 30/s 0.4-0.8s; Mist 8/s 2.5-4s. NoteBeam re-homed to canon master.
- 15/15 systems green. WaterHair MI: 19 overrides, 0 dead — untouched (other lane).
- Kawaii node present+wired in ABP_Melusina_WaterHair (root hair_root); symptom unnamed.
- LOOKDEV_Melusina_HairTest spawned for film; DELETE after review.

## Debts (owner gates)
- Gitignore exceptions for today's uassets; G: mirror real run (dry-run clean:
  162GB/120,878 files/0 failures; exclude .claude/worktrees + _TouchDesigner);
  Sir party-unit default; CURRENT_STATE row; lookdev value-guard; AOS pilot parked.
