# P0 Phase 1 Closeout + Quill Trigger Repair — 2026-08-28

**Status:** Phase 1 **CLOSED**. Phase 2 unblocked — the trigger that gates every Quill pillar was
dead and is now live and proven in PIE.

**Evidence standard:** every claim below was verified by live re-read or log capture, not by a
tool's return value. Two things in this session returned success and had done nothing; see §5.

---

## 1. Phase 1 — the 08-27 content commit is no longer inert

`DA_MelodiaIntegrationConfig` extended with the 26-ID delta. Read live with
`blueprint_query get_cdo_properties`, merged, written, saved, re-read.

| Set | Before | After |
|---|---|---|
| `QuestIds` | 4 | **9** |
| `NarrativeFlagIds` | 5 | **18** |
| `DialogueRewardIds` | 6 | **11** |
| `SocialStatIds` | 1 | **3** |
| `TravelLevelIds` | 3 | **4** |

Asset grew 3,000 → 4,216 bytes.

All five orphan `.qsc` compiled to `.uasset` via `UQuillscriptAssetFactory` (they **import**, they
are not "compiled" in the build sense): `MelodiaQuillP0Playthrough`, `MelodiaQuillWardrobeEquip`,
`MelodiaQuillChoralSheepRecruit`, `MelodiaQuillSeaAboveCutscene`, `MelodiaQuillHarmonyAwakening`.
All six checked scripts load as class `QuillscriptAsset`. **12 of 12 `.qsc` now have a paired
`.uasset`** (was 7 of 12).

`Content/Python/Tests/test_qsc_allowlist_contract.py` — written earlier this session as a
deliberately-red guard — went **red → 4/4 OK** without being touched. That is the proof Phase 1
landed: every ID the four P0 scripts emit now survives `UMelodiaNarrativeSubsystem::IsAllowed`.

### Authoring defects fixed en route

- `flags.melusina.sorrow_seam_restored` → `flag.` — the plural prefix existed in **five** places,
  not one: the `.qsc`, `MelodiaP0ContentQuestsTests.cpp`, `specs/progression/melodia_p0_slice_quests.v1.json`,
  `specs/wardrobe/wardrobe_equip_p0_manifest.v1.json`, and `test_melusina_systems_contract.py`.
- Duplicate reward grants removed from **three** scripts (Wardrobe, ChoralSheep, SeaAbove). A
  standalone `melodia:reward:` grant fires before the `questcomplete`, and because reward grants are
  idempotent it made the transaction's reward leg an unobservable no-op.
- `test_p0_quests_and_content_contract.py` asserted **both** defects. Those assertions encoded the
  bug; updated to assert the corrected form. 8/8 pass.

---

## 2. The Quill trigger was dead — this was the real Phase 2 blocker

Phase 2 could never have run. There is **no Quillscript interpreter placed in any level**, and both
trigger Blueprints were broken:

| Blueprint | Chain | Placed | Verdict |
|---|---|---|---|
| `BP_KaleidoNaveArrivalTrigger` | complete and correct | **nowhere** (0 referencers) | one wire from working |
| `BP_MelodiaSirMelodiousMorningIntro` | parented to quarantined **MelodiaCore** | `L_MelusinaMorning` | spawns nothing at BeginPlay |

`BP_KaleidoNaveArrivalTrigger`'s graph held the whole correct sequence —

```
Delay 0.5 -> SpawnActor QuillscriptInterpreter -> Cast -> Set Interpreter -> Start(ScriptAsset)
```

— but it hung off a **custom** event named `EventBeginPlay` that nothing called, while
`Event BeginPlay`, `Event ActorBeginOverlap` and `Event Tick` were all explicitly **disabled**
("This node is disabled and will not be called"). Someone stubbed it and never re-enabled it.

### The repair

1. Added `QuillTriggerVolume` (`SphereComponent`, radius 250). Defaults were already correct —
   `CollisionEnabled: QueryOnly`, `CollisionProfileName: OverlapAllDynamic`, Pawn → `ECR_Overlap`,
   `bGenerateOverlapEvents: True`. No collision config needed.
2. `Event ActorBeginOverlap`: `EnabledState` **Disabled → Enabled**.
3. Connected its `then` → the existing `Delay`.
4. Promoted the hardcoded script to an instance-editable variable **`QuillScriptToPlay`**
   (`object:QuillscriptAsset`, category `Melodia|Narrative`, CDO default `MelodiaQuillSmoke`) and
   wired a `Get` into the `Start` node's `ScriptAsset` pin.

Graph fingerprint `a2fe4a45fb93…` → `dc59e83587bb…`, connections 9 → 10, node count unchanged.
Compile clean, 0 errors / 0 warnings.

