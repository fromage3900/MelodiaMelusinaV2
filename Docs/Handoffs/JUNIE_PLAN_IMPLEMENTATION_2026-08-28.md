# Junie Plan Implementation — 2026-08-28

**Author:** Melusina (Hermes agent, z-ai/glm-5.2)
**Date:** 2026-08-28
**Status:** Offline parts implemented; editor-bound parts queued

---

## What Junie Is

Junie is the user's name for the Rider-based editor-lane agent (model: bedrock-mantle/qwen.qwen3-coder-next). Junie holds the editor lock for PIE/CDO/T3D work. The no-editor lane stays offline when Junie has the editor.

Reference session: @session:default/20260828_130816_78f2dc (2026-08-28, 13:08)

---

## Junie's Plan (from the 08-28 session)

Junie's session was the lookdev/shader day. The plan was:

1. **MelodiaShader module** — create a proper UE module so Rider can index .usf/.ush as first-class shader source (not inline Python strings)
2. **Six .ush shader files** — InkCommon, InkSdfNotation, InkBioluminescent, InkPatternRouter, NikkiCommon, BiolumCommon
3. **Register in .uproject + Build.cs** — wire the new module
4. **Update melodia-shader-rider skill** — point at the real shader source root
5. **Update unified PPV/Oceanology lookdev plan** — add Rider shader integration section

After the shader module:
6. Full closed-editor rebuild (new module — Live Coding can't register it)
7. Confirm Oceanology loads natively on editor boot
8. Fix M_PP_MelodiaInk: wire 4 missing SceneTexture inputs
9. Reconcile PPV state on ZenForestTest (live read)
10. Deploy 4-blendable hero stack to all 5 shipping levels
11. Create MI_Oceanology_NikkiHero + wire bioluminescence/Nikki SDF/MPC palette
12. Stage + capture niagara_sakura_ambience hero render

---

## What's Done (Offline, This Session)

| Item | Commit | Status |
|------|--------|--------|
| MelodiaShader module (.Build.cs, .h, .cpp) | `7b00aa81` | COMMITTED |
| 6 .ush shader files (39KB total) | `7b00aa81` | COMMITTED |
| MelodiaShader in .uproject (PostConfigInit) | `92af496b` | COMMITTED |
| MelodiaShader in BS_GodFile.Build.cs deps | `92af496b` | COMMITTED |
| melodia-shader-rider SKILL.md updated | `47eb208a` | COMMITTED |
| TWeakObjectPtr crash fix (NarrativeSubsystem) | `92af496b` | COMMITTED |
| Profiler traces (RhythmCombat + AudioReactive) | `92af496b` | COMMITTED |
| Docs/config/Python tools + task ledger | `47eb208a` | COMMITTED |
| Fixtures manifest refresh | `1dd37870` | COMMITTED |
| Contract tests 4/4 + 10/10 PASS | — | VERIFIED |

**Total commits this session:** 4 commits, 43 files changed

---

## What Remains (Editor-Bound)

1. **Full closed-editor rebuild** — MelodiaShader is a new module; needs UBT build, not Live Coding
2. **Oceanology load verification** — confirm the plugin loads on editor boot
3. **M_PP_MelodiaInk pin fix** — wire 4 missing SceneTexture inputs (editor session)
4. **PPV reconciliation** — live read of ZenForestTest PPV state
5. **Hero stack deployment** — 4 blendables across 5 shipping levels (editor session)
6. **MI_Oceanology_NikkiHero creation** — wire bioluminescence/Nikki SDF/MPC (editor session)
7. **Sakura ambience capture** — stage + render (editor session)
8. **Static gates** — `echo_run.py run static_gates` (5 tools, all editor-bound)
9. **5 open P0 gates** — PIE testing (rhythm_owner, wardrobe_equip_roundtrip, rhythm_grade_to_result, music_world_key, wardrobe_gameplay_hook)

All of the above HOLD until the editor is up and the full build completes.

---

## Reference Docs

| Doc | Location |
|-----|----------|
| Backend integration plan | `Docs/Backend/MELODIA_BACKEND_INTEGRATION_PLAN_2026-08-28.md` |
| UE58 Rider workflow (long-term) | `Docs/Backend/UE58_RIDER_WORKFLOW_LONG_TERM_2026-08-28.md` |
| Monolith text-injection scale-up | `Docs/Backend/MONOLITH_TEXT_INJECTION_SCALE_UP_2026-08-28.md` |
| Unified PPV/Oceanology lookdev plan | `Docs/Handoffs/UNIFIED_PPV_OCEANOLOGY_LOOKDEV_PLAN_2026-08-28.md` |
| melodia-shader-rider skill | `.claude/skills/melodia-shader-rider/SKILL.md` |
| Editor-up execution checklist | `Docs/Handoffs/EDITOR_UP_EXECUTION_CHECKLIST_2026-08-28.md` |
| P0 closeout action plan | `Docs/Handoffs/P0_CLOSEOUT_ACTION_PLAN_2026-08-28.md` |
