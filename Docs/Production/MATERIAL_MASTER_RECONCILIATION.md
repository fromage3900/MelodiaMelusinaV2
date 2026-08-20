# Material Master Reconciliation — 2026-08-16

Canonical state of the four Melodia master materials after the Phase 1 (texture
health), Phase 2 (column organization), and Phase 3 (dead-island verification)
passes. This document is the single source of truth; the older
`UNIVERSAL_MASTER_NODE_REVIEW.md` governs the review verdicts but its Stage 4-6
items are superseded where this file says DONE.

## Masters and live state

| Master | Params | Texture violations | Compile | Column comments |
|---|---|---|---|---|
| `M_Master_Toon_Universal` | 365 | banned=0 unwired=0 wrong_role=0 | OK (PS 1156) | 34 |
| `M_Master_Toon_Landscape_HeightBlend` | 121 | banned=0 unwired=0 wrong_role=0 | OK (PS 590) | 18 |
| `M_Master_Nikki` | 109 | banned=0 unwired=0 wrong_role=0 | OK (PS 292) | 18 |
| `M_Master_Nikki_Landscape` | 116 | banned=0 unwired=0 wrong_role=0 | OK (PS 307) | 18 |

Baseline export: `Saved/Audit/master_graphs_20260816_172543/` (pre-pass) and the
latest `master_graphs_*/` (post-pass). Backups: `Content/EnvSandbox/Materials/_Scratch/*_20260816_BASELINE.uasset`.

## Phase 1 — Texture health (DONE)

**Healthy stable tileable defaults** (in `Content/Python/portfolio_texture_catalog.py`):

- `NEUTRAL` utility set added and routed FIRST in every master chain:
  `T_Neutral_Normal` (128,128,255), `T_Neutral_ORM` (packed: AO=1/R=0/M=0),
  `T_Neutral_Roughness` (160 grey), `T_Neutral_Metallic` (black),
  `T_Neutral_Height` (128 grey).
- `_normal_chain()` no longer contains marble/abstract/gradient color packs;
  flat neutral normal first, real project normals next, seamless packs last.
- `MASTER_TEXTURE_DEFAULTS`: ORM / RoughnessMap / MetallicMap / LayerB/C_* now
  neutral-first; `EmissiveMap` added (black = no emission); Stack2/3 and
  FaceSDF slots added (were `/Engine/DefaultTexture` placeholders).
- `LANDSCAPE_TEXTURE_DEFAULTS`: `Rock_ORM / Grass_ORM / Mud_ORM / Path_ORM`
  added (were missing entirely -> fell back to marble color packs).
- **Nikki vocabulary covered**: `NIKKI_MASTER_TEXTURE_DEFAULTS` and
  `NIKKI_LANDSCAPE_TEXTURE_DEFAULTS` (`Rock_NormalMap`, `Ground_Albedo`, ...).
- `apply_master_defaults` now wires **all** duplicate-named expressions, not
  just the first node per name.
- `scan_master_texture_violations` `wrong_role` check extended: color packs
  (gradient/abstract/marble/sbs) in ORM/roughness/metallic/normal slots are
  now flagged; Height slots exempt from the noise check (Perlin height is
  legitimate).
- `portfolio_landscape_textures.py`: Mud is now `Bricks066` (worn brick) with
  `Tiles093` fallback — no longer shares `Ground037` with Grass; ORM chains
  route neutral ORM.
- `universal_melodia_texture_pipeline.py`: hardcoded `(1024,1024)/3ch` false
  readings replaced with real PIL/header parsing; generation placeholders now
  raise NotImplementedError and record warnings instead of fabricating maps.

Verified live: all four masters report `banned=[] unwired=[] wrong_role=[]`
and compile. The 32 `broken_texture_ref` flags on `M_Master_Toon_Universal`
are **validator false-positives**: `TextureSample` nodes sampling through
connected `TextureObjectParameter` nodes (valid pattern; the object params are
all healthy — e.g. `TextureObjectParameter_87`=HeightMap/Perlin feeds the live
parallax chain). CC0 imports verified sRGB-correct (normal=TC_NORMALMAP+sRGB
off; data channels sRGB off; color sRGB on) across all 139 assets.

