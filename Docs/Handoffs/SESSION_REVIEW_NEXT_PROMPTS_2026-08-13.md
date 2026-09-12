# Session review + next-session prompts — 2026-08-13 ~00:42 ET

**Pick up here.** This supersedes [TONIGHT_CONTINUATION_HANDOFF_2026-08-12.md](TONIGHT_CONTINUATION_HANDOFF_2026-08-12.md) for *what to do next*. That file remains valid for T1–T3 evidence paths.

**15-minute loop: STOPPED** (was PID **26352**, sentinel `AGENT_LOOP_TICK_tonight_prep`). Do not start another unless the owner asks.

Locks still hold: rhythm WORKED · Quill WORKED. One UnrealEditor. No v22 save without `MELODIA_ALLOW_STAGE_SAVE=1`.

---

## Do they need Unreal / Blender closed?

**No.** Leave both open if you are continuing tonight.

| App | PID | Close? | If you *do* quit |
|-----|-----|--------|------------------|
| UnrealEditor | *(check `Get-Process UnrealEditor`)* | Not required | **Save `L_KaleidoNave` first** or the `CathedralKit_Review` strip and `Melusina_V2Test` placed actors vanish. Imported uassets stay on disk. |
| Blender 5.2 | **27644** | Not required | **Do not save v22** unless `MELODIA_ALLOW_STAGE_SAVE=1`. Quit without save = discard unsaved `GN_BG_Prototype`, LIQUID smoke cube, live hair-domain moves. |

Agents do not need a closed editor. Do **not** spawn a second UnrealEditor or a second Blender on v22.

---

## What this session actually landed

| Lane | Result | Evidence |
|------|--------|----------|
| T1 ZenTrim | `MI_ZenTrim_Base4K` on wand + StreetLamp. Magicians skipped | `Saved/Audit/hero_zentrim_assign.json` |
| T2 Cathedral | **41/41** FBX → `/Game/EnvSandbox/Meshes/Cathedral/`. 8-piece review strip in KaleidoNave **umap unsaved** | `Saved/Audit/cathedral_fbx_import.json` |
| T3 Flip / ABC / GC | 480 `.bobj` (1–240). ABC frames 1–96. Geometry Cache `/Game/Cinematics/MelusinaWaterHair/GC_MelusinaHairFlip_v22`. Gameplay hair untouched | `Saved/Audit/flip_hair_bake_2026-08-12.md` |
| Melusina V2 test | Copies only under `/Game/Melodia/Characters/Melusina/V2Test/`. Live `SK_Melusina` / `SK_MelusinaHair` **not** replaced. Level folder `Melusina_V2Test` **unsaved** | `Saved/Audit/melusina_v2_test_import.json` |
| Blender idle | Exported live NLA `idle_animation` on `character_rig`. First import was **meters on a cm skeleton** → collapsed pose. **Pulled off locomotion.** Speed 0 is mocap again | `Saved/Audit/melusina_blender_idle_wire.md` |
| Idle clip on disk | `A_BL_Melusina_Idle_Loop` (cm-scaled, **not** wired). `A_CAS_Melusina_Idle_Loop` = Quaternius try, **not** wired. `Idle_Serene` = manifest only, **no FBX** | Cascadeur folder + Inbox |
| Locomotion now | `BS_Melusina_Locomotion` speed 0 = `A_Melusina_Idle_Mocap_RootX`. Walk 180 / run 420 / sprint 630 unchanged. AnimBP Idle still plays the blendspace | live editor |
| Handpaint hunt | 1208 hits. Zero named lantern/wand/cross BaseColor. Never `T_Hatch_Cross` | `Saved/Audit/handpainted_texture_inventory_2026-08-12.md` |
| D1 harness | `BP_MelodiaBattleUI` first in `playtest_harness.py` | `Saved/Audit/harness_battleui_paths_2026-08-12.md` |
| GN prototype | `GN_BG_Prototype` on unsaved v22 | `Saved/Audit/gn_bg_prototype_2026-08-12.md` |

