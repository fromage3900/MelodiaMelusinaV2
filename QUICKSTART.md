# 🚀 Quick Start Guide

**Get started in 5 minutes or less!**

---

## 💡 Working with a Team? Read This First!

**👥 Collaborators:** Don't download the full 300GB! Use the tiered onboarding scripts:
```bash
# Lightweight collaborator
bash deploy/collaborator_onboarding.sh lightweight

# Docs/code-only
bash deploy/collaborator_onboarding.sh docs

# Validate the UE-capable checkout
bash deploy/validate_collaborator_setup.sh . ue
```

This downloads only ~2-10GB instead of 300GB! 🎉

**📖 Full guide:** [COLLABORATOR_SETUP.md](COLLABORATOR_SETUP.md)

### If plugins such as MeshBlend or PCGEx are missing

The Blender-only sparse checkout does not contain the Unreal project or its
plugins. Use the UE-capable lightweight tier instead:

```bash
bash deploy/collaborator_onboarding.sh lightweight
bash deploy/validate_collaborator_setup.sh . ue
```

The project plugins are source-only. Install UE 5.8 and Visual Studio 2022
Desktop development with C++, then build with Unreal closed:

```powershell
$ueRoot = if ($env:MELODIA_UNREAL_ROOT) { $env:MELODIA_UNREAL_ROOT } else { "C:\Program Files\Epic Games\UE_5.8" }
& "$ueRoot\Engine\Build\BatchFiles\Build.bat" BS_GodFileEditor Win64 Development -Project="$PWD\BS_GodFile.uproject" -NoUBA -MaxParallelActions=1
.\deploy\validate_setup.ps1 -SkipServices -CheckLfsHydration -RequirePluginBinaries
```

---

## 🎮 I Want to Play the Vertical Slice (First Dream)

> **Status (2026-08-13):** The game **is playable** in PIE. After Melusina's unique skill, the rhythm highway works (clunky), damage procs, and the next turn applies on skill finish. Rhythm combat and QuillScript are **owner-locked WORKED** — do **not** reopen as P0 (`Docs/Handoffs/RHYTHM_GAME_LOCKED_2026-08-12.md`, `Docs/Handoffs/QUILLSCRIPT_LOCKED_2026-08-12.md`). Formal Echo `runtime` ledger (A/B + harness JSON) is still open. Alternate stock battle entry (Morning → KaleidoNave collider/dreamstate path) is still being worked. Living board: [Docs/Handoffs/PIE_RUNTIME_NOTES_2026-08-12.md](Docs/Handoffs/PIE_RUNTIME_NOTES_2026-08-12.md).

### Step 1: Install Unreal Engine 5.8
```
📥 Download from Epic Games Launcher
📁 Install to: C:\Program Files\Epic Games\UE_5.8\
```

### Step 2: Open the Project
```
📂 Open: BS_GodFile.uproject
⏳ Wait for shaders to compile (first run only)
📌 Prefer a fresh pull of main (RestoreParty + playable levels are on main)
```

### Step 3: Play the Live Route
```
🎮 Route: L_MelusinaMorning → L_KaleidoNave
   (L_Melodia_Dreamstate was merged into KaleidoNave on 2026-08-10 — do not hunt a live Dreamstate map)
📂 Real paths:
   /Game/Melodia/Levels/Opening/L_MelusinaMorning
   /Game/EnvSandbox/Environments/L_KaleidoNave

▶️ PIE from Morning (or open KaleidoNave if you only want the battle space)
⚔️ Reach the encounter → start battle → cast Melusina's unique skill
🎹 Rhythm highway appears (clunky OK) → hit lanes → damage should proc
⏭️ Next turn should apply when the skill finishes
```

### Step 4: Known Rough Edges (still playable)
```
• Rhythm highway feel is clunky — expected for now
• Some alternate battle entry paths (old dreamstate / collider-name) are still being worked
• Formal runtime gate needs Decision 024 A/B + record_gate.py before release claims
```

### Step 5: Current State Docs
```
📖 Docs/Handoffs/PIE_RUNTIME_NOTES_2026-08-12.md — living PIE board
📖 _SESSION_HANDOFF.md — most recent session state
📖 _VERTICAL_SLICE_SCOPE.md — scope authority
```

**✅ Done!** You've got a playable First Dream loop in PIE.

---

## ⚡ I Just Want to See the Environment Art (Viewer Mode)

### Step 1: Install Unreal Engine 5.8
```
📥 Download from Epic Games Launcher
📁 Install to: C:\Program Files\Epic Games\UE_5.8\
```

