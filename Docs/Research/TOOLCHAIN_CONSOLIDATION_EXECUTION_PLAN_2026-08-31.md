# Toolchain Consolidation Execution Plan — 2026-08-31

**Project:** Melodia Melusina / UE5.8  
**Status:** Git-ready consolidation plan for Issue #36  
**Related:** Issue #29, Issue #36, PR #28, `Docs/Research/AGENT_TOOLCHAIN_DISCOVERY_INDEX_2026-08-30.md`  
**Rule:** one real Melodia benchmark per tool; never judge from vendor demo scenes.

---

## 0. Why this document exists

The repository currently has two valid but divergent toolchain realities:

1. `main` contains live Houdini/Copernicus implementation work under `Tools/Houdini/copernicus/` plus current live reports.
2. PR #28 / branch `docs/2026-08-29-character-p1-p2-canon-audit` contains the larger Houdini + emerging-toolchain research corpus.

This plan turns that split into an executable cleanup path. It does **not** replace the existing research. It tells agents what to promote, what to reconcile, what to split into standalone docs, and what must remain research-only.

---

## 1. Source-of-truth ordering

Agents must read in this order before authoring new architecture:

1. `AGENTS.md`
2. `Docs/Research/AGENT_TOOLCHAIN_DISCOVERY_INDEX_2026-08-30.md`
3. `Tools/Houdini/copernicus/README.md`
4. `Docs/Plans/COPERNICUS_AAA_LIVE_REPORT_2026-08-31.md`
5. PR #28: `Docs/Research/EMERGING_3D_RENDERING_TOOLCHAIN_RESEARCH_2026-08-30.md`
6. PR #28: `Docs/Research/TOOLCHAIN_INTEGRATION_SPIKE_PLAN_2026-08-31.md`
7. PR #28 Houdini technical docs
8. Tool-specific standalone pages created by this consolidation pass

**Conflict rule:** current implementation outranks speculative branch research when they disagree. Do not delete older research; mark it superseded, constrained, or research-only.

---

## 2. Verified external anchors

These are the evidence anchors used for the current execution rules. Re-check them before any production adoption decision.

| Area | Verified anchor | Melodia implication |
| --- | --- | --- |
| Houdini 22 / Copernicus | SideFX Houdini 22 docs list Copernicus as Houdini's 2D/3D GPU image-processing framework and include COP nodes plus Copernicus terrain workflows: https://www.sidefx.com/docs/houdini/ | Keep Copernicus as geometry-aware texture/mask authoring, not a Substance-only replacement. |
| Copernicus + Unreal | SideFX documents Houdini Engine for Unreal support for Copernicus HDAs, including generating, previewing and baking texture outputs in Unreal: https://www.sidefx.com/docs/houdini/unreal/copernicus.html | The live HDA/lookdev path on `main` is strategically correct; finish verification before inventing parallel bake lanes. |
| Houdini 22 COPs | SideFX notes new HeightField, grunge, adjacency, time, ML and Unreal support in Copernicus: https://www.sidefx.com/docs/houdini/news/22/copernicus.html | The P2 molt, P3 filter-flow and terrain-to-Nanite lanes should use shared fields and adjacency where possible. |
| UE5.8 Mesh Terrain / PVE | Epic's UE5.8 release notes mark Mesh Terrain and Procedural Vegetation Editor as **Experimental**: https://dev.epicgames.com/documentation/unreal-engine/unreal-engine-5-8-release-notes | Never migrate production maps. Isolated R&D only. |
| UE5.8 PCG details | UE5.8 PCG notes include editor-camera points, actor data modes, dynamic mesh material setting, spline application and seed-related fixes: same release notes above | Good for sandbox automation and PCG evidence capture, not a license to rewrite world authority. |
| Cascadeur 2026.1 | Cascadeur docs state Live Link plugin support for UE 5.5–5.8 and Cascadeur 2026.1+: https://cascadeur.com/help/category/268 | Test Mara Anchor via UE-compatible skeleton export/import; Live Link requires exact version/license verification. |
| JangaFX suite | JangaFX docs state EmberGen exports flipbooks/image sequences/VDB, LiquiGen exports flipbooks/image sequences/Alembic caches, and IlluGen targets real-time VFX assets including normal maps, flowmaps, meshes, caustics, masks and distortions: https://docs.jangafx.com/ | Treat IlluGen/LiquiGen/EmberGen as authoring/bake accelerators, not runtime authority. |
| Dash | Polygonflow Dash docs describe an Unreal Engine 5 world-building ecosystem with content browser, scatter, physics placement, image board, channel packing, vines, blend materials and pivot tools: https://docs.polygonflow.io/ | Test Dash only as last-mile dressing/composition after Houdini/PCG/SpeedTree baseline. |
| Toolbag 5 | Marmoset Toolbag 5 docs list UDIM baking, interactive baking, bevel shader baking, material property baking, UDIM texture projects and texture-project/bake-project linking: https://docs.marmoset.co/docs/version-5-00/ | Test as hero-asset bake/lookdev QA station, not a core engine dependency. |
| World Creator | World Creator docs describe Unreal/Houdini bridge support and bridge sync/export workflow: https://docs.world-creator.com/reference/export/bridge-tools | Optional terrain ideation/front-end only; compare against Gaea and Houdini per artist-hour. |
| NVIDIA RTX Kit | NVIDIA RTX Kit lists neural texture compression, texture filtering, texture streaming, RTX Mega Geometry and neural materials: https://developer.nvidia.com/rtx-kit | WATCH/R&D only unless a specific foliage/material-memory benchmark justifies a branch. |

