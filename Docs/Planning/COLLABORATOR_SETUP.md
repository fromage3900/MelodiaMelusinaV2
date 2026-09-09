# 👥 Collaborator Setup Guide

**Work together on a source+levels+plugins repo (~3-4 GB). The bulk art is delivered out of band -- read the warning below before you expect a level to render.**

This guide covers Unreal-capable collaboration. For a Blender-only bridge
checkout with no Unreal project or plugin content, use
[Docs/SETUP_COLLAB.md](Docs/SETUP_COLLAB.md) and the `blender` onboarding tier.

```
✧ ┊ ⋆ ┊ . ┊ ┊┊ ┊⋆ ┊ .┊ ┊ ⋆˚  ✧
```

---

## ⚠️ Read this before anything else: the art is not in the repository

**Corrected 2026-08-13.** This document used to open with "Full Clone = 300 GB" and offer
a tier that pulled it. **That repository does not exist.** The 300 GB premise, the
"~1–3 GB material art" pull, and the audio pull were all describing a state the project
moved away from.

What is actually true:

| | |
|---|---|
| `Content/` on disk | **65 GB** |
| `Content/` tracked in git | **~2,700 files, ~2.7 GB** |
| Deliberately **not** tracked | Megascans 26 GB · Custom 6.4 GB · SmartAssets 5.1 GB · EnvSandbox art 4.7 GB · Greybox_Kit 4.0 GB · Meshes 3.3 GB · Brushify 2.9 GB · Library 2.2 GB · magicianlabatory 2.2 GB · _PROJECT 1.4 GB |

`.gitignore:99` blankets `Content/*` and re-includes a hand-curated list. The reasoning is
written into the file and is deliberate — see `.gitignore:116-159`.

**The consequence you will hit immediately:** `L_KaleidoNave` is tracked, but the meshes,
textures, and instance materials it references are not. **It will open with missing
references and pink/grey assets on a fresh clone.** That is expected. It is **not** an LFS
problem and **no `git lfs pull` will fix it** — the assets were never committed. Ignore any
older troubleshooting text that blames LFS for this.

**The art drop now exists.** As of 2026-08-14 the authored environment art is in S3:

```bash
aws s3 sync s3://melodia-artdrop-322037002075/EnvSandbox/ Content/EnvSandbox/ --profile artdrop
```

**6,720 objects, 3.06 GiB** — authored art only. `Library/Migrated` is excluded, and
Megascans / Brushify / `_ThirdParty` (~38 GB) are deliberately absent: those are vendor
packs you re-fetch from Quixel/Brushify yourself, not things this project redistributes.

**Access:** ask the owner for a key on the IAM user `melodia-artdrop-reader`. It is
read-only (`s3:GetObject`, `s3:ListBucket`) and scoped to that one bucket, so it cannot
touch anything else in the account and can be revoked for one person without affecting
others. Configure it as its own profile:

```bash
aws configure --profile artdrop     # region ca-central-1
```

Egress is about **$0.28** for a full pull. Sync only what you need if you are iterating.

As of 2026-08-13 the toon spine itself **is** tracked — 121 master materials and all 18
`TP_*` toon profiles under `Content/EnvSandbox/Materials/{Masters,ToonProfiles}` (8.6 MB).
Before that date they were excluded too, which is why the material "fold" commits of
2026-08-12 contain zero `.uasset` files.

## ✅ Tiered onboarding

Pick the tier that matches your role.

| Tier | Role | Clone size | Setup time | Can open a level? |
|------|------|-----------|------------|-------------------|
| **Tier 1 — Lightweight UE** | Level design, material art, UI work with project plugins | **~3–4 GB** | 10–15 min + first C++ build | Yes, **with missing art references** |
| **Tier 2 — Full Build** | Build engineer, packaging, PIE testing | **~3–4 GB from git + 3.06 GiB art drop (S3)** | 1–2 hours | Yes, once the art drop is synced |
| **Tier 3 — Code/Docs Reviewer** | Code review, planning, documentation review | ~50 MB | ~1 minute | No, and does not need to |

---

## 🚀 Quick Start

Use the tiered onboarding scripts:

