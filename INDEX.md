# BS_GodFile — Curated Index
> Single entry point for navigating 13,000+ files.
> **Updated:** 2026-09-03 — 15 new docs added today.

---

## Getting Started

| File | What |
|------|------|
| [UNIVERSITY.md](UNIVERSITY.md) | For professors/collaborators — what is this, what's in it |
| [PORTFOLIO.md](PORTFOLIO.md) | For job applications — reel, breakdowns, stills |
| [QUICKSTART.md](QUICKSTART.md) | Run something in 5 minutes |
| [INDEX.md](INDEX.md) | This file — master index |

---

## Systems

| System | Location | Doc |
|--------|----------|-----|
| **Melodia GN** (60+ builders) | `deploy/surreal_arch/melodia_gn/` | [GN Reference](Docs/Research/GEOMETRY_NODES_COMPLETE_REFERENCE.md) |
| **Melodia Studio** (MIDI→World) | `Tools/BlenderAddons/melodia_studio/` | [GN Reference](Docs/Research/GEOMETRY_NODES_COMPLETE_REFERENCE.md) |
| **Kawaii GN** (cute assets) | `Tools/BlenderAddons/blender_kawaii_gn/` | [GN Reference](Docs/Research/GEOMETRY_NODES_COMPLETE_REFERENCE.md) |
| **Brutalist GN** (concrete) | `Tools/BlenderAddons/blender_brutalist_gn/` | [GN Reference](Docs/Research/GEOMETRY_NODES_COMPLETE_REFERENCE.md) |
| **FACS Face Rig** | `Tools/build_melusina_face_rig.py` | [Animation Plan](Docs/Production/CHARACTER_ANIMATION_2_SEMESTER_PLAN.md) |
| **Mocap Pipeline** | `Content/Python/import_rokoko_mocap.py` | [Mocap Guide](Docs/Production/MOCAP_PIPELINE_GUIDE.md) |
| **Audio-Reactive** | `Source/BS_GodFile/MelodiaIntegration/` | [Audio Guide](Docs/Production/AUDIO_REACTIVE_GUIDE.md) |
| **Cymatic Fabric** | `MelodiaCymaticsSubsystem` | [Audio Guide](Docs/Production/AUDIO_REACTIVE_GUIDE.md) |
| **QuillScript** | `Plugins/QuillScript/` | [Architecture](../PROJECT.md) |
| **Monolith MCP** | `Plugins/Monolith/` | [T3D Reference](Docs/Production/T3D_MONOLITH_REFERENCE.md) |

---

## Key Directories

| Path | What | Size |
|------|------|------|
| `Content/Melodia/` | Ship-ready game content (characters, anims, levels) | 4.8G |
| `Content/MelodiaIntegration/` | Configs, allowlists, bridge content | 12M |
| `deploy/surreal_arch/melodia_gn/` | 60+ surreal architecture builders | ~500K |
| `Tools/BlenderAddons/melodia_studio/` | MIDI→World GN system (largest addon) | ~50K |
| `Source/BS_GodFile/MelodiaIntegration/` | UE C++ bridge code | ~1M |
| `studio/tracks/` | Music (MIDI, USTX) | ~100M |
| `Docs/Research/` | Deep-dive reference documents | ~500K |
| `Docs/Production/` | Production plans, pipelines | ~1M |
| `Content/EnvSandbox/` | Test environment (NOT shippable) | 24G |
| `Saved/` | Generated files, audit reports, backups | 12G |

---

## By Task

| I want to... | Go to... |
|--------------|----------|
| Build a castle | `deploy/surreal_arch/melodia_gn/castle.py` |
| Animate Melusina | `Tools/build_melusina_face_rig.py` |
| Generate terrain from MIDI | `Tools/BlenderAddons/melodia_studio/` |
| Understand the architecture | `Docs/Research/GEOMETRY_NODES_COMPLETE_REFERENCE.md` |
| Add a new GN builder | `deploy/surreal_arch/melodia_gn/core.py` (read first) |
| Run mocap on Melusina | `Tools/run_headless_mocap_retarget.ps1` |
| Make a kawaii asset | `Tools/BlenderAddons/blender_kawaii_gn/` |
| Make a brutalist asset | `Tools/BlenderAddons/blender_brutalist_gn/` |
| Write QuillScript dialogue | `Plugins/QuillScript/` |
| Use Monolith MCP | `Plugins/Monolith/` |
| Render a beauty shot | `Tools/setup_melusina_master_studio.py` |
| Make Melusina sing | `studio/tracks/` + OpenUtau |
| Understand project state | `Docs/Research/EMERGING_TOOLCHAIN_MASTER_INDEX_2026-08-31.md` |
| Plan animation work | `Docs/Production/CHARACTER_ANIMATION_2_SEMESTER_PLAN.md` |
| Plan long-term infra | `Docs/Production/LONG_TERM_INFRASTRUCTURE_PLAN.md` |
| Study animation | [ANIMATION_STUDY_GUIDE.md](Docs/Production/ANIMATION_STUDY_GUIDE.md) |
| Find reference links | [ANIMATION_REFERENCE_LINKS.md](Docs/Production/ANIMATION_REFERENCE_LINKS.md) |
| Work from a laptop | [LAPTOP_WORKFLOW.md](Docs/Production/LAPTOP_WORKFLOW.md) |
| Build audio-reactive stuff | [AUDIO_REACTIVE_GUIDE.md](Docs/Production/AUDIO_REACTIVE_GUIDE.md) |
| Understand mocap pipeline | [MOCAP_PIPELINE_GUIDE.md](Docs/Production/MOCAP_PIPELINE_GUIDE.md) |
| Develop GN builders | [GN_BUILDER_GUIDE.md](Docs/Production/GN_BUILDER_GUIDE.md) |
| Understand Faraway PCG | [FARAWAY_PCG_SPEC.md](Docs/Production/FARAWAY_PCG_SPEC.md) |
| Technical interview prep | [SYSTEMS.md](Docs/Portfolio/SYSTEMS.md) |

