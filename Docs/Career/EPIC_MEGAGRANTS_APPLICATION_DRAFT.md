# Epic MegaGrants — Application Draft

> **Downstream of the game.** This is marketing / funding / hiring material for
> **Melodia Melusina**, a single-person AAA-tier UE 5.8 rhythm-JRPG. It exists to fund and staff
> the game. **No agent may cite anything in this folder as project direction** — authority is
> [`../../../PROJECT.md`](../../../PROJECT.md).

Apply at: https://www.unrealengine.com/en-US/megagrants (Epic reviews on a rolling basis, typically 4–8 weeks to first response — apply now, keep building in parallel, don't wait on it).

---

## Project Name
Environment Portfolio Platform (working title — swap in whatever you're calling the live repo/site)

## One-line pitch
A procedural, toon-shaded environment art pipeline for UE 5.8 — a single reusable Substrate master material system, a 140+ graph PCG production library, and Python-driven build tooling — used to author a growing catalog of stylized environments, with select material/mesh packs shipping as standalone assets for other UE developers.

## Project stage
Active development, self-funded, solo. [X] environments built to varying completion (list your real count — the showcase levels: L_EscherAscent, L_FallenMoon, L_KaleidoNave, L_InfiniteScore, L_CelestialPond, L_VinylGalaxy, ZenForestTest, L_SakuraPath). First commercial assets (Gumroad kitbash packs, FAB material pack) in packaging now.

## What you're actually building (be concrete, this is your strongest material)
- **One production master material** (`M_Master_Toon_Universal`) — Substrate-based stylized/toon shading, ~685 nodes, 18 texture slots, ~192 exposed parameters across 12 style families, used across every environment in the project instead of one-off per-scene shaders.
- **A 140+ graph PCG production library** (`Content/EnvSandbox/PCG/`) — reusable scatter/density/exclusion-mask graphs organized by style (Baroque, Escher, Sakura, Cosmic, WP/world-partition pillars) plus a validated walkability/route-width mask system for player-navigable procedural spaces.
- **61 hand-authored procedural SDF "math-art" toon materials** — raymarched geometry (Klein bottle, Möbius strip, Mandelbulb, Penrose staircase, gothic rose windows) as pure material-graph math, no textures required.
- **Python build tooling** (`Content/Python/`, ~900+ scripts) — headless level generation, material batch operations, PCG graph assignment, portfolio/render pipeline automation. This is a genuine procedural-authoring pipeline, not one-off editor scripting.
- Currently standing up **Movie Render Queue** for AAA-grade portfolio stills (4K, 16-bit EXR) from this pipeline.

## Why UE
Because the toon/Substrate shading pipeline, PCG toolkit, and Python scripting surface together let one person build and iterate on environment art at a pace that would otherwise need a small team — which is the actual thesis of this project and the reason it's worth funding: it's a demonstration that a solo environment artist with the right tooling can produce a real content pipeline, not just individual scenes.

## Funding request
$[fill in — MegaGrants historically ranges roughly $5K–$500K; for a solo dev at this stage, framing a request in the $10K–$25K range against a specific 3–6 month deliverable (e.g. "ship 6 portfolio-grade environments + release 3 asset packs on FAB") is realistic and reviewable]

## Use of funds
- Sustained AI-assisted development time (agentic coding/tooling costs — be honest and specific here, it's a legitimate line item for a solo technical artist)
- [hardware/software if relevant — e.g. a render/compute upgrade]
- Living costs while completing final year at Humber College (3D Animation program) alongside this work — optional to include, some devs do, your call on how personal to get

## Links
- [Portfolio site URL]
- [GitHub/repo URL if public, or offer private access on request]
- [ArtStation / FAB / Gumroad links once live]

## About you
Final-year 3D Animation student, Humber College (Toronto). Background spans environment art (UE 5.8), ZBrush sculpting, traditional painting, and Python-based procedural world-building — this project is the intersection of all three: art direction, technical art, and tools engineering in one pipeline.

---

## Before you submit — fill in the brackets
1. Real funding number (pick one, don't leave it vague — reviewers respond better to a specific ask tied to a specific deliverable than an open-ended one).
2. Actual portfolio/site URL — if you don't have a public one yet, that's the highest-priority thing to stand up before or immediately after submitting (Epic will look).
3. Decide how personal you want "use of funds" to get. Naming AI tooling costs honestly is fine and increasingly normal for solo tech artists — naming living costs is optional, your call.
4. Attach 3–5 of your strongest images once the MRQ render pass produces real portfolio stills (L_EscherAscent and L_FallenMoon are your fastest path to those per the earlier art-director review — no BasicShapes, real meshes, lighting rig already in place).