```bash
# Tier 1: Lightweight (level design, materials, UI)
bash deploy/collaborator_onboarding.sh lightweight

# Tier 2: Full build (build engineer, PIE testing)
bash deploy/collaborator_onboarding.sh full

# Tier 3: Docs/code-only (reviewers, planners)
bash deploy/collaborator_onboarding.sh docs

# Validate the UE-capable checkout
bash deploy/validate_collaborator_setup.sh . ue
powershell -ExecutionPolicy Bypass -File .\deploy\validate_setup.ps1 -SkipServices -CheckLfsHydration
```

---

## Tier 1: Lightweight UE Collaborator

**Best for:** Level design, material art, UI work, documentation

```bash
# 1. Clone without hydrating the full LFS library
GIT_LFS_SKIP_SMUDGE=1 git clone https://github.com/fromage3900/MelodiaMelusinaV2.git MelodiaCollab
cd MelodiaCollab
git config core.hooksPath .githooks   # a fresh clone does NOT enable the repo's hooks

# 2. Install Git LFS
git lfs install

# 3. Apply the plugin-capable sparse manifest
bash deploy/collaborator_onboarding.sh lightweight

# 4. The manifest includes BS_GodFile.uproject, full tracked Plugins/,
#    plugin source, Content/Python, and the tracked gameplay paths.
#    There is no 300 GB content library in this repo to pull; see the note at the top.
```

### For Level Designers (Geometry/Levels):
```bash
# The lightweight onboarding script already hydrates the tracked route paths.
git lfs pull --include="Content/Melodia/Levels/**,Content/Melodia/PCG/**,Content/EnvSandbox/Environments/**,Content/EnvSandbox/PCG/**"
# Do not use the old Content/EnvSandbox/Levels path; it is not the tracked route.
```

### For Material Artists:
```bash
# The toon spine IS tracked (since 2026-08-13): 121 masters + 18 TP_* profiles, 8.6 MB.
git lfs pull --include="Content/EnvSandbox/Materials/Masters/**,Content/EnvSandbox/Materials/ToonProfiles/**"
```

Everything else under `Content/EnvSandbox/Materials/` -- Instances/, SDF/, Landscape/,
Textures/ -- is **not tracked**. The old instructions here pulled
`Content/EnvSandbox/Materials/**/*.uasset` and `Content/EnvSandbox/Textures/*.png` and
claimed "~1-3GB"; both matched **zero** tracked files, so the pull succeeded and
downloaded nothing. Use the S3 art drop instead (see the top of this document).

### For Character/NPC Work:
```bash
git lfs pull --include="Content/Characters/**"          # 71 tracked files
git lfs pull --include="Content/Melodia/Characters/**"  # Melusina, Kiritan, Itako, Zunko

# NOT tracked: Content/Audio/Voice/*.wav -- there is no un-ignore for Content/Audio,
# so the old `git lfs pull --include="Content/Audio/Voice/*.wav"` line here matched
# nothing. Voice WAVs are not in the S3 art drop either -- ask the owner directly.
```

---

## Tier 2: Full Build Collaborator

**Best for:** Build engineers, packaging, PIE testing

```bash
# 1. Clone with LFS (~3-4 GB -- NOT 300 GB; the bulk art is not in the repo)
git clone https://github.com/fromage3900/MelodiaMelusinaV2.git MelodiaCollab
cd MelodiaCollab
git config core.hooksPath .githooks

# 2. Install and pull all LFS assets
git lfs install
git lfs pull

# 3. Open BS_GodFile.uproject in UE 5.8
# 4. Install VS 2022 Desktop development with C++ and the Windows SDK
# 5. Build the source-only plugins with the editor closed:
powershell -ExecutionPolicy Bypass -File .\deploy\validate_setup.ps1 -SkipServices -CheckLfsHydration
$ueRoot = if ($env:MELODIA_UNREAL_ROOT) { $env:MELODIA_UNREAL_ROOT } else { "C:\Program Files\Epic Games\UE_5.8" }
& "$ueRoot\Engine\Build\BatchFiles\Build.bat" BS_GodFileEditor Win64 Development -Project="$PWD\BS_GodFile.uproject" -NoUBA -MaxParallelActions=1
# 6. Confirm compiled plugin binaries:
powershell -ExecutionPolicy Bypass -File .\deploy\validate_setup.ps1 -SkipServices -CheckLfsHydration -RequirePluginBinaries
```

---

## Tier 3: Code/Docs Reviewer

**Best for:** Code review, planning, documentation review

