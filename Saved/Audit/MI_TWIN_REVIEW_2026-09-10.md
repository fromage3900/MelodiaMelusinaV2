# MI Twin Review — PBR_Auto Orphan vs Pretty Twins — 2026-09-10

**Method (offline, no editor):** SHA-256 over all 240 `.uasset` files in
`Content/EnvSandbox/Materials/Instances/Environment/PBR_Auto/`, then per-stem
`/Game/…` reference-set extraction (`MI_Orphan_<S>` vs `MI_<S>`) for all 96 stems
present in both forms. Full per-stem data: `mi_twin_review_2026-09-10.csv` (same folder).

## Headline findings

1. **Zero byte-identical twins.** No two files in the folder share a SHA-256 hash.
   Nothing can be retired on hash equality alone.
2. **All 96 Orphans are uniformly bare.** Every `MI_Orphan_*` embeds exactly one
   `/Game/` reference — itself. No texture bindings, no overrides. They are
   parent-Universal shells (~9–15 KB).
3. **All 96 pretty twins carry the authored state** (+1.4–9.8 KB each) and split
   into two classes:

### Class A — wired twins (24): texture bindings present, just need verify-and-keep

The twin binds albedo/normal/ORM-family maps the Orphan lacks. These are **done
work, not rework** — confirm in one editor pass that each bound map resolves,
then the Orphan is redundant (pending referrer check).

| Stem | Extra refs bound in twin |
|---|---|
| BezierDetails, Foot, Strings, ViolinBase, ViolinTop | `_PROJECT/04_Materials/Textures/Violin/` Displacement/Metallic/Roughness ⚠️ _PROJECT-bound |
| T_Sand | `PBR_Sets/Sand/` Metallic/Roughness + `_PROJECT/…/T_Sand_BSS_ao/height` ⚠️ _PROJECT-bound |
| Untitled_material | _PROJECT-bound (see CSV) ⚠️ |
| crystal1 | `PackTextures/EnchantedForest/` height/metallic/roughness |
| T_Crystal | `Textures/Melusina/Crystal/` Height/Metallic/Roughness |
| T_Cello | `Textures/Melusina/Cello/` Height/Metallic/Roughness |
| T_MelodyToken_Heart, T_Note, T_Treble, T_Stem1, T_Stembell, T_GildedPea | music-prop map sets (see CSV) |
| T_PrettyRock, T_SadRock, T_LandscapeGrayscale | rock/landscape sets |
| T_Leafcool | foliage set |
| T_WaterBase, T_WaterHighlight, T_WaterLayer2, T_WaterLayerMid | water sets |

### Class B — scalar-only twins (72): overrides only, need in-editor value review

Twin embeds no extra texture refs — the delta is scalar/vector/texture-weight
overrides (incl. the current branch's dirty `MI_T_*` edits). Includes all 15
`T_Bling_Rhinestone`, all 6 Cathedral, all FarawayMother/Melusina/Houdini/Terrace
sets. **These are the "actually just need to be updated" set:** open each twin
vs its Orphan in the editor, confirm `TextureWeight`/override values are
intentional, then retire the Orphan.

## Cross-cutting: 7 twins bind into `_PROJECT`

`BezierDetails, Foot, Strings, T_Sand, Untitled_material, ViolinBase, ViolinTop`
reference `/Game/Melodia/_PROJECT/04_Materials/Textures/…`. **Do not empty
`_PROJECT` before migrating these 7 bindings** (plus the MPC from the brass
staging JSON). They are the load-bearing set.

## Recommended execution

1. Class A (24): editor referrer check on twin → resolve maps → quarantine Orphan.
2. Class B (72): value review in batches ≤25 per the 09-09 orphan-wire plan.
3. Retire `MI_Orphan_*` only after twin proves live in PIE (one map-load smoke per batch).
4. Migrate the 7 `_PROJECT`-bound texture sets before any `_PROJECT` emptying.

**Evidence level:** source-built (binary hash + embedded-ref census). Live-proven
status requires the editor pass above. No files in `Content/` were modified by
this review.
