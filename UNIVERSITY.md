# Melodia BS_GodFile — University & Portfolio Entry Point

> **Solo-developed rhythm-JRPG prototype** in Unreal Engine 5.8 with a procedural Geometry Nodes pipeline in Blender 5.2.
> The game's world is generated from MIDI files — music becomes terrain, rhythm becomes gameplay.

---

## What is this?

A game where you play as Melusina, a singing water-spirit, in a world made of music.
- **Dialogue** triggers **JRPG battles** with **rhythm-timed** inputs
- **Outfits** carry presentation AND gameplay meaning (wardrobe system)
- **The world itself** is procedurally generated from MIDI files
- **Everything reacts to music** — materials, fabric, terrain, particles

Built solo over 2+ years. ~130GB, 13,000+ files, 60+ Geometry Nodes builders, full C++ UE integration.

---

## What's in it?

### Core Systems

| System | Tech | Location |
|--------|------|----------|
| **60+ GN Builders** | Blender 5.2 Geometry Nodes | `deploy/surreal_arch/melodia_gn/` |
| **MIDI→World Pipeline** | Blender addon | `Tools/BlenderAddons/melodia_studio/` |
| **Kawaii GN** | Cute/chibi procedural assets | `Tools/BlenderAddons/blender_kawaii_gn/` |
| **Brutalist GN** | Monolithic architecture | `Tools/BlenderAddons/blender_brutalist_gn/` |
| **FACS Face Rig** | 68 morph targets, 15 visemes | `Tools/build_melusina_face_rig.py` |
| **Mocap Pipeline** | Rokoko → UE retarget | `Content/Python/import_rokoko_mocap.py` |
| **Audio-Reactive Subsystem** | UE C++ | `Source/BS_GodFile/MelodiaIntegration/` |
| **Cymatic Fabric** | Chladni eigenmodes | `Source/BS_GodFile/MelodiaIntegration/MelodiaCymaticsSubsystem` |
| **QuillScript** | Custom narrative language | `Plugins/QuillScript/` |
| **Monolith MCP** | 1330+ editor actions | `Plugins/Monolith/` |

### Content

| Content | Location |
|---------|----------|
| **Melusina character** (v25, split-mesh, weighted) | `Content/Melodia/Characters/Melusina/` |
| **30+ mocap clips** (dance, combat, locomotion) | `Content/Melodia/Characters/Melusina/Animations/Mocap/` |
| **Locomotion set** (idle/walk/run/jump) | `Content/Melodia/Characters/Melusina/Animations/Locomotion/` |
| **ZunZun family NPCs** (VRM) | `Content/NPCs/VRM_Sources/` |
| **Music** (MIDI + OpenUtau USTX) | `studio/tracks/` |
| **Melusina's voice** (UTAU bank) | `Documents/OpenUtau/Singers/Melusina JA VCV/` |

---

## How to Read This Repo

### For Professors / Collaborators
1. **`QUICKSTART.md`** — run something in 5 minutes
2. **`Docs/Research/GEOMETRY_NODES_COMPLETE_REFERENCE.md`** — every GN system, mapped
3. **`Docs/Production/CHARACTER_ANIMATION_2_SEMESTER_PLAN.md`** — 2-semester animation plan
4. **`Docs/Research/EMERGING_TOOLCHAIN_MASTER_INDEX_2026-08-31.md`** — what exists, what's research

### For Technical Interviews
1. **`PORTFOLIO.md`** — reel + breakdowns
2. **`Docs/Portfolio/SYSTEMS.md`** — "here's what I built" (coming soon)
3. **`Source/BS_GodFile/MelodiaIntegration/`** — C++ bridge code
4. **`Tools/BlenderAddons/melodia_studio/`** — largest single addon

### For Job Applications (Animation)
1. **`PORTFOLIO.md`** — reel link
2. **`Docs/Production/CHARACTER_ANIMATION_2_SEMESTER_PLAN.md`** — production plan
3. **`Content/Melodia/Characters/Melusina/Animations/`** — raw clips

---

## Key Documents

| Document | What |
|----------|------|
| [Geometry Nodes Reference](Docs/Research/GEOMETRY_NODES_COMPLETE_REFERENCE.md) | Every GN system, mapped and detailed |
| [Emerging Toolchain SSOT](Docs/Research/EMERGING_TOOLCHAIN_MASTER_INDEX_2026-08-31.md) | What exists, what's research, what's external |
| [Animation Plan](Docs/Production/CHARACTER_ANIMATION_2_SEMESTER_PLAN.md) | 2-semester production plan |
| [Long-Term Infrastructure](Docs/Production/LONG_TERM_INFRASTRUCTURE_PLAN.md) | LFS, laptop, portfolio strategy |
| [P0 Closeout Plan](Docs/P0_CLOSEOUT_PLAN_2026-08-28.md) | Integration architecture |
| [Orchestra Convergence](Docs/ORCHESTRA_CONVERGENCE_2026-08-20.md) | Authority map (who owns what) |

---

## Demo

Reel coming Semester 2 (Week 9-10).

Current work-in-progress clips:
- `Content/Melodia/Characters/Melusina/Animations/Mocap/A_Mocap_LittleDance.uasset`
- `Content/Melodia/Characters/Melusina/Animations/Mocap/A_Mocap_Dodge.uasset`
- `Content/Melodia/Characters/Melusina/Animations/Locomotion/A_Melusina_Idle_Mocap_RootX.uasset`

---

## My Role

**Solo developer.** I built everything except:

| Excluded | Why |
|----------|-----|
| `Content/TurnBasedJRPGTemplate/` | Stock UE template (heavily modified) |
| `Content/_ThirdParty/` | Third-party assets |
| `Plugins/VRM4U/` | VRM import plugin (vendored) |
| `Plugins/HoudiniEngine/` | SideFX plugin (vendored) |
| `Plugins/Claireon/` | Vendored AI plugin (open source) |
| `Content/EnvSandbox/` | Test environment (not shippable) |

---

## Tech Stack

| Layer | Technology |
|-------|------------|
| **Game Engine** | Unreal Engine 5.8 |
| **3D Modeling** | Blender 5.2 |
| **Procedural** | Geometry Nodes (60+ builders) |
| **Programming** | C++ (UE subsystems), Python (tooling) |
| **Animation** | FACS face rig, Rokoko mocap, IK Retargeter |
| **Audio** | OpenUtau (UTAU), FL Studio, TouchDesigner |
| **Voice** | Melusina JA VCV (VC renders) |
| **Version Control** | Git + Git LFS |
| **Documentation** | Markdown (Docs/) |

---

## Contact

- **GitHub:** [fromage3900](https://github.com/fromage3900)
- **Portfolio:** [coming soon]
- **Reel:** [coming Semester 2]

---

*Last updated: 2026-09-03*
