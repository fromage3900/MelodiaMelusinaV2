# P0 Closeout — Loose-End Review and Updated Plan

> **2026-08-28 final C++ amendment:** the water `FGameplayTag` migration is complete, the
> `MelodiaShader` virtual path is registered, the closed-editor Development Editor build passes,
> and `Melodia.Wardrobe.EquipRoundtrip` passes with a real cataloged accessory. The focused test is
> preparation evidence only; the save/restart/material and Glide gates remain open.

**Date:** 2026-08-28
**Supersedes as the P0 router:** `Docs/Handoffs/P0_BATTLE_UI_CLOSEOUT_HANDOFF_2026-08-27.md` (still the
evidence record for the two gates it closed).
**Method:** offline audit of the ledger, the allowlist asset, the four newly authored `.qsc` scripts,
the wardrobe/rhythm/PCG source, and the working tree. No editor was running, so nothing here is a
live claim.

---

## 1. What is actually closed

| Gate | State | Evidence |
|---|---|---|
| `battle_integration_map` | **pass** | 2026-08-27 live PIE, all four terminal outcomes, Quill resumed exactly once each |
| `hud_single_writer` | **pass pending owner decision** | runtime widget identity proven; two vestigial vars await a retire/keep call |
| `runtime`, `save_load`, `repeat_consume`, `package_launch` | bounded historical pass | captured baselines only (08-13/08-14), not current certification |
| P0-NARR-01 | closed | atomic quest+reward+flag proven live on the victory branch |

---

## 2. Loose ends found

### A. The gate ledger no longer matches the truth

`Saved/gate_ledger.json` ends at **2026-08-22**. The two gates closed on 08-27 exist only in
`Docs/P0_TASK_LEDGER.json` and handoff prose. `Saved/gate_ledger_report.md` still prints
`battle_integration_map | fail`, and it is the file the site sync publishes. Anything reading the
ledger is currently being told P0 is further behind than it is.

### B. The four new P0 scripts cannot run — two independent reasons

Commit `f78f00f8` authored `MelodiaQuillP0Playthrough`, `MelodiaQuillWardrobeEquip`,
`MelodiaQuillChoralSheepRecruit` and `MelodiaQuillSeaAboveCutscene`. Both blockers below are
invisible to the tests that were run, because those tests validate the JSON spec packages, not the
runtime path.

**B1 — no compiled assets.** All four exist only as `.qsc`. Every playable script in that folder has
a paired `.uasset`; these four (and `MelodiaQuillHarmonyAwakening.qsc`) do not. `Quill.play_script`
takes a loaded asset, so none of them can be started.

```
MelodiaQuillSmoke.qsc              + MelodiaQuillSmoke.uasset     <- playable
MelodiaQuillP0Playthrough.qsc      (no .uasset)                   <- inert
MelodiaQuillWardrobeEquip.qsc      (no .uasset)                   <- inert
MelodiaQuillChoralSheepRecruit.qsc (no .uasset)                   <- inert
MelodiaQuillSeaAboveCutscene.qsc   (no .uasset)                   <- inert
```

**B2 — every new ID is outside the allowlist.** `UMelodiaNarrativeSubsystem::IsAllowed` rejects any
ID absent from `DA_MelodiaIntegrationConfig`. The live asset contains, in full:

| Set | Contents |
|---|---|
| `QuestIds` | `melodia_q_echo_01/02/03`, `melodia_smoke_quest` |
| `NarrativeFlagIds` | `melodia_q_echo_0N_complete`, `melodia_smoke_complete`, `melodia_battle_won` |
| `DialogueRewardIds` | `melodia_reward_dawn_veil / dreamweave_shawl / solstice_drum / star_charm / tuning_fork`, `melodia_smoke_reward` |
| `SocialStatIds` | `melodia_harmony` |
| `EncounterIds` | `melodia_smoke_encounter`, `Encounter_CrystalShard` |
| `TravelLevelIds` | `L_KaleidoNave`, `L_MelusinaMorning`, `melodia_integration_map` |
| `StockSkillRhythmIds` | `cadence_strike`, `crescendo_wave`, `downbeat_break`, `resonant_arc` |

Of everything the four scripts emit, only `melodia_smoke_encounter` and `melodia_harmony` are
present. Missing, and therefore rejected at runtime:

- **Quests:** `quest.first_dream`, `quest.wardrobe.equip_outfit`, `quest.companion.choral_sheep`, `quest.cutscene.sea_above`
- **Flags:** `flag.first_dream.quest.completed`, `flag.p0.playthrough.completed/attempted/fled`, `flag.wardrobe.outfit_equipped`, `flag.wardrobe.equip_completed`, `flags.melusina.sorrow_seam_restored`, `flag.companion.choral_sheep_recruited`, `flag.companion.choral_sheep_completed`, `flag.cutscene.sea_above_witnessed`, `flag.sea_above.membrane_pulse_active`, `flag.cutscene.sea_above_completed`
- **Rewards:** `reward.first_resonance_echo`, `reward.wardrobe.first_outfit`, `reward.companion.choral_sheep`, `reward.cutscene.sea_above_memory`
- **Stats:** `melodia_elegance`, `melodia_resonance`
- **Travel:** `/Game/EnvSandbox/Monoliths/SeaAbove/Prototype/LV_SeaAbove_Prototype`

