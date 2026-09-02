# Wardrobe-Gated Orbital Traversal — BS_GodFile UE5.8

**Date:** 2026-08-27  
**Status:** Spec only (no runtime proof)  
**Engine:** UE 5.8 — MeshTerrain-only, NO ALandscape  
**Related:** `Content/Python/build_pcg_hero_orbital_rings.py` · `Plugins/MelodiaWardrobe/Source/MelodiaWardrobe/Public/MelodiaWardrobeSubsystem.h` · `Source/BS_GodFile/MelodiaIntegration/MelodiaPCGNarrativeChallengeBridgeComponent.h` · `Source/BS_GodFile/MelodiaIntegration/MelodiaNarrativeSubsystem.h` · `Source/BS_GodFile/MelodiaIntegration/MelodiaNarrativeTypes.h` · `Content/Python/pcg_scale_world_pipeline.py` (`WP_CELL_SIZE_CM=25600`) · Houdini fallback HDA `hda/SpaceTraversal_OrbitalRings_1.0.hda`  
**Pillars:** `Quill -> Battle -> Wardrobe -> Music-as-key` (AGENTS.md)

---

## 1. Goal

Wardrobe gates **space traversal**, not just cosmetics.

- Orbital rings `PCG_Hero_OrbitalRings` (PCG fallback for `SpaceTraversal_OrbitalRings`, 2 rings x 12 platforms = 24, `stable_chunk_seed` deterministic, `FPCGPoint.Seed`) remain deterministic geometry. Whether the player can **use** a ring is gated by outfit ownership/equip + optional challenge completion.
- Outfits carry gameplay meaning (pillar 3). Equipping `SpaceVeil` does not merely re-skin — it unlocks the outer ring's platforms, bridges, and collision. No outfit = ring is visible as dressing or hidden, but never traversable.
- No second wardrobe authority. `UMelodiaWardrobeSubsystem` remains the single writer for `OwnedCosmeticIds` / `EquippedCosmeticIds`; narrative flags remain on `FMelodiaNarrativeRecord`. The gate is a **reader** of both.

Non-goal: per-frame wardrobe tick, quantum hit detection, or a new pawn. Classical equip/flag check only.

---

## 2. Outfit -> Ring Mapping — Data Table Design

### 2.1 Row struct

New row type for a `UDataTable` (or `UDataAsset` map — table preferred for designer iteration):

`Source/BS_GodFile/MelodiaIntegration/MelodiaOrbitalWardrobeGateTypes.h` (proposed)

```cpp
UENUM(BlueprintType)
enum class EOrbitalGateUnlockType : uint8
{
    Immediate,   // outfit equipped => gate opens this session
    OnChallenge  // outfit equipped + RequiredChallengeId completed => gate opens
};

USTRUCT(BlueprintType)
struct FOrbitalWardrobeGateRow : public FTableRowBase
{
    GENERATED_BODY()

    // Stable id for save/Quill/metrics: orbital.gate.ring1, orbital.gate.core
    UPROPERTY(EditAnywhere, BlueprintReadWrite) FName GateId;

    // Must match catalog row CosmeticId in /MelodiaWardrobe/Catalog/DA_MelodiaCosmeticCatalog
    // Validated via FindGrantableRecord path; unknown id => gate never opens (fail closed).
    UPROPERTY(EditAnywhere, BlueprintReadWrite) FName RequiredOutfitId;

    // 0-based ring index in build_pcg_hero_orbital_rings.py layout (0 = inner, 1 = outer, 2 = core if added)
    UPROPERTY(EditAnywhere, BlueprintReadWrite) int32 RingIndex = 0;

    // Optional challenge that must be completed for OnChallenge gates.
    // Example: challenge.orbital.ring0.completed (set via CommitWorldChallenge)
    UPROPERTY(EditAnywhere, BlueprintReadWrite) FName RequiredChallengeId;

    UPROPERTY(EditAnywhere, BlueprintReadWrite) EOrbitalGateUnlockType UnlockType = EOrbitalGateUnlockType::Immediate;

    // Quill localisation key shown when gate is blocked. Not a free string.
    UPROPERTY(EditAnywhere, BlueprintReadWrite) FName FailMessageKey;
};
```

Asset path (proposed): `/Game/MelodiaIntegration/Config/DT_OrbitalWardrobeGates`

