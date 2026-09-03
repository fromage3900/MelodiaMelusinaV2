# Long-Term University & Portfolio Infrastructure Plan
> **State:** 2026-09-03 | **Branch:** main (b04ec94b, 5 ahead of origin/main) | **LFS:** BROKEN (404s on fetch)
> **Goal:** Make this project accessible for university, portfolio-ready, laptop-friendly, GitHub-synced, GN-healthy.

---

## Current State Assessment

| Component | State | Health |
|-----------|-------|--------|
| **Git remote** | `origin` = MelodiaMelusinaV2.git | ✅ Configured |
| **Local branch** | main, 5 commits ahead of origin | ⚠️ Diverged |
| **LFS** | 4838 objects, 28GB, fetch returns 404s | ❌ BROKEN |
| **Content/** | 88GB (EnvSandbox 24G, Melodia 4.8G, rest misc) | ⚠️ Large |
| **Saved/** | 12GB | ⚠️ Large |
| **.git/** | 29GB (mostly LFS cache) | ⚠️ Large |
| **Total** | ~130GB | ❌ Too big for laptop |
| **Docs** | Scattered, no single entry point | ❌ Inaccessible |
| **Portfolio** | Nothing assembled | ❌ Missing |

---

## The 5 Problems (and Solutions)

### Problem 1: LFS is Broken
`git lfs fetch --all` returns 404 for 14,000+ objects. The LFS objects don't exist on the server.

**Cause:** At some point, LFS objects were lost or the remote was reset. The local `.git/lfs` has cached copies, but the server rejects them.

**Solution: Rebuild LFS from local cache**
1. The local `.git/lfs/objects/` cache has the files
2. Re-push all LFS objects to origin: `git lfs push --all origin`
3. If that fails, the objects need to be re-uploaded from the working tree:
   - `git lfs migrate export` (remove from LFS)
   - `git lfs migrate import` (re-add to LFS with fresh uploads)

**If LFS stays broken:** Move to a different strategy (see Problem 2).

---

### Problem 2: 130GB is Too Big for a Laptop
You can't clone this on a laptop. You can't even fit it on a 256GB SSD.

**Solution: Split into 2 tiers**

#### Tier 1: "Source of Truth" (Desktop/Cloud, full 130GB)
- Keep on desktop workstation or external drive
- Contains everything: Content/, Saved/, full LFS
- This is the archive

#### Tier 2: "Laptop Working Copy" (Laptop, ~15-30GB)
- Contains only what you need to work:
  - `Source/` (C++ code)
  - `Tools/` (Python scripts, GN builders)
  - `Docs/` (documentation, plans, research)
  - `Content/Melodia/` (4.8G — the actual game content)
  - `Content/MelodiaIntegration/` (12M — configs)
  - `Plugins/` (if small enough)
  - `specs/`, `deploy/`, `projects/`
- **Excluded:**
  - `Content/EnvSandbox/` (24G — test environment, not shippable)
  - `Content/_ThirdParty/` (stock template)
  - `Content/TurnBasedJRPGTemplate/` (stock template)
  - `CompatibilityLabs/` (backups)
  - `Saved/` (12G — generated, regenerable)

**How to create the laptop copy:**
```bash
# On desktop: create a sparse/filtered bundle
git bundle create BS_GodFile_source.bundle --all --glob=HEAD \
  ':Content/Melodia' ':Content/MelodiaIntegration' \
  ':Source' ':Tools' ':Docs' ':specs' ':deploy' ':projects' \
  ':Plugins/*/Source' ':Plugins/*/Config'

# Or: clone with --filter to skip blobs, then selectively checkout
```

**Alternative:** Use `git sparse-checkout` to only materialize the paths you need on the laptop.

---

### Problem 3: No Entry Point for University
A professor opens this repo and sees 13,000 files. They close it.

**Solution: Create `UNIVERSITY.md` at the repo root**

This file is the single entry point. It contains:
- **What is this?** — 2-sentence pitch
- **What's in it?** — bulleted list of systems
- **How to read it** — suggested reading order
- **Key docs** — links to the most important reference documents
- **Demo** — link to a video reel
- **Your role** — what you built vs. what's stock/template

Also create:
- `PORTFOLIO.md` — portfolio-specific entry point (reel, breakdowns, stills)
- `QUICKSTART.md` — "I'm new, how do I run something in 5 minutes"

---

### Problem 4: No Portfolio Assembled
You have 30+ mocap clips, GN builders, shaders, tools — but no reel.

**Solution: Assemble `Docs/Portfolio/`**

Structure:
```
Docs/Portfolio/
├── REEL_2026-09.md          — reel breakdown (what's in the reel)
├── PIECES/
│   ├── 01_melusina_plea.md  — Piece #1 breakdown
│   ├── 02_melusina_rage.md  — Piece #2 breakdown
│   ├── 03_dialogue.md       — Piece #3 breakdown
│   └── 04_experimental.md   — Piece #4 breakdown
├── STILLS/                  — exported PNGs
├── SYSTEMS.md               — "Here's what I built" (for technical interviews)
└── LINKS.md                 — YouTube, ArtStation, GitHub links
```

The reel itself comes in Semester 2 Week 9-10. Start the breakdown docs now.

---

### Problem 5: QOL — Can't Find Anything
13,783 tracked files. No search. No index.

**Solution: Create `INDEX.md` at repo root**

A curated index:
```
# BS_GodFile Index

## Getting Started
- [QUICKSTART.md](QUICKSTART.md) — run something in 5 min
- [UNIVERSITY.md](UNIVERSITY.md) — for professors/collaborators
- [PORTFOLIO.md](PORTFOLIO.md) — for job applications

## Systems
- [Character Animation](Docs/Production/CHARACTER_ANIMATION_2_SEMESTER_PLAN.md)
- [Geometry Nodes Reference](Docs/Research/GEOMETRY_NODES_COMPLETE_REFERENCE.md)
- [Emerging Toolchain SSOT](Docs/Research/EMERGING_TOOLCHAIN_MASTER_INDEX_2026-08-31.md)

## Key Directories
| Path | What |
|------|------|
| `Content/Melodia/` | Ship-ready game content |
| `Tools/BlenderAddons/melodia_studio/` | MIDI→World GN system |
| `deploy/surreal_arch/melodia_gn/` | 60+ surreal architecture builders |
| `Source/BS_GodFile/MelodiaIntegration/` | UE C++ bridge code |
| `studio/tracks/` | Music (MIDI, USTX) |

## By Task
- "I want to build a castle" → `deploy/surreal_arch/melodia_gn/castle.py`
- "I want to animate Melusina" → `Tools/build_melusina_face_rig.py`
- "I want to generate terrain from MIDI" → `Tools/BlenderAddons/melodia_studio/`
- "I want to understand the architecture" → `Docs/Research/GEOMETRY_NODES_COMPLETE_REFERENCE.md`
```

---

## Execution Plan

### Phase 1: Stabilize (This Week)

| Task | Time | Priority |
|------|------|----------|
| **1.1 Fix LFS** — try `git lfs push --all origin` | 1h | CRITICAL |
| **1.2 Commit current work** — stage the 5 modified + 1 untracked | 15min | HIGH |
| **1.3 Create `UNIVERSITY.md`** | 1h | HIGH |
| **1.4 Create `INDEX.md`** | 1h | HIGH |
| **1.5 Create `PORTFOLIO.md`** (stub) | 30min | MEDIUM |
| **1.6 Create `QUICKSTART.md`** | 30min | MEDIUM |

### Phase 2: Slim Down (Week 2)

| Task | Time | Priority |
|------|------|----------|
| **2.1 Identify what can be excluded** — run `du -sh` on every top-level dir | 30min | HIGH |
| **2.2 Set up sparse-checkout** for laptop | 1h | HIGH |
| **2.3 Test laptop clone** — can you clone the slim version? | 1h | HIGH |
| **2.4 Document the split** — what's in Tier 1 vs Tier 2 | 30min | MEDIUM |

### Phase 3: Document (Week 3-4)

| Task | Time | Priority |
|------|------|----------|
| **3.1 Write `Docs/Portfolio/SYSTEMS.md`** — "here's what I built" | 2h | HIGH |
| **3.2 Write `Docs/Production/CHARACTER_ANIMATION_2_SEMESTER_PLAN.md`** ✅ DONE | 0 | DONE |
| **3.3 Write `Docs/Research/GEOMETRY_NODES_COMPLETE_REFERENCE.md`** ✅ DONE | 0 | DONE |
| **3.4 Create `Saved/AnimationReference/` structure** | 30min | MEDIUM |
| **3.5 Build `Templates/Melusina_Animation_Stage.blend`** | 1h | MEDIUM |

### Phase 4: Portfolio Assembly (Semester 1-2)

| Task | Time | Priority |
|------|------|----------|
| **4.1 Piece #1** — "Melusina's Plea" | 10 weeks | HIGH |
| **4.2 Piece #2** — "Melusina's Rage" | 4 weeks | HIGH |
| **4.3 Piece #3** — Dialogue scene | 4 weeks | HIGH |
| **4.4 Piece #4** — Experimental | 4 weeks | MEDIUM |
| **4.5 Reel + breakdowns** | 2 weeks | HIGH |

---

## LFS Recovery — Detailed Steps

### Step 1: Diagnose
```bash
cd C:\EnvironmentPortfolio\BS_GodFile
git lfs env | grep Endpoint
git lfs ls-files | wc -l
git lfs fetch --all 2>&1 | grep "404" | wc -l
```

### Step 2: Try re-push
```bash
git lfs push --all origin
```

If this succeeds, the LFS objects are re-uploaded. Verify:
```bash
git lfs fetch --all 2>&1 | grep "404" | wc -l
# Should be 0
```

### Step 3: If re-push fails — migrate
```bash
# Export everything from LFS (files become normal blobs)
git lfs migrate export --include="*.uasset,*.umap,*.fbx,*.png,*.blend" --everything

# Re-import (fresh LFS objects, fresh upload)
git lfs migrate import --include="*.uasset,*.umap,*.fbx,*.png,*.blend" --everything

# Push
git push --all origin
git lfs push --all origin
```

### Step 4: If migration fails — nuclear option
If LFS is permanently broken:
1. Keep the local `.git/lfs` cache as an archive
2. Remove LFS tracking from `.gitattributes`
3. Commit the actual files (they'll be in the git object store, not LFS)
4. Accept that the repo will be large but at least syncable
5. Use `git filter-repo` or `git filter-branch` to strip the largest files from history

---

## Laptop Strategy — Detailed

### Option A: Sparse Checkout (Recommended)
```bash
# On laptop:
git clone --no-checkout https://github.com/fromage3900/MelodiaMelusinaV2.git
cd BS_GodFile
git sparse-checkout init --cone
git sparse-checkout set \
  Source \
  Tools \
  Docs \
  specs \
  deploy \
  projects \
  Content/Melodia \
  Content/MelodiaIntegration \
  Plugins/Monolith/Source \
  Plugins/QuillScript/Source \
  INDEX.md UNIVERSITY.md PORTFOLIO.md QUICKSTART.md
git checkout main
```

This gives you ~10-15GB instead of 130GB.

### Option B: Separate "Source" Repo
Create a new repo `MelodiaMelusina_Source` that only has the source code + docs. Use the main repo as the archive.

### Option C: Git LFS Partial Clone
```bash
git clone --filter=blob:limit=1m https://github.com/fromage3900/MelodiaMelusinaV2.git
```
This skips downloading large blobs on clone. You only download what you checkout.

---

## QOL Improvements

### 1. Scene Templates
Create `Templates/`:
- `Melusina_Animation_Stage.blend` — rig + lighting + cameras
- `Melusina_Face_Rig_Template.blend` — FACS face setup
- `ResonantWorld_Generator.blend` — MIDI terrain setup

### 2. Reference System
Create `Saved/AnimationReference/`:
- `body_mechanics/` — jumps, turns, lifts
- `acting/` — emotional performances
- `lipsync/` — mouth/jaw reference
- `walk_cycles/` — different moods

### 3. GN Health
- Run `python Tools/bp_sweep.py` project-wide (it died mid-run during the 3-editor incident)
- Run `python Tools/test_ui_style_audit.py`
- Run `python Tools/test_cute_gn_ornaments.py`
- Verify all GN builders still work in Blender 5.2

### 4. Automation
- Set up a cron job that runs `git fetch` + `git status` daily to detect drift
- Set up a pre-commit hook that checks for large files before commit
- Set up a weekly `git gc` to keep the repo healthy

---

## The `UNIVERSITY.md` Template

```markdown
# Melodia BS_GodFile — University Reference

## What is this?
A rhythm-JRPG game prototype in Unreal Engine 5.8 with a procedural
geometry-nodes pipeline in Blender 5.2. The game's world is generated
from MIDI files — music becomes terrain, rhythm becomes gameplay.

## What's in it?
- **60+ Geometry Nodes builders** — surreal architecture, castles, ornaments
- **MIDI→World pipeline** — Blender addon that turns songs into walkable terrain
- **Character animation system** — FACS face rig, mocap retarget, lip-sync
- **Audio-reactive presentation** — UE subsystem that drives materials from music
- **Cymatic fabric system** — Chladni plate eigenmodes drive cloth simulation

## How to read this
1. Start with `QUICKSTART.md` — run something in 5 minutes
2. Read `Docs/Research/GEOMETRY_NODES_COMPLETE_REFERENCE.md` — the big picture
3. Read `Docs/Production/CHARACTER_ANIMATION_2_SEMESTER_PLAN.md` — animation plan
4. Browse `Docs/Research/` for deep dives on specific systems

## Key Documents
| Document | What |
|----------|------|
| [Geometry Nodes Reference](Docs/Research/GEOMETRY_NODES_COMPLETE_REFERENCE.md) | Every GN system, mapped |
| [Emerging Toolchain SSOT](Docs/Research/EMERGING_TOOLCHAIN_MASTER_INDEX_2026-08-31.md) | What exists, what's research |
| [Animation Plan](Docs/Production/CHARACTER_ANIMATION_2_SEMESTER_PLAN.md) | 2-semester production plan |
| [P0 Closeout Plan](Docs/P0_CLOSEOUT_PLAN_2026-08-28.md) | Integration architecture |

## Demo
[Reel coming Semester 2]

## My Role
Solo developer. I built everything except:
- `Content/TurnBasedJRPGTemplate/` — stock UE template (modified)
- `Content/_ThirdParty/` — third-party assets
- `Plugins/VRM4U/` — VRM import plugin (vendored)
- `Plugins/HoudiniEngine/` — SideFX plugin (vendored)
```

---

## Summary

| Problem | Solution | Phase |
|---------|----------|-------|
| LFS broken | Re-push or migrate | 1 |
| 130GB too big | Sparse checkout / tiered repo | 2 |
| No entry point | `UNIVERSITY.md`, `INDEX.md` | 1 |
| No portfolio | `Docs/Portfolio/` structure | 3-4 |
| Can't find anything | `INDEX.md`, templates, reference system | 3 |
| GN health | Run sweep + audit tests | 3 |

---

*Plan written 2026-09-03. Review after Phase 1.*
