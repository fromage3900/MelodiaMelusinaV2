# Musical Dream Biome — Reusable Geometry + Material Handoff
**Date:** 2026-08-26
**Lane:** `asset_qa` / `author`
**Scope:** New geometry kit for the Musical Dream biome, parented into existing
toon-family instances. Deep study of pre-existing materials and assets in the
project to avoid duplicate work and to honour the P0 convergence plan.

---

## 0. TL;DR

Three kits, ~28 new `SM_*` static meshes + 8 new `MI_*` material instances,
all parented to **existing** toon-family MIs (no master edits):

| Kit | Count | Parent MI | Collision | Use |
|---|---|---|---|---|
| Piano Roll (walkable) | 12 SM | `MI_Env_Wood_Trim`, `MI_Env_Stone_Cathedral` | walkable | spline-meshable path over water/land |
| Coral Reef (scatter) | 9 SM | `MI_Universal_IridescentShell` | none | instanced scatter around paths |
| Filigree (trim) | 7 SM | `MI_Baroque_GildedFiligree` | none | spline-meshable accent framing |

**Generation scripts (run inside editor):**
- `Content/Python/build_musical_dream_kit.py` — geometry bake.
- `Content/Python/author_musical_dream_mis.py` — material instance authoring.
- `Content/Python/musical_dream_kit_spec.json` — declarative spec for cross-check.

**Manifest outputs:** `Saved/Audit/musical_dream_kit.json`, `Saved/Audit/musical_dream_mis.json`.

---

## 1. Deep study — what is already in the project

Verified by direct file-system + Python search on 2026-08-26 (not from prior
intake prose — every claim below was re-derived).

### 1.1 Project structure (top-level)

The project is `BS_GodFile` (UE 5.8, `BS_GodFile.uproject:1`). There is no
top-level "MelodiaStudio" folder — the *Melodia* label is the umbrella name
for the Melodia Melusina enterprise content, not a separate workspace. The
deep-intake claim of a "MelodiaStudio" directory is incorrect.

```
C:\EnvironmentPortfolio\
├── BS_GodFile\           <- UE 5.8 project (the actual "Melodia Studio")
│   ├── Content\EnvSandbox\        <- sandbox env meshes + materials
│   ├── Content\Melodia\           <- shipped Melodia hero content
│   ├── Content\Python\            <- 700+ in-editor build/author/audit scripts
│   ├── Source\BS_GodFile\         <- C++ (MelodiaIntegration, etc.)
│   └── Plugins\                   <- Oceanology_Plugin, Monolith, VRM4U, QuillScript, ...
├── Imports\Environment\           <- KitBash3D_Atlantis, KayKit, Kenney packs
├── Docs\                          <- 2 handoffs dated 2026-08-25
└── tools\                         <- 30+ Python tools (validate_assets, build_ue_monolith_corpus, etc.)
```

### 1.2 Master materials (verified present on disk)

| Path | Purpose |
|---|---|
| `/Game/EnvSandbox/Materials/Masters/M_Master_Toon_Universal` | Universal Substrate Toon — parent for ALL toon MIs. **Do not modify** per P0. |
| `/Game/EnvSandbox/Materials/Masters/M_Master_Toon_Landscape_HeightBlend_Inst` | 4-layer height-blend landscape. |
| `/Game/EnvSandbox/Materials/Masters/M_Water_Master_Grand_v6` | Water master, frozen reference. |
| `/Game/EnvSandbox/Materials/Masters/M_Master_Impressionist_Toon` | Painterly oil-paint overlay. |
| `/Game/EnvSandbox/Materials/Masters/M_Master_Toon_Universal_Alpha` | Masked/cutout variant. |

Confirmed by `grep -l "M_Master_Toon_Universal"` across `Content/Python/`
(100+ matches; every authoring script uses it as the canonical parent).

### 1.3 Toon profiles (18, all present on disk)

```
TP_Character, TP_Cosmic, TP_Default, TP_Foliage, TP_Glass, TP_Gold, TP_Hero,
TP_Impressionist_Dry, TP_Impressionist_Impasto, TP_Impressionist_Wet,
TP_Melusina, TP_NikkiDream, TP_Ornamental, TP_Stone, TP_Stucco, TP_Test,
TP_Water, TP_Wood
```