- `GateId` is namespaced `orbital.gate.*` to avoid colliding with travel/quest ids.
- `RequiredOutfitId` is `FName(CosmeticId)`, not a mesh path. Keeps the wardrobe catalog as the single appearance authority.
- `RequiredChallengeId` is `FName(ChallengeId)` consumed by `CommitWorldChallenge` / `IsWorldChallengeCompleted` — no duplicate completion tracking.

### 2.2 Example table (3 rows)

| GateId | RequiredOutfitId | RingIndex | RequiredChallengeId | UnlockType | FailMessageKey | Effect |
|---|---|---|---|---|---|---|
| `orbital.gate.ring0` | `Cos_StoneCourt_Dress` (or `NAME_None` = free) | 0 | `NAME_None` | `Immediate` | `quill.orbital.ring0.locked` | Inner ring always usable; Stone Court dress satisfies lore but gate is free for proof |
| `orbital.gate.ring1` | `Cos_SpaceVeil` | 1 | `NAME_None` | `Immediate` | `quill.orbital.ring1.need_spaceveil` | Outer ring + `PCGEx orbital ring 1 rail` hidden/disabled until SpaceVeil equipped |
| `orbital.gate.core` | `Cos_Muse` | 2 (core) | `challenge.orbital.ring1.completed` | `OnChallenge` | `quill.orbital.core.need_muse_and_ring1` | Core orrery unlocks only when Muse equipped AND ring-1 challenge flag true |

Tuning note: Ring0 row exists so every ring has a gate row (auditable completeness). Set `RequiredOutfitId = NAME_None` for truly free, or bind the starter outfit. Ring1/Core rows are the real gates. Core uses `OnChallenge` to require both wardrobe and play — outfit alone does not skip the outer ring.

---

## 3. Runtime Flow

```text
Player equips via UI -> UMelodiaWardrobeSubsystem::EquipCosmetic(Cos_SpaceVeil)
        |  validates via FindGrantableRecord, writes EquippedCosmeticIds on FMelodiaNarrativeRecord,
        |  broadcasts OnWardrobeChanged(Slot, CosmeticId)  [single writer — subsystem only]
        v
UOrbitalWardrobeGateComponent (on APCGHeroMusicGraphHost, alongside
  UMelodiaPCGNarrativeChallengeBridgeComponent) receives delegate
        |  reads DT_OrbitalWardrobeGates rows for this host's rings
        |  for each row: IsOwned + GetEquipped == RequiredOutfitId ? (+ IsWorldChallengeCompleted if OnChallenge)
        v
  Gate evaluation -> ApplyGating()
        |  for locked rings: hide/disable platforms & bridge spline actors (see §4)
        |  for unlocked rings: show/enable, fire OnGateUnlocked(GateId, RingIndex)
        v
  OnGateUnlocked -> VFX/SFX via MPC_Melodia_Palette (existing reactivity/MPC owner only)
                  -> optional Quill flag commit (see §6)

  No direct save write in the component.
  Persistence is via ::CommitWorldChallenge / ::SetNarrativeFlag with
  ConsumedIntentIds idempotency on the narrative record (see §5).
```

### 3.1 Bridge pattern — reuse, not fork

`UMelodiaPCGNarrativeChallengeBridgeComponent` (h) is the reference adapter:

- It never writes a save object directly; it calls `CommitWorldChallenge`.
- Idempotency is `ConsumedIntentIds`, not a local `bAlreadyFired`.
- It is independent from the water bridge; both consume `OnPatternCompleted` without interacting.

`UOrbitalWardrobeGateComponent` follows the same boundaries:

- **Reads** wardrobe (`IsOwned`, `GetEquipped`, `GetState`) and narrative (`Flags`, `ConsumedIntentIds`).
- **Never** calls `GrantCosmetic`/`EquipCosmetic` itself; never mutates `FMelodiaNarrativeRecord` except through `CommitWorldChallenge` / `SetNarrativeFlag` with an allowlisted intent.
- Delegates: `FOrbitalGateUnlocked(GateId, RingIndex, bUnlocked)` + `FOrbitalGateBlocked(GateId, FailMessageKey)` for UI/Quill.

Placement: same `APCGHeroMusicGraphHost` that owns the orbital PCG graph. GraphHost already carries `InitializeFromPCGPoint` identity (`seed = stable_chunk_seed + stepIdx`, with `ring`/`lane`/`midiNote` metadata). One host = one gate table evaluation = one orbital system.

---

## 4. PCG Integration — How Locked Rings Are Filtered

Locked means **not traversable**. Visual treatment (hidden vs ghosted) is a presentation choice; collision/nav is the gameplay gate.

### Option A — PCG graph boolean param (pre-spawn filter)