---

## By Role

| Role | Start Here |
|------|------------|
| **Professor** | `UNIVERSITY.md` → `Docs/Research/GEOMETRY_NODES_COMPLETE_REFERENCE.md` |
| **Collaborator** | `QUICKSTART.md` → `Docs/Production/` |
| **Technical interviewer** | `PORTFOLIO.md` → `Docs/Portfolio/SYSTEMS.md` → `Source/BS_GodFile/MelodiaIntegration/` |
| **Animation lead** | `Docs/Production/CHARACTER_ANIMATION_2_SEMESTER_PLAN.md` → `Docs/Production/ANIMATION_STUDY_GUIDE.md` → `Content/Melodia/Characters/Melusina/Animations/` |
| **Artist** | `Tools/BlenderAddons/melodia_studio/` → `deploy/surreal_arch/melodia_gn/` |
| **New student** | `UNIVERSITY.md` → `QUICKSTART.md` → pick a system |

---

## Reference Documents

| Document | Lines | What |
|----------|-------|------|
| [GEOMETRY_NODES_COMPLETE_REFERENCE.md](Docs/Research/GEOMETRY_NODES_COMPLETE_REFERENCE.md) | ~600 | Every GN system, mapped and detailed |
| [EMERGING_TOOLCHAIN_MASTER_INDEX_2026-08-31.md](Docs/Research/EMERGING_TOOLCHAIN_MASTER_INDEX_2026-08-31.md) | ~121 | What exists, what's research, what's external |
| [CHARACTER_ANIMATION_2_SEMESTER_PLAN.md](Docs/Production/CHARACTER_ANIMATION_2_SEMESTER_PLAN.md) | ~300 | 2-semester production plan |
| [LONG_TERM_INFRASTRUCTURE_PLAN.md](Docs/Production/LONG_TERM_INFRASTRUCTURE_PLAN.md) | ~250 | LFS, laptop, portfolio strategy |
| [BLENDER_AUDIO_GEOMETRY_NODES_PIPELINE_2026-09-02.md](Docs/Research/BLENDER_AUDIO_GEOMETRY_NODES_PIPELINE_2026-09-02.md) | ~191 | Audio→GN research (5 tools compared) |
| [GN_TAXONOMY_2026-08-29.md](Docs/Production/GN_TAXONOMY_2026-08-29.md) | ~700 | GN builder taxonomy |
| [SYSTEMS.md](Docs/Portfolio/SYSTEMS.md) | ~450 | Technical systems breakdown for interviews |
| [ANIMATION_STUDY_GUIDE.md](Docs/Production/ANIMATION_STUDY_GUIDE.md) | ~1350 | 12 principles, curriculum, exercises |
| [ANIMATION_REFERENCE_LINKS.md](Docs/Production/ANIMATION_REFERENCE_LINKS.md) | ~92 links | Curated reference links |
| [LAPTOP_WORKFLOW.md](Docs/Production/LAPTOP_WORKFLOW.md) | ~708 | Laptop clone, sync, git config |
| [AUDIO_REACTIVE_GUIDE.md](Docs/Production/AUDIO_REACTIVE_GUIDE.md) | ~585 | Audio→GN→UE pipeline |
| [MOCAP_PIPELINE_GUIDE.md](Docs/Production/MOCAP_PIPELINE_GUIDE.md) | ~455 | Rokoko→UE retarget, cleanup |
| [GN_BUILDER_GUIDE.md](Docs/Production/GN_BUILDER_GUIDE.md) | ~633 | How to create GN builders |
| [FARAWAY_PCG_SPEC.md](Docs/Production/FARAWAY_PCG_SPEC.md) | ~358 | 3 missing PCG graphs spec |

---

## Glossary

| Term | Definition |
|------|------------|
| **GN** | Geometry Nodes — Blender's procedural geometry system |
| **FACS** | Facial Action Coding System — 46 action units driving facial animation |
| **Mocap** | Motion capture — recording real movement for animation |
| **Retarget** | Apply mocap from one skeleton to another |
| **LFS** | Git Large File Storage — stores binaries outside the git object store |
| **MIDI** | Musical Instrument Digital Interface — note events, not audio |
| **uasset** | Unreal Engine asset file (binary) |
| **umap** | Unreal Engine map/level file (binary) |
| **MCP** | Model Context Protocol — AI tool interface |
| **PCG** | Procedural Content Generation |
| **Cymatic** | Visual pattern from sound vibration (Chladni plates) |
| **AuraColor** | Vertex color attribute storing note velocity → drives material emission |

---

*Last updated: 2026-09-03 — 15 new docs, 8 subagent tasks completed*
