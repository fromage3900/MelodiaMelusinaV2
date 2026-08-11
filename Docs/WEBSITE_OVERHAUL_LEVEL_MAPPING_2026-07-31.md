# Website Overhaul — Level Inventory & Mapping

**Date:** 2026-07-31
**Author:** BLACKBOXAI (portfolio lane)
**Source data:** Full `.umap` scan of `Content/` (~65 maps listed below) cross-referenced against
`_SESSION_HANDOFF.md`, `_DECISION_LOG.md`, `_TASK_QUEUE.md`, `_VERTICAL_SLICE_SCOPE.md` (all dated
2026-07-26 → 2026-07-31; the dated-doc rule in `_ROADBLOCKS_2026-07-31.md` applies — files' mtimes
beat prose claims).
**Feeds:** Cline's `Docs/WEBSITE_OVERHAUL_PLAN_2026-07-31.md` Phase 2/4 (website structure +
content).

---

## ⚠️ Two corrections to the overhaul plan (authoritative source: the 2026-07-31 session state)

1. **`L_Melodia_Dreamstate` is no longer a live route destination.** The standalone Dreamstate map
   was merged into `L_KaleidoNave` on 2026-07-30 (route change, `_SESSION_HANDOFF.md`; Decision
   021b's owner report covers the merged-BPs-not-functioning fallout, assigned to Cline). The
   "First 20 Minutes" route is therefore **`L_MelusinaMorning` → `L_KaleidoNave` (merged
   Dreamstate) → `ZenForestTest` → Roguelike expedition rooms**, not
   `L_Melodia_Dreamstate` as a standalone leg. `L_Melodia_Dreamstate.umap` still exists on disk but
   is the pre-merge standalone; do not advertise it as the playable Dreamstate.
2. **There are two `L_MelusinaMorning.umap` files** (Decision 029h). Live:
   `/Game/Melodia/Levels/Opening/L_MelusinaMorning` (modified 2026-07-31 18:15, uses
   `BP_MelodiaJRPGGameMode`). Stale: `/Game/L_MelusinaMorning` at Content root (last indexed
   2026-07-26, references the legacy `BP_MelodiaGameMode` → `BP_Melusina` chain). The website must
   reference the live path only; quarantine of the stale map is pending in-editor verification
   (Decision 029h, not scripted).

---

## A. Gameplay levels — "First 20 Minutes" vertical slice

| # | Level (live path) | Role in the slice | State (2026-07-31) | Tech highlights for the website |
|---|---|---|---|---|
| 1 | `/Game/Melodia/Levels/Opening/L_MelusinaMorning` | Bedroom interior / opening scene with Sir Melodious intro | Live route map; hair fix PIE-verified here (`MELUSINA_HAIR_SOCKET`); uses `BP_MelodiaJRPGGameMode` | Opening-flow state machine (`MelodiaOpeningFlowSubsystem`), ReunionTrigger → Sir departure (currently `OpenLevel` in MelodiaCore, see "Travel authority" row), save-slot fallback routed through `UMelodiaTravelSubsystem` |
| 2 | `/Game/EnvSandbox/Environments/L_KaleidoNave` | Dreamstate content merged here (2026-07-30) — traversal leg | **Merge fallout open (P0, Cline):** placed Dreamstate BPs don't proc. Contains `Dreamstate_PlayerStart` (loc `[9,10,741]`) + `NaveStart` (loc `[200,0,760]`), both untagged. Allowlisted in `DA_MelodiaIntegrationConfig -> TravelLevelIds`. | 4 PlayerStarts (2 inventoried), `melodia traversal` spawn-tag authoring decision pending dialogue emission |
| 3 | `/Game/ZenForestTest` (Content root) | Combat smoke-test map — first JRPG encounter | `BP_BattleController` present (2026-07-29); NPC encounter should initiate after PIE restart. **Decision 021 content leak:** `ZenForestTest.umap → MelodiaDungeonRunCoordinator` (quarantined-lane class) — in-editor cleanup, human. | Stock TurnBasedJRPG battle + co-op skills (Petal Cadence / Skybound Refrain / Resonance), Quill battle dialogue (42-statement smoke test logged 2026-07-28) |
| 4 | `/Game/Melodia/Roguelike/Rooms/*` (15 rooms × V1/V2/V3 iterations) | Recursive expedition rooms (procedural) | Present in Content root `Melodia/Roguelike/Rooms/`; lane parked P3 — not required for the first-20-minutes sendoff | PCG-driven room generation; `melodia_rules.json` grade multipliers are historical (Decision 016 — do not present as current combat math) |

**Beat mapping (level → minute of the slice, as documented in the handoffs):**

| Beat | Level | What the player does |
|---|---|---|
| 0:00–2:00 Opening | `L_MelusinaMorning` | Wake up, meet Sir, intro dialog, ReunionTrigger sphere arms the departure window |
| 2:00–8:00 Traversal | `L_KaleidoNave` (merged Dreamstate) | Cross the bifrost bridge content; musical-time ambient layer (Harmonix/Quartz clock project-wide, Decision 015) |
| 8:00–13:00 First combat | `ZenForestTest` | NPC encounter → stock JRPG turn combat; co-op skills; resonance buff visible (Decision 017 corollary — UI visibility is an **open** task) |
| 13:00–20:00 Expedition | Roguelike rooms | Recursive expedition rooms; save round-trip boundaries (Decision 019: post-battle, travel, quest change) |

---

## B. Portfolio worlds (current website "Environments")

These are the **WP showcase worlds** — the current website's four "environments". They are portfolio
content / future-world candidates, **not** the vertical-slice route. The overhaul plan's Task 2.2
(reorganize "Environments" into Gameplay Levels + Portfolio Worlds) is correct.

| World | Level(s) | Also present as render-test |
|---|---|---|
| Sakura Dream | `/Game/EnvSandbox/Environments/WP/L_WP_SakuraDream` | `/Game/_PROJECT/Levels/RenderTests/L_Render_SakuraDream` |
| Space Cathedral | `/Game/EnvSandbox/Environments/WP/L_WP_SpaceCathedral` | `/Game/_PROJECT/Levels/RenderTests/L_Render_SpaceCathedral` |
| Cosmic Orrery | `/Game/EnvSandbox/Environments/WP/L_WP_CosmicOrrery` | — |
| Baroque Grotto | `/Game/EnvSandbox/Environments/WP/L_WP_BaroqueGrotto` | `/Game/_PROJECT/Levels/RenderTests/L_Render_BaroqueCastle`, `L_Render_BioGrotto` |

**Caveats (source: Decision 029a/029f):** the four `L_WP_*.umap` maps are World Partition and all
reference `AMelodiaGameMode` (quarantined-lane guard — Decision 020 guards it in place, so these
references still resolve). `L_WP_SakuraDream` is the portfolio pipeline's captured level
(`/Game/EnvSandbox/Environments/Sakura/L_SakuraPath` is the pipeline path in task 1.1 — note
`L_SakuraPath` is the *pipeline* capture level referenced by `generate_portfolio.py`, separate from
`L_WP_SakuraDream`). `L_SakuraPath` art direction is human-owned.

---

## C. Other EnvSandbox environments (candidates for "future content")

`L_CelestialPond`, `L_EscherAscent`, `L_FallenMoon`, `L_InfiniteScore`, `L_VinylGalaxy`
(`EnvSandbox/Environments/`), plus templates `EnvSandbox/_Template/L_MaterialPreview_Studio` and
`L_Template`. `L_FallenMoon` is already referenced by the website worlds section (replaced
placeholder levels 2026-07-29 by Cline).

---

## D. Support / system levels

| Level | Purpose |
|---|---|
| `/Game/Melodia/Levels/Menu/L_MelodiaMainMenu` | Boot map (`DefaultEngine.ini:13` → `AOrreryMainMenuGameMode`); Main Menu here is `WBP_MainMenu` |
| `/Game/MelodiaIntegration/Maps/MelodiaIntegrationMap` | Core-mechanics one-off test map (all test BPs in one area); `melodia_integration_map` in the travel allowlist |
| `/Game/Melodia/Levels/DistanceFieldBlendLab` | Lookdev/lab |
| `/Game/TurnBasedJRPGTemplate/Maps/{MainMenu,BattleMap,Gameplay}` | **Stock template maps.** `MainMenu` here is exactly what `BP_DefeatDialogue` wrongly routes party death to (Decision 021b — fourth leak, traced 2026-07-31, defer-fixed; do not present as the game's menu) |
| `/Game/Melodia/_PROJECT/PCG/TestLevels` (+ root `_PROJECT/PCG/TestLevels`) | PCG test levels |
| Third-party: Brushify Floating Islands, Genshin Shader samples, UltraDynamicSky DemoMap, RVTDecals Showcase | Vendor content — not for the website |

---

## E. Known stale / duplicate / quarantined level references (do not feature)

- **Content-root `L_MelusinaMorning.umap`** — stale duplicate of the live opening map (029h); keep
  off the site.
- **`L_Melodia_Dreamstate.umap`** — standalone pre-merge map; superseded by the KaleidoNave merge.
- **`ZenForestTest_PreRestore_Backup.umap`**, `Untitled.umap`, `L_InfiniteScore.umap` (root) —
  dev/scratch/sandbox; exclude.
- **`L_Render_*`** — are they the *render-test* versions of the portfolio worlds; usable only as
  technical capture levels, not as "gameplay".
- **`DA_OrreryRegistry` / `WBP_ComicOrrery` still reference `ZenForestTest`** as a travel
  destination (filed) — the Orrery UI must not be described as wired to the vertical-slice route yet.
- **Packaged build** (`Saved/StagedBuilds_20260730/`, 2.1 GB, cook `Success - 0 errors`) contains all
  five route maps but has **never been launch-tested** outside the editor — "it packages" is not
  "it launches"; do not claim playable shipping until that open P0 is closed.

---

## F. Capture plan (this lane, pending sessions)

| Asset | Tool | Status |
|---|---|---|
| Beauty renders: `L_MelusinaMorning`, `L_KaleidoNave`, `ZenForestTest`, Roguelike room (e.g. `L_MelodiaGrove`) | UE Monolith (:9316) | QUEUED — user is prepping UE renders; do not duplicate |
| Wireframe / graybox views | UE Monolith | QUEUED (same session) |
| Material breakdowns | UE Monolith | QUEUED (same session) |
| PCG overlay visualizations | UE Monolith | QUEUED (same session) |
| Character turntable / env concepts / lookdev | Blender MCP (:9878) | Blender reported live — verify adapter (`deploy/blender_mcp_adapter.py`) before use |

**Any captured render must NOT touch the preserved asset sets** (EEVEE/Melusina character renders,
material loops, nightshift isolates, melodia-game-ui textures — see the overhaul plan's preservation
rules; these are current hybrid-pipeline proof).

---

## G. Prop-to-level mapping (static pass — Task 1.3, live-verified 2026-07-31)

**Corrected 2026-07-31 (round 2 — live verification).** Round 1 sources were the static
`BS_GodFile/_github_deploy/generated/*.json` catalogs (NOT `local_asset_inventory.json`, which is a
**material/texture support manifest** with zero props; the first pass over-claimed from that file and
is retracted). Round 2 ran live `project_query("search")` against Monolith on the running editor
(port 9316) and upgraded every row below with **confirmed UE asset paths** (or the lack of one).

| Prop (catalogued) | Inventory source (evidence) | Likely home level | **Live UE verification (2026-07-31)** |
|---|---|---|---|
| Cross | `blender_portfolio_intake.json` — category `Prop / cross` | `L_SakuraPath` / WP worlds / ZenForestTest | **NOT FOUND as a prop in the live index.** Only `T_Hatch_Cross` hatched-pattern textures exist (`/Game/Stylization/T_Hatch_Cross`, `/Game/EnvSandbox/Stylization/T_Hatch_Cross`) — material/texture, not a prop. The catalogue entry has no UE-mesh counterpart. **Do not feature as a gameplay prop.** |
| Melody Tokens (×3) | `blender_portfolio_intake.json` — category `Prop / melody_token`; `geometry_nodes_pipelines.json` — "musical kitbash lane is 10 FBX (7 polish + 3 Melody Tokens)" | Melodia gameplay levels (Morning intro / KaleidoNave) | **CONFIRMED — `SM_MelodyToken`** at `/Game/EnvSandbox/SM_MelodyToken` (StaticMesh, live index). Placement in a specific level still requires a reference query per level; the asset exists. |
| Ornament kitbash | `ornament_kitbash_catalog.json` — product `melodia-ornamental-architecture-kitbash-v1` | Architecture-heavy levels (`L_KaleidoNave`, WP worlds, Roguelike rooms) | **CONFIRMED — `SM_Orn_QuatrefoilArch`** at `/Game/EnvSandbox/Meshes/Ornament/SM_Orn_QuatrefoilArch` (StaticMesh). The full ornament family is live at the same folder: SpiralStaircase, PendantFinial, OculusFrame, CrownMolding, WovenRing, GothicTracery, CorbelBracket, FiligreeRing, VaultRibs, TorusKnot, ColumnCapital, RosetteMedallion, DoorArchway (13 meshes indexed). |
| TrebleClef / MusicalCorner | `musical_ornament_kitbash_catalog.json` — "sibling_of melodia-ornamental-architecture-kitbash-v1" | Melodia gameplay levels | **NOT FOUND as mesh props.** Only `M_SDF_TrebleClef_Ornament` (`/Game/_PROJECT/04_Materials/SDF/M_SDF_TrebleClef_Ornament`, Material) — an SDF ornament material, not a kitbash mesh. The musical-ornament meshes are not in the live index. **Do not feature as props.** |
| Zen Lantern | `zbrush_breakdown_manifest.json` — id `zen_lantern`, sku "Stylized Props Mini" | `ZenForestTest` | **NO `zenlantern.fbx` asset in the live index.** Actual lanterns live at `/Game/Library/Migrated/MagiciansLibrary/Lantern/` (`SM_Lantern` StaticMesh + `MI_Lantern`/`M_Lantern` + textures) plus `/Game/EnvSandbox/Library/Migrated/MagiciansLibrary/Lantern/` and `/Game/EnvSandbox/Materials/Instances/Sakura/MI_Sakura_Lantern`. Use the **Magicians Library lantern** as the ZenForest lantern evidence, not the ZBrush breakdown name. |
| Zen Torii / Zen Sando (greybox) | `unreal_portfolio_intake.json` — ids `GB_ZEN_TORII`, `GB_ZEN_SANDO` (greybox props) | `ZenForestTest` (same intake `level_path: /Game/ZenForestTest`) | **Torii CONFIRMED — two variants:** `/Game/EnvSandbox/Greybox_Kit/SM_Greybox_Torii` and `/Game/Greybox_Kit/SM_SM_Torii` (StaticMeshes). **Sando NOT FOUND** — `GB_ZEN_SANDO` does not exist in the live index (no Sando result). Refer to the Torii greybox only; drop Sando from the site copy. |
| Sakura textures (blossom/petal) | `local_asset_inventory.json` — `material_support.sakura` | `L_SakuraPath` / `L_WP_SakuraDream` | **CONFIRMED as material support** — `MI_Sakura_Lantern` is indexed at `/Game/EnvSandbox/Materials/Instances/Sakura/MI_Sakura_Lantern`. Not a prop; shader/material reference only. |

**Deliverable for this task:** this corrected + live-verified table. The `_TASK_QUEUE.md` row
("Website overhaul — prop-to-level mapping") is now **Done** with the live-query gap closed — the
remaining per-level *placement* reference queries are captured as a follow-up but no longer block the
website copy. First-pass fabrications (gazebo, violin, magical wand, melody slime) were retracted —
they matched no catalogued asset. Round-2 live verification upgrades: Melody Tokens / Ornament
kitbash / Torii greybox / Sakura material support **confirmed**; Cross-as-prop, TrebleClef meshes,
Sando, and `zenlantern.fbx` **have no live UE counterpart — excluded from site copy**.

---

## H. Technical description feedstock (for the website's technical notes)

Settled facts from the decision log / handoffs that the website can cite without qualification:

- **Combat authority:** stock TurnBasedJRPG template owns turn/damage/results/save (Decision 009);
  co-op skills are `BP_BattleSkillBase` / `BP_BuffBase` children (Petal Cadence applies Resonance,
  Skybound Refrain exploits it — conditional bonus wiring **open**, Qwen lane).
- **Musical time:** Harmonix preferred, Quartz second, no wall-clock beat (Decision 012);
  `UMelodiaMusicClockSubsystem`; project-wide ambient beat (Decision 015).
- **Travel:** single authority `UMelodiaTravelSubsystem` (Decision 023) — allowlist, spawn-tag
  placement, input-context clear; authored legs only (Decision 028).
- **Save schema:** `FMelodiaNarrativeRecord` v2, `SocialStats` canonical, `MigrateRecord` versioning
  (Decision 013).
- **Art/pipeline:** Substrate Toon master material (916–1015 expressions per the overhaul plan),
  PCG scattering (77 graphs), Blender 5.2 Geometry Nodes → UE import (49 GN builders per handoff;
  **note: the overhaul plan says Blender 5.1 — 5.1 is not installed, roadblock C7**).
- **Rhythm:** expressive, never evaluative — no miss penalty (Decision 016); `melodia_rules.json`
  `grade_multipliers` are historical, not current (do not publish).