- Graph exposes `OrbitalGate_Ring1_Unlocked` (bool, default false) consumed by a `PCGAttributeFiltering` or `PCGFilterByAttribute` node on `ring` param.
- Host sets param via `PCGComponent->SetDynamicParameter(OrbitalGate_Ring1_Unlocked, bUnlocked)` before generate.
- Requires `Regenerate` on gate change; re-seeds are stable (`FPCGPoint.Seed` unchanged), but costs a PCG generate.

### Option B — Actor-level hide/disable (post-spawn, recommended)

- Graph stays deterministic and unaware of wardrobe. PCG spawns all 24 + core as `hero_interactive` tier: `PCGSpawnActorSettings[NoMerging, ExcludeFromHLOD]` on `DL_Musical_HeroGameplay` (see `pcg_scale_world_pipeline.scale_contract()`).
- Gate component owns the spawned actors per ring (mapped by `ring` attribute baked into `FPCGPoint.Seed`/metadata, or by stable `PCGInteractivePlacementSpec`-style tagging if wrapped).
- On lock: `SetActorHiddenInGame(true)`, `SetActorEnableCollision(false)` on platforms; same for `PCGEx orbital ring rail` spline-mesh bridges for that ring.
- On unlock: reverse, then optionally pulse MPC (`MPC_Melodia_Palette`) and call `INavigationSystem::OnNavigationBoundsUpdated` if needed.

### Decision: Recommend **B (actor-level)** for `hero_interactive` tier

| Criterion | A (PCG param) | B (actor-level) |
|---|---|---|
| Determinism | graph output changes per gate state | graph output identical; gating is post-spawn overlay |
| Cost | regenerate on equip/unequip | O(ringSize) actor toggles, no regenerate |
| `NoMerging` / `ExcludeFromHLOD` | must reassert per generate | set once at spawn, never merged into HLOD |
| WP streaming | regeneration races with `IsPartitioned` | actors are `Is Spatially Loaded`, streaming owns lifetime |
| Debugging | need PCG debug view to see filter | outliner + collision view is sufficient |

B keeps `build_pcg_hero_orbital_rings.py` wiring contract (`PCGCreatePoints -> PCGTransformPoints -> PCGSpawnActorSettings[NoMerging] -> Output` with `clear_graph_nodes` workaround) untouched. Gating is reversible in PIE without rebuilding the graph.

If ghosted visuals are desired for locked rings, keep actors visible but collision-disabled and drive a desaturated MI parameter (still B — no graph change).

---

## 5. Save / Load — Why No Local Bool

Gate unlock persists through the **canonical narrative record** on the JRPG save, not a component bool.

Canonical fields (`MelodiaNarrativeTypes.h`):

- `FMelodiaNarrativeRecord::Flags` (`TMap<FName,bool>`, `SaveGame`) — e.g., `orbital.gate.ring1 = true`.
- `FMelodiaNarrativeRecord::ConsumedIntentIds` (`TArray<FName>`, `SaveGame`) — e.g., `orbital.gate.ring1.intent`.
- `FMelodiaNarrativeRecord::OwnedCosmeticIds` / `EquippedCosmeticIds` — wardrobe persistence (v3+).
- Versioned via `CurrentVersion = 5` + `MigrateRecord`; sync via `SyncNarrativeRecordToSave` / `RestoreNarrativeRecordFromSave` on `BP_JRPGSaveGame::melodiaNarrativeRecord`.

On unlock, the gate component (or the challenge bridge that drives it) commits:

```cpp
EMelodiaContentCommitFailure F;
EMelodiaContentCommitResult R = Narrative->CommitWorldChallenge(
    /*ChallengeId=*/      FName("challenge.orbital.ring1"),
    /*CompletionFlagId=*/ FName("orbital.gate.ring1"),   // Flags[orbital.gate.ring1]=true
    /*RewardId=*/         FName("reward.orbital.ring1"), // allowlisted, may be NAME_None
    /*CompletionIntentId=*/FName("orbital.gate.ring1.intent"),
    F);
```

Replay (Quill resume, save reload, re-equip) hits `ConsumedIntentIds` → `AlreadyApplied`, no double-grant. The flag check `IsWorldChallengeCompleted(challenge.orbital.ring1, orbital.gate.ring1)` is the load-time authority for `ApplyGating()`.

**Why a local `bRing1Unlocked` would desync:**