---

## 3. Immediate consolidation work packages

### Package A — preserve the branch research without dragging stale mega-PR state forward

- [ ] From a fresh branch off `main`, copy/reconcile only the still-valid docs from PR #28.
- [ ] Keep PR #28 as historical context until it can be split or merged safely.
- [ ] Do not merge old Copernicus plans without comparing them to `Tools/Houdini/copernicus/`.
- [ ] Add a short `Superseded / current live lane` note anywhere branch research contradicts main.
- [ ] Link every promoted doc from the discovery index.

### Package B — split buried tool research into discoverable standalone files

- [x] Create standalone Dash spike page: `Docs/Research/DASH_ENVIRONMENT_DRESSING_SPIKE_2026-08-31.md`.
- [x] Create standalone Magpie watch page: `Docs/Research/MAGPIE_SIMULATION_VISUAL_TRUTH_WATCH_2026-08-31.md`.
- [ ] Add standalone `PROCEDURA_EDITABLE_PROCEDURAL_ASSEMBLY_WATCH_2026-08-31.md` only if deeper implementation evidence is found.
- [ ] Add one-page `TOOLCHAIN_VERSION_LICENSE_LEDGER_TEMPLATE_2026-08-31.md` if repeated tool installs begin.

### Package C — recover/regenerate missing toolchain boards

The following paths are reserved only; do not cite them until files exist:

- [ ] `Docs/Research/Images/Toolchain/melodia_super_pipeline_16x9_2026-08-30.png`
- [ ] `Docs/Research/Images/Toolchain/houdini_copernicus_unreal_ownership_map_16x9_2026-08-30.png`
- [ ] `Docs/Research/Images/Toolchain/dash_environment_dressing_integration_map_16x9_2026-08-30.png`
- [ ] `Docs/Research/Images/Toolchain/magpie_simulation_vs_visual_truth_research_board_16x9_2026-08-30.png`

If a board cannot be found in Git, mark it `CHAT-ONLY / UNCOMMITTED VISUAL REFERENCE` and regenerate rather than searching indefinitely.

---

## 4. Updated adoption ladder

| Rank | Tool/lane | Status | Reason |
| ---: | --- | --- | --- |
| 0 | SpeedTree | CORE | Established botanical pillar. Not under evaluation. |
| 1 | Houdini + Copernicus | CORE / ACTIVE | Already live on `main`; finish reproducible HDA/bake verification. |
| 2 | IlluGen | TEST NOW | Best chance of quick Sea Above/P3 flow/distortion texture win. |
| 3 | Cascadeur | TEST NOW | UE5.8-compatible Live Link path exists; Mara Anchor is a clean benchmark. |
| 4 | Unreal MCP/editor automation | TEST NOW, sandbox only | Potentially huge agent productivity but dangerous without action-surface limits. |
| 5 | UE5.8 Mesh Terrain + PCG | R&D TEST | Experimental, but directly relevant to overhang/cavity/folded terrain. |
| 6 | Dash | TEST AFTER baseline | Only useful if it beats manual UE dressing after Houdini/PCG/SpeedTree baseline. |
| 7 | Toolbag 5 | TEST | Potential hero bake/lookdev QA acceleration. |
| 8 | LiquiGen / EmberGen | TEST | Useful motion/atmosphere sketchbooks; bake outputs only. |
| 9 | Gaea / World Creator | OPTIONAL COMPARE | Pick at most one terrain ideation front-end unless both prove distinct value. |
| 10 | UE Procedural Vegetation Editor | R&D TEST | Must prove unusual secondary Monolith growth, not replace SpeedTree. |
| 11 | RTX Kit / neural materials | WATCH | Real future value; too platform/branch-heavy for current production adoption. |
| 12 | Procedura / Magpie | RESEARCH ONLY | Watch for architecture ideas; no production integration. |

