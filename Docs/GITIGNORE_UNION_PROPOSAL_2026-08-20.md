# .gitignore Union Proposal — 2026-08-20

**Status: proposal only. The working-tree `.gitignore` has NOT been changed.** This doc exists so
the owner can review and apply it deliberately — `.gitignore` is a never-touch file per
`CLAUDE.md`, and it currently shows modified in the working tree from a peer lane's Claireon rule
that must not be disturbed.

## What this is

A three-way union of the `.gitignore` rules currently spread across the repo:

1. **Base: `origin/feature/repo-lockin-20260813:.gitignore`** (316 lines). This is the branch
   whose asset carve-outs (`Masters/`, `ToonProfiles/`, `Functions/`, `Instances/`, etc.) keep the
   2,243 assets adopted in commit `309a575d` actually tracked instead of silently re-ignored. It
   also inverted the old `Tools/*` blanket-ignore-plus-61-line-allowlist pattern (see its own
   `LOST_TOOL_SOURCES_2026-08-14.md` reference) into targeted ignores under `Tools/**`, so new
   tool scripts are tracked by default — no more `git add -f` required to land one.
2. **Minus its `.agents/` rule.** repo-lockin's version ignores `.agents/` wholesale. The owner
   decided against this: `.agents/plans/*.md` files are committed and meant to stay that way, and
   a blanket ignore would silently shadow every future plan doc.
3. **Plus main's root scratch-script block** (`check_bp*.py`, `check_fix*.py`,
   `check_discover2.py`, `check_live.py`, `fix_rhythm*.py`, `fix_var*.py`, `pie_*.py`,
   `pie_*.json`, `deploy/_stub_*`, `_Quarantine_*/`) — session debris patterns from 2026-08-13
   that repo-lockin's own (differently-scoped) root scratch block doesn't fully cover
   (`pie_*.json`, `deploy/_stub_*`, `_Quarantine_*/` have no equivalent in repo-lockin).
4. **Plus the Claireon rule** currently sitting in the working-tree `.gitignore` (peer-lane,
   2026-08-20): `Plugins/Claireon/` with its "vendored upstream clone, not project source" comment.

## Verification counts (all pass on the proposal below)

| Check | Required | Actual |
|---|---|---|
| `ToonProfiles` occurrences | 3+ | 3 |
| `.venv-guardrails/` occurrences | 1 | 1 |
| `check_bp*` occurrences | 1 | 1 |
| `Plugins/Claireon/` occurrences | 1 | 1 |
| Lines exactly `.agents/` | 0 | 0 |
| Lines exactly `Tools/*` | 0 | 0 |

## Proposed final `.gitignore`