```bash
# 1. Clone without LFS (~50MB, ~1 minute)
git clone --filter=blob:none https://github.com/fromage3900/MelodiaMelusinaV2.git MelodiaCollab
cd MelodiaCollab

# 2. That's it! All source code, configs, and docs are available.
```

---

## 📋 Work-Specific Download Sizes

| Role | What is in the repo | Size | Time |
|------|---------------------|------|------|
| 🔍 **Viewer** | Source, configs, docs | ~50 MB | 1 min |
| 🏗️ **Level Design** | Route `.umap`s + PCG graphs (`Content/Melodia/Levels`, `Content/EnvSandbox/Environments`) | ~50 MB | 2 min |
| 🎨 **Material Art** | 121 masters + 18 toon profiles | 8.6 MB | 1 min |
| 🧑‍🤝‍🧑 **Character/NPC** | Melusina/Kiritan/Itako/Zunko + `Content/Characters` | ~150 MB | 3 min |
| 🏭 **Full Build** | All of the above + tracked plugins | **~3-4 GB** | 1-2 hours incl. C++ build |

**None of these rows includes the environment art.** Meshes, instance materials, textures
and voice WAVs (~13 GB of authored work plus ~40 GB of re-downloadable marketplace content)
are not in git. Levels will open with missing references until the owner supplies the drop.
The old version of this table promised up to 300 GB from a `git lfs pull`; that was wrong in
every row.

---

## 🔄 Working Together

### Source Control Ownership

Use Git for code, configuration, plugins, tools, documentation, and automation. Perforce is being
introduced for large and lock-sensitive creative assets. The current `//melodia/Exports/...` seed is
on a workstation-local pilot server (`localhost:1667`), so it is not a collaborator download path yet.

Until a shared Perforce server, backup, and clean-machine acceptance test are complete:

- Continue to clone and hydrate the project through Git/Git LFS and the documented S3 art drop.
- Do not configure a collaborator against the local Perforce pilot.
- Do not edit an `Exports/` asset through both Git and Perforce.
- Keep `Content/` Git-owned; its Perforce migration has not begun.

See [Docs/PERFORCE_MIGRATION_PLAN_2026-08-13.md](Docs/PERFORCE_MIGRATION_PLAN_2026-08-13.md)
for cutover gates and [Docs/Handoffs/SESSION_CLOSEOUT_SOURCE_CONTROL_2026-08-27.md](Docs/Handoffs/SESSION_CLOSEOUT_SOURCE_CONTROL_2026-08-27.md)
for the current verified pilot state.

### Sharing Changes
```bash
# When you save changes, commit and push:
git add <your-changed-files>
git commit -m "feat: describe your change"
git push origin <your-branch>
```

Before creating a text-only commit, run:

```powershell
python Tools/source_control_triage.py
```

It runs every 12 hours locally in report-only mode and classifies binaries and future Perforce-owned
paths as review-only. It never stages or commits work automatically.

### Branch Naming
Use the `collab/[role]/[feature]` convention:

```
collab/level-design/kaleido-nave
collab/material-art/toon-outline
collab/ui/combat-widget
collab/docs/collab-guide
```

### Pulling Collaborator Changes
```bash
git pull
git lfs pull --include="Content/Path/To/New/Assets/*"
```

---

## 🚨 Important Notes

### What Collaborators CAN Do:
- ✅ Work on levels you've already created
- ✅ Modify existing geometry and materials
- ✅ Add new levels and assets
- ✅ Use all gameplay systems
- ✅ Run the validation scripts

### What Collaborators CANNOT Do (without full download):
- ❌ Access ALL character assets
- ❌ Access ALL texture libraries
- ❌ Access ALL voice files
- ❌ Use some specialized content
- ❌ Build the full project for shipping

### Solution: Expand as Needed
```bash
# If a collaborator needs more content later:
git lfs pull --include="Content/Characters/**"
git lfs pull --include="Content/Audio/**"
```

---

## ✅ Validation

Run the UE validator to confirm the project and plugin checkout is healthy:

```bash
bash deploy/validate_collaborator_setup.sh . ue
```

Then run the strict Windows validator:

```powershell
.\deploy\validate_setup.ps1 -SkipServices -CheckLfsHydration
```

Source-only plugin binaries are expected to warn before the first build.
After compiling, add `-RequirePluginBinaries` and require an exit code of `0`.

---

## 🆘 Troubleshooting

**Problem:** "Asset appears as pink/missing in Unreal"
**Solution:** First work out which of two different problems you have.

