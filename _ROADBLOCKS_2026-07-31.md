# Roadblocks & Contradiction Register — 2026-07-31

**Purpose:** one place for what is actually blocked, and for which documents currently contain false
claims. The project's own `FOUNDATION_LOCKIN_PLAN_2026-07-30.md` named documentation drift as
Bottleneck 6; this is the register for it.

**Scope note:** this is a snapshot. Rows are dated. Anything here can go stale the same way the docs
it catalogues did — check source mtimes before acting.

---

## ⏱ The dated-doc rule

**A doc's filename date is when it was written, not when it was last true.**

This project produces same-day contradictions because code lands faster than prose:

- `Docs/GAMEPLAY_REVIEW_2026-07-30.md` (21:14) was wrong about the travel system by 21:17, when
  `MelodiaTravelSubsystem.cpp` was written.
- `Docs/MELODIA_SYSTEMS_COMPOSITION_CONTRACT_2026-07-30.md` contradicts itself between §2 and §5a,
  appended hours apart on the same day.
- `_SESSION_HANDOFF.md` said cook exit 25 was "cleared" and "still blocks all packaged builds"
  98 lines apart in one file.

Before acting on a claim that something is missing or broken, check the mtime of the source file it
describes. Prefer the artefact over the prose.

---

## Top blockers — what will actually stop you

| # | Blocker | Why it ranks here |
|---|---|---|
| 1 | ~~**No reversible Git checkpoint.** `BS_GodFile\.git` was corrupt; recovered from `.git.backup.mirror` on 2026-08-05 and restored to a normal repo on `main`.~~ | **RESOLVED 2026-08-05.** Working tree re-synced (`6154cc1e`), post-recovery fixes landed (`ec20b015`), review doc committed (`62eab10d`). Plain `git add`/`commit` work again. |
| 2 | **Save round trip across a full process restart, including one social stat, is unproven.** | The standing gate for everything downstream. Now meaningfully testable: the record is v2, `SocialStats` is canonical and `SaveGame`-flagged, and the `melodia:stat:` intent is wired end to end in C++. It needs one Quill choice and one run. |
| 3 | **Packaged build has never been launch-tested.** `Saved/StagedBuilds_20260730/` cooks clean at 2.1 GB with all five maps — but packaging is not launching. | The cheapest remaining unknown with the largest blast radius. |
| 4 | **17 orphaned Python scripts** (below). | Silent, and it compounds: each one is only discovered when someone tries to run it. |
| 5 | **KaleidoNave merged-content and death-menu fixes are authored but not PIE-verified.** The portal destination and `BP_BattleController.mainMenuMapName` CDO were corrected; end-to-end arrival and party-wipe confirmation remain open. | These are runtime proof gates now, not unresolved implementation blockers. |

Resolved since the last handoff: the MCP surface (agents could not reach the editor at all), the
rules generator (recovered), and the Blueprint-verification gap (Decisions 024/025).

**2026-08-05 update:** Git recovery completed; checkpoint commit `6154cc1e` captures the full live
working tree on recovered history. Local `main` is healthy and diverged from `origin/main`; push is
currently blocked by network connectivity to `github.com:443`. Collaborator environment design is
in progress: tiered onboarding scripts and validation added under `deploy/`.

**In progress as of 2026-07-31 (session 3):** UEBlueprintMCP installed and registered, disabled by
default (Decision 027) — needs one closed-editor build before first use. Blueprint wiring checklist
items 2-4 handed off to Cline; UI polish to Gemini; Persona-lite remaining lanes + quest-authority
investigation to Qwen/DeepSeek. See `_SESSION_HANDOFF.md` for the full state and each agent's
standalone handoff doc under `Docs/Handoffs/`.

---

## Contradiction register

Ranked by how likely each is to send someone down a dead end. **Status** is as of 2026-07-31.

