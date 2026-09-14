# Outline Finalization — Longterm (started 2026-09-14)

Master: M_PP_StorybookOutline_Premium_Candidate (73 expr, Custom HLSL V6.2).
Live PPV blendable identity unconfirmed via API (Blendables protected from
Python); owner to confirm in viewport which profile PPV_NikkiDream carries.

## Measured profiles (live CDO values)

| Param | Master default | Hero | Gameplay | AASane (new) |
|---|---|---|---|---|
| OutlineWidth | 1.5 | -7079.59 | 0.133 | 1.5 |
| DepthRelativeThreshold | 0.015 | 40.61 | 0.044 | 0.015 |
| AAWidth | 1.5 | 1.6 | 1.5 | 1.5 |
| JitterCompensation | 1.0 | 1.586 | -1.424 | 1.0 |
| FoliageDepthInkStrength | 0.12 | 0.55 | -35.38 | 0.12 |
| HalftoneAmount | 0 | 0.11 | 4672.06 | 0 |
| HalftoneScale | 6 | 5.19 | -2.34 | 6 |
| InkBlurRadius / Strength | 1 / 0 | 1.1 / 0.45 | 8.02 / 0.92 | 1 / 0 |
| MaxWidthPx / MinWidthPx | 3 / 0.6 | 3 / 1 | 4.47 / 0.6 | 3 / 0.6 |
| DepthWeight / NormalWeight | 1 / 1 | 0.043 / ? | 0.269 / 0.519 | 1 / 1 |
| RefractionDepthBias (dead) | — | 0 | 0 | cleared |

AASane: /Game/EnvSandbox/Materials/PostProcess/Candidates/Profiles/MI_Outline_PremiumV3_AASane
(compiled, saved 2026-09-14; Hero duplicate + 21 sane scalars + dead override cleared).
AAProto master duplicate (no-op copy, study only):
/Game/EnvSandbox/Materials/PostProcess/Candidates/M_PP_StorybookOutline_Premium_AAProto

## Study conclusion (read-only + shader tail evidence)

The edge output (float4(ink, edge)) is already saturate/smoothstep-built;
AOS MF_StencilDepthAlpha's hard Ceil had nothing left to teach it. The drift
is all in instance VALUES (slider extremes), not shader math. Graft cancelled;
curation is the fix.

## Recommendation

1. Adopt AASane as the Gameplay baseline (master-true + foliage-safe).
2. Keep Hero for portfolio stills only after resetting OutlineWidth/DepthThr.
3. Add a value-range guard (min/max per param above) to the lookdev audit so
   slider drift fails loudly instead of shipping silently.
4. PIE A/B/C: Hero vs Gameplay vs AASane from CAM_MelusinaMorning_Portfolio;
   owner eye is the gate (agent captures are byte-unreliable).

## PIE evidence (2026-09-14)

Runner: Tools/pie_smoke_runner.py --map L_MelusinaMorning (their harness).
Report + frames: Saved/PIE/morning_water_20260914/ (gitignored, beside frames).
Result: OK/clean, 25s, 0 errors; frame_000 black (loading), frames 001-021 lit,
all distinct hashes (real footage, not cached). Image-view service 500'd, so
beauty judgment stays with the owner at CAM_MelusinaMorning_Portfolio.
Frame honesty rule: byte-identical frames = cached/black, reported not hidden.

## Engine.ini verdict (2026-09-14, editor closed)

DefaultEngine.ini already carries the full engine-side outline contract
(CustomDepth=3, MotionBlur off, TSR thin-geometry foliage relaxation). No
functional cvars added — fineness/stability are profile values, and blind
AA/resolution switches were refused on purpose. Comment block records this
in the ini itself. Protected-file note: committing this needs SKIP_PROTECTION=1
with owner approval cited.

## Freeze verdict (2026-09-14, OWNER EYES) — FXAA calms the ink

r.AntiAliasingMethod 1 (FXAA) froze the jitter live; TSR 4 and TAA 2 both crawl.
Mechanism, finally nailed: fullscreen depth-edge ink reads a temporally jittered
buffer under any temporal AA — Borderlands ran world ink on UE3 with no temporal
jitter at all. Persisted as r.DefaultFeature.AntiAliasing=1 in DefaultEngine.ini
(protected file — commit needs SKIP_PROTECTION=1 with owner approval cited).
V7.2/V7.3 protos + AASane + NoJitter candidates stand SUPERSEDED, kept on disk
until owner says delete. Remaining freeze rites: framed _e/_f captures at the
portfolio camera, value-range guard in the lookdev audit, frozen-profile hash row.

