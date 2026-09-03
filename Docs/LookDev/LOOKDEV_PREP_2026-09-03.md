# Lookdev Prep — Melusina V2, Oceanology, MF_Nikki, Main Menu (2026-09-03)

All findings below come from live editor queries (Monolith 0.20.3, UE 5.8), not from docs.

---

## 1. Melusina — I was tuning the wrong instances (owner was right)

The current outfit is **V2**, and it is **modular: 5 skeletal meshes**, not one, under
`Content/Melodia/Characters/Melusina/Outfits/V2/`. Its `Materials/` folder is **empty** —
no V2-specific instances have been authored, so every V2 mesh falls back to the
**base** `Melusina/Materials/MI_Melusina_*` set.

| V2 mesh | Slots | Instances actually bound |
|---|---|---|
| `SK_Melusina_V2_Body` | 5 | `SBW_MELUSINA_006`, `SBW_MELUSINA_007` (skin), `IRISFRONT_001` (eyes), `Outline_005` |
| `SK_Melusina_V2_Shirt` | 1 | **`MI_Melusina_UpdatedShirt`** |
| `SK_Melusina_V2_Skirt` | 4 | `SKIRT_003`, `Halftone_3_Inputs_-_Lines___Circles_002`, `skirtpanel_002`, `Outline_005` |
| `SK_Melusina_V2_Boots` | 2 | `MI_Melusina_Material_017`, `Outline_005` |
| `SK_Melusina_V2_Accessories` | 10 | gloves / sleeve / bow / frontpanel / shawl — **cross-wired, see 1a** |

**Consequences for the outstanding deltas:**

- **Grey torso** = the SHIRT mesh, one slot, instance **`MI_Melusina_UpdatedShirt`** —
  not `Material_023` / `_013` / `_021`, which is what I had been probing.
- **Boots too dark** = `MI_Melusina_Material_017`.
- **Skirt trim** = `skirtpanel_002` / `Halftone_3_Inputs_-_Lines___Circles_002`.

`SK_Melusina_V2_Body` carries 120 morph targets (full viseme + ARKit facial set) and
3 sockets (`S_HairAnchor` on `head_x`, `S_Instrument_L/R` on the hands).

### 1a. `SK_Melusina_V2_Accessories` slot to instance is cross-wired

| idx | slot name | bound instance | matches name? |
|---|---|---|---|
| 0 | `GLOVES_001` | `MI_Melusina_GLOVES_001` | yes |
| 1 | `sleeve_003` | `MI_Melusina_GLOVES_001` | **no** |
| 2 | `bow_002` | `MI_Melusina_sleeve_003` | **no** |
| 3 | `frontpanel_001` | `MI_Melusina_Material_023` | **no** |
| 4 | `SHAWL_001` | `MI_Melusina_SBW_MELUSINA_007` (SKIN) | **no** |
| 5 | `SHAWL_001` | `MI_Melusina_Outline_005` | ambiguous |
| 6 | `SHAWL_001` | `MI_Melusina_bow_002` | **no** |
| 7 | `SHAWL_001` | `MI_Melusina_frontpanel_001` | **no** |
| 8 | `SHAWL_001` | `MI_Melusina_SHAWL_001` | yes |
| 9 | `SHAWL_001` | `MI_Melusina_Outline_005` | ambiguous |

Indices 1-3 look like a clean **off-by-one shift** — slot N holds slot N-1's instance.
Indices 4-9 all share the imported name `SHAWL_001`, so name-matching alone cannot
resolve them; those need a visual pass.

This explains why the earlier tint probes appeared to do nothing: editing
`MI_Melusina_sleeve_003` changes the **bow**, not the sleeves.

**Owner decision needed before rewiring.** Options:
(a) fix only the unambiguous indices 1-3, or
(b) rewire all ten against a reference render.

---

## 2. Oceanology — the hero instance is an orphan

`/Game/EnvSandbox/Materials/Instances/Oceanology/MI_Oceanology_Melodia_Hero`

- parent: `/Oceanology_Plugin/Design/Ocean/Materials/Water/SingleLayerWater/M_Oceanology_Inst`
- **`total_overrides: 0`** — scalar, vector and texture override lists are all empty
- `find_references` returns `depends_on: []` and `referenced_by: []` — **nothing uses it**

