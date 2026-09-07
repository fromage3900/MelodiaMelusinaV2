# 𝄞 MELUSINA HOUSE GN — START HERE

> **AGENT DISCOVERY KEY:** `MELUSINA_HOUSE_GN_START_HERE`  
> Search aliases: `Melusina House GN` · `MH foundation` · `Melodia Studio house` · `MEL_mh_` · `round baroque house`

**This file is the current agent entrypoint for Melusina's House Geometry Nodes.**  
Do **not** begin with dated Phase-2/Phase-3 plans. Those are design memory. Begin here, then follow the live builder modules.

## ♪ The correction

Earlier house plans used names like `GN_MH_01_FoundationPorch` as **conceptual scene-wrapper names**. Agents repeatedly mistook them for shipped Melodia Studio builder IDs.

The live Melodia Studio contract is:

```text
MEL_* = registered Melodia Studio builder ID
GN_MH_* = optional scene-local composition name only
```

If you cannot find a `GN_MH_*` node group, that is not proof the house system is missing.

## ♬ Live source modules

Read these in this order:

1. `deploy/surreal_arch/melodia_gn/melusina_house_foundation.py`
2. `deploy/surreal_arch/melodia_gn/melodia_house.py`
3. `deploy/surreal_arch/melodia_gn/melusina_house.py`
4. `deploy/surreal_arch/melodia_gn/house_dress.py`
5. `deploy/surreal_arch/melodia_gn/__init__.py`
6. `deploy/surreal_arch/melodia_gn/core.py`
7. `deploy/surreal_arch/melodia_gn/presets.py`

Detailed integration notes:
`Docs/MelodiaStudio/MELUSINA_HOUSE_GN_BUILDER_INTEGRATION_2026-09-04.md`

**Current next-builder roadmap:**
`Docs/MelodiaStudio/MELUSINA_HOUSE_GN_FOUNDATION_TO_SHELL_ROADMAP_2026-09-04.md`

Visual/design plan:
`melusinashouseplan.md`

Reference boards:
`Docs/References/MelusinasHouse/`

## ♫ Builder ladder

### Foundation — start here

```text
MEL_mh_foundation_pod
MEL_mh_foundation_cluster
MEL_mh_foundation_porch
MEL_mh_foundation_master
```

Use **Foundation Master** for the first whole-house blockout.

### Structural shell

```text
MEL_mh6_room_shell
MEL_melusina_house_round_interior
```

### House-specific AAA detail

```text
MEL_mh_aaa_cornice
MEL_mh_aaa_dentil
MEL_mh_aaa_scallop_uv
MEL_mh_aaa_lissajous_pearl
```

### House dressing

```text
MEL_mh_piano_walk
MEL_mh_sheet_rail
MEL_mh_staff_rows
MEL_mh_xylo_fountain
MEL_mh_stepping_stones
MEL_mh_lantern_row
MEL_mh_tree_line
```

After this integration pass, these live under the **Melusina House** GN Stack category instead of being scattered across Structures / Ornament / Set Dressing.

## ♪ Correct build order for an agent

```text
1 foundation master
→ 2 clay silhouette screenshot
→ 3 room shell / round interior
→ 4 openings + roof work
→ 5 AAA cornice/scallop/pearl detail
→ 6 house dressing
→ 7 materials
→ 8 Unreal export proof
```

Do not begin with furniture, shaders, foliage, or Nanite.

### ♫ Current next-builder batch

After the Foundation Master Blender smoke, the canonical next implementation batch is:

```text
MEL_mh_roof_ribbon
MEL_mh_opening_family
MEL_mh_porch_stair
```

Build these one at a time. The full contracts, reuse rules, evidence gates, and later `Listening Tower → shingle distributor → Melusina Loop` sequence live in the foundation-to-shell roadmap linked above.

## 𝄞 Verification

From repo root:

```powershell
python Tools/verify_melusina_house_gn_catalog.py
```

Then in Blender 5.2:

1. Open **Melodia Studio → GN Stack**.
2. Search `MH Foundation`.
3. Confirm the **Melusina House** section exists.
4. Add `MH Foundation Master` to a disposable mesh.
5. Change `Side Spread`, `Porch Offset`, and `Tower X`.
6. Confirm the footprint visibly changes.
7. Do **not** save over the live v22 portfolio stage from agent automation.

## ♬ What counts as proof

```text
source file exists
≠
registered in GROUP_BUILDERS
≠
visible in Melusina House GN Stack section
≠
builder constructs in Blender 5.2
≠
artist-approved house asset
```

State which level you have.

> **Start from live builder IDs, not prose aliases. Foundation first. Ornament later.** ♪