---

## 5. First five spikes — concrete pass/fail gates

### 5.1 Copernicus → P2 matched molt material states

**Map/assets:** isolated `LV_RND_P2_MoltMaterial_COP` or equivalent test level; one owned molt fragment mesh/curve.  
**Timebox:** 90 minutes hands-on after Houdini license/version confirmed.  
**Required outputs:** BaseColor, Normal/detail, Roughness, Wetness/Reactivity mask, packed utility mask, JSON manifest.  
**Pass:** one shared procedural source drives geometry + at least 4 synchronized material states and recooks deterministically after one geometry change.  
**Fail/Park:** output is only a slower Substance clone; Houdini license blocks real bake; UE ingest contract remains ambiguous.  
**Commit after pass:** HDA/COP spec or script changes, manifest template, screenshot/contact sheet, result block, no large generated binaries unless policy permits.

### 5.2 IlluGen → Sea Above/P3 animated flow/distortion/VFX textures

**Map/assets:** `LV_RND_SeaAbove_IlluGenFlow` and/or `LV_RND_P3_FilterFlow_IlluGen`.  
**Timebox:** 60 minutes.  
**Required outputs:** flow map, distortion, caustic/interference or particulate breakup, packed mask/flipbook, UE material/MID test.  
**Pass:** visually useful motion in UE faster than current Houdini/COP/Substance route and export lands as ordinary UE textures/flipbooks.  
**Fail/Park:** poor packing/color-space control, hard-to-reproduce vendor graph, no meaningful speed gain.  
**Commit after pass:** source graph only if license allows, export settings, UE material notes, screenshot/video reference, result block.

### 5.3 Cascadeur → Mara Anchor animation + UE iteration

**Map/assets:** `LV_RND_MaraAnchor_Cascadeur`; production-compatible proxy skeleton from UE.  
**Timebox:** 90 minutes.  
**Required outputs:** 3–5 second brace/Anchor motion, UE round-trip proof, contact/root-motion notes.  
**Pass:** skeleton/retarget/root motion survives round-trip and physically convincing blocking is clearly faster than Blender/UE-only path.  
**Fail/Park:** paid Live Link/version friction, skeleton divergence, foot sliding/contact cleanup erases the speed win.  
**Commit after pass:** small notes, retarget settings, before/after captures; avoid committing paid sample content.

### 5.4 Unreal MCP → tightly constrained sandbox editor automation

**Map/assets:** `LV_RND_MCP_Sandbox`; disposable test Blueprint/primitive/material instance.  
**Timebox:** 60 minutes.  
**Allowed day-one actions only:** inspect selection, spawn one known test actor, create/configure one MID, run/read one validation command.  
**Forbidden:** deletion, bulk rename, plugin toggles, source-control writes, production map migration, arbitrary shell/Python bridge.  
**Pass:** reliable repeatable editor actions with auditable logs and a documented allowlist.  
**Fail/Park:** transport instability, unsafe permissions, ambiguous action logging.  
**Commit after pass:** allowlist doc, command transcript, sandbox-only scripts/config, rollback notes.

### 5.5 UE5.8 Mesh Terrain + PCG → impossible folded/overhung terrain patch

**Map/assets:** `LV_RND_MeshTerrain_FoldedPatch`; one Houdini-authored 20–40m folded terrain/anatomy mesh.  
**Timebox:** 90 minutes.  
**Required checks:** collision, Nanite/material behavior, PCG read/decorate operation, editor stability, packaging attempt.  
**Pass:** survives as promising R&D with clear advantage over static mesh + landscape hybrid for overhang/cavity/folded forms.  
**Fail/Park:** crash/stability issues, collision is unreliable, PCG cannot query/decorate as needed, packaging fails.  
**Commit after pass:** isolated map notes, mesh-generation settings, PCG graph description, failure log; never migrate production terrain.