Two authoring defects visible while reading them:

- `flags.melusina.sorrow_seam_restored` uses the plural prefix `flags.`; every other flag uses
  `flag.`. Fix the script, not the allowlist.
- `MelodiaQuillWardrobeEquip` grants `reward.wardrobe.first_outfit` on line 28, then names the same
  reward as the reward leg of the `questcomplete` on line 36. Reward grants are idempotent, so the
  transaction's reward leg is a guaranteed no-op and can never be observed. Give the `questcomplete`
  its own reward ID, or drop the line-28 grant.

Non-blockers confirmed while checking: the `item` verb **is** registered
(`Handlers.Add(TEXT("item"), …)`), and `LV_SeaAbove_Prototype.umap` **does** exist on disk.

### C. Gates still genuinely open

- **`music_world_key`** — `UMelodiaPCGNarrativeChallengeBridgeComponent` is source-only. A content
  reference search returns nothing but two unrelated Python files: **no level or Blueprint attaches
  it to a host actor.** Level wiring is the whole blocker; no code is needed.
- **`rhythm_owner` / `rhythm_grade_to_result`** — the source seam is already single-path and
  correct: `UseSkillWithRhythm` → `ApplyRhythmAttackScalar()` → `InvokeStockUseSkill`, with the
  scalar folded into attacker stats *before* dispatch. What is unproven is runtime: that the battle
  UI actually calls `UseSkillWithRhythm` rather than stock `UseSkill`, and that a real-key grade
  moves the number. Both need a live battle, which per the 08-27 handoff means a Quill interpreter
  must be running.
- **`wardrobe_equip_roundtrip` / `wardrobe_gameplay_hook`** — better positioned than the docs say.
  `BP_Melusina` is **deprecated** (Decision 044); the live pawn `BP_MelusinaJRPGCharacter` already
  carries `MelodiaWardrobeComponent`, `MelodiaTraversalComponent`, `MelusinaSorrowSeamComponent` and
  the V2 body/shirt/skirt/boots/accessory meshes. `FMelodiaNarrativeRecord` already has
  `SaveGame`-tagged `EquippedCosmeticIds` (Decision 043, additive v3). This should be provable with
  no new code — only a live equip → save → process restart → load.
- **`static_gates`** — `Docs/T3D_Baseline/verify_baseline.py` talks to Monolith over HTTP and dies
  with connection-refused when the editor is down, so this gate **cannot be checked offline at all**.
  The two material drifts are against a baseline frozen **2026-08-07**
  (`M_Master_Simple_Universal` 25→26 nodes, `M_Master_Toon_Landscape_HeightBlend` 290→304 nodes).
  Owner call: re-freeze if the edits were intended, revert if not.

### D. Known defects carried forward

| Defect | Impact |
|---|---|
| Player death asserts `AnimMontage.h:781` and kills the editor ~10s after `SetHP(0)` | Defeat result lands first, so it does not block the gate, but it makes repeated defeat testing impractical. Prefer the flee path. |
| `LiveResultsWidgetPath` is empty and cannot be set from ini (no `config` specifier) | Needs the `Initialize()` backfill mirrored from `MelodiaBattleWidgetPath`; **requires a rebuild** |
| Quill background panel never renders | No `.qsc` in the project calls `Background()`/`Bg()` at all; separately the plugin calls `ShowBackgroundBox()` twice at `QuillscriptInterpreter.cpp:438-439`, where the second is almost certainly meant to be `ShowSelectionBox()` |

### E. Working-tree hygiene

- 27 modified + ~30 untracked paths sitting uncommitted.
- **`BS_GodFile.uproject` has one real change buried in whole-file churn.** The diff reads
  331 insertions / 327 deletions; ignoring whitespace it is a UTF-8 **BOM added**, a full reindent,
  and the actual change: `HoudiniEngine` **enabled**. Enabling an unaudited binary plugin changes
  build and cook. The BOM and reindent should be reverted regardless.
- The whole `Plugins/HoudiniEngine/` tree is untracked.
- Four zero-byte stray files at repo root — `Checking`, `Installing`, `Set`, `uv` — all timestamped
  2026-08-27 22:02, consistent with a PowerShell redirect accident. Safe to delete.
- Choral Sheep FBXs untracked, including the unskinned source mesh.

### F. Asset blockers (owner-side, unchanged)