| # | Contradiction | Verdict | Status |
|---|---|---|---|
| C1 | `_SESSION_HANDOFF.md` said cook exit 25 was both cleared and still blocking. | Cleared. Decision 022; staged build exists on disk. | **Fixed** — line struck. |
| C2 | `GAMEPLAY_REVIEW_2026-07-30.md` §2 wrong on **four** counts about travel (executor "MISSING", broadcast unheard, spawn context unused, transition component bypassing the allowlist). | All four false; code landed 3 min after the doc. One residual truth: `MelodiaSaveSlotLibrary.cpp:50` is still a genuine bypass. | **Fixed** — superseded banner added. |
| C3 | `BLUEPRINT_WIRING_CHECKLIST_2026-07-30.md`: *"Graph topology I cannot read reliably."* | **False, and load-bearing** — it is why five items of mechanical graph surgery were assigned to a human. `export_graph` / `get_graph_data` read the live `UEdGraph`. Origin: misreading `MONOLITH_GUIDE.md`'s staleness warning about `project_query("get_asset_details")`, which concerns the *asset index*. | **Fixed** — section rewritten. |
| C4 | Three docs say "editor open, cannot build / everything runtime unproven". | Build gate closed 2026-07-30 (three green builds); re-confirmed 2026-07-31. | **Fixed** in `_TASK_QUEUE.md`; the two `Docs/*_2026-07-30.md` plans keep their historical text but are annotated. |
| C5 | `MELODIA_SYSTEMS_COMPOSITION_CONTRACT_2026-07-30.md` §2–3 vs §5a: `SocialStats` transient / version 1 vs v2 shipped. | §5a is current; source confirms `CurrentVersion = 2`. | **Fixed** — historical banner added. |
| C6 | Hair: Decision 010 ("no re-export"), the 07-30 checklist ("still broken, `shared_bones=0`"), the handoff ("root cause = ARP Match to Rig"), and the wiring checklist (presumes re-export worked) all disagreed. | **All of it was the wrong question.** Shared bones never mattered: the hair mesh is authored in *character space*, so parenting it to `head_x` stacked that bone's bind transform on geometry that already accounted for it — the ~3 ft offset was head height, the wrong rotation was the bone's axis convention. Applying the inverse of `head_x`'s bind-pose component-space transform cancels both. Three lines. | **Resolved and PIE-verified 2026-07-31.** Every compensating mechanism deleted. Wiring-checklist §1 rewritten — it had been instructing the next agent to re-create the bug. |
| C7 | Blender 5.1 targeted by `MELODIA_STUDIO_SHIP_CHECKLIST.md` and `SETUP_COLLAB.md`. 5.1 is **not installed**. | Only 4.3 / 4.5 / **5.2** have executables. Every 5.1 acceptance step is unrunnable. | **Fixed 2026-08-07** — `MELODIA_STUDIO_SHIP_CHECKLIST.md` retargeted to 5.2 (install path, version references, socket rebind, all 8 verification steps). `SETUP_COLLAB.md` was already retargeted (5.2+ prerequisites, install path, G:→C: path fix). `sync_surreal_to_live.ps1` default already confirmed at 5.2 by `_health_check_full.py`. |
| C8 | Website ship task: **Blocked** in `_PORTFOLIO_SHIP_CHECKLIST.md:19`, **In Progress** in `_TASK_QUEUE.md:87`. | Blocked is correct — waits on user-supplied renders. | **Fixed** — reconciled to Blocked. |
| C9 | Git health: `Docs/QUEUE.md:86` says committing through `BS_GodFile\.git` "has continued to work reliably, confirmed 2026-07-30"; `_SESSION_HANDOFF.md:202` says it is corrupt, do not commit. | Newer doc wins; `QUEUE.md` actively invites the dangerous behaviour and cites the same date. | **Fixed** — repo recovered 2026-08-05, `QUEUE.md` "2026-08-05 RESOLVED" note added, commits verified. |
| C10 | **Decision 023 cited in `MelodiaMapTransitionComponent.cpp:37` but never written down.** Four different claims about how far the log runs (011 / 012–021 / 022 / 001–011). | The decision was real and implemented; only the record was missing. | **Fixed** — 023 written retroactively; 024–025 added. |
| C11 | `_TASK_QUEUE.md` had both "Package the route — Done" and "Package and launch — Available, after cook crash is fixed". | Duplicate; cook crash long fixed. | **Fixed** — merged into one launch-test row. |
| C12 | `_TASK_QUEUE.md:20` marked a **runtime** P0 gate Done on static evidence, self-labelled "Tool-proven, not PIE-tested". | Exactly the failure mode `2026-07-29_PROJECT_HANDOFF.md:22` warns about. | **Fixed** — reopened, static finding retained. |
| C13 | `_VERTICAL_SLICE_SCOPE.md:1` corrupted heading (`Deep roject intake#` fused into the H1, breaking the Markdown); `:7` claimed `DefaultGame.ini` was intentionally not modified when `+MapsToCook` was added. | Both literal defects. | **Fixed.** |
| C14 | `Docs/QUEUE.md:75` declares "BLOCKED: *(none right now)*" while the same file discusses corrupt git objects and same-day plans list P0 blockers. | Scope note at `:3` limits the file to environment-art, but the BLOCKED heading is unqualified and reads project-wide. | **Fixed** — clarifying scope-qualifier block added at `QUEUE.md:79` after the "*(none right now)*" line. |