### Step 2: Open the Project
```
📂 Open: BS_GodFile.uproject
⏳ Wait for shaders to compile (first run only)
```

### Step 3: Explore the Levels
```
🎮 Open: /Game/Melodia/Levels/L_MelusinaMorning
🎮 Open: /Game/EnvSandbox/Environments/L_KaleidoNave
🎮 Open: /Game/EnvSandbox/Environments/L_KaleidoNave
🎮 Open: /Game/EnvSandbox/Environments/WP/L_WP_SakuraDream
```

**✅ Done!** You've seen the project's environments.

---

## 🏗️ I Want to Build Things (Geometry Mode)

### Step 1: Install Blender 5.2+
```
📥 Download: https://www.blender.org/download/
📁 Install to: C:\Program Files\Blender Foundation\Blender 5.2\
```

### Step 2: Open Both Apps
```
📂 Open: BS_GodFile.uproject (Unreal)
📂 Open: Any .blend file (Blender)
```

### Step 3: Start Live Bridge
```
🔧 In Blender (press N for side panel):
├── Click "Melodia Studio" tab
├── Find "Live Bridge" 
├── Click "Refresh Status"
└── Click "Start Server" under LiveLink :9876
```

### Step 4: Create & Send Asset
```
🎨 In Blender Melodia Studio:
├── Go to "Genome Carousel"
├── Pick "ZEN_SHRINE" → Click "Apply"
└── Click "Send + Materials" in Live Bridge
```

### Step 5: Use in Unreal
```
🎮 In Unreal:
├── Find your asset in /Game/LiveLink/
├── Drag it into /Game/EnvSandbox/Environments/L_KaleidoNave
└── Position it where you want!
```

**✅ Done!** You're now building live levels!

---

## 🎨 I Want to Make Materials (Material Mode)

### Step 1: Open Test Level
```
🎮 Open: /Game/EnvSandbox/Environments/L_KaleidoNave
```

### Step 2: Create Material Instance
```
🎨 In Content Browser:
├── Find: /Game/EnvSandbox/Materials/Masters/M_Master_Toon_Universal
├── Right-click → "Create Material Instance"
└── Name it: MI_MyTestMaterial
```

### Step 3: Test It
```
🎮 In the level:
├── Create a cube (Place Actors panel → Basic Shapes → Cube)
├── Apply your material
├── Double-click material to edit parameters
└── See changes in real-time! ✨
```

**✅ Done!** You're creating materials!

---

## 🆘 Something Went Wrong

| Problem | Quick Fix |
|---------|-----------|
| 🔴 Unreal won't open | Make sure UE 5.8 is installed |
| 🔴 Can't find Melodia Studio | Enable `surreal_architecture_gen` / **Melodia Studio** in Blender preferences |
| 🔴 Port 9876 in use | Close other Blender instances |
| 🔴 Materials look gray | Run this in UE Python: `import resolve_material_crosswalk; resolve_material_crosswalk.resolve_all()` |

---

## 📚 Want to Learn More?

**📖 Full Guide:** [README.md](README.md) - Complete onboarding paths  
**📖 Gameplay Scope:** [_VERTICAL_SLICE_SCOPE.md](_VERTICAL_SLICE_SCOPE.md)  
**📖 Level Design:** [Docs/LEVEL_DESIGNER_ONBOARDING.md](Docs/LEVEL_DESIGNER_ONBOARDING.md)  
**📖 Materials:** [MATERIAL_LOOKDEV_PIPELINE.md](MATERIAL_LOOKDEV_PIPELINE.md)  
**📖 All Docs:** [DOC_INDEX.md](DOC_INDEX.md) - Complete documentation map  

---

## 🎯 Common Tasks

| Task | Command / Location |
|------|-------------------|
| 🎮 Play vertical slice | `L_MelusinaMorning` → `L_KaleidoNave` — unique-skill rhythm **playable**; stock battle entry still being worked |
| 🏗️ Test geometry | Open `/Game/EnvSandbox/Environments/L_KaleidoNave` |
| 🎨 Test materials | Create instance from `M_Master_Toon_Universal` |
| 🔧 Check services | Run `deploy/status.ps1` in terminal |
| 📖 View documentation | Open [DOC_INDEX.md](DOC_INDEX.md) |

---

**💡 Tip:** Want the game first? Use the vertical-slice path above. For art/tools, start with Viewer Mode, then Geometry Mode.

**🎉 Welcome to the team!**