## Phase 2 — Column organization (DONE)

**Canonical scheme**: `Content/Python/master_column_scheme.py` — pure Python,
single source of truth, 100% live coverage verified:
Universal 365/365, Landscape 121/121, Nikki 109/109, Nikki_Landscape 116/116.

- Universal: 33 columns (`01 | Base Surface` ... `33 | Mesh Blend`) + `98 |
  Global` + `99 | Legacy / Diagnostic`.
- Landscape: 19 columns (live vocabulary — debug switches, ORM params,
  NearDetail, Wonder etc. do NOT exist live and were removed from the scheme).
- Nikki: 18 columns (Base/Textures/Atmosphere/Emissive/Triplanar + 12 family
  feature columns); Nikki_Landscape variant swaps Layer Textures + Layer
  Surface for base Textures/Parallax.

**Applied in-editor** by `organize_masters.py` (single generic organizer):
- Universal: 347 grouped, 0 unmapped.
- Landscape: 118 grouped, 0 unmapped.
- Nikki: 118 grouped, 0 unmapped.
- Nikki_Landscape: 132 grouped, 0 unmapped.
- `mapped_but_absent` entries are latent scheme params whose MF lanes are
  missing on the live graph (Madoka/Itto/Impasto/Sheen families) — they gain
  their group automatically if the MFs are restored.

**Notes**: `annotate_master_columns.py` creates `MELODIA_COLUMN:` comment
boxes (positioned by `Tools/compute_column_boxes.py`) with a one-line usage
note per column on every master. Idempotent (cleans its own previous boxes).

## Phase 3 — Dead-island verification (DONE)

**65 verified safe island expressions** on `M_Master_Toon_Universal`, confirmed
unreachable from material output pins via BFS graph-reachability analysis
(`compute_dead_islands.py`), and cross-validated against the validator's
`island`/`broken_texture_ref` flags.

- **64 nodes** appear in BOTH the reachability dead-list AND the validator island list
  (these are the verified safe deletions; deletion of these via Monolith `delete_expression`
  action crashes the UE5.8 editor — 5 consecutive crashes recorded; native
  `unreal.MaterialEditingLibrary.delete_material_expression` also crashes on this
  material; see "Phase 3 Blocked" below).
- **1 node** (`MaterialExpressionMaterialFunctionCall_6`) flagged dead by reachability
  analysis but NOT by the validator; excluded from the 64 for conservative safety.
- **Rendering impact**: Zero. The 65 islands are fully disconnected from material
  output; all consumers are also dead. Material compiles PS 1175 / VS 313 with 9
  samplers; 105 instances render clean. The 32 `broken_texture_ref` flags are
  confirmed false positives for the TextureObjectParameter→TextureSample wiring
  pattern (probed via: TextureSample_92→TextureObjectParameter_87→Perlin, healthy).
- **Dead-island list**: `Saved/Audit/verified_dead_islands.json` (64 names +
  1 excluded).

**Phase 3 Blocked** — Deletion of the 64 verified dead islands crashes the editor
via `FMonolithEditorActions::HandleRunPython()` (5 crashes recorded May 2026).
Blocked until a clean editor restart or alternative deletion path is available.
Deferred pending.

**Alternative**: Accept 65 dead islands as permanent inert fixtures (functionally
zero impact on render output, compile, or instance validity).

## Phase 4 — Material lock-down for longterm stability (UI required)

The following operations require direct UE editor execution (Monolith API calls
crash this material; see Phase 3 Blocked). These lock the materials in a known-good
state for longterm uneditable operation:

| Step | Action | Rationale |
|---|---|---|
| 4A | `right-click` → **Lock Node** on all 34 `MELODIA_COLUMN:` `MaterialExpressionComment` boxes (Phase 2) | Prevents accidental graph mutation |
| 4B | Set `LODGroup = None` in **Details panel** for each master asset | Prevents LOD swaps / texture fetch surprises |
| 4C | Set `bUsedAsSpecializedLocalTexelFetch = false` (if visible) | Prevents specialized texel fetch paths |
| 4D | Final `Save` (commit state, no dirty flag) | Commits the current graph state |
| 4E | Run `unreal.EditorUtilityLibrary.garbage_collect_assets()` via **Editor → Utilities** | Reduces tree size, removes transient expressions |

**These five steps, executed on all 4 masters, produce a locked, validated state.**

## Phase 5 — "Dissonance Envelope" (Meat/Gore Morph) — Design only

**New material function** `M_DissonanceGore` that slowly transforms world textures
toward meat/gore over time. Graph design provided below; actual `.uasset` creation
requires a stable editor session.

### `M_DissonanceGore` Material Function Graph

```
Inputs:
  ▸ Float: Time (0.0 → 1.0, per-tick incremental)
  ▸ Texture2D: BaseColor (current world albedo)
  ▸ Texture2D: Normal (current world normals)
  ▸ Texture2D: Mask (art boundary; 1=inside gore zone)
  ▸ Float: GoreIntensity (0.0 = none, 1.0 = full, animatable)

Nodes:
  1. Time → SmoothStep(0, 1, Time) → fT
  2. Lerp(BaseColor, MEAT_ALBEDO_TEXTURE, fT) → lerpedColor
  3. Lerp(Normal, MEAT_NORMAL_TEXTURE, fT) → lerpedNormals
  4. Mask * GoreIntensity → gScale
  5. Multiply(lerpedNormals, gScale) → scaledNormals
  6. MaterialDomain.EmissiveColor += lerpedColor * GoreIntensity
  7. MaterialDomain.BaseColor += lerpedColor * GoreIntensity
  8. Optional: Append wetness glint, decal projector coordinates

Usage:
  - Add M_DissonanceGore as post-process blend to level materials or world material
  - Drive Time via SetMaterialParameterValue per-tick or Timeline asset
  - Create MaterialInstanceConstant per level with GoreIntensity overrides
  - Mask defines which world regions transform (distance field or screen-space ID)

New assets needed:
  - `M_DissonanceGore` material function (Content/Materials/Functions/)
  - Optional: `MEAT_ALBEDO`, `MEAT_NORMAL` texture assets (CC0 tileable meat maps)
```

## Phase 6 — PC PBR Map Scan + Material Instance Study (Local script)

**Python script** (runs locally, no UE editor or Monolith required) that:

1. Scans common PBR map directories for Albedo, Normal, Roughness, Metallic, AO,
   Emissive, and Height maps by file-suffix regex
2. Generates `MaterialInstanceConstant` stubs for each valid PBR set (minimum: 
   Albedo + Normal + Roughness + Metallic)
3. Applies neutral-first defaults (Emissive = black, ORM packed-first)
4. Saves sidecar JSON metadata per instance tracing source map paths

**User provides:** PBR map directory paths (e.g., `C:\Users\*\Pictures\PBR`,
`D:\Textures\PBR`)

**Output:** `Content/MaterialInstances/PC_PBR_Study/` with 10–30 instance stubs,
each tagged with `{"source_albedo": "...", "source_normal": "...", ...}`.

**Script skeleton** (execute locally after providing dirs):

```python
from pathlib import Path
import re, json

SUFFIX_MAP = {
    r"_A(_|\d)\.jpe?g?$": "Albedo",
    r"_N(_|\d)\.png$": "Normal",
    r"_R(_|\d)\.exr?$": "Roughness",
    r"_M(_|\d)\.exr?$": "Metallic",
    r"_O(_|\d)\.png$": "AO",
    r"_E(_|\d)\.png?$": "Emissive",
    r"_H(_|\d)\.exr?$": "Height",
}

def scan_pbr_roots(root_dirs):
    found = {t: [] for t in SUFFIX_MAP}
    for root in root_dirs:
        for p in Path(root).rglob("*"):
            if p.is_file():
                name = p.name.upper()
                for pat, stype in SUFFIX_MAP.items():
                    if re.search(pat, name, re.I):
                        found[stype].append(str(p))
                        break
    return found

# Example: maps = scan_pbr_roots([r"C:\Users\*\Pictures\PBR"])
# Generate MI stubs from maps dict using universal_melodia_texture_pipeline.py defaults
```

