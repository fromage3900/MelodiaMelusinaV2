# MI Reparent — Execution Spec — 2026-08-30

**Source**: `Saved/Audit/orphan_mi_resolution_2026-08-31.json`
**Prerequisites**: Live Monolith MCP (`:9316`), editor open, no modal blocking

---

## Summary

| Group | Count | Action | Confidence |
|---|---|---|---|
| Foliage cards (Niagara) | 5 | REPARENT to M_ToonFoliage | HIGH |
| Melusina SorrowSeam | 1 | REPARENT to M_Master_Toon_Character | HIGH |
| Oceanology Hero water | 1 | REPARENT to M_Water_Master_Grand_v10_Upgrade | HIGH |
| StarryNight (Nikki) | 2 | REPARENT to M_Master_Nikki | HIGH |
| Water v10 native default | 1 | REPARENT to M_Water_Master_Grand_v10_Upgrade | HIGH |
| Rhythm surfaces | 5 | REPARENT to M_RhythmSurface_Pulse | MEDIUM |
| Grotto UnderwaterPP | 1 | REVIEW_IN_EDITOR (post-process master) | LOW |
| Showcase MelodiaVoid | 5 | REVIEW_IN_EDITOR (showcase master) | LOW |
| SDF parent redirects | 4 | REDIRECT stale strings | MEDIUM |

**Total**: 17 reparent, 4 review, 4 SDF redirects

---

## Step 0 — Pre-flight (MUST PASS FIRST)

```bash
# Verify Monolith live
curl http://localhost:9316/health

# Verify M_RhythmSurface_Pulse exists (search offline)
find Content/ -name "M_RhythmSurface_Pulse*" -o -name "M_RhythmSurface*"
# If missing, mark Rhythm orphans as REVIEW

# Verify M_PP_Grotto exists
find Content/ -name "M_PP_Grotto*"
# If missing, mark MI_Grotto_UnderwaterPP as REVIEW

# Verify MelodiaVoid referencers
# Run get_cdo_referencers on each MI_Show_MelodiaVoid_*
# If only used in presentation maps, they may use a dedicated showcase master
```

## Step 1 — Reparent HIGH Confidence (safe)

```
1. MI_Niagara_Foliage_Grass     → M_ToonFoliage
2. MI_Niagara_Foliage_Leaf1     → M_ToonFoliage
3. MI_Niagara_Foliage_Leaf2     → M_ToonFoliage
4. MI_Niagara_Foliage_Leaf3     → M_ToonFoliage
5. MI_Niagara_Foliage_Vine      → M_ToonFoliage
6. MI_Melusina_SorrowSeam       → M_Master_Toon_Character
7. MI_Oceanology_Melodia_Hero   → M_Water_Master_Grand_v10_Upgrade
8. MI_StarryNight_Impressionist_Swirl → M_Master_Nikki
9. MI_StarryNight_VanGogh       → M_Master_Nikki
10. MI_WaterV10_NativeDefault   → M_Water_Master_Grand_v10_Upgrade
```

**Monolith command** (example):
```python
# In editor Python console
import melodia_mcp_server
melodia_mcp_server.mi_set_parent(
    "Content/EnvSandbox/Materials/Instances/Foliage/MI_Niagara_Foliage_Grass.uasset",
    "M_ToonFoliage"
)
```

Or via REST:
```
POST http://localhost:9316/tools/mi_set_parent
{"mi_path": "...", "parent_name": "..."}
```

## Step 2 — Reparent MEDIUM Confidence (Rhythm)

```
11. MI_Rhythm_Arena_Neon       → M_RhythmSurface_Pulse
12. MI_Rhythm_Floor_Dream      → M_RhythmSurface_Pulse
13. MI_Rhythm_Floor_Stone      → M_RhythmSurface_Pulse
14. MI_Rhythm_Note_Highlight   → M_RhythmSurface_Pulse
15. MI_Rhythm_Podium_Hero      → M_RhythmSurface_Pulse
```

**Gate**: Only after M_RhythmSurface_Pulse verified in Step 0.

## Step 3 — SDF Parent Redirects

These MIs have stale parent strings referencing non-existent masters. Redirect to closest verified master:

| Stale Parent String | Redirect Target | Rationale |
|---|---|---|
| M_SDF_Bioluminescence | M_HybridStone_SDF | Organic/underwater SDF |
| M_SDF_BubbleColumn | M_SDF_ParallaxPulse | Animated/flowing SDF |
| M_SDF_CoralBranching | M_HybridStone_SDF | Organic stone/moss |
| M_SDF_FloatingNotes | M_SDF_TrueParallax_Inst | Magical/musical SDF |

```
Action: REDIRECT_STALE_PARENT_STRINGS in editor
These are likely cached names from renamed/removed SDF masters.
```

## Step 4 — Review in Editor (do NOT auto-reparent)

| Asset | Proposed Master | Risk |
|---|---|---|
| MI_Grotto_UnderwaterPP | M_PP_Grotto (verify exists) | PostProcess master — wrong parent breaks rendering |
| MI_Show_MelodiaVoid_Baroque | M_Master_Toon_Universal (tentative) | Showcase variant — may intentionally use non-standard master |
| MI_Show_MelodiaVoid_Cosmic | same | same |
| MI_Show_MelodiaVoid_Neutral | same | same |
| MI_Show_MelodiaVoid_Sakura | same | same |
| MI_Show_MelodiaVoidGradient | same | same |

**Action**: Open each in editor, check referencer list, pick correct parent manually.

## Step 5 — Verify

```bash
python Tools/project_state.py
python Tools/bp_sweep.py
melodia_material_audit
```

---

## Safety Notes

- ⚠️ Requires live Monolith MCP. If MODAL_OPEN warnings persist, dismiss editor modals first.
- ⚠️ Never hand-edit `.uasset` — always use editor Python or Monolith.
- ⚠️ Reparent changes MI parent — does NOT modify the master itself.
- ⚠️ `delete_asset` only on assets you created; never on anything you didn't.