# UE 5.8 Lookdev Pipeline Research — 2026-09-17

**Kind:** research (durable reference). Not a plan, not a status document. Status lives only in [`CURRENT_STATE.md`](../../CURRENT_STATE.md).
**Scope:** what UE 5.8 changed for lookdev and procedural worldbuilding, what Infinity Nikki actually does under the hood, and an ADOPT / PARK / REJECT gate per item for Melodia. Every gate is a proposal for the owner; nothing here changes the frozen identity (PPV V7.1 stack, `M_Master_Toon_Character`, `M_Master_Toon_Universal`, hero stencil 4).

---

## 1. Verification ladder used here

| level | meaning |
|---|---|
| **EPIC-VERIFIED** | stated by Epic in the 5.8 release post / forum release notes (2026-06-17) |
| **COMMUNITY-REPORTED** | reported by multiple users on the Epic forums or a tutorial; not yet reproduced in this project |
| **PROJECT-VERIFIED** | reproduced in `BS_GodFile` on 2026-09-17 with a receipt under `Saved/Audit/` |

Sources: [UE 5.8 release post](https://www.unrealengine.com/news/unreal-engine-5-8-is-now-available), [5.8 released — forum thread with release notes](https://forums.unrealengine.com/t/unreal-engine-5-8-released/2729274), [5.8 preview thread](https://forums.unrealengine.com/t/unreal-engine-5-8-preview/2721597), [CG Channel 5.8 summary](https://www.cgchannel.com/2026/06/see-5-key-features-for-cg-artists-in-unreal-engine-5-8/), [Substrate Toon walkthrough](https://www.projprod.com/post/unreal-engine-5-8-substrate-toon-shader), [Epic developer interview: Infinity Nikki](https://www.unrealengine.com/developer-interviews/behind-the-scenes-of-infinity-nikki-tracing-a-glamorous-turn-to-an-unreal-open-world), [Silicon Studio: Enlighten in Infinity Nikki](https://www.siliconstudio.co.jp/en/news/pressreleases/2025/250206InfinityNikki/250206InfinityNikki.html).

Context that shapes every gate: Epic has described 5.8 as the **last planned major** UE5 release before UE6 (forum thread, developer replies). That is not a claim that no further UE5 patches will ship. **Experimental** in 5.8 may never become production-ready inside UE5. Treat experimental features as variants beside the frozen identity, never as replacements.

---

## 2. UE 5.8 facts

### 2.1 Rendering / materials

| item | state in 5.8 | verification | notes |
|---|---|---|---|
| **Substrate Toon BSDF** | Experimental | EPIC-VERIFIED | New `SubstrateToonBSDF` material expression; "supports the full range of UE5 target platforms". No forward-rendering support (CG Channel). |
| **Toon Profile** asset | Experimental | COMMUNITY-REPORTED | Diffuse ramp, specular ramp, shadow transition/tint, GI response, experimental shadow hatching. Reported rough edges: blurry / black-striped VSM shadows, Toon Profile overrides not surviving editor restart. |
| Built-in outline | Absent | COMMUNITY-REPORTED | Tutorials pair the Toon BSDF with an Overlay Material outline. Melodia already owns its outline in the frozen PPV stack (Outline V7 after tonemapping) and hero stencil 4 — the PPV is the outline authority. |
| **MegaLights** | Production-Ready | EPIC-VERIFIED | Reduced noise, 60 fps target on current consoles, SSS, froxel translucency, lighting channels, cloud shadows, new debug tools. Project already sets `r.MegaLights.EnableForProject=True` (`Config/DefaultEngine.ini:43`). |
| **Lumen Lite** | New | EPIC-VERIFIED | Irradiance-field GI with probe occlusion, "up to 2x faster than Lumen High Quality"; handheld / low-end PC target. |
| **Fog Screen Space Scattering** | New | EPIC-VERIFIED | Better lit fog / smoke / dust. Relevant to `NS_Morning_Mist` style sheets. |
| Substrate AxF import | New | EPIC-VERIFIED | X-Rite AxF scanned materials into Substrate. Not relevant to a toon identity. |
| Substrate in project | on | PROJECT-VERIFIED | `r.Substrate=True`, `r.Substrate.ProjectGBufferFormat=0` (`Config/DefaultEngine.ini:50-51`). `M_MelodiaPlant_Wind` (Muse-brief plant master, uncommitted) already contains a `MaterialExpressionSubstrateToonBSDF` and renders in `L_MelusinaMorning` via the `MI_RainbowPetal_Wind_B0..B6` family (`Saved/Audit/Screens/world_compiler_morning_wind_*`). So Substrate Toon is already *in* Melodia — on plants, not on the frozen character/universal masters. |

### 2.2 Worldbuilding / procedural

| item | state in 5.8 | verification | notes |
|---|---|---|---|
| **Mesh Terrain** | Experimental | EPIC-VERIFIED | True 3D mesh terrain (overhangs, islands, tunnels); nondestructive modifiers; "fully interoperable with PCG". Tightly integrated with World Partition + OFPA; non-WP use is possible but not the recommended path. Crash fix on extreme tessellation shipped with a 100M-element cvar cap. Project already targets it in `Docs/WorldGen/TERRAIN_HANDOFF_CONTRACT.md`. PCG should sample via World Ray Hit / Mesh Partition Query, not Landscape nodes. |
| **PCG nondestructive manual edits** | New | EPIC-VERIFIED | Select / exclude / modify / restore generated instances; Data Overrides window per node; Query and Isolate tools. Edits survive regeneration. |
| PCG complex attribute types | New | EPIC-VERIFIED | Arrays, structs, sets, maps as attributes; new spatial example graphs (buildings, streets). |
| PCG Editor Mode | Experimental | COMMUNITY-REPORTED | Spline / spline-surface / paint / volume placement tools; the graph still owns generation. |
| **Fast Geometry Streaming** (FastGeo) | New | EPIC-VERIFIED | Rapid loading of static, non-gameplay assets. PCG componentless ISMs ride on it; the 09-15 soft-release popping report is COMMUNITY-REPORTED — the World Compiler keeps component ISMs (contract §6). |
| **Procedural Vegetation Editor** | Experimental | EPIC-VERIFIED | Nanite-ready vegetation, external mesh import with skeleton extraction, 2D sketch / photo input, wind, embedded PCG subgraphs. Preview-thread reports: gravity nodes broke 5.7 samples, "Make Static Mesh" from PVE SKMs broken, non-Nanite export ignored. Plugin already enabled (`BS_GodFile.uproject:174`). |
| **Unreal MCP plugin** | New | EPIC-VERIFIED | LLM → editor. Forum report: toolset registries must be enabled by hand or it does nothing. Melodia already runs Monolith (:9316) as its single editor bridge; a second bridge is a second authority. |
| Movie Render Graph | Production-Ready | EPIC-VERIFIED | Graph-based cinematic rendering, render layers. Fits the fixed-frame A/B rig below. |

### 2.3 PCG facts learned in this project on 09-17 (PROJECT-VERIFIED, receipts in `Saved/Audit/world_compiler_morning_rainbow_bloom_proof_2026-09-17.json`)

- `PCGGraph` Output node's *input* pin is labelled `Out`; `add_edge(..., "In")` returns True and wires nothing. Read the label back.
- `Load Data Table` attribute mapping (`FPCGAttributePropertyInputSelector`) is not authorable from UE Python (protected members, by-value copies); Monolith `blueprint.set_property_at_path` with `PCGBegin($Position)PCGEnd` import text works.
- UE `FName` is case-insensitive: a `Scale` column aliases a `scale` column in a DataTable and every instance lands at the origin.
- `PCGMeshSelectorByAttribute.MaterialOverrideAttributes` is positional (index == material slot). Two-slot flower kits need a neutral stem attribute at index 0.
- The CSV importer silently drops columns the row struct lacks; read every column back.
- PCG caches the DataTable: `pcg.FlushCache` before regenerate or the old rows come back.

---

## 3. Infinity Nikki as the visual/wardrobe bar (what they actually ship)

From the Epic developer interview and Silicon Studio's release. GPU-driven vegetation, OIT, ShellFur, Enlighten, and restrained post are **PUBLISHER-REPORTED**. Two plan claims did **not** verify against a primary source and stay unlabeled: "no Nanite" and a "multi-lobe fabric system" (the interview describes four-layer UV-blended fabric textures, not lobes).

- **GPU-driven vegetation renderer.** Infold: compute + rasterization culling per instance, LOD on GPU, `DrawIndirect` / `MultiDrawIndirect` batches, GPU feedback to the CPU to cull draws and stream mesh LODs — "millions of vegetation instances". Reviewers note LOD pop-in on trees; that is not proof the project shipped without Nanite.
- **Fabric**: one master material with **four-layer UV-blended fabric textures**, minimal parameters to cover cotton / linen / silk / satin / velvet / flannel; custom reflection and **sparkle response** models for gauze and silk. Keep that idea in `specs/materials/m_fabric_melusina.v1.json`, not a new master.
- **Jewelry**: a dedicated gemstone material — refraction, 3S transmission, variable specular highlights.
- **Transparency**: re-engineered **Order-Independent Transparency** for layered sheer fabrics.
- **Fur**: runtime **ShellFur** layers, shell count by screen size.
- **Cloth**: Chaos Cloth plus a proprietary constraint-based skeletal-chain solver and real-time clipping fixes.
- **Lighting**: **Enlighten** GI (chosen 2022), critical on mobile interiors; custom tone mapping; deliberately restrained post.
- **UV animation** on hero outfits: custom mitigation of engine motion blur on animated UVs; three-orbit celestial motif system.

What this means for Melodia: the Nikki bar is not a feature list, it is *restraint plus one bespoke system per fabric family*. Melodia already has `bNikkiHero`, `FabricType`, `FabricAnisoLevel`, `FabricWeaveScale`, `Iridescence*`, `Sparkle*`, `Glint*`, `Gemstone*` on `M_Master_Toon_Universal` (probe 09-17: 300+ scalar params). The gap is not parameters, it is **per-family presets and proof stills**, i.e. specs under `specs/materials/`, not a new master.

---

## 4. Gates for Melodia (ADOPT / PARK / REJECT — owner decides)

| # | item | recommendation | bounded test | stop rule |
|---|---|---|---|---|
| G1 | Substrate Toon BSDF + Toon Profile on the **frozen** character / universal masters | **REJECT as migration; ADOPT-as-variant only** | The A/B lane in §5 (one petal MI twin beside the current master, same frame). | No edit to `M_Master_Toon_*`, PPV, or hero stencil. Toon Profile restart bug must be re-tested on this build before any variant is used in a shipped level. |
| G2 | Substrate Toon on **plants** (`M_MelodiaPlant_Wind`) | **ADOPT (already live)** | Wind A/B stills exist. Owner judges the MF hue-reveal weight at PIE under day lighting. | Stays a plant master; never re-parent characters to it. |
| G3 | MegaLights on `L_MelusinaMorning` | **ADOPT — cheap test first** | Toggle `r.MegaLights` in a PIE session; capture the dolly frame; check toon-band interplay and the existing −5.4 exposure warning. | If the frozen PPV outline or stencil read changes, PARK. |
| G4 | Lumen Lite | **PARK** | None now. | Revisit only if a handheld / low-end target appears in `CURRENT_STATE.md`. |
| G5 | Mesh Terrain for compiled worlds | **ADOPT (already contracted)** | `TERRAIN_HANDOFF_CONTRACT.md` path; PCG samples through World Ray Hit / Mesh Partition Query, not Landscape nodes. The World Compiler's `ground_probe` stage is the interim (no dell floor exists in Morning today — contract §2). | Experimental: bake a static-mesh fallback for any shipped level. |
| G6 | PCG nondestructive edits + Data Overrides | **ADOPT for art direction over compiled fields** | Move / exclude a handful of compiled blooms in `WC_morning_rainbow_bloom_Field`, regenerate, confirm they persist. | The compiler's DataTable stays the source; overrides are documented exceptions with an owner and a reason. |
| G7 | PCG hierarchical generation for Sea Above and compiled worlds | **ADOPT at bake time** | Biome grid 51,200 / feature 25,600 (Resonant World chunk size) / dressing 12,800; runtime generation only in Sea Above open water. | No runtime generation in interiors. |
| G8 | FastGeo componentless ISMs | **PARK** | Re-test the soft-release popping report on this build with the compiled Morning field. | Component ISMs until the popping is gone. |
| G9 | Procedural Vegetation Editor | **PARK** | Plugin stays enabled; no PVE assets in shipped levels until the 5.7→5.8 sample breakage and non-Nanite export are fixed. | SpeedTree lane (`stage_melodia_speedtree_plants.py`) remains the meadow source. |
| G10 | Unreal MCP plugin | **REJECT for now** | None. | Monolith is the single editor bridge; a second bridge is a second authority. |
| G11 | Nikki fabric bar | **ADOPT as specs, not masters** | `specs/materials/m_fabric_melusina.v1.json` presets per fabric family (cotton, silk, satin, velvet, gauze) on the existing `FabricType/Aniso/Weave/Sparkle` params; one proof still per family in the §5 rig. | No new master, no fifth parameter family. |
| G12 | GPU-driven instancing (Nikki) | **REJECT** | None. | Nanite + ISM + World Partition are the project lane; a custom renderer is out of scope for a solo team. |
| G13 | Fixed-frame lookdev turntable rig | **ADOPT** | §5. | Every A/B (Substrate toon, MegaLights, hue reveal, fabric presets) uses the same frame or it does not count as evidence. |

---

## 5. The fixed-frame A/B rig

Purpose: every lookdev decision compares two things in **one frame** with fixed exposure, or it is opinion.

- **Scratch map** `/Game/Melodia/Lookdev/L_Lookdev_ToonAB` (never a shipped level).
- **HDRIBackdrop** (plugin) or a fixed SkyLight + DirectionalLight pair when the plugin is absent; `PostProcessVolume` unbound with fixed manual exposure, OCIO off (a second pass with OCIO on when the pipeline needs it).
- **Subjects**: the same mesh twice (`flower_redA` at scale 3, and `MI_ChoralSheep_Body` when a character read is needed); A = current master MI, B = variant MI. Both in frame, same rotation, 200 cm apart.
- **Capture**: `SceneCapture2D` → `ImageWriteBlueprintLibrary.export_to_disk` (the path that worked on 09-17; `AutomationLibrary.take_high_res_screenshot` wrote nothing) or Movie Render Graph stills when a sequence is involved. Frame names carry the date and the A/B pair.
- **Receipt**: `Saved/Audit/lookdev_ab_<pair>_<date>.json` with the two MI paths, the parent masters, the exposure, the CVars toggled, and the still paths. Verdict field is `ADOPT-as-variant | PARK | REJECT`, written by the owner, never by an agent.

First run of the rig (Substrate Toon plant master vs `M_Master_Toon_Universal`, band B3) is recorded in `Saved/Audit/lookdev_ab_substrate_toon_2026-09-17.json` when it lands; see `CURRENT_STATE.md` for its evidence level.