---

## 6. Hidden dependency / failure-mode register

| Risk | Likely failure | Guardrail |
| --- | --- | --- |
| Branch split | Agents duplicate old Copernicus research already implemented on main | Discovery index first; compare against `Tools/Houdini/copernicus/`. |
| Houdini licensing | HDA/COP/Pyro features blocked by edition or license server | Record license/build before test; dry-run where possible; do not promise COP Pyro under Core. |
| UE experimental features | Mesh Terrain/PVE destabilize project | Dedicated R&D map/branch only; no production map migration. |
| Plugin creep | 16 tools become maintenance burden | ADOPT only on measured Melodia benchmark improvement. |
| Export opacity | Vendor graphs become non-reproducible black boxes | Commit settings/manifests/source graphs only when license allows; prefer baked UE-native outputs. |
| Runtime authority split | Authoring tools start owning gameplay truth | UE remains runtime authority; Houdini/SpeedTree/Cascadeur/JangaFX are authoring lanes. |
| Color-space/packing errors | Flow/ORM/mask channels misinterpreted in UE | Add texture contract checks and channel packing notes per asset family. |
| AI/editor automation hazard | MCP makes destructive editor changes | Explicit allowlist, sandbox-only, logs, no destructive/bulk operations in phase 1. |
| Toolchain images missing | Agents hallucinate paths | Mark absent boards as chat-only/uncommitted; regenerate into reserved folder. |
| Paid/trial limitation | Tool appears useful but cannot export commercially | Record license terms, export limitations, watermarks/trial caps before adoption. |

---

## 7. Required result block for every spike

```markdown
## Result — <Tool> — <YYYY-MM-DD>

- Tool/version/build:
- License/trial state:
- Branch/map/assets:
- Setup minutes:
- Hands-on minutes:
- Current workflow comparator:
- What was faster:
- What was worse:
- Export/runtime dependency:
- Determinism/reproducibility notes:
- UE import/material/collision/perf result:
- Evidence committed:
- Rollback path:
- Decision: ADOPT / PARK / REJECT / WATCH
- Next owner/action:
```

---

## 8. Commit policy after each experiment

Commit:

- Markdown result blocks and decisions.
- Small Melodia-owned test scripts/configs.
- Export manifests, channel packing specs, version/license notes.
- Lightweight screenshots/contact sheets when useful.
- UE map/asset changes only if isolated, owned, and source-control policy permits.

Do not commit:

- Vendor binaries/installers.
- Proprietary demo/sample content.
- Large generated caches unless explicitly approved.
- Marketplace assets or downloaded examples without license clearance.
- Experimental plugin enablement for production maps.

---

## 9. GitHub execution structure

### Current branch

`docs/toolchain-consolidation-2026-08-31`

### PR target

`main`

### PR should claim only

- Adds executable consolidation plan.
- Adds standalone Dash spike page.
- Adds standalone Magpie WATCH page.
- Updates Issue #36 with concrete next steps.
- Does **not** migrate production tools or merge the old PR #28 corpus wholesale.

### Issue #36 checklist additions

- [ ] Merge or copy this consolidation plan to `main`.
- [ ] Add/merge Dash standalone page.
- [ ] Add/merge Magpie standalone WATCH page.
- [ ] Create board recovery/regeneration pass under `Docs/Research/Images/Toolchain/`.
- [ ] Reconcile PR #28 Copernicus notes against current main implementation.
- [ ] Promote only still-valid Houdini research into fresh docs.
- [ ] Close PR #28 only after valuable docs are extracted or explicitly retired.

---

## 10. Next actions in order

1. Finish this docs-only PR and link it from Issue #36.
2. Run Copernicus P2 molt state spike against the live `Tools/Houdini/copernicus/` path.
3. Run IlluGen Sea Above/P3 flow texture spike.
4. Run Cascadeur Mara Anchor spike.
5. Run Unreal MCP sandbox-only allowlist spike.
6. Run Mesh Terrain + PCG folded patch spike.
7. Only then spend time on Dash/Toolbag/LiquiGen/EmberGen/Gaea/World Creator/PVE.
8. Keep RTX/neural/Procedura/Magpie as WATCH unless a specific benchmark graduates them.
