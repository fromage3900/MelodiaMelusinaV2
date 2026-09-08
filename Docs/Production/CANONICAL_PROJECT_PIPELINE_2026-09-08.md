# Canonical Melodia Project Pipeline — 2026-09-08

**Status:** CANONICAL CROSS-REPO FRONT DOOR  
**Use this document before dated handoffs, recovery branches, or historical workspace notes.**

## 1. Repository authority

| Lane | Canonical repository | Local / operational home | Owns |
|---|---|---|---|
| Game / Unreal / capstone | `fromage3900/MelodiaMelusinaV2` | `C:/EnvironmentPortfolio/BS_GodFile` | UE5.8 runtime, gameplay, maps, assets, C++/Blueprint contracts, semester/capstone truth |
| Portfolio website | `fromage3900/my-site` | independent checkout, optionally under `C:/EnvironmentPortfolio/` | recruiter-facing pages, Three.js/browser presentation, deployment |
| TouchDesigner / AE | `fromage3900/MelodiaTouchDesigner` | `C:/MelodiaTouchDesigner` | TD show rig, TDN/TOE, hand/audio performance layer, AE finishing |
| Historical umbrella | `fromage3900/EnvironmentPortfolio` | old root `C:/EnvironmentPortfolio/.git` only | archive/provenance only; never current authority |

The folder `C:/EnvironmentPortfolio/` may remain a workspace container. Its old root Git repository is not Melodia authority.

## 2. Git truth rule

1. `main` is the only canonical durable state for the game and website.
2. A feature/recovery branch is evidence or work-in-progress, not current status.
3. Runtime claims require runtime evidence; repository structure alone proves only source state.
4. Dated handoffs never override newer source, current `main`, or newer evidence.
5. Do not merge old cleanup/recovery branches wholesale. Extract a specific unique file or change with provenance.
6. The dedicated `render-queue` branch is operational infrastructure and is intentionally not merged into `main`.

## 3. Game / Unreal lane

**Engine:** Unreal Engine 5.8.

The game repo is the single authority for:
- QuillScript narrative/progression;
- JRPG combat and canonical save state;
- rhythm execution and gameplay interpretation;
- Wardrobe ownership/equip/traversal capabilities;
- Starskiff and world traversal;
- environment, material, PCG, Houdini/Blender integration contracts;
- Choral Sheep runtime/companion state;
- capstone and semester ledgers.

Runtime ownership remains explicit:
- narrative/progression → `UMelodiaNarrativeSubsystem` / QuillScript;
- combat/state persistence → existing JRPG/Phoenix authority;
- rhythm → execution quality, never a second combat authority;
- Wardrobe → owned/equipped outfit state and traversal capability;
- Convergence → derived interpretation unless a fact is explicitly promoted to durable state.

## 4. DCC / procedural authoring lane

Blender/Houdini/Geometry Nodes tooling that produces game assets is coordinated from the game repository.

Pipeline:

```text
reference / design lock
  → Blender / Houdini / procedural authoring
  → tracked script/spec/provenance
  → export/import candidate
  → UE validation
  → runtime or render evidence
  → main
```

Large source binaries may live outside Git when appropriate, but the current import contract, scripts, manifests, evidence, and promoted game assets must resolve through the canonical game repo.

## 5. Choral Sheep / capstone lane

Current durable game-side state includes:
- Choral Sheep source assets and runtime actor work;
- owner-approved concept/reference boards;
- Day 1 execution and capstone ledgers;
- ARP re-export as the fallback if the current UE skeletal export needs refresh.

Current TD-side state at `MelodiaTouchDesigner/main` includes a landed Chladni Fleece performance scene with six harmonic states and rendered evidence:
`REST → ROOT_C → INTERVAL_CE → RESOLUTION_CEG → WORLD_HIT → AFTERIMAGE`.

Do **not** re-open the old “weight-paint blocked / no rig” interpretation.