1. **The asset is not in the repository at all** — by far the more likely case, and the
   expected state on a fresh clone. Bulk environment art is gitignored on purpose. Check:
   ```bash
   git ls-files "Content/EnvSandbox/Meshes" | head    # empty => never committed
   ```
   If that is empty, **no `git lfs pull` will help.** Sync the S3 art drop instead. The
   previous version of this entry told you to run a pull, which silently succeeds and
   downloads nothing — that dead end cost real time.

2. **The asset is tracked but its LFS content is not hydrated** — a pointer file on disk
   instead of the real binary. Check for a 130-byte text file starting with
   `version https://git-lfs.github.com/spec/v1`:
   ```bash
   git lfs ls-files --long | grep -i "<asset name>"   # '-' = not hydrated, '*' = hydrated
   git lfs pull --include="Content/Path/To/Missing/Asset/**"
   ```
   Unreal reports an unhydrated pointer as an invalid package tag, which reads like file
   corruption and is not.

**Problem:** "A `.uasset` or `.umap` is read-only and Unreal will not save it"
**Solution:** Working as intended. `.gitattributes` marks 2,224 files `lockable`, and LFS
checks lockable files out read-only. Take the lock first:
```bash
git lfs lock Content/EnvSandbox/Environments/L_KaleidoNave.umap
# ... edit, commit, push ...
git lfs unlock Content/EnvSandbox/Environments/L_KaleidoNave.umap
```

**Problem:** "My push was rejected before it started"
**Solution:** `.githooks/pre-push` enforces branch prefixes — `feature/ fix/ docs/ cleanup/
collab/ codex/ recovery/ cursor/`. A bare lane name like `gameplay` is rejected. It also
enforces an LFS batch budget: **50 MB** on `collab/`, `cursor/` and `docs/` branches,
512 MB elsewhere.

**Problem:** "MeshBlend, PCGEx, or another plugin is missing"
**Solution:** Confirm the collaborator used the `lightweight` UE tier, not the
Blender-only sparse tier. Verify `BS_GodFile.uproject` and the complete
`Plugins/` tree are present, then run the closed-editor UE 5.8 source build.

**Problem:** "Plugin module DLL could not be loaded"
**Solution:** Plugin binaries are intentionally not tracked. Install VS 2022
Desktop development with C++, close Unreal, run the `Build.bat` command above,
and rerun `validate_setup.ps1 -RequirePluginBinaries`.

**Problem:** "Git LFS not working"
**Solution:**
```bash
git lfs install
git lfs pull
```

**Problem:** "Need more content later"
**Solution:**
```bash
git lfs pull --include="Content/AdditionalFolder/**"
```

**Problem:** "Pre-commit hook blocked my commit"
**Solution:** The hook validates LFS tracking and file sizes. If you're committing a large binary:
```bash
git lfs track "<pattern>"
git add <file>
```

---

## 🖥️ Multi-machine development

If you're setting up a second machine (laptop, workstation) for this project, see:

- `Docs/Production/TWO_PC_DEVELOPMENT_WORKFLOW_2026-09-02.md` — five-lane workflow (Gateway, VS Code SSH, UBA, Git handoff, Hermes orchestration)
- `Docs/Production/MASTER_INDEX.md` — full doc navigation hub

Each workstation gets its own clone. Git/Git LFS + explicit handoff branches are shared authority. Do not edit the same binary asset from both machines at once.

---

## 📊 Storage Comparison

| Approach | Download Size | Time | Suitability |
|----------|--------------|------|-------------|
| **Full Clone** | ~3-4 GB + 3.06 GiB art drop | 1-2 hours (mostly the C++ build) | Leads/build engineers. Sync the S3 art drop to render a level. |
| **Level Design** | ~2-5GB | 5-10 min | **Perfect for collaboration** |
| **Material Work** | ~1-3GB | 3-8 min | Material artists |
| **Source Only** | ~50MB | 1 min | Code review, planning |

---

## 🎉 Summary

**For level design collaboration:**
1. Collaborator clones repo **without LFS** (~50MB)
2. Downloads **only level design essentials** (~2-5GB)
3. Works together with you on shared levels
4. Only downloads additional content as needed

**Result:** Fast onboarding (10-15 min vs 1-2 hours) and minimal storage usage!

---

**💡 Pro Tip:** Share this guide with your collaborators before they start. It will save them hours of download time and disk space!
