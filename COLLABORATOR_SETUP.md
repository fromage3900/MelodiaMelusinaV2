# 👥 Collaborator Setup Guide

**Work together without downloading the full 300GB project!**

```
✧ ┊ ⋆ ┊ . ┊ ┊┊ ┊⋆ ┊ .┊ ┊ ⋆˚  ✧
```

---

## 🎯 Problem: Full Clone = 300GB Download

The current project tracks all binary files in Git LFS (textures, models, audio, etc.), which means a full clone is ~300GB. For collaborators working on specific tasks, this is overkill.

## ✅ Solution: Tiered Onboarding

Pick the tier that matches your role. Each tier downloads only what you need.

| Tier | Role | Clone Size | Setup Time |
|------|------|-----------|------------|
| **Tier 1 — Lightweight** | Level design, material art, UI work, documentation | 2–10 GB | 10–15 min |
| **Tier 2 — Full Build** | Build engineer, packaging, PIE testing | ~300 GB | 1–2 hours |
| **Tier 3 — Code/Docs Reviewer** | Code review, planning, documentation review | ~50 MB | ~1 minute |

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

# Validate your setup
bash deploy/validate_collaborator_setup.sh
```

---

## Tier 1: Lightweight Collaborator

**Best for:** Level design, material art, UI work, documentation

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