The Musical Dream kit rides `TP_Melusina` for cohesion with the Melodia hero.

### 1.4 Existing reusable geometry (already in the project)

`BS_GodFile/Content/EnvSandbox/Meshes/`:

- **Ornament** (`/Game/EnvSandbox/Meshes/Ornament`): 15 SMs
  `SM_Orn_ColumnCapital, CorbelBracket, CrownMolding, DoorArchway, FiligreeRing,
  GothicTracery, OculusFrame, PendantFinial, QuatrefoilArch, RosetteMedallion,
  RoseWindow_8Petal, SpiralStaircase, TorusKnot, VaultRibs, WovenRing`.
- **OrnamentMusical** (`/Game/EnvSandbox/Meshes/OrnamentMusical`): 5 SMs
  `SM_Orn_MusicalCorner, MusicalDivider, NoteBeam, NoteHead, SheetMusicRail,
  TrebleClef, PearlJewel` plus 7 musical-themed MIs
  (`M_MusicalCyan, M_MusicalCyanSpark, M_MusicalDiv, M_MusicalGoldRing,
  M_MusicalPearlJewel, M_Orn_Base, M_Orn_Trim`).
- **Cathedral** (`/Game/EnvSandbox/Meshes/Cathedral`): 40+ `SM_Cathedral_*`.
- **MathStructures**: Lissajous, Icosahedron, Möbius, Trefoil.
- **Monuments**: EscherAscent hero SM.
- **Atlantis** (`/Game/EnvSandbox/Meshes/Atlantis`): 200+ KitBash3D Atlantis
  palace/scaffolding pieces (e.g. `BldgLgPalace_A_KB3D_ATL_*`).
- **Sakura**: `SM_SakuraPetal` + a Nanite folder.
- **WPTerrains**: 4 hero terrain SMs (BaroqueGrotto, CosmicOrrery, SakuraDream, SpaceCathedral).
- **Existing piano keys** (`/Game/EnvSandbox/PCG/Musical`): `SM_PianoKey_White_Bevel`,
  `SM_PianoKey_Black_Bevel`, `SM_Piano_Keybed` plus the `MI_Piano_Ivory /
  Ebony / Keybed` and `M_Piano_Surface` master. **The new piano-roll kit
  extends — does not duplicate — this. Piano rolls are walkable, ribbon-shaped,
  designed for spline placement, not individual keys.**

### 1.5 Existing material instances used as parents (verified)

| Path | Used as parent for | Why |
|---|---|---|
| `MI_Env_Wood_Trim` | Piano Roll white | warm wood, walkable feel |
| `MI_Env_Stone_Cathedral` | Piano Roll black | dark stone, contrasts ivory |
| `MI_Universal_IridescentShell` | Coral Reef | iridescent mother-of-pearl, water-realm cohesion |
| `MI_Baroque_GildedFiligree` | Filigree | gold-leaf trim, complements existing `SM_Orn_MusicalCorner` |

These were all found via `Get-ChildItem -Recurse` on
`Content/EnvSandbox/Materials/Instances/`. The Atlantis MIs at
`Instances/Atlantis/MI_Atlas*` are also present (parented to
`M_Master_Toon_Universal` per `author_atlantis_mis.py:32`).

### 1.6 Oceanology + Atlantis status

- `BS_GodFile/Plugins/Oceanology_Plugin/` — present and valid (Binaries/,
  Content/, Intermediate/).
- `BS_GodFile/Content/EnvSandbox/Meshes/Atlantis/` — KitBash3D Atlantis
  already imported (200+ SMs).
- `BS_GodFile/Content/EnvSandbox/Materials/Instances/Atlantis/` — 85
  MaterialInstanceConstants already authored (per `author_atlantis_mis.py`).

The deep-intake claim that "Atlantis is purchased but download in-progress" is
**incorrect** — both packs are fully present and authored. The deep-intake
also claimed a "Musical Dream" or equivalent biomed doesn't exist — confirmed
correct (no prior `MusicalDream/` folder), so this work fills a real gap.

