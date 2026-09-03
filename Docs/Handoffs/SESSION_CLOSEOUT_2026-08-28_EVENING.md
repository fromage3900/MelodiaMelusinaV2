# Session Closeout — 2026-08-28 evening

> **Final amendment:** this handoff captured an intermediate broken state. The tree now builds,
> the `FGameplayTag` migration and `/Melodia` shader mapping are complete, and
> `Melodia.Wardrobe.EquipRoundtrip` passes. Current evidence is in
> `SESSION_CLOSEOUT_2026-08-28_FINAL_CPP_RIDER.md`; statements below that the build is broken,
> shaders are unreachable or wardrobe tests never ran are historical only.

Continues `P0_PHASE1_CLOSEOUT_AND_QUILL_TRIGGER_2026-08-28.md`, which covers Phase 1 and the Quill
trigger repair. This document covers what happened after those, and the three things that are
**still open at handoff**.

**Branch:** `feature/p0-phase1-allowlist-quill-trigger` (4 commits, not merged to main).

---

## 1. State at handoff — read this first

| Thing | State |
|---|---|
| P0 Phase 1 | **CLOSED** — allowlist +26 ids, 12/12 `.qsc` playable, contract test 4/4 |
| Quill trigger | **REPAIRED + PIE-proven**, four pillar triggers placed and saved |
| **The C++ tree** | **DOES NOT COMPILE** — see §3. A build is in flight to fix it. |
| Narrative use-after-free | **FIXED in source, not yet built** — see §2 |
| Sea Above docs branch | **MERGED** (`67ed8a33`) |

**Do not trust any PIE result taken before that build succeeds.** The running editor DLL was from
08-28 03:06; the `FGameplayTag` migration landed at 05:27. Every PIE run after 05:27 tested
pre-migration binaries.

---

## 2. Crash fix — async use-after-free in the narrative path

The owner hit this live while walking the new triggers:

```
EXCEPTION_ACCESS_VIOLATION reading address 0x000000030000032a
UMelodiaNarrativeSubsystem::HandleQuillNotification::<lambda_1>::operator()
  [MelodiaNarrativeSubsystem.cpp:1053]
MelodiaOllamaValidation::ValidateMessageAsync::<lambda_1>::operator()
  [MelodiaOllamaValidation.cpp:49]
```

**Cause.** `HandleQuillNotification` fires a fire-and-forget Ollama validation over HTTP and the
callback captured raw `this`. `UMelodiaNarrativeSubsystem` is a `GameInstanceSubsystem`, so it dies
when PIE ends — but the HTTP request is still in flight. The response lands afterwards and
dereferences freed memory. Every Quill notify queues one of these, so any notify + PIE-stop race
could hit it.

**Fix.** Capture `TWeakObjectPtr<UMelodiaNarrativeSubsystem>` and bail if the subsystem is gone.
Applied at `MelodiaNarrativeSubsystem.cpp:~1051`. **Not yet compiled** — blocked behind §3.

**Worth knowing:** `MelodiaOllamaValidation.cpp` already guards this exact hazard, with a
2026-07-31 comment stating that a reference would dangle. The helper was careful; the caller was
not. It was the only async call site in the file — the other three `[this, …]` captures are
synchronous local lambdas and are safe.

---

## 3. The tree does not compile — half-landed FGameplayTag migration

Commit `694b7250` (08-28 05:27, "feat(integration): FGameplayTag migration, …") moved
`UMelodiaWaterGameplaySubsystem`'s public API from `FName` to `FGameplayTag` but left callers —
and the subsystem's **own internal storage** — on `FName`. ~20 errors across six files:

```
MelodiaWaterGameplaySubsystem.cpp:205,207,334,341   TSet<FName>::Contains( FGameplayTag )
MelodiaPCGWaterGameplayBridgeComponent.cpp          6 errors
MelodiaWaterGameplayControllerComponent.cpp         6 errors
MelodiaWaterGameplayDeviceAnchor.cpp                2 errors
MelodiaWaterBuoyancyComponent.cpp                   1 error
MelodiaWaterPlatformMotionComponent.cpp             1 error
MelodiaWardrobeAutomationTests.cpp:11               C1083 missing GameFramework/GameInstance.h
```

The subsystem is inconsistent with itself: `GetNodeState` takes `FGameplayTag` while the set it
queries is `TSet<FName>`.

**Sequencing note.** `Docs/P0_COMPLETE_REVIEW_AND_EXPANSION_PLAN_2026-08-28.md` schedules this as
**"Phase 5 — FGameplayTag Completion (post-P0)"**. The plan was right; half of it shipped early and
took the build with it.

**In flight at handoff:** a delegated agent is completing the migration *toward* `FGameplayTag`
(not reverting), fixing the wardrobe test include, and building to green. If it stalls, the
decision to re-take is: complete forward, or revert `694b7250` back to post-P0 as planned.
Completing forward was chosen because reverting a partially-landed API change across six files is
the riskier direction.

**The wardrobe consequence:** `MelodiaWardrobeAutomationTests.cpp` is one of the files that does
not compile. It contains the four tests that would prove the two open wardrobe gates —
`FMelodiaWardrobeEquipRoundtripTest` and `FMelodiaWardrobeGameplayHookTest`. They have never run.

---

## 4. MelodiaShader module — compiles, but shaders are not yet reachable

The new `Source/BS_GodFile/MelodiaShader/` module (6 `.ush` files) is correctly registered:
`BS_GodFile.uproject` line 13, `BS_GodFile.Build.cs` line 26. The in-flight build is its first
compile.

**Gap: no virtual shader path mapping.** `StartupModule()` is empty and nothing calls
`AddShaderSourceDirectoryMapping`. `MelodiaShader.Build.cs` uses `PrivateIncludePaths` for
`Shaders/`, but that is a **C++ include path for UBT**, not a shader virtual path — UE resolves
`.ush` includes through its own virtual filesystem.