```gitignore
# UE generated / transient
Binaries/
DerivedDataCache/
Intermediate/
Saved/
!Saved/Portfolio/
!Saved/Audit/
Build/
.vs/
*.sln
*.slnx
*.VC.db
*.VC.opendb
Thumbs.db
Desktop.ini
.DS_Store

# Local backups / bundles and repository recovery copies (never commit)
*.bundle
Saved/Backups/
.git.backup/
BackupBeforeRebuild/

# Local toolchains, IDE state, and agent caches
# These are machine-specific and must not become project dependencies.
dotnet10/
dotnet6/
.ai/
.claude/
.claude.json
.codex_staged_paths.txt
.continue/
.cursor/
.devin/
.idea/
.junie/
.kiro/
.opencode.json
.mcp.json
.pytest_cache/
.rider/
.windsurf/
._site_aside_untracked/
_ollama_experiments/

# Local level overrides (editor-generated)
Content/ZenForestTest.ini

# World Partition conversion artifacts (experimental — tracked on wp-experiments branch)
Content/ZenForestTest_WP*
Content/ZenForestTest_HLODLayer_*
Content/__ExternalActors__/ZenForestTest/
Content/__ExternalActors__/ZenForestTest_WP/

# Python cache / Blender autosave junk
Content/Python/__pycache__/
**/__pycache__/
*.pyc
*.pyo
*.blend1
**/.venv/
.env.local
# Unreal scratch assets created by editor-analysis scripts; these are not project source.
Content/Python/_doonce.uasset
Content/Python/_eventgraph.uasset
Plugins/UEBlueprintMCP/Python/venv/

# Q# build output (dotnet artifacts under the quantum experiment)
Content/Python/quantum/qsharp_project/bin/
Content/Python/quantum/qsharp_project/obj/

# Editor-generated backup files and IDE user settings (never commit)
*.h~
*.cpp~
*.cs~
*.DotSettings.user

# Node.js (my-site-clean website subproject) - never commit, always npm install
node_modules/
.npm/
npm-debug.log*

# Autonomous worker output and local process state
_staging/
Products/_Staging/
deploy/*.pid
*.blend1
nul
target_file.md
*.tmp

# Blender Flip/cache output; source .blend and exported deliverables remain tracked explicitly.
KitbashExport/flip_cache_*/

# --- Core systems and playable vertical-slice scope (2026-07-27) ---
# Git tracks native/runtime systems plus the narrowly authored packages required
# to reproduce the working Melodia loop. Bulk environment/art libraries remain
# local unless explicitly promoted through a reviewed allowlist entry.
Content/*
!Content/Python/
!Content/Melodia/
Content/Melodia/*
!Content/Melodia/DataStuctures/

# Authored Melodia JRPG integration and presentation packages.
!Content/MelodiaIntegration/
!Content/MelodiaIntegration/**
!Content/Experiments/
Content/Experiments/*
!Content/Experiments/MelodiaJRPG/
!Content/Experiments/MelodiaJRPG/**

# --- IRREPLACEABLE CHARACTER CONTENT — tracked in full (2026-08-08) ---
# These are hand-authored over two years and cannot be re-downloaded or rebuilt.
# Until today they were NOT tracked: the `Content/*` blanket above never had a
# matching un-ignore for Content/Characters/, so SK_Melusina -- the protagonist,
# 36 MB -- lived on disk with no version history at all. A `git clean -fd` would
# have erased her permanently, and one was started on 2026-08-08 and interrupted
# by luck. Everything below is now recoverable from git.
#
# Anything re-downloadable (marketplace kits, Brushify, Greybox, UltraDynamicSky,
# Library, _ThirdParty, CC0 surfaces) stays ignored on purpose -- roughly 15 GB
# that would blow the LFS budget for no protective value.
!Content/Characters/
!Content/Characters/**

!Content/Melodia/Characters/
!Content/Melodia/Characters/**

# Exact stock packages intentionally changed for the playable loop.
!Content/TurnBasedJRPGTemplate/
Content/TurnBasedJRPGTemplate/*
!Content/TurnBasedJRPGTemplate/Blueprints/
Content/TurnBasedJRPGTemplate/Blueprints/*
!Content/TurnBasedJRPGTemplate/Blueprints/Battle/
Content/TurnBasedJRPGTemplate/Blueprints/Battle/*
!Content/TurnBasedJRPGTemplate/Blueprints/Battle/BP_BattleController.uasset

# --- PLAYABLE ROUTE LEVELS — tracked (2026-08-12) ---
# The `Content/*` blanket meant the two levels that ARE the vertical slice had no
# version history: L_MelusinaMorning and L_KaleidoNave. KaleidoNave is the only
# level in which a battle has ever started (the BP_BattleController placement on
# 2026-08-10). Losing either one loses the loop, and neither can be re-downloaded.
#
# Authored PCG graphs come with them -- they are logic, not art, and they are what
# the levels reference. Bulk EnvSandbox art (meshes, textures, Megascans, ~4.6 GB)
# stays ignored on purpose, same reasoning as the 2026-08-08 block above.
# Added here: ~48 MB, well inside the 512 MB CI budget gate.
!Content/Melodia/Levels/
!Content/Melodia/Levels/**
!Content/Melodia/PCG/
!Content/Melodia/PCG/**

!Content/EnvSandbox/
Content/EnvSandbox/*
!Content/EnvSandbox/Environments/
!Content/EnvSandbox/Environments/**
!Content/EnvSandbox/PCG/
!Content/EnvSandbox/PCG/**

# The toon spine itself (2026-08-13). `Content/EnvSandbox/*` above was excluding all
# 121 master materials and all 18 TP_* toon profiles, including
# M_Master_Toon_Universal -- the asset MATERIAL_PIPELINE.md:26 calls "the primary
# surface master". Both material fold commits prove the consequence:
# `git show --name-only 9c59c8f3 8ced728f | grep -c uasset` returns 0. 9c59c8f3
# ("fold 65 _PROJECT masters") changed four files -- three Python scripts and a
# JSON manifest. The masters those scripts produced were never committed, so the
# "9/9 compile-verified, BSDF wired" claim in the message cannot be checked against
# anything, and there is no revert path for the spine every material inherits from.
#
# Masters + ToonProfiles are 8.6 MB combined -- there was never a budget reason to
# exclude them. Scoped deliberately to these two folders: the rest of
# EnvSandbox/Materials (137 MB, mostly generated instances and textures) stays
# ignored under the bulk-art reasoning above.
!Content/EnvSandbox/Materials/
Content/EnvSandbox/Materials/*
!Content/EnvSandbox/Materials/Masters/
!Content/EnvSandbox/Materials/Masters/**
!Content/EnvSandbox/Materials/ToonProfiles/
!Content/EnvSandbox/Materials/ToonProfiles/**

# Curated material surface (2026-08-15). The 08-14 organization pass promoted the
# Nikki masters, created 7+ new MF_Nikki* functions, restored 77 MIs from git/LFS,
# and swept 1,468 mesh-referenced MIs onto the core standard. All of it is
# hand-curated instance work the same `git clean`-class accident would destroy --
# Functions and Instances are logic/preset layers, not bulk downloadable art.
# Sizes here: Functions 2.3 MB, Instances 11.4 MB, SDF/Instances 1.9 MB,
# Impressionist 0.16 MB, VFX 0.1 MB, Textures/Utility 0.05 MB. SDF/Textures
# (36 MB), _Scratch/, _Archive/ and _PROJECT/04_Materials/Textures (651 MB)
# stay ignored under the bulk-art reasoning above.
!Content/EnvSandbox/Materials/Functions/
!Content/EnvSandbox/Materials/Functions/**
!Content/EnvSandbox/Materials/Instances/
!Content/EnvSandbox/Materials/Instances/**
!Content/EnvSandbox/Materials/SDF/
Content/EnvSandbox/Materials/SDF/*
!Content/EnvSandbox/Materials/SDF/Instances/
!Content/EnvSandbox/Materials/SDF/Instances/**
!Content/EnvSandbox/Materials/Impressionist/
!Content/EnvSandbox/Materials/Impressionist/**
!Content/EnvSandbox/VFX/
Content/EnvSandbox/VFX/*
!Content/EnvSandbox/VFX/Materials/
!Content/EnvSandbox/VFX/Materials/**
!Content/EnvSandbox/Textures/
Content/EnvSandbox/Textures/*
!Content/EnvSandbox/Textures/Utility/
!Content/EnvSandbox/Textures/Utility/**

# Restored MIs from the 08-14 restore pass (git history + LFS). Small, load-bearing
# instance sets; the 651 MB _PROJECT Textures folder stays ignored. Each directory
# level must be re-included first or git never descends into it (Content/* excludes
# the parents at line 99).
!Content/_PROJECT/
Content/_PROJECT/*
!Content/_PROJECT/04_Materials/
Content/_PROJECT/04_Materials/*
!Content/_PROJECT/04_Materials/Cosmo/
!Content/_PROJECT/04_Materials/Cosmo/**
!Content/_PROJECT/04_Materials/Landscape/
!Content/_PROJECT/04_Materials/Landscape/**
!Content/_PROJECT/04_Materials/water/
!Content/_PROJECT/04_Materials/water/**
!Content/Materials/
Content/Materials/*
!Content/Materials/MI_ToonLayer.uasset
!Content/Art/
Content/Art/*
!Content/Art/Materials/
Content/Art/Materials/*
!Content/Art/Materials/Master/
Content/Art/Materials/Master/*
!Content/Art/Materials/Master/Materials/
Content/Art/Materials/Master/Materials/*
!Content/Art/Materials/Master/Materials/MI_ToonLayer.uasset

# Nested site repo + deploy staging dir (mirrors, not tracked content)
my-site-clean/
_github_deploy/

Backups/
Imports/*
!Imports/Animations/
Imports/Animations/*
!Imports/Animations/Cascadeur/
Imports/Animations/Cascadeur/*
!Imports/Animations/Cascadeur/Inbox/
Imports/Animations/Cascadeur/Inbox/*
!Imports/Animations/Cascadeur/Inbox/README.md
# --- Tools/ INVERTED 2026-08-14 ---
# Was `Tools/*` plus a hand-maintained allowlist of 61 `!Tools/...` entries. That
# allowlist failed silently and repeatedly: ~17 tool sources under Tools/ now survive
# only as .pyc bytecode with no git history, including the whole portfolio/stage
# pipeline (komikaze stage looks, EEVEE batch render, review-queue population, asset
# passports) and a doc-link validator that was rebuilt from scratch because nobody
# could find it. Eight contract test suites were sitting in the same position.
# See Docs/Reports/LOST_TOOL_SOURCES_2026-08-14.md.
#
# Now: track source, ignore build output and heavy binaries. Source under Tools/ is
# ~5 MB across 337 .py plus docs/specs -- there was never a budget reason to exclude
# it. The 34 MB of .blend and 12 MB of .pyd stay out, which is what the size actually
# was. Adding a new tool no longer requires remembering to edit this file.
Tools/**/__pycache__/
Tools/**/*.pyc
Tools/**/*.pyo
Tools/**/*.pyd
Tools/**/*.blend
Tools/**/*.blend1
Tools/**/*.fbx
Tools/**/*.uasset
Tools/ubt_feedback/