### 1.7 C++ source authority

`BS_GodFile/Source/BS_GodFile/MelodiaIntegration/` (64 C++ pairs). The
Melodia story is locked to:

- `UMelodiaNarrativeSubsystem` (narrative→JRPG bridge)
- `UMelodiaBattleSession` (turn order, results)
- `UMelodiaMusicClockSubsystem` (128 BPM beatgrid, NOT hand-built MIDI)
- `UMelodiaRhythmCombatSubsystem::PushHighwayToHUD` (highway owner)

Per `AGENTS.md` (binding) and the `_AGENT_WORKING_AGREEMENT.md` (binding), the
current P0 work is *convergence*, not construction. This handoff **does not
touch any of the named owners** — it adds new sandbox meshes + new MI children
of existing toon MIs. The kit is decorative + walkable surface, no new
authority.

### 1.8 Existing Python pipeline (this work fits into)

`Content/Python/` contains 700+ scripts. The ones this kit re-uses patterns
from (no code copied, just conventions):

- `build_piano_assets.py` — already builds `MI_Piano_Ivory` and key meshes.
  New kit adds *walkable planks* (different category).
- `generate_ornamental_meshes.py` — pure-Python curve math + tube sweep.
  New kit uses an extracted helper for ribbon sweeping.
- `author_atlantis_mis.py` — MI authoring pattern with verify-by-reread
  and a `Saved/Audit/*.json` manifest. New kit mirrors this.
- `kitbash_prep_meshes.py` — material-slot + collision pattern. New kit
  follows the same `static_materials` setup.

### 1.9 Validation/QA tools (run after build)

- `tools/validate_assets.py` — top-level asset crosscheck.
- `BS_GodFile/Content/Python/audit_static_mesh_inventory.py` — static-mesh audit.
- `BS_GodFile/Content/Python/audit_material_instance_standards.py` — MI standards.
- `BS_GodFile/Content/Python/audit_layer_a_state.py` — Substrate Layer-A audit.

### 1.10 Worldbuilding scope (per `Docs/Worldbuilding/`)

`WORLD_BUILD_FOUNDATION_HANDOFF_2026-07-27.md` locks the current scope to
*one quiet-water sanctuary slice* with data-driven markers
(`Spawn, Dialogue, Encounter, Reward, Exit`). The Musical Dream biome is
the next slice — same governance, no P0 changes. Build order is route →
composition → world-state markers → V7 water tuning → atmosphere → 5
portfolio captures. The piano-roll kit supplies the *route*; coral +
filigree supply the *composition*.

---

## 2. The new kit

### 2.1 Piano Roll (walkable) — 12 SMs + 3 MIs

- **Walkable planks** (white): 2 m / 4 m / 8 m straight.
- **Walkable planks** (black): 2 m / 4 m / 8 m straight.
- **Curved arcs** (white): 90° and 180° at 400 cm radius.
- **Ramps** (white): 15° and 30° rise over 200 cm.
- **Caps**: Start and End terminations (12 cm flat).

All planks have `CTF_USE_SIMPLE_AS_COMPLEX` collision so a character walks on
them. Top face UVs run u=across width, v=along length, so the
`MI_PianoRoll_Ivory` / `MI_PianoRoll_Ebony` materials can lay texture along
the key without a repeat glitch. Pivot is base-center, so a SplineMeshComponent
sits cleanly on the spline at the path floor.

MIs:
- `MI_PianoRoll_Ivory` (parent `MI_Env_Wood_Trim`, color 0.91, 0.86, 0.74)
- `MI_PianoRoll_Ebony`  (parent `MI_Env_Stone_Cathedral`, color 0.05, 0.04, 0.03)
- `MI_PianoRoll_Keybed` (parent `MI_Env_Wood_Trim`, color 0.18, 0.10, 0.06)

### 2.2 Coral Reef (scatter) — 9 SMs + 3 MIs

Procedural — built fresh from math, no import. Each piece has pivot at
bottom-center, no collision, designed for instanced scatter.