---

## Roadblock inventory

### (a) Build / packaging
- Cook exit 25 — **resolved** (Decision 022; five assets quarantined, paths mirrored, reversible).
- Packaged build never launch-tested — **open, P0**.
- `FSlateFontInfo` deprecations in `MelodiaMinimalHUD.cpp` become errors in a future engine version — parked, worth a ticket.
- Two pre-existing deprecation warnings in Monolith (`GetObjectsWithOuter`, `GetSamplerTypeForTexture`) — same class, parked.

### (b) Infrastructure / git / storage
- ~~Corrupt `BS_GodFile\.git`; commit through `.repo_recovery_20260727\.git`~~ — **RESOLVED 2026-08-05**: recovered from `.git.backup.mirror`, normal repo on `main`, commits verified.
- LFS quota blocks pushing the recovery branch — **open** (only matters if the recovered `main` ever needs pushing pre-LFS; the 08-05 local commits succeeded without it).
- Backup predates the 2026-07-30 afternoon source edits — **open**; re-sync before relying on it.
- **Disk: ~65 GB reclaimable.** `.clone_v2`, `.temp_work`, `.transform_temp` are ~21.8 GB each — git-only working clones left over from the 2026-07-27 history rewrite. `.git.backup.mirror` (21.8 GB) is the bare safety mirror. C: has ~56 GB free.
  **Recorded, not actioned — deletion is the user's call.** `.repo_recovery_20260727` (9.9 GB) must stay: it is the healthy Git directory. Recommendation if space is needed: keep the bare mirror, drop the three working clones.