melodia-design-system/
KitbashExport/
research/
Products/
Assets/
pipeline/
Samples/
.kiro/
.junie/

# Root-level session debris and scratch assets. Ad-hoc probes agents drop at the repo root
# during a live editor session. Ignored rather than deleted, per the standing note in
# _SESSION_HANDOFF.md: "session debris, propose a .gitignore line rather than deleting".
# Anchored with a leading slash on purpose -- Tools/fix_*.py and Tools/check_*.py are
# real, CODEOWNERS-assigned tools and must stay visible to git.
/check_*.py
/fix_*.py
/pie_*.py
/pie_*_report.json
/scratch_*.py
/setup_room_commands.py
/test_vrm_import.py
/Temp/

# --- Session scratch scripts at repo root (never commit -- 2026-08-13) ---
check_bp*.py
check_fix*.py
check_discover2.py
check_live.py
fix_rhythm*.py
fix_var*.py
pie_*.py
pie_*.json
deploy/_stub_*
_Quarantine_*/

# Root-level loose binary scratch meshes and textures
/*.fbx
/*.png
/*.bundle
/*.sln
/*.slnx
/*.uproject.DotSettings.user
/*_smoke_report.json
/*_postclean_report.json
/*_probe_check_report.json
/g
/nul

/Plugins/Oceanology_Plugin/

# Claireon: vendored upstream clone of believer-oss/Claireon.git (pinned ed0b457).
# Not project source -- see Docs/CLAIREON_PREP_2026-08-20.md to re-clone.
Plugins/Claireon/
*.log
.venv-guardrails/
```

## Note on overlap, not addressed here

repo-lockin's own root scratch block (`/check_*.py`, `/fix_*.py`, `/pie_*.py`, `/pie_*_report.json`
— unanchored except leading `/`) already covers most of main's later, more specific block
(`check_bp*.py` etc. would match `/check_*.py`). They are not identical (`pie_*.json` vs.
`/pie_*_report.json`; `deploy/_stub_*` and `_Quarantine_*/` have no repo-lockin equivalent), so
per the task spec both blocks are kept side by side rather than deduplicated. Collapsing them is a
harmless follow-up, not required for this proposal.

## Not applied

This file is a proposal for owner review. Nobody should copy this into `.gitignore` without a
sign-off — see `_SESSION_HANDOFF.md` next-actions for where this sits in the sequence (after
`aws login`, before the LFS cold-archive push).