Do **not** claim the previously reported twelve `MI_ChoralSheep_Coat_PC*` instances or Shot06 tracking files are in the game repo unless they actually appear on current `main`. They were not present during the 2026-09-08 reconciliation.

A historical `Humber_FinalYear_Prep/Capstone_Portfolio_Tracker.md` exists on the preserved `cleanup/root-trim-docs-2026-09-06` branch. It is recovery material, not current canon, until deliberately migrated and updated.

## 6. TouchDesigner / live-performance lane

Canonical repo: `fromage3900/MelodiaTouchDesigner`.

Current interface contract:
- MediaPipe / camera bridge → OSC UDP `:7001` + Spout sender `MelodiaHandCam`;
- game ↔ TD semantic/show-control lane → UDP `:9000`;
- TD → Blender auxiliary lane → `:9001` where used;
- TD consumes game semantics; it does not own gameplay state.

Current Chladni Fleece scene is live-evidenced in TD. The later UE integration work prepares material/telemetry contracts.

**UE → TD `UE_Beauty` Spout ingest remains VERIFY LIVE until an actual Unreal sender/receiver capture proves it.**

The AE lane remains downstream:
- 12-pass 32-bit linear scaffold;
- lookdev LUT / grading;
- gesture/audio keyframe injection;
- editorial/reel assembly.

## 7. Render / evidence lane

Evidence levels must be named accurately:

```text
SOURCE-BUILT
  → LIVE-PROVEN
  → RESTART-PROVEN
  → PACKAGED-PROVEN
```

Do not promote a claim to a stronger level without corresponding evidence.

Machine roles:
- Humber lab → primary interactive semester workstation;
- home Windows PC → render/bake/long-job worker;
- ASUS Nitro laptop → auxiliary/recovery/secondary task lane.

All machines start from `main` unless explicitly assigned a feature branch.

## 8. Website / recruiter lane

Canonical repo: `fromage3900/my-site`.

The website consumes approved downstream proof; it never becomes gameplay authority.

Publishing flow:

```text
approved game / DCC / TD evidence
  → curated site asset / manifest update
  → site validation
  → my-site/main
  → GitHub Pages
  → Wix Studio shell / fromageart.xyz
```

GitHub Pages hosts the portfolio files. Wix owns the top-level custom domain/shell and embeds the stable GitHub Pages entry.

The recruiter-facing site remains under the 2026-09-07 soft freeze:
- approved render promotion;
- factual/contact/accessibility fixes;
- social-preview correctness;
- critical deployment fixes;
- no broad route/layout/effect expansion unless the freeze is explicitly lifted.

## 9. Cross-lane handoff

```text
GAME / DCC
authoritative state + assets + renders
        ↓
TOUCHDESIGNER
performance interpretation + visual layers
        ↓
AFTER EFFECTS
editorial / compositing / reel finishing
        ↓
WEBSITE
curated recruiter-facing proof
```

Direction of authority is one-way for facts:
- TD may visualize game state but does not redefine it.
- AE may editorialize captures but does not redefine runtime state.
- Website copy may summarize evidence but does not create evidence.

## 10. Branch policy after 2026-09-08 reconciliation

Superseded documentation/feature refs reviewed in this pass have been normalized to the canonical `main` tip.

The following game branches remain intentionally separate because they contain recovery/history or operational state and must **not** be treated as current truth:
- `cleanup/root-trim-docs-2026-09-06` — historical cleanup/recovery source;
- `collab/laptop/longterm` — large diverged laptop history;
- `docs/stale-session-start-fix-2026-09-06` — stale but potentially unique recovery source;
- `integration/semester-closeout-salvage-2026-09-07` — salvage source requiring deliberate extraction;
- `render-queue` — operational queue branch, intentionally non-merge.

All safe superseded refs now point at `main`; only the recovery/operational exceptions listed above remain intentionally separate.

**One lane, one authority, one current branch: `main`.**