- Stale `G:\` paths in generated data manifests (`my-site-clean/generated/*`, `Products/*/product_manifest.json`, `pipeline/figma/*`, `Saved/SourceControl/UncontrolledChangelists.json`) — cosmetic; regenerated by their own pipelines. MCP configs are **fixed**.

### (c) Gameplay wiring
The original five-item checklist is partially complete: items 1, 2a, 2c, and 5a are done and verified; item 2b remains blocked on an authored travel notification/tag decision. Remaining runtime or presentation gates are:
- Rhythm clock infrastructure and `RecordInputNow()` exist, but the authored MIDI/clock actor and visible stock-lane consumer still require editor wiring and PIE A/B proof.
- ZenForest NPC/Quill binding remains protected-map owner work; do not script or save `ZenForestTest` to close it.
- Social-stat persistence exists in narrative record v2; the authored Quill choice and full process-restart proof remain open.
- Resonance remains insufficiently visible in the active battle UI — Decision 017 corollary: "a mechanic the player never learns".
- Of the original Decision 021 content leaks, `BP_Melusina.uasset` is resolved; protected map references require deliberate owner-led editor cleanup.
- `DA_OrreryRegistry` / `WBP_ComicOrrery` destination semantics require current live-asset readback before modification.
- MelodiaCore subsystems still auto-instantiate; the 13 guards block new Blueprints/placements only. Gating needs `ShouldCreateSubsystem` and a separate decision.

### (d) Content / asset damage
- 5 damaged assets quarantined; 3 corrupt in 11,425 files (0.026%) — contained, not systemic, consistent with the USB migration. Do not delete them.
- 4 crashing PCG graphs + 10 spline-blocked graphs — parked P3 behind the vertical slice.
- Shipping content lives under `/Game/Experiments/` — "exactly the folder a future cleanup pass deletes". Open P0, one-time move.
- **Standing hazard:** never run `patch_portfolio_texture_paths.py` / `patch_portfolio_uasset_paths.py` — they corrupt uassets (FString length mismatch).
- **New duplicate found 2026-07-31:** ~64 custom UI textures (`T_Melodia_*`, `SoftMG_*`) duplicated with identical names across `/Game/EnvSandbox/Textures/Melodia/GameUI/`, `/Game/EnvSandbox/Textures/Source/MelodiaGameUI/`, and partially in `/Game/EnvSandbox/Alphas_Melodia/` — unresolved, needs in-editor reference audit to pick the canonical copy; see Decision 032.

### (e) Tooling / pipeline
- **17 of the 45 `.pyc` files in `Tools/__pycache__/` have no surviving `.py`.** The handoff recorded only one. Compiled paths inside them point at `G:\EnvironmentPortfolio\...`, so these are migration casualties.

  Recovered 2026-07-31: `generate_melodia_rules`, `export_melodia_rhythm_web_config`.

  Still orphaned — recoverable **today** with the local interpreter (cpython-314):
  `audit_project_hygiene`, `build_technical_breakdown_manifest`, `melodia_asset_passport`,
  `rewrite_content_paths`, `validate_local_doc_links`.

  Orphaned, needs a 3.11/3.13 interpreter to unmarshal (`xdis` is installed and can cross-read):
  `batch_eevee_komikaze_portfolio`, `komikaze_stage_looks`, `populate_stage_review_queue`,
  `prep_portfolio_render_day`, `setup_tier_b_diorama`, `setup_tier_c_audvis_truedepth`,
  `setup_tier_p2_glam`, `setup_tier_p3_proc`, `setup_tier_p4_wild`,
  `upgrade_stage_core_and_waterhair`.

  **Method (proven):** `marshal.loads(pyc[16:])` → `dis` disassembly → reconstruct → verify by
  comparing instruction streams against the original **and** diffing regenerated outputs.
  `uncompyle6` is installed but does **not** support 3.14 — do not rely on it.
  **Import the module from a scratch copy**, not from `Tools/` — importing regenerates and
  overwrites the `.pyc` you are recovering from. (Originals survive in the F: backup.)

- **Generated files have been hand-edited.** `MelodiaRulesGenerated.h` carried seven `Opening*`
  constants added by hand in violation of its own DO-NOT-EDIT header, referenced by four C++ files;
  the restored generator now emits them from `opening_flow`. It also carries a hand-added UTF-8 BOM,
  CRLF endings, and a mojibake em-dash that regeneration will correct. Worth a periodic
  "does the generator still reproduce its output" check.
- Blender: sub-second UI stalls; `surreal_architecture_gen.py` is 1.9 MB / 38,508 lines and a
  headless `addon_enable` probe ran >6 minutes. Six addons held in `_HOLD_20260730/` — **do not bulk-restore.**
- Monolith goes unresponsive while a modal dialog is open — grep the log for `MODAL_OPEN` before
  assuming the plugin is at fault.
- `create_material` MCP action broken (workaround: `duplicate_material`); `Add_npc_parameter` ignores
  `type` for vectors.
- `scene_metadata_exporter.py` returns all-null; `render_exporter.py` reports a filename that does
  not match disk.

### (f) Portfolio / website
- Ship website — **Blocked** on user-supplied hero renders (reconciled; see C8).
- Stats exporter has no producer — schema slot ready, parked P3.
- Render-capture verification (1.3) and a full end-to-end pipeline run (1.4) never done. The pipeline
  has never produced a complete package.
- 22/65 SDF-Melodia copy masters lack `SubstrateToonBSDF` — blocks the SDF portfolio lane.

### (g) Documentation drift
- ~30 root `.md` files plus `Docs/`; several actively contradict (see register above).
- `CLAUDE.md` was misinforming every session in its first 200 tokens — **fixed**.
- `DOC_INDEX.md` was ~12 h behind and indexed none of the 07-30 afternoon docs — **fixed**.
- `Docs/PCG_CATALOG.md` confirmed stale — retire/rewrite queued, not done.
- `target_file.md` (0 bytes) and `nul` (0 bytes) are junk artefacts at the project root.
- ~~Stale `G:\` paths in copy-pasteable commands across `CURRENT_STATE.md`, `INTEGRATION_WORKFLOW.md`,
  `README.md`, `WEBSITE_MAINTENANCE.md`, `Docs/ONBOARDING_LIVE_COLLAB.md`, `Docs/BLENDER_LIVELINK.md`,
  `Docs/NIKKI_VERTICAL_SLICE_PLAN.md`.~~ **Resolved 2026-08-07** — verified 0 `G:` matches across all `.md`
  and `.py` files; `SETUP_COLLAB.md`'s G:→C: path also corrected. Remaining G: refs only in non-text
  generated manifests (cosmetic, pipeline-regenerated) — see (b) above.
- `NEXT_ACTIONS.md` (07-20) and `WORKING_SOLUTION.md` (07-19) still drive workflows Decision 002
  retired.

---

## What changed on 2026-07-31

| Area | Change |
|---|---|
| **Cross-module authority (Claude, Stages C/D)** | Decisions 030/031 landed. `MelodiaSharedAuthorityInterfaces.h` (`IMelodiaTravelProvider`, `IMelodiaInputContextProvider`) + `UMelodiaAuthorityLocator` (MelodiaCore-native, GameInstance subsystem) resolve the "MelodiaCore cannot reach the game module" inversion without a circular `Build.cs` dependency. `UMelodiaTravelSubsystem`/`UMelodiaInputContextSubsystem` implement + self-register on `Initialize()`. Sir's departure rerouted through the locator (fallback `OpenLevel` until Cline's 2a allowlist lands — correct degrade). `UMelodiaPacingSubsystem` + `UMelodiaPacingProfile` scoped to Sir's two departure timings as the proof case; `DA_MelodiaPacingProfile` now authored (7 IDs) and auto-set active on `Initialize` — missing asset still degrades to EditAnywhere fallbacks. |
| **Stage B quarantine set confirmed (Claude)** | Reference set enumerated via Monolith `get_saved_asset_state`. Stop condition does NOT trip: `BP_Melusina` referencers are only `BP_MelodiaGameMode` (itself referenced only by the **stale** `/Game/L_MelusinaMorning` — the Decision 029h duplicate), the `DefaultEngine.ini:111` redirector artifact, and `WBP_Battle_Rhythm`. `BP_Melusina_BACKUP_20260729` has zero referencers — clean to quarantine. Physical moves deferred to Claude's closed-editor batch (no live move-asset surface in Monolith). |
| **New files on disk (Claude, this session)** | Beyond the three listed above: `MelodiaExplorationPoint.h/.cpp`, `MelodiaOpeningFlowSubsystem.h/.cpp` (MelodiaCore), plus interface/locator/pacing. 14 files total edited or created 2026-07-31 21:12–21:29. |
| **PIE risk flagged (DeepSeek, verification only)** | `UMelodiaTravelSubsystem::Initialize` registers with the locator via `GetSubsystem<UMelodiaAuthorityLocator>()`. If it initializes before the locator's own `Initialize`, that call returns `nullptr` and the registration call could crash — the "degrades gracefully" contract protects consumers, not the registration path. Worth a guarded registration at PIE. Not a change request. |
| **DeepSeek lane closed (2026-07-31 evening, built green)** | Item 1: `MelodiaOllamaValidation` wired into `HandleQuillNotification`, `_popen` probe removed. Item 2: all 6 orphaned `OpenLevel` calls rerouted through `IMelodiaTravelProvider` (OrreryMainMenuGameMode `TravelToOpeningMap()` helper ×5, MelodiaOpeningPortal ×1) with `OpenLevel` degrade fallback. Item 3: all remaining scattered pacing floats migrated to `UMelodiaPacingSubsystem` (battle staged-turn windows, arena hitstop/dolly, platform `TravelDuration` resolved once in BeginPlay). Every consumer keeps its `EditAnywhere` default as the false-return fallback. Build green, 36.9 s, zero new failures. |
| Agent surface | Monolith registered in `.mcp.json` — it had **no registration at all**; the file was lost in the G:→C: migration while `enabledMcpjsonServers` still listed it. Three adapters repointed off the dead USB drive. Proxy smoke-tested with the editor closed: 28 namespace tools. |
| Verification | `get_graph_fingerprint` + `assert_graph_matches` added; hidden-pin asymmetry, pin-ID addressing and missing `node_id` in `get_execution_flow` fixed. Build green, 38.5 s. |
| Node config | `set_node_property` added, with a denylist covering the head members that produce nodes which look right and compile wrong. |
| **Latent bug found** | `FMonolithReflectionWalker` had no `FClassProperty` branch, so **every `TSubclassOf` write** through `set_cdo_property`, `set_property_at_path`, `set_cdo_properties` and `seed_data_asset` silently failed for Blueprint class paths. Fixed. |
| Source recovery | Two generators reconstructed and proven equivalent; 15 more orphans catalogued above. |
| Docs | 9 files corrected in place; Decisions 023–025 recorded. |

## Verification still owed

- **Fingerprint stability gate.** Call `get_graph_fingerprint` twice on an untouched graph and once
  after a no-op resave; require byte-identical output **before** anything relies on
  `assert_graph_matches`. A flaky fingerprint teaches the agent to ignore assertions, which is worse
  than having none.
- `assert_graph_matches` against an unmodified export → `matched:true`; against a trimmed one →
  precise `missing_connections`.
- `set_cdo_property` writing a `TSubclassOf` with a `/Game/...` Blueprint path — fails before the fix.
- `set_node_property` binding an `InputAction` to a `K2Node_EnhancedInputAction` → `pins_added`
  contains the trigger exec pins, `compile_blueprint` clean.

All four need the editor running. None have been run yet.

---

## Verification results — 2026-07-31 (all four gates now run and PASSING)

Ran against live editor via Monolith (editor rebuilt green this session; five build breakers fixed,
see `_SESSION_HANDOFF.md`). Target graph: `BP_MelodiaJRPGGameInstance` EventGraph (217 nodes).

| Gate | Result |
|---|---|
| **Fingerprint stability** | `get_graph_fingerprint` → `ce961a1949d25073f257e8a114703ea97fd23f71` three times, including after a no-op `save_asset`. Byte-identical across all calls. |
| **assert_graph_matches** | Unmodified subset spec (`K2Node_CustomEvent_0`) → `matched:true`. Bogus-connection spec → `matched:false` with precise `missing_connections` (names each unresolved connection + a "why"). `forbidden_nodes: [{K2Node_CallFunction, OpenLevel}]` → correctly reported **4 live `OpenLevel` calls** in the GameInstance EventGraph (nodes `_10/_30/_46/_52`) — the exact pattern handoff item 3 replaces with `TravelTo`. |
| **TSubclassOf write** | `set_cdo_property` on `BP_MelodiaJRPGGameMode -> DefaultPawnClass` (`TSubclassOf<APawn>`) with `/Game/MelodiaIntegration/Blueprints/BP_MelusinaJRPGCharacter.BP_MelusinaJRPGCharacter_C`. `dry_run` → `ok:true, errors:0`; real write → `old_value == new_value` (resolved to `BlueprintGeneratedClass`); readback confirms. The FClassProperty fix holds. |
| **InputAction binding** | Created throwaway `BP_InputActionGateTest` in `/Game/Tests/Monolith/`, added `K2Node_EnhancedInputAction` (generic fallback), `set_node_property path=InputAction value=/Game/Melodia/Input/IA_ToggleOrrery` → `applied:true, reconstructed:true, pins_added:[InputAction]`, node retitled `EnhancedInputAction IA_ToggleOrrery` with `default_object` resolved. `compile_blueprint` → `UpToDate, 0 errors, 0 warnings`. Test asset deleted via `cleanup_generated_assets` (no referencers). |

**Allowlist readback (same session):** `DA_MelodiaIntegrationConfig -> TravelLevelIds` now contains
`melodia_integration_map` (the core-mechanics test map —
`/Game/MelodiaIntegration/Maps/MelodiaIntegrationMap`, a one-off level holding all test BPs in one
area) plus the newly added `/Game/EnvSandbox/Environments/L_KaleidoNave`. `SocialStatIds` now contains
`melodia_harmony`. Both writes readback-verified and saved; `list_dirty_packages` empty. Verification
tooling is now proven and safe to rely on for the `Open Level` → `TravelTo` swap.