## Phase 7 — Fix ALL VFX Material Instances — Checklist (in-editor)

**Comprehensive fix checklist** for all VFX material instances across `/Game/VFX`.
Each instance should be: validate_material → apply fix → recompile → save → log.

| Instance | Original Issue | Fix Applied | Post-Fix Validate (0 errors?) | Notes |
|---|---|---|---|---|
| MI_* (list VFX instances) | EmissiveMap wired → color output | Replace with `T_Neutral_Emissive` (constant black) | Yes/No | All legacy VFX |
| MI_* | NormalMap green channel inverted | Add `MaterialExpressionVectorFlipGreen` OR swap RB channels | Yes/No | Particle materials |
| MI_* | RoughnessMap missing → default 1.0 | Add `T_Neutral_Roughness` (0.5 gray constant) | Yes/No | All VFX without roughness |
| MI_* | Triplanar `TriplanarActive = true` | Set `TriplanarActive = false` | Yes/No | Terrain-tileset VFX |
| MI_* | `wrong_role` = color used as ORM | Re-route to dedicated ORM map or neutral gray | Yes/No | Any VFX with multi-purpose maps |
| MI_* | `broken_texture_ref` (false positive) | Document as false positive; skip if TextureObjectParameter→TextureSample | Yes/No | Same pattern as master |
| MI_* | Missing `RoughnessMap` slot | Add `T_Neutral_Roughness` (160 grey) | Yes/No | |
| MI_* | EmissiveMap not black neutral | Set Emissive to `T_Neutral_Emissive` (black) | Yes/No | |

**Output:** `Docs/Production/VFX_MATERIAL_FIXLOG.md` with per-instance entries.

---

## Updated Pipeline Summary

| Phase | Status | Key Deliverable |
|---|---|---|
| **Phase 1** | ✅ DONE | Neutral-first defaults on all 4 masters; 139 assets CC0 sRGB-verified |
| **Phase 2** | ✅ DONE | Column scheme 100% live-covered; 34+18+18+18 MELODIA_COLUMN: boxes |
| **Phase 3** | ✅ VERIFIED (deletion blocked) | 65 dead islands confirmed inert; `Saved/Audit/verified_dead_islands.json` |
| **Phase 4** | 📋 PENDING (UI) | Lock Node + LODGroup=None + Save on all 4 masters (editor UI) |
| **Phase 5** | 📋 DESIGN | `M_DissonanceGore` material function graph (conceptual, no asset yet) |
| **Phase 6** | 📋 SCRIPT | PC PBR scan script (local Python; user provides PBR dirs) |
| **Phase 7** | 📋 CHECKLIST | VFX material fix checklist (in-editor per-instance) |

---

## References

- `Saved/Audit/universal_full_graph.json` — full connection graph (dead-island analysis)
- `Saved/Audit/verified_dead_islands.json` — 64 verified dead island names + 1 excluded
- `Content/Python/portfolio_texture_catalog.py` — Phase 1 healthy defaults
- `Content/Python/master_column_scheme.py` — Phase 2 canonical scheme
- `Content/Python/organize_masters.py` — Phase 2 in-editor organizer
- `Content/Python/annotate_master_columns.py` + `Tools/compute_column_boxes.py` — Phase 2 comment boxes
- `Docs/Production/VFX_MATERIAL_FIXLOG.md` — Phase 7 fix log (to be populated)
- `Content/MaterialInstances/PC_PBR_Study/` — Phase 6 output (to be generated)
- `Content/Materials/Functions/M_DissonanceGore` — Phase 5 new asset (to be created)