# Current State — Melodia (BS_GodFile)

**Canonical State Document**
**Last Updated:** 2026-09-02 20:00 EDT
**Target Engine:** Unreal Engine 5.8.0 | Blender 5.2 LTS | C++20 | Python 3.11
**Overall Status:** **27/31 P0 Gates PASS | 108/116 Tests PASS (1 fail, 3 errors)**

---

## 1. Executive Summary

Melodia has converged from disparate exploratory prototypes into a unified, production-grade **Rhythm-JRPG**. The codebase and content pipeline operate under a strict separation of concerns governed by **Two Absolute Authorities** and **Four Converged Pillars**, with a standardized **6-Phase Reusable Gameplay Loop**.

### Two Absolute Authorities
1. **QuillScript Narrative Authority (`UMelodiaNarrativeSubsystem`)**: Sole authority for narrative flow, branching dialogue, cutscene triggering, quest flag evaluation, and 7-verb structured notifications (`melodia:quest`, `melodia:battle`, `melodia:stat`, `melodia:wardrobe`, `melodia:item`, `melodia:inspect`, `melodia:checkpoint`).
2. **Turn-Based JRPG State Authority (`BP_JRPGSaveGame` & Combat Subsystem)**: Sole authority for turn queue resolution, combat calculations, party stats, inventory, and canonical game state persistence.

### Four Converged Pillars
1. **Rhythm Combat Layer**: Rhythm timing highway executes directly over JRPG command selections. Note accuracy (`Poor: 0.35`, `Good: 1.0`, `Great: 1.2`, `Perfect: 1.5`) scales base damage and pulses `MPC_Melodia_Palette` without bypassing JRPG turn logic.
2. **Wardrobe Traversal System**: Outfits provide visual mesh customization and grant physical world traversal capabilities (Glide, Swim, Dash), fully persisted across save/reload cycles.
3. **Music-as-Key World Puzzles**: Environmental barriers respond to played musical phrases, dispatching 7-verb narrative notifications to unlock routes.
4. **Single-Writer UI Architecture**: Every surface has exactly one designated writer (`UMelodiaUIBridgeSubsystem`), eliminating race conditions.

---

## 2. P0 Completion Gate Matrix (`Saved/gate_ledger.json`)

| Gate ID | Target System | Status | Date |
|---|---|---|:---:|---|
| `runtime` | Core Gameplay Loop | ✅ PASS | 2026-08-13 |
| `save_load` | State Persistence | ✅ PASS | 2026-08-14 |
| `repeat_consume` | Narrative Queue | ✅ PASS | 2026-08-14 |
| `rhythm_owner` | Rhythm Subsystem | ✅ PASS | 2026-08-28 |
| `rhythm_grade_to_result` | Combat Multiplier | ✅ PASS | 2026-08-28 |
| `hud_single_writer` | UI Hierarchy | ✅ PASS | 2026-08-28 |
| `wardrobe_equip_roundtrip` | Wardrobe Subsystem | ✅ PASS | 2026-09-01 |
| `wardrobe_gameplay_hook` | Traversal Provider | ✅ PASS | 2026-09-01 |
| `music_world_key` | Resonant World | ✅ PASS | 2026-09-01 |
| `static_gates` | Material Baselines | ✅ PASS | 2026-08-29 |
| `battle_integration_map` | Allowlist | ✅ PASS | 2026-08-28 |
| `package_build` | Shipping Cook | ✅ PASS | 2026-09-03 |
| `package_launch` | Standalone Boot | ✅ PASS | 2026-09-03 |
| `world_field_bus_pie` | Audio Bus Runtime | ⏳ PENDING | 2026-09-02 |
| `gaeA_live_pie` | Gaea Terrain Runtime | ⏳ PENDING | 2026-09-02 |

**PASS: 29 | FAIL: 0 | PENDING_CAPTURE: 2**

> Cook #3 (2026-09-03) exited 0 with 0 cook errors and 0 ensures. Archive:
> `G:\melodia_packages\P0_Closeout_20260902\Windows\BS_GodFile.exe` (2.8 GB, .pak + IoStore .utoc).
> Packaged boot verified outside the editor: mounted `BS_GodFile-Windows.utoc`, `LoadMap`
> `/Game/Melodia/Levels/Menu/L_MelodiaMainMenu` in 0.349 s, 0 fatals, Narrative/UIBridge/Wardrobe
> subsystems all initialised.
>
> **Caveat — the build boots but the ROUTE cannot run yet.** Three assets exist on disk but were
> not cooked: `DA_MelodiaIntegrationConfig`, `DA_MelodiaPersonaContent`, and the music-clock
> beat-grid MIDI `128BPMarpeggiomelody_beatgrid`. Fix is two `+DirectoriesToAlwaysCook` entries
> (`/Game/MelodiaIntegration/Config`, `/Game/MelodiaIntegration/MIDI`) plus a re-cook. That missing
> MIDI is also why `BeatPulse` reads zero.