- It is `Transient` and empty after `RestoreNarrativeRecordFromSave`. PIE save/reload would show the flag true in the save but the component still locked, or vice-versa if the component set a bool without committing the flag.
- Two sources of truth for the same fact always diverge after a restart — the bridge spec (§3 Boundaries) explicitly forbids a local `already fired` bool for this reason.
- Wardrobe equip itself already persists via `EquippedCosmeticIds`; the *gate-derived* fact (ring usable) must persist via `Flags` + `ConsumedIntentIds` so unequip/re-equip semantics are well-defined (Immediate gates re-lock on unequip; OnChallenge gates stay unlocked via the committed flag even if the outfit is later swapped — designers choose per row).

---

## 6. Quill Integration — No New Verbs

The subsystem's seven-verb dispatch (`MelodiaNarrativeSubsystem.cpp:HandleQuillNotification`) is the only Quill ingestion path. Orbital gates reuse two verbs:

- `melodia:flag:orbital.gate.ring1:true` — sets `Flags[orbital.gate.ring1]`. Consumed via `CommitWorldChallenge`'s `CompletionFlagId` or direct `SetNarrativeFlag` if the challenge route is not used. Flag id must be in `DA_MelodiaIntegrationConfig` allowlist; add `orbital.gate.ring1`, `orbital.gate.core`, and challenge ids there.
- `melodia:reward:reward.orbital.ring1` — optional one-time grant (e.g., cosmetic shard, token). Idempotent via `ConsumedIntentIds`; second resume is a no-op for the same `IntentId`.
- `melodia:item:give:...` remains a logging stub — do not use it to grant the ring.

Quill dialogue for blocked traversal references `FailMessageKey` (e.g., `quill.orbital.ring1.need_spaceveil`) via the dialogue WBP chain (`Content/Melodia/UI/Quill/`). Do **not** invent a new `melodia:gate:` verb or a custom notification — the 7-verb contract is the P0 gate `rhythm_owner`/`hud_single_writer`-adjacent boundary: one ingestion table, fail-closed on unknown ids.

`melodia:stat:` idempotency note still applies — intent id is `FMelodiaNarrativeRecord::ConsumedIntentIds` key, not `StatId`. Same pattern for gate rewards.

---

## 7. Validation Checklist

Run in order; each row is a gate. Record evidence beside frames (JSON, not just PNG).

| # | Check | Steps | Pass |
|---|---|---|---|
| 1 | Equip -> ring appears | PIE → equip `Cos_SpaceVeil` via `MelodiaWardrobeSubsystem::EquipCosmetic` → `OnWardrobeChanged` fires → `UOrbitalWardrobeGateComponent::ApplyGating` shows ring-1 platforms/bridge, collision enabled, `OnGateUnlocked` fires (MPC pulse if wired) | Ring 1 traversable within 1 tick, no PCG regenerate |
| 2 | Unequip -> hides (Immediate) | Unequip slot for `Cos_SpaceVeil` → `OnWardrobeChanged` → ring-1 hides/disables again (Immediate row) | Re-lock is immediate; nav updates |
| 3 | OnChallenge requires play | With `Cos_Muse` equipped but `challenge.orbital.ring1.completed` false → core stays locked. Complete ring-1 musical pattern (`OnPatternCompleted` -> `CommitWorldChallenge` -> flag true) → core unlocks | Core needs both outfit AND challenge |
| 4 | Flag already consumed is harmless | Replay pattern or re-equip after unlock → `CommitWorldChallenge` returns `AlreadyApplied`, no second reward, gate stays unlocked | Idempotency via `ConsumedIntentIds` |
| 5 | Save / reload persists | Equip SpaceVeil → commit ring-1 flag → `SyncNarrativeRecordToSave` → close PIE → reopen → `RestoreNarrativeRecordFromSave` → `ApplyGating` on `BeginPlay` restores ring-1 unlocked without re-equipping this session | Flag + equipped map survive restart; no local-bool desync |
| 6 | Free ring unaffected | Ring 0 always traversable regardless of outfit; unequipping Stone Court dress does not lock it | No regression on always-free content |
| 7 | Nav still valid | After each toggle, `Build Navigation` / `UNavigationSystemV1` query on ring-1 platforms: locked = no nav poly, unlocked = traversable; no `EXCEPTION_ACCESS` from malformed song map | Nav bounds update is explicit, not implicit |
| 8 | No second wardrobe writer | `grep -r MelodiaWardrobeSubsystem` outside `Plugins/MelodiaWardrobe/` shows only readers; `bp_sweep` has no shadowed `OnWardrobeChanged` or empty-bodied gate events; only `UMelodiaWardrobeSubsystem` writes `EquippedCosmeticIds` | Single-writer invariant holds |
| 9 | Determinism untouched | `build_orbital_layout` point count still 24 (+1 core landmark), `stable_chunk_seed` + `WIRING_CONTRACT` strings present, graph diff is only the new component on GraphHost — no PCG node edits for gating | Graph fingerprint baseline unchanged except host |
| 10 | WP / Data Layer correct | Spawned platforms remain `hero_interactive` tier: `exclude_from_hlod true`, `no_merging true`, Data Layer `DL_Musical_HeroGameplay`, `Is Spatially Loaded` true, origin = `chunk_origin_cm(chunk_x,chunk_y)` | `validate_chunk_manifest` / outliner report |