**Step 4 is what makes this a loop rather than a pile** — one trigger Blueprint now drives all five
scripts by per-instance assignment, instead of five near-duplicate Blueprints.

### Live proof

Placed as `Morning_QuillTrigger_P0` in `L_MelusinaMorning`, 400 uu ahead of `Morning_PlayerStart`,
saved to the WP external actor package, then reproduced **from the saved placement**:

```
✔  ❰ QuillscriptInterpreter0 ❱   Script 'MelodiaQuillSmoke' started.
MELUSINA_LOOP_QUILL_PLAY  interpreter=QuillscriptInterpreter_0  dialog=04F9FF14…
MELODIA_INPUT_PUSH        context=EMelodiaInputContext::Dialogue  depth=1
MELODIA_INPUT_CONTEXT     None -> Dialogue  (movement=0 interact=0 save=1)
```

The script starts **and** the input stack pushes to Dialogue with movement locked — the UI loop
engages, which is the seam Phase 2's four pillars all run through.

**PIE smoke on `MelodiaIntegrationMap`: PASS** — `ok: true`, 38 samples / 12.08 s, 0 Blueprint
Runtime Error and 0 Accessed None across active runtime *and* teardown.

---

## 3. Known-open, carried forward

- The trigger fires on overlap. A pawn that **spawns inside** the volume gets no begin-overlap
  transition — this is why the first placement (on top of `Morning_PlayerStart`) appeared inert.
  Placement must be offset from spawn.
- `in_viewport=false` on `MELUSINA_LOOP_QUILL_PLAY` — the dialog widget is created but not added to
  the viewport in this path. Not chased.
- Phase 2's four pillars are not yet driven end to end. The trigger is the prerequisite and is now
  in place.

---

## 4. Sea Above (side lane, same session)

`LV_SeaAbove_Prototype` is now the canonical World Partition map — the old non-WP map (which
carried integration-map battle actors, not Sea Above content) and both redirectors were deleted,
and the WP map was renamed into the canonical name so **all 9 text references resolved with zero
edits**. 14 external actors carried over intact.

Content added: `SeaAbove_InfiniteOcean_Canopy` (native `AOceanologyInfiniteOcean` — the
`BP_OceanologyInfiniteOcean` wrapper is **deprecated** and `SpawnActor` refuses it, which is why
placement had been failing), `SeaAbove_PlayerStart`, `SeaAbove_FalseOcean_Plane` (plain static mesh
+ `MI_SeaAbove_FalseOcean`, deliberately **not** a second Oceanology ocean), 12 floating islands
(24 actors, Megascans, z 380–1820), and four Data Layers.

`OceanologyWaterVolume` had no `OceanologyWater` assigned, so `Init()` bailed before setting
`bWaterVolume` — that is why swimming was dead. Assigned; `bWaterVolume` now `True`. The volume is
still a 2 m cube and must be scaled to the swimmable region.

---

## 5. Tooling traps proven this session — read before repeating

1. **Never hold a PIE `UObject` reference in Python across `stop_pie`.** A retained
   `get_editor_property('Script')` handle pinned the PIE world via `FPyReferenceCollector` and
   asserted `PlayLevel.cpp:553` ("from PIE level still referenced"), killing the editor. Read to a
   string; drop the handle.
2. **`material_query delete_expressions` crashes the editor** — asserts `!IsRooted()` at
   `MonolithMaterialActions.cpp:9245`. Orphan nodes by rewiring instead of deleting.
3. **`blueprint_query save_asset` fails silently on read-only `.uasset`.** Run
   `attrib -R <path>` first. Hit twice.
4. **`EditorAssetLibrary.delete_asset` returns `True` without deleting** when source control is
   enabled. Verify with `does_asset_exist`, never the return value.
5. **`blueprint_query set_cdo_properties` reports as `would_apply` / `would_modify` even on a real
   write.** It looks like a dry run and is not. Confirm by re-reading the CDO.
6. **`material_query preview_texture` returns solid white for known-good textures.** Not usable as
   evidence of texture content.
7. **World Partition placement is invisible to name-grep.** Actors live in `__ExternalActors__`, not
   the `.umap`. Any "unreferenced" verdict on a WP-placed asset must be re-checked with
   `AssetRegistry.get_referencers`.

---

## 6. Next

1. Assign `QuillScriptToPlay` per pillar and place a trigger for each of the four P0 scripts.
2. Drive the P0 playthrough victory branch; verify atomic commit order and that Quill resumes once.
3. Wardrobe equip → canonical save → **full process restart** → load → `wardrobe_equip_roundtrip`.
4. Record ledger rows. No row, no gate.

Known hazard for step 2: killing the player unit still crashes the editor on the
`AnimMontage.h:781` assert. Use the flee path for a second terminal outcome.
