# Environment Sandbox — Long-Term Foundation Plan

A professional plan for making `BS_GodFile` (UE 5.8) a durable core for an **environment-design portfolio**: fast iteration across many styles, portfolio-quality output, and — critically — *no repeat of the Melodia fragility*. Grounded in current UE5 best practices (sources at end).

**North star:** UE is a *tool*. Optimize for (1) iteration speed, (2) stylistic range, (3) presentation quality, (4) longevity. Stay lean — every system must earn its place.

---

## 1. The longevity rules (lessons from Melodia)
These are guardrails, not suggestions — they're why the old project broke.
1. **Stay on stock UE 5.8.** No engine fork (MooaToon). Stock = official support, working builds, no precompiled-engine dependency, painless upgrades.
2. **Minimize C++/plugin lock-in.** The portfolio should open and work on a fresh stock-engine install. Avoid custom C++ nodes whose absence breaks content (the exact reason the old PCG graphs won't port).
3. **No gameplay systems.** No battle/dialogue/AI. Environments, lighting, materials, scatter, renders. Full stop.
4. **Disk & cache discipline.** Never commit `DerivedDataCache/`, `Intermediate/`, `Saved/`, `Binaries/` (already in `.gitignore`). These are what ballooned `MelodiaMelusina` to 305 GB.
5. **One change at a time, committed.** Small commits, clean working tree. No 200-file uncommitted piles.

## 2. Project structure (feature/style-based, not type-based)
Single root, shallow (3–4 levels). Organize by *what it is in the world*, not asset type.
```
Content/
  EnvSandbox/
    _Template/            # the reusable showcase level + its rig (see §4)
    Materials/            # shared masters, SDF, instances, functions, toon profiles (see MATERIAL_MIGRATION.md)
      Masters/  SDF/  Instances/  Functions/  ToonProfiles/  PostProcess/
    Shared/
      Decals/  HDRIs/  Skies/
    Environments/
      <StyleName>/        # one folder per environment iteration
        Meshes/ Materials/ Textures/ Maps/  (Map: L_<Style>.umap)
    PCG/                  # reusable scatter graphs (§7)
    _Dev/                 # experiments — underscore sorts to top, excluded from cook
  Python/                 # Blender live-link (already staged)
```
External (DCC) side, kept *out* of the repo: `_Source/` (Blender/.blend), `_Reference/`, `_Bake/`, `_Export/` (FBX destined for UE).

## 3. Naming conventions (Epic standard)
Prefixes for instant identification: `SM_` static mesh, `SK_` skeletal, `M_` material, `MI_` material instance, `MF_` material function, `MPC_` material parameter collection, `T_` texture (suffix `_D/_N/_ORM/_M`), `BP_` blueprint, `L_` level, `PCG_` graph. Variants `_01/_02` (zero-padded), sizes `_S/_M/_L`. Match Epic's [official naming doc](https://dev.epicgames.com/documentation/en-us/unreal-engine/recommended-asset-naming-conventions-in-unreal-engine-projects).

## 4. The `_Template` level (the iteration multiplier)
One polished, reusable level you **duplicate per style** — this is what makes "many iterations" fast:
- **Lighting rig:** Directional + Sky + SkyAtmosphere + height fog + a couple of local lights; Lumen GI/reflections (already on).
- **Post-process volume (unbound):** the **Substrate Toon Profile** + a **post-process outline** material; exposure locked (no auto-exposure surprises); AgX/ACES tonemap.
- **MegaLights** enabled for cheap many-light scenes.
- **CineCamera + flythrough** (Camera Rig Rail or Sequencer) wired for Movie Render Graph.
- Workflow: `Duplicate _Template → rename L_<Style> → block out → scatter → light → render`.

## 5. Material architecture (Substrate toon)
Keep it to a **small set of master materials**, not hundreds:
- `M_Toon_SDF` (SDF batch 1 — Substrate Toon + world-band proxy), then `M_Master_Toon`, `M_Master_PBR`, `M_Master_Foliage`, `M_Master_Glass`. See `Docs/MATERIAL_MIGRATION.md`.
- Reusable logic in **Material Functions** (`MF_`); per-surface variation via **Material Instances** (`MI_`) — never new master materials per asset.
- **Outline** = shared post-process material (not per-mesh).
- ⚠️ **Limit static switches.** 10 chained switches = 1024 shader permutations → brutal compile times. Use switches only for high-impact toggles; use scalar params for the rest.
- Substrate Toon is **experimental** in 5.8 (Blendable GBuffer legacy mode) — fine for a portfolio; verify the Toon BSDF + Toon Profile flow in-editor before committing to it.

## 6. Asset pipeline (Blender → UE)
- **Source of truth = Blender.** Bring meshes via FBX export or the staged Blender→UE live-link (Python 3.11, confirmed compatible with 5.8).
- Consistent **scale/units** (1 uu = 1 cm), clean pivots, real-world sizing.
- **Nanite** for high-poly meshes (no manual LODs / lightmap UVs needed under Lumen).
- Megascans / kit assets via the **Fab** plugin into `Shared/` or `_Source/`.

## 7. PCG strategy (rebuild lean, don't port the C++ graphs)
- Enable `PCG` + `PCGExtendedToolkit`.
- **Rebuild** a small library of *stock-node* scatter graphs: `PCG_FoliageDensity` (surface sampler + falloff), `PCG_RockScatter`, `PCG_WallDetail`. These are version-portable and won't break on a fresh engine.
- The old custom-C++ graphs (`DreamWalls` Bezier system) are **reference only** — re-implement their intent with stock + PCGEx nodes.

## 8. Rendering & presentation
- Lumen + Nanite + Virtual Shadow Maps + MegaLights (all already configured).
- **Movie Render Graph** (production-ready in 5.8) for beauty stills + flythroughs.
- Consistent color management (AgX/ACES), fixed exposure, output specs sized for ArtStation (e.g. 2560×1440 stills, 1080p/4K video).
- Per environment: 3–5 hero stills + one flythrough = a portfolio piece.

## 9. Source control
- Private repo **`environment-portfolio`** (created), Git LFS for binaries, the UE `.gitignore` already excludes transient dirs.
- Commit per meaningful milestone; one environment or system per branch if experimenting.

## 10. Roadmap
- **Phase 0 — Foundation (now):** repo ✅, structure, `M_Master_Toon` + Toon Profile, the `_Template` level, plugin enables.
- **Phase 1 — First piece:** one complete styled environment end-to-end (greybox → scatter → light → render) to validate the whole loop.
- **Phase 2 — Library:** reusable scatter graphs, master-material variants, 3–4 style templates (e.g. baroque / brutalist / art-nouveau, leveraging the Blender greybox toolset).
- **Phase 3 — Portfolio polish:** consistent presentation, breakdowns, ArtStation.

## 11. Immediate next actions
1. Enable plugins in `BS_GodFile`: `PCG`, `PCGExtendedToolkit`, `MovieRenderPipeline`, `GeometryScripting`, `Fab`, (`Water` optional) + Python Editor Script Plugin + Editor Scripting Utilities; restart.
2. Set `r.MegaLights.EnableForProject=1`.
3. Verify Substrate Toon (Toon BSDF + Toon Profile) in-editor → build `M_Master_Toon`.
4. Build the `_Template` level (§4).
5. Follow [`TOON_MIGRATION_RUNBOOK.md`](TOON_MIGRATION_RUNBOOK.md) — Batch 3: convert copied SDF masters to Substrate Toon.

---
*Sources: Epic naming conventions; UE5 project-structure guides (Auke Huys, StraySpark, Hyperdense); UE 5.8 release notes / Substrate Toon docs. Links provided in chat.*
