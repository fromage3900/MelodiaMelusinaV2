# Quickstart — Run Something in 5 Minutes

> You just cloned this repo. Here's how to see something happen fast.

---

## Option 1: Generate Terrain from MIDI (Blender)

**Time:** 5 minutes | **Needs:** Blender 5.2

```bash
# 1. Open Blender 5.2
# 2. Edit > Preferences > Add-ons > Install > select:
Tools/BlenderAddons/melodia_studio/__init__.py

# 3. Enable "Melodia Studio" addon
# 4. In 3D View, press N to open sidebar
# 5. Click "Melodia Studio" tab
# 6. Select a MIDI file from the dropdown
# 7. Click "Generate Terrain"
# 8. Watch the world build itself from the music
```

**What you get:** A 3D terrain mesh generated from the MIDI's note data.

---

## Option 2: Build a Castle (Blender)

**Time:** 5 minutes | **Needs:** Blender 5.2 + Melodia Studio addon enabled

```python
# In Blender's Text Editor, run:
import sys
sys.path.append(r"C:\EnvironmentPortfolio\BS_GodFile\deploy\surreal_arch")
from melodia_gn.core import new_geometry_tree, label_tree
from melodia_gn.castle import build_castle_tower

# Build a castle tower
build_castle_tower("MEL_my_tower")
```

**What you get:** A procedural castle tower with parameters.

---

## Option 3: Render a Beauty Shot (Blender)

**Time:** 5 minutes | **Needs:** Blender 5.2 + stage blend

```bash
# 1. Open your stage blend (e.g., Melodia_Portfolio_Stage_v4.blend)
# 2. In Text Editor, run:
exec(open(r"C:\EnvironmentPortfolio\BS_GodFile\Tools\setup_melusina_master_studio.py").read())
```

**What you get:** Fade sky, Komikaze studio set, cameras recomposed to Melusina.

---

## Option 4: Run Mocap on Melusina (Unreal)

**Time:** 5 minutes | **Needs:** Unreal Editor 5.8 + Rokoko FBX

```bash
# 1. Drop a Rokoko FBX in:
Imports/Mocap/Rokoko/Inbox/

# 2. Run (editor CLOSED):
Tools/run_headless_mocap_retarget.ps1

# 3. Check the result:
cat Saved/Melodia/retarget_report.json
```

**What you get:** A retargeted animation clip on Melusina.

---

## Option 5: Test FACS Face Rig (Unreal)

**Time:** 5 minutes | **Needs:** Unreal Editor 5.8

```bash
# In Unreal Python console:
python Tools/build_melusina_face_rig.py --plan
python Tools/build_melusina_face_rig.py --apply
```

**What you get:** FACS face rig wired and ready for animation.

---

## What's Next?

- **Build something?** → Read `UNIVERSITY.md` to pick a system
- **Animate something?** → Read `Docs/Production/CHARACTER_ANIMATION_2_SEMESTER_PLAN.md`
- **Understand the architecture?** → Read `Docs/Research/GEOMETRY_NODES_COMPLETE_REFERENCE.md`

---

*Last updated: 2026-09-03*