Evidence to keep per run: `Saved/Echo/state.txt` + gate ledger via `Tools/echo_run.py record wardrobe_orbital_gate pass|fail` + adjacent JSON (`gate_id, ring, bUnlocked, reason, flag, intent`) next to any captured frames.

---

## 8. Rollout — Component, Not a Second System

Do not create a new pawn, new `UMelodiaWardrobeSubsystem`, or new save field. Implement as a component on the existing GraphHost, mirroring the water/narrative bridge split.

### 8.1 New file

`Source/BS_GodFile/MelodiaIntegration/UOrbitalWardrobeGateComponent.h/.cpp` — `UActorComponent` (BlueprintSpawnable), `ClassGroup=(Melodia)`.

- Properties: `DataTable DT_OrbitalWardrobeGates`, `bool bHideLockedRings`, `bool bGhostLockedRings`, delegates `OnGateUnlocked` / `OnGateBlocked`.
- Methods: `RebindToHost()`, `IsGateUnlocked(GateId)`, `GetLockedRings()`, `ApplyGating()` (BlueprintCallable for PIE probes).
- Dependencies: `UMelodiaWardrobeSubsystem` (read), `UMelodiaNarrativeSubsystem` (flag/commit), `APCGHeroMusicGraphHost` (actor registry). No dependency on `MelodiaWardrobe` at the `BS_GodFile` module level beyond the existing `IMelodiaTraversalCapabilityProvider` indirection if needed.

### 8.2 Config

- Allowlist: `DA_MelodiaIntegrationConfig` → add `orbital.gate.ring1`, `orbital.gate.core`, `challenge.orbital.ring1`, `challenge.orbital.ring0`, `reward.orbital.ring1` to `WorldChallengeIds` / `FlagIds` / `RewardIds` as applicable. Keep `bRelaxedAllowlistInEditor` true for iteration but verify once with it off — typos pass in PIE and fail in shipping.
- DataTable: `DT_OrbitalWardrobeGates` with the 3 rows §2.2; validate `RequiredOutfitId` resolves via `FindGrantableRecord` on `BeginPlay` (warn, fail closed).

### 8.3 Sequencing

1. Land the DataTable + config allowlist entries (no code).
2. Land `UOrbitalWardrobeGateComponent` with actor-level gating (B) + `RebindToHost` + `OnWardrobeChanged` subscription; keep `bGhostLockedRings=false` for first proof.
3. Wire GraphHost in `/Game/EnvSandbox/PCG/Musical/Hero/L_PCG_Hero_OrbitalRings` proof level: add component, set `DT_OrbitalWardrobeGates`, PIE through checklist 1–5.
4. Add `OnGateUnlocked` → `MPC_Melodia_Palette` pulse (reuse `MelodiaRhythmReactivitySubsystem` owner; do not add a second MPC writer) + optional Quill flag commit.
5. `echo_run.py record wardrobe_orbital_gate pass` only after save/reload + nav checks pass.

### 8.4 Guardrails

- One editor, one MCP surface, verify `Binaries/Win64/UnrealEditor-BS_GodFile.dll` lock directly — do not trust lane reports.
- `save_asset` success is not proof — check `list_dirty_packages`.
- `load_blueprint_class` on skill BPs still crashes (Python glue for `D_DamageType`) — use `blueprint_query` for skill reads.
- Keep `hda/SpaceTraversal_OrbitalRings_1.0.hda` as the Houdini path; PCG fallback stays the deterministic gate target. Do not add a second graph per chunk — `WP_CELL_SIZE_CM=25600` remains single source of truth (`pcg_scale_world_pipeline.py`).

---

*Spec file: `Docs/WorldGen/WARDROBE_ORBITAL_GATE_SPEC_2026-08-27.md` — under 350 lines by contract.*
