# Sea Above — Atlantis MI Diagnosis & Foliage Plan (2026-09-03)

## Atlantis Material Override Bug

**Root cause:** The level's `pick_mi()` function overrides ALL material slots on every
Atlantis mesh with a single Copernicus MI. Meshes authored with 1-5 specialized
materials (stone trim, gold, marble, leaves, grass) get ONE Copernicus MI (usually
FrostBloom) applied to every slot.

### Verified slot mapping (default vs override)

| Mesh | Default materials (authored) | Override (buggy) |
|---|---|---|
| SM_ATL_Palace_TreeA | AtlasTreeA (1 slot) | FrostBloom |
| SM_ATL_Palace_ShrubsA | Grass, FlowersA, LeafA, LeafB (4 slots) | FrostBloom |
| SM_ATL_Palace_ColumnsA | BrickStoneTrimB, StoneTrimA/B, FloorPillars, PillarsA (5 slots) | CavernWeave |
| SM_ATL_Palace_ArchA | BrickStoneTrimB, StoneTrimA, StoneTrimB (3 slots) | CavernWeave |
| SM_ATL_Palace_TableA | StoneTrimB, Baskets, GoldWornA, MarbleWhiteA (4 slots) | PearlWeave |

### What breaks
1. **Texture weights wrong**: FrostBloom (a leaf/frost atlas) applied to stone/gold/marble slots — the albedo doesn't match the material's expected channels.
2. **Albedo maps wrong**: UV layout expects trim-atlas, receives a full-tile frost texture; normals/ORM meaningless on wrong slots.
3. **Visual result**: Stone looks like frost, gold looks like leaves, marble looks like CavernWeave.

### Fix options

**Option A (clean): Drop the override → restore authored KB3D materials.**
- Pro: Materials match what the artist authored (brick, stone, gold, marble, grass, leaves).
- Con: Doesn't get the Copernicus cymatic palette.

**Option B (targeted): Slot-aware override.**
- Map each slot index to an appropriate MI:
  - Stone/brick slots → CavernWeave or keep KB3D stone MIs
  - Foliage/leaf slots → FrostBloom
  - Gold/metal slots → GoldWornA (keep default)
  - Marble slots → MarbleWhiteA (keep default)
- Pro: Keeps both the cymatic identity AND the authored material logic.
- Con: Requires per-mesh slot mapping.

**Recommended: Option B.** Keep KB3D for non-foliage (stone/gold/marble/metal),
override foliage slots (grass/flowers/leaves) with FrostBloom. This preserves the
Atlantis kit's material identity while adding the cymatic palette where it belongs.

## Foliage Scattering Plan

### Palace environs (near loop)
- SpeedTree trees (M_SpeedTreeMaster) flanking the walkway ribbon
- SM_Flora_Chime/Fern/Reed along the XylophoneTrail corridor
- Megascans 3D_Plants (palms/ferns/bushes) in courtyard gaps

### Island foliage (above-sea, golden radii)
- Use `specs/water_veil/sea_above_foliage.v1.json` (already generated, 86 pts)
- Add SpeedTree canopy on the larger islands (radius > 21k)
- Megascans AlexandraPalm/BeechFern/BostonFern on island slopes

### Underwater (already dressed)
- 136 reef/abyss/jelly + SM_Kelp_* — no duplication

## Execution order

1. **Fix Atlantis overrides** → slot-aware MI mapping (editor UI)
2. **Scatter palace foliage** → SpeedTree + reef-kit flora along ribbon
3. **Apply island foliage manifest** → 86 pts, Megascans + SpeedTree
4. **Verify** → reload, screenshot, record gate row