## MelodiaInk ambush (2026-09-14) — the second inkwell

The live PPV blends FIVE frozen MIs, not one: StorybookOutline, MelodiaInk,
MeluColorGrade, StarryNight (+GlitterPile ref). MelodiaInk is print texture
(halftone/hatch/grain/paper — no edges), built for STATIC grain per its own
comments. Its live MI carried slider garbage: InkHatch=802.68 (master 1),
InkGrainOn=44.7 (master 1), InkHalftone=-1.27 (master 1). An 802-density hatch
crawling fullscreen reads exactly as "jittering like crazy" while every suspect
is the edge shader. Reset all four to master defaults, recompiled, saved.
No prior agent edits touched MelodiaInk — all 09-14 outline work was
StorybookOutline-family; the ambush predates today.

## V7.3 proto (2026-09-14) — pattern swim fix

Live blendable proven = MI_StorybookOutline_Frozen (binary actor scan, 2 actors).
Deeper cause found in V7 core: with JitterCompensation=1 the tap rose rotation
(radOff) and the paper grain hash were computed from JITTERED uvC — the pattern
itself swam every frame, more visible than any value noise. V7.3 hashes both
from the snapped grid (uvSnap); taps stay on uvC so TSR tracking is kept.
Same proto asset (now V7.3 code), wires 55/55, compiled, saved. V72 MI already
parents the proto, so preview = one blendable swap, fully reversible.

Preview: PPV_NikkiDream -> Blendables -> swap MI_StorybookOutline_Frozen for
MI_StorybookOutline_V72. Kill-switch (if the ink must die): same list, set the
frozen outline entry weight 0 or remove it — hull outlines, Melusina, sheep and
Sir all keep their own lines regardless.

## V7.2 proto (2026-09-14, staged candidate, NOT live)

V7.2 grafts two minimal wiring changes onto a frozen-master proto:
- mean-bias floor 0.5 -> 0.75 (dMax is the noisiest tap statistic under TSR jitter)
- hero-skip (stencil 4) dilated by one texel (kills 0<->4 border popping on silhouettes)
Proto: /Game/EnvSandbox/Materials/PostProcess/Candidates/M_PP_StorybookOutline_V72Proto
(compiled clean, 329 PS instr, saved). MI: .../Profiles/MI_StorybookOutline_V72
(reparented to proto, 0 params lost, recompiled, saved). All 55 Custom_0 wires
verified intact after the code update. Frozen master + Frozen MI untouched.
Live PPV swap deliberately NOT attempted (blendable write path unproven; no blind writes).

## Shimmer metric experiment (2026-09-14) — NEGATIVE result, recorded honestly

Three 25s Morning smokes, all OK/0 errors: pre (twins new), post Sir-4 + twins,
clean (twins hidden). Frame-diff shimmer (mean-subtracted): 1.66 / 4.27 / 11.90.
The clean run shimmers MOST with the fewest systems — run-to-run variance
(TSR/Lumen warmup, sky, sheep idle) swamps any outline signal. Full-frame diff
cannot judge ink in a living scene. Verdict: beauty proof stays viewport-only
(last night's _c/_d framed-capture method). No further blind runs burned.

## Sir Melodious exclusion (DONE 2026-09-14, Morning instance)

Sir keeps his inverted-hull outlines; the PP ink must skip him. Finding: his mesh
wrote NO stencil (custom-depth off, value 0), so V7.1's skip never caught him and
he took default ink. Fix applied on the Morning instance
(Morning_SirMelodious_STATIC_INTRO.SirMelodiousRigged): render_custom_depth=True,
custom_depth_stencil_value=4 — the proven hero ward. Verified holding, map saved.
Party-unit BP default left untouched (needs your call: omit Sir everywhere or
Morning only?). Targets for full rollout:
- /Game/MelodiaIntegration/Party/BP_SirMelodiousPlayerUnit (party unit)
- /Game/MelodiaIntegration/Blueprints/Opening/BP_MelodiaSirMelodiousMorningIntro
  (Morning_STATIC_INTRO actor)
Lane: single editor, Monolith get_components -> set_component_property
RenderCustomDepth false per skeletal/static mesh comp, recompile, save only
those two BPs, PIE-check Morning. Estimated minutes once the editor wakes.
Alternative if hull needs stencil elsewhere: narrow StenciRange on the live
profile instead — owner call at the viewport.
