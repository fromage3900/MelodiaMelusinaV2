# Accessory Staging & Lookdev — Execution Plan

**Status:** Addon synced to live Blender (274/274 files). Silhouette grid blend exists but uses empties (GN doesn't evaluate on empties headless). MCP server needs restart.

---

## Step 0 — Start Blender with MCP (5 min)

The previous MCP session was killed. Restart:

```
blender.exe --python-expr "import bpy; import sys; sys.path.insert(0, r'P:/MelodiaMelusinaV2-Laptop/Plugins'); import blender_mcp; bpy.ops.blender_mcp.start_server()"
```

Or open Blender normally and run `blender_mcp.start_server()` from the Python console.

**Verify:** `netstat -ano | grep 9876` shows LISTENING.

---

## Step 1 — Verify addon loads (2 min)

In Blender Python console:
```python
from surreal_arch.melodia_gn.core import GROUP_BUILDERS
print([k for k in GROUP_BUILDERS if 'eyewear' in k])
```

Expected: `['MEL_eyewear_front', 'MEL_eyewear_temple', 'MEL_eyewear_hinge', 'MEL_eyewear_pair', 'MEL_eyewear_lens', 'MEL_eyewear_hero']`

---

## Step 2 — Fix silhouette grid (5 min)

The current grid uses empties. GN needs a mesh host. Two options:

**Option A — Fix the blend (recommended):**
- Open `Silhouette_Grid_v1.blend`
- For each empty, replace with a `Mesh > Cube` (or `Mesh Line` with count=1)
- Re-apply `MEL_eyewear_hero` modifier
- Rotate -90° X
- Re-save

**Option B — Regenerate headless:**
- Run `Tools/eyewear_verify/stage_silhouette_grid.py` (already creates mesh hosts)

---

## Step 3 — Compare silhouettes (10 min)

- Open the fixed grid blend
- For each of the 6 pairs, set viewport to front orthographic
- Screenshot: `Saved/Accessories/silhouette_{name}.png`
- User picks 1-2 shapes for lookdev

---

## Step 4 — Stage studio (10 min)

Create `Saved/Accessories/Melodia_Accessory_Studio_v1.blend`:

- **World:** Fade `Sky Night` (from `C:\Users\brenn\AppData\Roaming\Blender Foundation\Blender\5.2\extensions\user_default\fadeassets\data\data.blend`)
- **Lighting:** 3-point (Key 600W area, Rim 300W, Fill 200W)
- **Cameras:** 5 cams (Beauty/Front/Macro/Low/Turntable), clip_start=0.001
- **Render:** EEVEE, 1600×2000, 64 TAA, bloom 0.05

---

## Step 5 — Materials (15 min, user live)

Wire Principled materials to the hero builder's 5 slots:
- Frame: acetate (roughness 0.35-0.55, clearcoat 0.6-1.0)
- Bridge: acetate or metal
- Temple: acetate
- Hinge: metal (metallic 1.0, roughness 0.2-0.3)
- Lens: glass (alpha 0.15-0.35, NOT transmission for web)

Komikaze materials layered in after sync from desktop.

---

## Step 6 — Render (5 min)

- Beauty render from Cam_Beauty
- Turntable sequence (24-36 frames) from Cam_Turntable
- Save to `Saved/Accessories/renders/`

---

## Open Questions

1. **MCP start method** — does the addon auto-start, or do you run `blender_mcp.start_server()` manually?
2. **Komikaze sync** — copy from desktop now, or work with Principled first?
3. **Hero shape** — which silhouette(s) to take into lookdev?

---

*Plan by Melodia Agent, 2026-09-12. Awaiting approval to execute.*