---

## What broke (do not repeat)

1. **Blender idle unit mismatch.** Live mocap translations are centimeters (`c_spine_02_x` local Y ≈ **-12.84**). Raw Blender FBX was meters (Y ≈ **-0.128**). Playing that on `SK_Melusina_Skeleton` collapses the mesh. A later `×100` scale pass made the numbers match; **do not re-wire until PIE proves the mocap idle looks normal**, then treat blender as a second pass.
2. **Quaternius UAL1 takes are not Lane A.** Same-size Inbox FBXs (`A_CAS_Melusina_Idle_Loop.fbx` etc.) are the split library. Provenance forbids sending them through `import_cascadeur_animation.py`. They failed retarget last time.
3. **`Idle_Serene` has no FBX.** Only `A_CAS_Melusina_Idle_Serene.manifest.json`. Do not hunt Inbox again.
4. **Interchange + large ARP SK.** `SK_MelusinaRigARP.fbx` (~33 MB) hung the editor ~15 min with an empty modal. V2 test script now skips the rig unless `--include-rig`.
5. **`BS_Melusina_Locomotion.uasset` was ReadOnly.** Clear `attrib -R` before saving sample changes.
6. **Do not** `blueprint_query:compile_blueprint`. Do not load skill BPs from Python (`D_DamageType` fatal). Do not spawn a second editor.

---

## Live processes (as of stop)

| Process | PID | Note |
|---------|-----|------|
| UnrealEditor | *(check `Get-Process UnrealEditor`)* | One editor. Monolith **9316**. Keep if continuing. |
| Blender 5.2 | **27644** | v22. MCP **9876**. Connect via **N → BlenderMCP**, not Live Bridge. |
| Tonight loop | **stopped** | Was 26352. |

Stage: `G:\EnvironmentPortfolio\BS_GodFile\Melodia_Portfolio_Stage_v22_ZenRebuild_WIP.blend` — unsaved.

---

## Do next (ordered)

1. **Owner in the already-open editor:** PIE / viewport-check that standing idle is the mocap clip (not collapsed). Then **Save `L_KaleidoNave`** if Cathedral + V2-test review strips should persist.
2. Socket Geometry Cache cine actor to Melusina head. Do not replace `SK_MelusinaHair`.
3. Optional second pass: blender idle `A_BL_Melusina_Idle_Loop` onto speed 0 **only after** mocap idle looks right.
4. T4 lean vow-cross FBX from v22. Never `T_Hatch_Cross`.
5. A1 stock battle: Morning → KaleidoNave, tag `melodia_smoke_encounter`, real Q/W/O/P.
6. B2 website plate dry-run (`stage_publish.py`, git push off). Undo LIQUID smoke cube before a beauty plate.
7. Do not save v22 without the env flag. Do not restart the 15m loop unless asked.

---

## Facts other agents must not re-hunt

- Komikaze `Textures: 0` = stills, not missing albedo.
- Magicians lantern = marketplace. Use ZenTrim on wand + StreetLamp.
- Flip cache lives on **G:** (`KitbashExport/flip_cache_melusina_waterhair`). 480 `.bobj`.
- Hair look is already `MI_Melusina_WaterHair` + `ABP_Melusina_WaterHair`. Flip is cine GC only.
- Cathedral kit is imported. Vow-cross mesh still missing.
- Live deform skeleton is `SK_Melusina_Skeleton` (465 bones, underscore names, cm). Blender ARP uses dotted names and meters.

---

## Paste-ready next-session prompts

Copy **one** block into a new chat. Claim the lane. One UnrealEditor.

### N0 — Coordinator (read this first)