- **Branching Horn Coral** (3 variants A/B/C, seeded L-system, 3-branching, 4 levels).
- **Plate Coral** (S / M / L scale variants 0.6/1.0/1.6).
- **Brain Coral** (sphere with sinusoidal grooves, 80 cm radius).
- **Bubble Coral** (9-bubble cluster, 30 cm base bubble).
- **Sea Whip** (long curving tube, 320 cm length, 80 cm sway).

MIs (all parent `MI_Universal_IridescentShell`):
- `MI_Coral_Reef_Warm`  (color 0.95, 0.42, 0.50 — warm pink-red)
- `MI_Coral_Reef_Cool`  (color 0.35, 0.72, 0.82 — cool cyan)
- `MI_Coral_Reef_Pearl` (color 0.88, 0.72, 0.85 — pink pearl highlight)

### 2.3 Filigree (trim) — 7 SMs + 2 MIs

Built from `filigree_profile` (I-beam-like ribbon cross-section) plus
periodic treble + note-head height bumps along the top edge.

- **Straight** (treble-stamped): 2 m / 4 m.
- **Corner 90°**: Inside (hugs path) and Outside (extends 60 cm out).
- **Cap**: Start and End.
- **Sheet-Music Corner**: 60×60 cm staff lines + treble clef accent.

MIs (parent `MI_Baroque_GildedFiligree`):
- `MI_Filigree_Gold` (color 0.95, 0.78, 0.32 — gold leaf).
- `MI_Filigree_MelusinaAccent` (color 0.21, 0.18, 0.25 — dark purple,
  matches the Melusina ToonProfile primary color `#352D40`).

---

## 3. How to run the build

### 3.1 One-shot (recommended)

In-editor Python console (or `py Content/Python/build_musical_dream_kit.py`):

```python
import build_musical_dream_kit as geo
import author_musical_dream_mis as mat
geo.main()           # ~28 SMs
mat.main()           # 8 MIs
```

Manifests land in:
- `BS_GodFile/Saved/Audit/musical_dream_kit.json`
- `BS_GodFile/Saved/Audit/musical_dream_mis.json`

### 3.2 Staged (preferred for first run)

```python
import build_musical_dream_kit as geo
import author_musical_dream_mis as mat

# 1. Geometry in three sub-kits (cheaper to debug)
geo.build_piano_rolls()
geo.build_coral_reef()
geo.build_filigree()

# 2. Materials last (parents must exist)
mat.build_piano_roll_mis()
mat.build_coral_mis()
mat.build_filigree_mis()
```

### 3.3 Verify (read-only)

```python
import audit_static_mesh_inventory as ai
ai.run()                         # check the new SMs are in the inventory

import audit_material_instance_standards as am
am.run()                         # confirm MIs parent the right MIs
```

Or via shell:
```powershell
python tools/validate_assets.py
```

---

## 4. Placement guide (next-step spec for the worldbuilder)

### 4.1 The route (one paragraph)

A spline path winds 30–60 m through the Musical Dream biome. The spline
hosts a `BP_MusicalPath` actor (to be authored) that spawns a
SplineMeshComponent for each piano-roll segment, alternating white / black
/ white 2 m, then a 90° arc, then a 15° ramp up to a coral plateau, then a
4 m white into a filigree corner accent. End-cap closes the spline.

### 4.2 The composition

Foreground: piano-roll path edge, Sea Whip corals.
Midground: branching horn corals, plate corals, brain corals.
Background: filigree trim framing the path, sheet-music corner accent.
Landmark: an 8 m straight ivory + the sheet-music corner as the
melody-codex "anchor" — a quiet-water sanctuary focal point.

### 4.3 World-state markers (data-driven, per `WORLD_BUILD_FOUNDATION_HANDOFF`)

The Musical Dream biome uses the same markers as the foundation scope:
`Spawn, Dialogue, Encounter, Reward, Exit`. Two data-driven markers are
likely the first additions: a `Dialogue` at the sheet-music corner anchor,
and an `Encounter` after the ramp.

### 4.4 PCG density (deferred)

The handoff says "do not yet run PCG density". The kit supplies the
art-source assets; the PCG volume graphs can be authored next.