Consequence: Rider indexes and validates all six files today (filesystem-based, so the
`melodia-shader-rider` skill's claim holds), and the module compiles — but a Custom node doing
`#include "/Melodia/MelodiaInkCommon.ush"` will fail to resolve. Needs, in `StartupModule`:

```cpp
AddShaderSourceDirectoryMapping(TEXT("/Melodia"),
    FPaths::Combine(FPaths::ProjectDir(), TEXT("Source/BS_GodFile/MelodiaShader/Shaders")));
```

Minor drift: the Build.cs comment lists `MelodiaInkHalftone.ush`, which is not on disk. Six files,
not seven.

---

## 5. Convergence hazard — three copies of the Nikki rim HLSL

While `MelodiaNikkiCommon.ush` was being authored (7 Nikki bodies extracted from
`expand_nikki_features.py`), this session independently added the Nikki rim family to
`M_Niagara_MelodiaFlipbook` as **inline `MaterialExpressionCustom` nodes** — `SpriteRim` (radial
falloff) and `DreamRimBand` (cycled band), plus `bNikkiHero` / `bDreamRim_Active`, matching the
`master_column_scheme.py` "10 | Nikki Rim & Glow" column.

That is now: the Python source, the new `.ush`, and inline material nodes — three copies, no stated
owner. The `.ush` should win. Once §4's mapping exists, those Custom nodes should `#include` from
`/Melodia/MelodiaNikkiCommon.ush` instead of carrying their own bodies.

This is the same antipattern documented in `VFX_NIAGARA_FLIPBOOK_SYSTEM_PLAN_2026-08-28.md` §2 for
flipbooks (engine SubUV vs material-side atlas math). Worth settling before it calcifies.

---

## 6. Corrections to existing docs

- **`P0_COMPLETE_REVIEW_AND_EXPANSION_PLAN_2026-08-28.md` §4 is wrong about RiderLink.** It says
  "Not Yet Installed" and instructs cloning into `Plugins/Developer/RiderLink/`. RiderLink **is**
  installed engine-side at `Engine/Plugins/Marketplace/Developer/RiderLink` and loads every
  session (`Mounting Engine plugin RiderLink`; `UnrealEditor-RD.dll` and
  `UnrealEditor-RiderLink.dll` both load). Following that instruction would create a second
  RiderLink and a module conflict. Its three "need to install" features already work.
- **`RIDER_UE58_INTEGRATION_ROADMAP_2026-08-28.md` is one step stale** — its stated Next Action is
  Phase 1 step 5, which closed this session. Its "IMPLEMENTED" quick wins verified true:
  `TRACE_CPUPROFILER_EVENT_SCOPE` now in 6 files, qodana 73 lines on `QDJB`.

---

## 7. Sea Above — merged and extended

`origin/docs/sea-above-system-shader-breakdowns-2026-08-26` merged as `67ed8a33` (docs only, 5
files) — the 477-line system/shader breakdown, the **Shorelistener P0 outfit** concept board, the
Melusina character board, and two diagrams. The Shorelistener board is concept art; no `Cos_*`
cosmetic exists for it. The P0 wardrobe pillar still runs on `item.outfit.melusina_v2` → Glide.

Level work this session (all gitignored under `Content/*`, on disk only): `LV_SeaAbove_Prototype`
canonicalised as the WP map, native `AOceanologyInfiniteOcean` placed (the BP wrapper is
**deprecated** and `SpawnActor` refuses it), false-ocean plane, PlayerStart, 12 floating islands,
four Data Layers, and `OceanologyWaterVolume` finally given its `OceanologyWater` reference so
`bWaterVolume` is `True` (this is why swimming was dead). The volume is still a 2 m cube and must
be scaled to the swimmable region.

---

## 8. Next, in order

1. **Confirm the build went green.** Nothing below is meaningful until it does.
2. Add the shader virtual path mapping (§4) — same closed-editor window, or pay a second rebuild.
3. Run the four wardrobe automation tests now that they compile — they may close
   `wardrobe_equip_roundtrip` and `wardrobe_gameplay_hook` without live PIE.
4. Walk the four pillar triggers in `L_MelusinaMorning` + `LV_SeaAbove_Prototype`, drive the P0
   playthrough victory branch, record ledger rows.
5. Settle the Nikki HLSL owner (§5).

**Standing hazards:** killing the player unit crashes the editor on `AnimMontage.h:781` — use the
flee path for a second terminal outcome. And the trigger fires on overlap, so a pawn that *spawns
inside* the volume gets no begin-overlap transition; placement must be offset from spawn.

---

## 9. Tooling traps proven this session

1. **Never hold a PIE `UObject` in Python across `stop_pie`** — `FPyReferenceCollector` pins the
   world and asserts `PlayLevel.cpp:553`. Killed the editor once.
2. **`material_query delete_expressions` crashes the editor** — asserts `!IsRooted()` at
   `MonolithMaterialActions.cpp:9245`. Orphan by rewiring instead. Killed the editor once.
3. **`save_asset` fails silently on read-only `.uasset`** — `attrib -R` first. Hit three times.
4. **`EditorAssetLibrary.delete_asset` returns `True` without deleting** under source control.
   Verify with `does_asset_exist`.
5. **`set_cdo_properties` reports `would_apply` / `would_modify` on real writes** — looks like a
   dry run, isn't. Re-read the CDO.
6. **`preview_texture` returns solid white for known-good textures** — not evidence.
7. **World Partition placement is invisible to name-grep** — actors live in `__ExternalActors__`,
   not the `.umap`. Re-check any "unreferenced" verdict with `AssetRegistry.get_referencers`.
8. **`unreal.Rotator(roll, pitch, yaw)`** — not (pitch, yaw, roll). Wrong order sends the viewport
   camera straight up.