```text
Pick up Docs/Handoffs/SESSION_REVIEW_NEXT_PROMPTS_2026-08-13.md.
Repo C:\EnvironmentPortfolio\BS_GodFile.
15m loop STOPPED — do not start another.
Locks: rhythm WORKED, Quill WORKED. One UnrealEditor the one running editor (`Get-Process UnrealEditor`). Blender 27644 / MCP 9876.
Do not save v22 without MELODIA_ALLOW_STAGE_SAVE=1.
Locomotion speed 0 is A_Melusina_Idle_Mocap_RootX (blender idle collapsed; not wired).
KaleidoNave umap still unsaved (CathedralKit_Review + Melusina_V2Test actors).
Do not spawn a second UnrealEditor. Do not reopen rhythm/Quill.
Owner does not need to close UE/Blender. If they quit UE, they must Save L_KaleidoNave first.
```

### N1 — Owner / A-idle: save KaleidoNave + prove mocap idle (EDITOR — exclusive)

```text
Lane N1. Use already-open UnrealEditor the one running editor (`Get-Process UnrealEditor`). Do not spawn a second editor.
1) Viewport or PIE: Melusina standing idle must be A_Melusina_Idle_Mocap_RootX, not collapsed.
   Blendspace: /Game/Melodia/Characters/Melusina/Animations/BS_Melusina_Locomotion speed 0.
2) If idle looks normal, File → Save Current (L_KaleidoNave) so CathedralKit_Review and Melusina_V2Test persist.
3) Do not replace SK_Melusina or SK_MelusinaHair. Do not wire A_BL_Melusina_Idle_Loop in this lane.
Evidence: Saved/Audit/kaleidonave_save_idle_check_<stamp>.md
```

### N2 — Optional blender idle retry (EDITOR — only after N1)

```text
Lane N2. Only if N1 confirmed mocap idle looks correct in PIE.
Clip already imported: /Game/Melodia/Characters/Melusina/Animations/Cascadeur/A_BL_Melusina_Idle_Loop
(cm-scaled; spine local Y should be ~-12.84). Replace ONLY speed-0 sample on BS_Melusina_Locomotion.
Keep walk/run/sprint. Keep A_Melusina_Idle_Mocap_RootX on disk.
Do not import Quaternius Inbox FBX. Do not import Idle_Serene (no FBX).
If pose collapses again, restore mocap to speed 0 immediately.
Evidence: Saved/Audit/melusina_blender_idle_retry_<stamp>.json
```

### N3 — Socket Flip Geometry Cache cine actor (EDITOR)

```text
Lane N3. Same editor the one running editor (`Get-Process UnrealEditor`). Do not spawn another.
Asset: /Game/Cinematics/MelusinaWaterHair/GC_MelusinaHairFlip_v22
Place a NEW GeometryCacheActor (cine). Socket to Melusina head.
Do NOT replace SK_MelusinaHair, MI_Melusina_WaterHair, or ABP_Melusina_WaterHair.
Save L_KaleidoNave if N1 has not already.
```

### N4 — T4 lean vow-cross FBX (Blender, no stage save)

```text
Lane T4. Blender PID 27644 already has v22. MCP 9876: N → BlenderMCP → Connect.
Lean-export a vow-cross mesh FBX. Never T_Hatch_Cross. Never Magicians lantern maps.
Do not save v22 unless MELODIA_ALLOW_STAGE_SAVE=1.
```

### N5 — A1 stock battle path (EDITOR — exclusive)

```text
Lane A1 from Docs/Handoffs/PARALLEL_LANES_2026-08-12.md.
One UnrealEditor. Rhythm + Quill LOCKED WORKED — do not reopen.
Route: L_MelusinaMorning → L_KaleidoNave. Tag melodia_smoke_encounter + StartBattle.
UI: BP_MelodiaBattleUI (D1 already patched harness). Real Q/W/O/P, not probe-only.
Do not compile_blueprint via MCP. Do not load skill BPs from Python.
```

### N6 — B2 website plate dry-run (Blender / tools)

```text
Lane B2. Undo MEL_Smoke_EffectMagic_LIQUID before a beauty plate.
stage_publish.py — git push OFF. Do not save v22 without MELODIA_ALLOW_STAGE_SAVE=1.
Website root via Tools/melodia_website_root.py.
```