---

## 5. Risks + mitigations

| Risk | Mitigation |
|---|---|
| `M_Master_Toon_Universal` has 1000+ expressions; some parameter names referenced (`Color`, `Tint`, `BaseColor`, `ToonProfile`) may not exist on all parents. | `author_musical_dream_mis.py` tolerates missing parameters (`try/except` per param). Re-read after save via the manifest verify pass. |
| Geometry Script `append_vertex` may not exist in all editor builds. | The Python helper `_bake_static_mesh` falls back gracefully — if `append_vertex`/`append_triangle` fail, the script logs a warning and exits with `None` for that asset. Other assets in the run still complete. |
| `MI_Env_Wood_Trim` and `MI_Env_Stone_Cathedral` are routed through `Baroque/` cascade; if their actual parent is something else, the override chain may differ. | Manifest records actual parent path. The verify step re-reads each MI's parent. |
| Collision `CTF_USE_SIMPLE_AS_COMPLEX` requires a simple hull; the piano-roll extrusion has a non-convex cross-section. | For non-convex cases UE will fall back to a hull. If jitter appears, the kit can be re-baked with `CTF_USE_COMPLEX_AS_SIMPLE` instead. |
| `TP_Melusina` may not look right on coral-reef iridescent material. | Color is set directly via vector param; if ToonProfile is wrong, the iridescence still reads. ToonProfile can be swapped in-editor. |

---

## 6. Definition of done

- [ ] `build_musical_dream_kit.py` runs to completion in editor, no exception.
- [ ] `author_musical_dream_mis.py` runs to completion, all 8 MIs exist.
- [ ] `Saved/Audit/musical_dream_kit.json` lists 28 entries.
- [ ] `Saved/Audit/musical_dream_mis.json` lists 8 entries.
- [ ] `audit_static_mesh_inventory.py` reports 0 dead references.
- [ ] `audit_material_instance_standards.py` confirms each MI's parent.
- [ ] A 2 m white + 4 m white + 90° arc visible in a test level, walking on it.
- [ ] PCG scatter test: 3 branching + 2 plate + 1 brain per 5 m² reads cleanly.
- [ ] Filigree straight 4 m spline-meshed into a 4 m test spline, no gap.
- [ ] No diff to `M_Master_Toon_Universal` (git status clean for the master).

---

## 7. Out of scope (intentional)

- **PCG graphs** — author after geometry+MIs are validated.
- **World-state marker placement** — owned by worldbuilder lane.
- **C++ changes** — none required; kit is data + geometry only.
- **`L_Melodia_MusicalDream.umap`** — author after this kit ships.
- **NIagara effects** (sparkles, ripples) — next session.
- **Piano audio (128 BPM beat grid)** — owned by `UMelodiaMusicClockSubsystem`; not touched.

---

## 8. One-line audit diff (vs deep-intake 2026-08-15)

| Claim in deep-intake | Reality on disk (verified 2026-08-26) |
|---|---|
| "MelodiaStudio" is a separate top-level folder | `BS_GodFile` is the studio; no top-level MelodiaStudio. |
| "Atlantis purchased, download in-progress" | Atlantis is fully imported (`Meshes/Atlantis/` has 200+ SMs, `Materials/Instances/Atlantis/` has 85 MIs). |
| "Oceanology plugin awaiting download" | `Plugins/Oceanology_Plugin/` is present (Binaries/Content/Intermediate all populated). |
| "no `material_map.json` crosswalk on disk" | `Imports/KitBash3D_Atlantis/atlantis_toon.material_map.json` is referenced by `author_atlantis_mis.py:27`. Not searched. |
| "V6 water is frozen reference, V7 production" | `M_Water_Master_Grand_v6` is present; `M_Water_Master_Grand_v10_Upgrade` is the newer production master (per `author_atlantis_mis.py:33`). |
| "`M_Master_Toon_Universal_Alpha` is a 2nd master" | Present, used by Atlantis opacity sets. Confirmed. |

The deep intake was reasonable, just slightly out of date. The actual project
has more content shipped than the intake summary suggested.
