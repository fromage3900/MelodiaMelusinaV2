# PCG Portfolio Handoff — for DeepSeek — 2026-07-26

## Read this first

This project is in an active **portfolio-first push** (see `Docs/PROJECT_STATUS_2026-07-25.md` and `Docs/QUEUE.md`). The goal is AAA-quality environment-art renders for hire/income, not gameplay systems. **Do not touch `Plugins/MelodiaCore`, battle/dungeon/save/C++ systems, or anything under the "PAUSED — gameplay" section of `Docs/QUEUE.md`.** That work is intentionally frozen, not abandoned. Your scope is the PCG/environment-art side only.

## The lens for this work: depth over breadth

The project already has **136+ PCG graphs** on disk under `Content/EnvSandbox/PCG/`, spanning a dozen biome styles: Baroque, Escher, Grotto, Sakura, Alpine, Cosmic, Cyberpunk, Desert, plus several World-Partition (`WP`) variants. Breadth is done. What's missing is **verified depth**: almost none of these have been confirmed, this session or recently, to actually compile clean, populate non-empty, and render as a walkable, photographable scene.

**Do not add more PCG graphs or biome styles.** The instruction from the project owner, verbatim: *"for a portfolio, 2-3 flawless, fully-rendered vertical slices beat 30+ half-verified graphs."* Your job is to take 2-3 existing graphs from "exists on disk" to "proven, rendered, portfolio-ready," and to clean up the two known structural-health issues below. That's it.

## Recommended flagship candidates (pick 2-3, don't spread wider)

1. **Baroque cathedral family** (`Content/EnvSandbox/PCG/Styles/Baroque/`) — the deepest, most mature style: `PCG_CathedralNave`, `PCG_Cloister`, `PCG_BaroqueColonnade`, `PCG_M1_GrammarNave_BS`, plus Bezier-path variants (`PCG_BezierCathedralAxis`, `PCG_BezierCloisterRing`). A prior session got a 25-instance greybox cathedral genuinely walkable and real-scale — verify that state still holds, then push it to final materials/lighting/render.
2. **Escher / impossible-geometry family** (`Content/EnvSandbox/PCG/Styles/Escher/`) — `PCG_PenroseShrine`, `PCG_FloatingStairways`, `PCG_DreamWalls`, `PCG_EscherDecks`, `PCG_EscherPenroseStairEx`, `PCG_EscherFloatingIslandEx`, `PCG_EscherGravityBridgeEx`, `PCG_EscherImpossibleArchEx`. This ties in directly with fresh work: `/Game/EnvSandbox/VFX/NS_EscherTorusKnot`, a real (p,q) torus-knot Niagara system (genuine knot-theory math — provably closes because p,q are integers, no fake seam) placed in `L_EscherAscent` at `[7500,800,3000]`. Consider whether a PCG graph could scatter *parameter variations* of that VFX (different p/q pairs, radii) along a spline for a whole "impossible geometry" showcase — that's a natural, low-risk extension of tonight's work, not new invention.
3. **Sakura** (`Content/EnvSandbox/PCG/Styles/Sakura/`) — `PCG_Sakura_Showcase`, `SMC_Sakura_ScatterKit`, plus WP petal/blossom variants. Per `Docs/QUEUE.md`, Phase 1 (petals) was done and placed; this is the closest to already-finished if you want a faster third slice.

Whichever 2-3 you pick, **verify each one this way, not by trusting an old script's self-report**:
- Load the level in a live editor session (not headless — `Docs/QUEUE.md`'s OPEN section already flags headless log-visibility problems).
- Confirm the PCG component actually generates non-empty output (`PCGComponent.Graph` is reflection-protected — use the real `set_graph()` API if you need to reassign anything, not `set_editor_property`, per a real bug hit and fixed in the M1 pass).
- Confirm it's walkable at real-world scale (no giant/tiny scaling artifacts).
- Get a real render out of it via the existing pipeline (`Content/Python/render_exporter.py` is confirmed working end-to-end this session; `Content/Python/scene_metadata_exporter.py` has a known unresolved null-output bug — non-blocking, don't chase it, `render_exporter.py` is the one that actually produces pixels).

## Two known structural-health issues to resolve (already scoped, in `Docs/QUEUE.md` NOW section)

1. **`Docs/PCG_CATALOG.md` is stale** — it describes a graph library that has since been fully renamed/reorganized; zero current graph names match it. Rewrite it against the *actual* current `Content/EnvSandbox/PCG/` tree (the file list above is a real, current snapshot — start there).
2. **`PCG_RockScatter` vs `PCG_Universal_RockScatter`** — confirmed NOT an accidental duplicate (both have independent builder scripts and are independently referenced elsewhere), but the naming is confusing and needs a real decision, not an auto-resolve. Pick one naming convention and document the reasoning in the rewritten catalog.

## Fresh assets from tonight's session (for context, not necessarily in scope)

- `M_Toon_SDF_Merged` — SDF/toon master, recently extended with a genuine quasicrystal (De Bruijn multigrid) interference pattern and procedural PBR derivation (height/roughness/normal all derived from the same math driving the color bands, not textures). 37 instances, all verified.
- `M_Water_Master_Grand_v7` / `M_WaterCausticsProjector_v7` — user's own water shader rework, reviewed and one real bug fixed (`CausticTint` was fully transparent).
- `M_PP_ToonOutline` / `M_PP_StorybookVines` — post-process outline materials, now with `CustomStencil`-based selective gating (`OutlineStencilGateAmount` param) so outlines can target specific hero props instead of the whole screen.
- `NS_EscherTorusKnot` — see above.

## A real gotcha you will likely hit

Monolith's `build_material_graph`/`create_module_from_hlsl` actions **silently drop `parameter_name`/`default_value`/`SceneTextureId` fields on newly-created nodes**, and partially drop boolean mask flags on new `ComponentMask` nodes (defaults to R+G regardless of what you pass). This isn't PCG-specific but you'll hit the equivalent class of "the tool said success but the thing it created doesn't have the name/value you gave it" — always verify with a follow-up `get_expression_details`/`get_instance_parameters`-equivalent read after any creation call, before trusting it.

## What "done" looks like

2-3 PCG scenes, each: loads clean, generates real non-empty output, walkable at correct scale, rendered through the real pipeline into `portfolio_package.json` per `ART_DIRECTOR_REVIEW.md`'s shot list (hero still → material grid → breakdown/wireframe → procedural-axis diagram → perf spec card). Plus a rewritten `PCG_CATALOG.md` that matches reality, and a documented decision on the RockScatter naming. Nothing else — no new biome styles, no new graphs, no gameplay-adjacent PCG work.
