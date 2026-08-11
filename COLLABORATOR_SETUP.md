# Collaborator Setup Guide — MelodiaMelusinaV2

**Public repo:** https://github.com/fromage3900/MelodiaMelusinaV2  
**Live-ops + Echo:** [Docs/LIVEOPS_GIT_SOP_2026-08-11.md](Docs/LIVEOPS_GIT_SOP_2026-08-11.md)  
**Full clone is huge.** Use a ≤50 MB slice unless you need gameplay assets.

## Quick start (recommended)

```bash
git clone https://github.com/fromage3900/MelodiaMelusinaV2.git
cd MelodiaMelusinaV2
git config core.hooksPath .githooks

# ≤50 MB — pick one
bash deploy/collaborator_onboarding.sh docs50        # source/docs/Python
bash deploy/collaborator_onboarding.sh slice50       # MelodiaIntegration BPs (~10 MB LFS)
bash deploy/collaborator_onboarding.sh placement50   # Universal placement (needs EnvSandbox on workstation)

# ~2 GB Melodia+EnvSandbox+JRPG (formerly misnamed "lightweight")
bash deploy/collaborator_onboarding.sh gameplay

# Everything
bash deploy/collaborator_onboarding.sh full
```

Lock before editing binaries:

```bash
git lfs lock Content/MelodiaIntegration/Blueprints/BP_MelodiaTravelVolume.uasset
# ... edit in UE ...
git lfs unlock Content/MelodiaIntegration/Blueprints/BP_MelodiaTravelVolume.uasset
```

Push budgets (hooks enforce): `collab/` `cursor/` `docs/` → **50 MB** LFS batch; other branches → **512 MB**. Override: `MELODIA_LFS_LIMIT_MB=50`.

## Echo reminder

Gameplay claims need ledger rows (`python Tools/echo_run.py status`). A green clone is not a `runtime` pass.

## Tier table

| Tier | Size | Use |
|------|------|-----|
| `docs50` | ≤50 MB | Code/docs/Python review |
| `slice50` | ≤50 MB | Integration travel/UI/water BPs |
| `placement50` | target ≤50 MB | Universal PCG + physics placement |
| `gameplay` | ~2 GB | Level/material work with Melodia+EnvSandbox+JRPG |
| `full` | full LFS | Build / PIE / cook |

Manifests: `specs/collab_slices/*.json`. Blender-only sparse kit also documented in [Docs/SETUP_COLLAB.md](Docs/SETUP_COLLAB.md).

---

## Older notes

The sections below retain historical detail. Prefer the Quick Start tiers above when they conflict.

```bash
# 1. Clone the repo (skip LFS download — ~50MB)
git clone https://github.com/fromage3900/MelodiaMelusinaV2.git
cd MelodiaCollab

# 2. Install Git LFS
git lfs install

# 3. Enable sparse checkout (only needed folders)
git sparse-checkout init --cone
git sparse-checkout set \
  Content/Melodia/Levels \
  Content/EnvSandbox \
  Plugins/MelodiaCore/Source \
  Docs \
  Source \
  Config \
  deploy

# 4. Pull targeted LFS assets for your work
```

### For Level Designers (Geometry/Levels):
```bash
git lfs pull --include="*.umap"
git lfs pull --include="Content/Melodia/Levels/*.umap"
git lfs pull --include="Content/EnvSandbox/Levels/*.umap"
git lfs pull --include="Content/EnvSandbox/Meshes/*.uasset"
git lfs pull --include="Content/EnvSandbox/Materials/*.uasset"
# Total: ~2-5GB instead of 300GB!
```

### For Material Artists:
```bash
git lfs pull --include="Content/EnvSandbox/Materials/**/*.uasset"
git lfs pull --include="Content/EnvSandbox/Materials/Masters/*.uasset"
git lfs pull --include="Content/EnvSandbox/Textures/*.png"
# Total: ~1-3GB
```

### For Character/NPC Work:
```bash
git lfs pull --include="Content/Characters/**/*.uasset"
git lfs pull --include="Content/Characters/**/*.fbx"
git lfs pull --include="Content/Audio/Voice/*.wav"
# Total: ~5-10GB
```

---

## Tier 2: Full Build Collaborator

**Best for:** Build engineers, packaging, PIE testing

```bash
# 1. Clone with LFS (full ~300GB)
git clone https://github.com/fromage3900/MelodiaMelusinaV2.git
cd MelodiaCollab

# 2. Install and pull all LFS assets
git lfs install
git lfs pull

# 3. Open BS_GodFile.uproject in UE 5.8
# 4. Build the editor (Development)
```

---

## Tier 3: Code/Docs Reviewer

**Best for:** Code review, planning, documentation review

```bash
# 1. Clone without LFS (~50MB, ~1 minute)
git clone --filter=blob:none https://github.com/fromage3900/MelodiaMelusinaV2.git
cd MelodiaCollab

# 2. That's it! All source code, configs, and docs are available.
```

---

## 📋 Work-Specific Download Sizes

| Role | What to Download | Size | Time |
|------|------------------|------|------|
| 🔍 **Viewer** | Source code + docs only | ~50MB | 1 min |
| 🏗️ **Level Design** | Levels + geometry + materials | ~2-5GB | 5-10 min |
| 🎨 **Material Art** | Materials + textures | ~1-3GB | 3-8 min |
| 🧑‍🤝‍🧑 **Character/NPC** | Characters + voice | ~5-10GB | 10-20 min |
| 🏭 **Full Build** | Everything | ~300GB | 1-2 hours |

---

## 🔄 Working Together

### Sharing Changes
```bash
# When you save changes, commit and push:
git add <your-changed-files>
git commit -m "feat: describe your change"
git push origin <your-branch>
```

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

Run the setup validator to confirm your environment is healthy:

```bash
bash deploy/validate_collaborator_setup.sh
```

Expected output: exit code `0` with all checks passing.

---

## 🆘 Troubleshooting

**Problem:** "Asset appears as pink/missing in Unreal"
**Solution:**
```bash
git lfs pull --include="Content/Path/To/Missing/Asset/*"
```

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

## 📊 Storage Comparison

| Approach | Download Size | Time | Suitability |
|----------|--------------|------|-------------|
| **Full Clone** | ~300GB | 1-2 hours | Only for leads/build engineers |
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