- No slime or Cosmic Reaver meshes exist in UE Content. The MelodySlime variant recipe is written
  and executes the moment meshes land.
- `Skin_Sheep_ZSpheres2` has **0 vertex groups**. The owner's blendshape-driven approach is the
  agreed unblock.
- Unresolved map conflict: `L_ChoralSheep_Prototype` vs `MelodiaIntegrationMap`.

---

## 3. Plan

Sequenced by dependency. Phase 1 is the one that matters — without it the entire 08-27 content
commit is decorative.

### Phase 0 — Hygiene (no editor, ~15 min)

1. Delete the four zero-byte root files: `Checking`, `Installing`, `Set`, `uv`.
2. Restore `BS_GodFile.uproject` from HEAD, then re-apply **only** the `HoudiniEngine` entry by hand
   — no BOM, no reindent. Confirm with the owner that HoudiniEngine should ship-enable at all; if it
   is editor-only tooling it should not be enabled in a cooked target.
3. Decide tracked-vs-ignored for `Plugins/HoudiniEngine/` and the Choral Sheep FBXs.
4. Record the 08-27 gate rows into `Saved/gate_ledger.json` and regenerate
   `Saved/gate_ledger_report.md`, so the published ledger stops contradicting the handoff.

### Phase 1 — Make the authored content real (editor, ~1 h)

5. **Extend `DA_MelodiaIntegrationConfig`** with the full missing-ID list from §B2. Read it with
   `blueprint_query get_cdo_properties` — `melodia_config_get_allowlist` returns stale fixture data
   and will lie to you.
6. **Fix the two authoring defects first**, before compiling: the `flags.` → `flag.` prefix, and the
   duplicated `reward.wardrobe.first_outfit`.
7. **Compile the five `.qsc` files to `.uasset`** — the four new ones plus
   `MelodiaQuillHarmonyAwakening` — and confirm each loads via `unreal.load_asset`.
8. Add an offline contract test asserting that *every* ID emitted by any `.qsc` appears in the
   allowlist asset. This class of bug shipped once and is cheap to make impossible.

### Phase 2 — Live-prove the four pillars (editor + PIE)

Drive each through the 08-27 procedure: `Quill.play_script` → `get_options_set(-1)` →
`option_selected` → `next()`, remembering that post-battle dialogue does not self-advance.

9. **P0 Playthrough** — victory branch end-to-end; verify the atomic commit order and that Quill
   resumes exactly once. Use the flee path if a second terminal outcome is needed (defeat crashes).
10. **Wardrobe equip** → `wardrobe_equip_roundtrip`: equip, canonical save, **full process restart**,
    load, confirm outfit and materials restore.
11. **Glide** → `wardrobe_gameplay_hook`: one equipped item, one observable capability.
12. **Choral Sheep** — script-side proof only; the companion stays `PRESENTATION_ONLY` until the
    mesh is skinned.
13. **Sea Above** — travel, membrane pulse, droplets. Requires the travel path in `TravelLevelIds`.

### Phase 3 — The remaining rhythm gates

14. `rhythm_owner`: prove at runtime that exactly one path reaches stock damage — confirm the battle
    UI calls `UseSkillWithRhythm`, not stock `UseSkill`.
15. `rhythm_grade_to_result`: real-key timing changes a stock result, progression never blocks, Quill
    resumes once.
16. `music_world_key`: attach `UMelodiaPCGNarrativeChallengeBridgeComponent` to a host actor in a
    level, then prove one Piano phrase commits one idempotent typed result and visibly opens a route.

### Phase 4 — Closeout

17. Owner decision: retire the two vestigial `melodiaBattleUI` / `MelodiaUI` vars → `hud_single_writer`
    fully closed.
18. Owner decision on the two material drifts → re-freeze or revert → rerun the full static chain
    with the editor **up** (it cannot run otherwise) → `static_gates`.
19. Fix `LiveResultsWidgetPath` by mirroring the `MelodiaBattleWidgetPath` backfill in `Initialize()`;
    bundle it with any other C++ change so the closed-editor rebuild is paid once.
20. Repackage and rerun `package_launch` against current content — the standing pass is an 08-14
    baseline and 150+ commits stale.
21. Full 20–30 minute golden run, then record the ledger rows.

### Deferred — not P0

Slime and Cosmic Reaver meshes; Choral Sheep skinning; the Quill background-panel render path and the
`ShowBackgroundBox` double-call; the `AnimMontage.h:781` death crash; itch tooling (no `butler`, no
`.itch.toml` — first upload is manual, and `deploy/package_game.ps1` still contradicts Decision 004).

---

## 4. The one thing to do first

**Phase 1, step 5.** Four scripts, four manifests, a spec package, a C++ automation test and 100+
green contract assertions were authored on 08-27 against IDs the runtime will refuse. Nothing in
Phase 2 can start until the allowlist and the compiled assets exist.