---

## 3. Current Test Suite Status

```
Automated Test Execution Summary (2026-09-02):
  Content/Python/Tests/                          116 tests run
    PASS:                                         108
    FAIL:                                           1  (test_qsc_allowlist_contract)
    ERROR:                                          3  (wardrobe slot mappings, toon monotonicity, PBR tier2)
```

**Known failures:**
- `test_qsc_allowlist_contract` — allowlist mismatch (new gate added without allowlist update)
- `test_wardrobe_disk_textures_and_slot_mappings` — slot binding drift
- `test_on_disk_authored_textures_toon_monotonicity` — toon shadow assertion
- `test_real_world_generated_assets_verification` — PBR tier2 asset check

---

## 4. Level & Environment Verification Status

1. **`L_MelusinaMorning` (Sanctuary / Chapter Opening)**
   - **Role:** Narrative initialization, NPC dialogue, departure gate.
   - **Status:** Verified. QuillScript NPC anchor dispatches `melodia:quest:first_dream.started`.

2. **`LV_SeaAbove_Prototype` (Overworld Traversal & Music-as-Key)**
   - **Role:** Traversal, Starskiff navigation, musical puzzle, route unlock.
   - **Status:** Verified. 221 cathedral pieces at Z=13,455. 2 PCG volumes. Cutscene trigger at (-910, 500, 13,145).

3. **`L_KaleidoNave` (Battle Arena / Boss Encounter)**
   - **Role:** Turn-based combat, Rhythm Highway interaction, victory resolution.
   - **Status:** Verified. Single HUD writer (`UMelodiaUIBridgeSubsystem`). Rhythm note highway scales boss damage.

4. **`MelodiaMainMenu` (Title & Frontend)**
   - **Role:** Title screen, new game / load game entry point.
   - **Status:** Verified. Clean bootstrap into sanctuary level.

---

## 5. Cross-Machine Development Status

This project is actively developed across three workstations:

| Machine | Role | OS | Specs | Status |
|---|---|---|---|---|
| Desktop PC (froma) | Primary authoring | Windows 11 | High-end | ✅ Active |
| Laptop | On-the-go / Humber Labs | TBD | Portable | 🔄 Setup pending |
| Humber Labs | College workstation | TBD | Shared | 🔄 Setup pending |

**Authoritative workflow:** [Docs/Production/CROSS_MACHINE_WORKFLOW_2026-09-02.md](Docs/Production/CROSS_MACHINE_WORKFLOW_2026-09-02.md)

---

## 6. Blockers & Open Decisions

| Issue | Impact | Status |
|---|---|---|
| ~~Package cook exits -1~~ | ~~Shipping blocked~~ | **RESOLVED 2026-09-03** — root cause was engine asset `MPD_Default.uasset` (`/MeshPartition/`, Editor-only module) failing to cook for Win64. Quarantined in the UE_5.8 install. **An engine update restores it and breaks packaging again.** |
| C: disk ~85 GB free / Content 88 GB | Cook may fail on disk space | **DONE** — cook + staging both routed to G: |
| Packaged route missing 3 configs | Build boots, route cannot run | Add `DirectoriesToAlwaysCook` for `/MelodiaIntegration/Config` + `/MIDI`, re-cook (~15 min warm) |
| ~~Shorewake 2-bone vs Melusina 465-bone~~ | ~~Outfit import broken~~ | **RESOLVED 2026-09-03** — rebind landed (`SK_ShorewakeDress_Melusina465`). Real blocker was a missing catalog record; `Cos_ShorewakeDress` now registered (SKIRT/Rare) and equip round-trip PASSES. |
| Shorewake renders untextured | Equips but reads flat grey | All 48 `SW_Dress_P*` MIs bind 0 texture params; `T_MelusinaC_DressShorewake_*` suite unused on disk |
| Push blocked | No remote backup for 650+ commits | 3 LFS objects are **corrupt, not missing** — stored bytes do not hash to their OID (`Blue_Nebula_6/7/8`). Push uploads 5903/5906 then S3 rejects. G: mirror copies are corrupt too, so this predates the backup. Needs history excision or an orphan branch. |
| 4 test failures | Not blocking P0 | Under repair |

---

## 7. What's Next

1. **Fix test failures** — update allowlist, repair slot bindings, fix toon assertion
2. **Package cook** — cold cook on closed editor, output to G: drive
3. **PIE captures** — world_field_bus_pie, gaeA_live_pie
4. **Cross-machine setup** — implement the workflow in CROSS_MACHINE_WORKFLOW doc
5. **itch.io upload** — `package_launch` now passes, but no butler/`.itch.toml`/upload script exists in either repo; needs credentials + a target page

---

*Melodia © 2026. Authoritative State Ledger.*