The oceans therefore render at Oceanology stock defaults, and tuning this instance would
have been a **no-op**. Any ocean fix must first identify the instance the ocean actors
actually bind, or make this hero MI the bound one.

### Knobs that control "too deep and dark" (parent defaults)

| Parameter | Default | Direction for brighter / shallower |
|---|---|---|
| `DeepScatteringColor` | `(0.05, 0.25, 0.30, A=0.15)` | **raise** — this dark teal *is* the deep-water colour |
| `DeepAbsorptionCoefficient` | `7` | **lower** — light survives deeper |
| `Absorption` | `(70, 180, 350)` | scale down to extend penetration |
| `ShallowScatteringColor` | `(0.5, 0.85, 0.05)` | yellow-green; shift toward aqua |
| `SurfaceScatteringIntensity` | `2` | raise for a milky, lit shallow |
| `ScatterBoost` | `10` | raise with the above |
| `FadeOffsetScattering` / `FadeLengthScattering` | `1000` / `600000` | shorten to bring scattering closer to camera |

Supporting values already in a good place: `WaterRoughness` 0.05, `WaterSpecular` 0.225,
`BeaufortScale` 5, `MaxWaveHeight` 13.7.

**Unverified, do not assume:** whether `Absorption` is an extinction *coefficient*
(higher = darker) or an extinction *distance* (higher = clearer). The `B=350 > R=70`
ordering suggests distance, but this must be settled by moving the value and capturing,
not by reasoning about it.

---

## 3. Melusina hair via Oceanology

- `MI_Melusina_WaterHair` **already exists** at
  `/Game/EnvSandbox/Materials/Instances/Melusina/MI_Melusina_WaterHair`.
  The 2026-09-01 spec claiming it does not exist is **stale**.
- That spec's intent: parent `M_Water_Master_Grand_v7`, roughness 0.15, metallic 0.0,
  sheen 0.6, sheen roughness 0.25, ShadowDream blue `#8AA0D6`
  (linear `0.541, 0.627, 0.839`), strength 0.5.
- Blocker recorded there and still unconfirmed: **`SK_MelusinaHair` does not exist** —
  separate import scope. Confirm before authoring further hair instances.
- Also present: `MI_Character_Melusina_Hair`, `GC_MelusinaHairFlip_v22`.

---

## 4. MF_Nikki library — 14 functions exist

`MF_NikkiDreamGrade`, `DreamWatercolor`, `GlitterHalo`, `IridescenceSheen`, `PastelGrade`,
`PearlSheen`, `PetalShadow`, `RimGlow`, `SDFRibbon`, `Sparkle`, `SquishWPO`, `StickerEdge`,
`StickerShade`, `TwinkleIris` — all under `/Game/EnvSandbox/Materials/Functions/`.

Per-master wiring status is **not yet audited**. That is the next query, not a claim.

---

## 5. `L_MelodiaMainMenu` — concrete layout bugs

Widget `/Game/Melodia/UI/WBP_MainMenu`, 34 widgets, root `RootCanvas`.

1. **The entire orrery is off-screen.** `OrreryCore`, `OrbitAstral1`, `2`, `3` and `4`
   all sit at `left:-320, top:-120` against a **top-left anchor (0,0)** — up and to the
   left of the viewport. Five elements, none visible.
2. **`OrreryStarfield` is 100x30 px** (`right:100, bottom:30`) in the top-left corner at
   z-order -5. A starfield backdrop almost certainly wants full-screen anchors.
3. **`Background` and `CosmicVoid` are `ESlateVisibility::Collapsed`** — both full-screen
   backdrop images are switched off, leaving `NebulaParchment` (z -47) carrying the
   background alone.

Text blocks present: `TitleText`, `MenuKicker`, `MenuSubtitle`, `MenuSectionLabel`,
`MenuCornerNote`, `MenuWorldKicker`, `MenuWorldTitle`, `SaveStateText`, plus four button
labels. Their literal strings and fonts have not been read yet.

Level `L_MelodiaMainMenu` also contains `BP_MelodiaPuzzleRelay_FirstResonance` and
`BP_MelodiaInteraction_DreamAnchor` — gameplay fixtures in a menu level. Flagged, not
touched.

---

## Status

Nothing in this document has been edited yet. Each item needs a render to confirm intent
before changing it — three of the four lanes above contain a trap that would have
produced a confident but invisible no-op.
