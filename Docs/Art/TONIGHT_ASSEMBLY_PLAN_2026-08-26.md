# Tonight Assembly Plan — Choral Sheep × The Sea Above — 2026-08-26

**Lens:** Infinity Nikkilike production values — serene readable vistas, fashion/material fantasy, cozy traversal, "dressing changes what the world lets you do." Both deliverables tonight are dress-up-compatible: sheep coats are wearable palette kits; the Sea Above membrane opens paths based on outfit motif (per concept backlog §Sea Above gameplay notes).

**Status:** execution-ready · **Branch:** `main` @ merge `297a130f` lineage
**Variant system:** **12 chromatic ChoralSheep variants — variant N = pitch class N (C=0 … B=11)**

---

## Part 1 — Choral Sheep assembly (motif creature lane)

### 1.0 Material pipeline intake (what exists)

| Asset | Role | State |
| --- | --- | --- |
| `Tools/BlenderAddons/melodia_studio/sheep_shine.py` | shader/color variation panel (**10 presets**) | extend → 12 |
| `Tools/BlenderAddons/melodia_studio/sheep_shapekeys.py` | expression shape keys (`c_jaw`, `c_eye`, ear chains) | ready |
| `Tools/BlenderAddons/melodia_studio/export_choral_sheep.py` | deform-only FBX (`use_armature_deform_only=True`, 106 bones) | verified |
| `Skin_Sheep_ZSpheres2` | source mesh, 5,918 verts | ⚠️ **0 vertex groups** |

**Nikki-lens rule for coats:** each of the 12 variants reads as an *outfit fabric kit* on one silhouette — same dye regions (wool body / face / hooves / bell collar), swapped palette + trim. No new geometry per note. A player should be able to say "that's the B-flat sheep" at render distance.

### 1.1 Registration contract (new, small)

Create `Content/MelodiaIntegration/ResonantWorld/MotifCreatures/ChoralSheep/ChoralSheepVariants.json`, schema:

```json
{ "schema": "melodia.motif_creature.v1",
  "creature": "ChoralSheep",
  "variant_axis": { "type": "pitch_class", "count": 12,
                    "labels": ["C","C#","D","D#","E","F","F#","G","G#","A","A#","B"] },
  "material_slot_map": {
    "MI_ChoralSheep_Coat_PC{n}": "/Game/_PROJECT/ResonantWorld/MotifCreatures/ChoralSheep/Materials/",
    "scalar_overrides": ["CoatHueShift","CoatSaturation","TrimEmissive","BellToneScale"]
  },
  "behavior_binding": { "motif_cell_source": "pitch_class",
                        "graze_pulse_bpm": "tempo_of_region",
                        "call_response_route": true },
  "reimport_policy": "master_edit_only_no_instance_deletion"
}
```

Pipeline per variant i ∈ [0..11]:
1. In `sheep_shine.py`, drive preset by `hue = i * 30°` with pastel lift/dream-saturation scalars already in house style (`PastelLift≈0.24`, `DreamSaturation≈0.22` — same grammar as Gaea substrate MIs).
2. Export `SM_ChoralSheep` **once**, instantiate **12 MIs** (`MI_ChoralSheep_Coat_PC00…PC11`) off one master. Never edit the master after batch creation (`reimport_policy` above).
3. Motif cell: behavior timer quantized to region tempo; PC(i) sheep bleats/pulses on scale-degree i of the local mode — this is the Resonant World "Motif creature" clause (`RESONANT_WORLD_SYSTEM.md` §48) made concrete.


### 1.2 Assembly steps (tonight)

1. **Blocker first:** weight-paint `Skin_Sheep_ZSpheres2` → 106 deform groups (mirror L→R, quadruped: spine/neck/4 legs/tail/ears). Verify zero zero-weight lock errors in Blender.
2. Re-run `export_choral_sheep.py` headless; confirm `106/474`, ~455 KB FBX.
3. UE import → `/Game/_PROJECT/ResonantWorld/MotifCreatures/ChoralSheep/SK_ChoralSheep` (**new skeleton**; never reuse `IK_Melusina_Body_Current`).
4. Batch-create 12 coat MIs per §1.1 + wire `DA_ChoralSheepDefinition.SkeletalMesh` variants via data-table row per pitch class.
5. Author `IK_ChoralSheep` chains (root/spine/neck/head + 4× thigh-foot-toes + tail4), retargeter `RT_QuadrupedMocap_To_ChoralSheep` vs horse/deer source.
6. `ABP_ChoralSheep` blendspace over `GroundSpeed` (walk/trot/run); add **Baa-note notify** keyed by variant PC → feeds world resonance ledger.

---

## Part 2 — The Sea Above level via Gaea2UE (tonight)

### 2.0 Why the Gaea lane fits

Liquid Cathedral's validated recipe (`GAEA_SETUP_LIQUID_CATHEDRAL_2026-08-24.json`) already contains: ASTER metric terrain (Yoshino 12 km window), `Canyon → HydroFix → FlowMap → SeaLevel → SatMap → WaveShine` chain, **waterline mask at 36 m**, and a literal `"Canyon River with Sea"` Gaea reference graph. That sea/waterline mask *is* our false-ocean plane geometry donor.

### 2.1 Terrain tonight (headless-capable path)

```powershell
Tools\WorldGen\prepare_gaea_unreal_export_native.ps1 `
  -Source  "C:/Program Files/QuadSpinner/Gaea 2/Examples/Canyon River with Sea.terrain" `
  -Destination "Saved/Audit/gaea_setups/sea_above/" `
  -Report  "Saved/Audit/gaea_setups/sea_above/handoff_manifest.json"
```

The script injects a `QuadSpinner.Gaea.Nodes.Unreal` node (`WillExport`, Height + 3 masks, PNG, `x2017`) directly into the `.terrain` via Gaea 2.2.3.2 assemblies — no GUI required. Rename node id to `Unreal_SeaAbove`. Output: heightfield + flow/slope/waterline masks → import as **Mesh Terrain** (not classic Landscape) into `/Game/_PROJECT/ResonantWorld/Offline/GaeaSetups/SeaAbove/`.

Material: follow the `apply_gaea_substrate_materials.py` pattern to mint `MI_Gaea_SeaAbove_Substrate` off `M_Master_Toon_Landscape_HeightBlend` — triplanar active, `ShoreWetnessBoost≈0.46`, plus the Nikki polish trio (`PastelLift`, `DreamSaturation`, `DreamContrast`). Master untouched.

### 2.2 The Sea Above stack (Water V10 — duplicates only)

Per `SEA_ABOVE_TONIGHT_EXECUTION_AND_AGENT_HANDOFF_2026-08-26.md` constraints:

- Level `/Game/_PROJECT/ResonantWorld/Offline/GaeaSetups/SeaAbove/LV_SeaAbove_Prototype`
- Surface ocean: duplicate of `MI_WaterV10_Integrated_RiverClear` → `MI_SeaAbove_SurfaceOcean`, placed at real sea level over the Gaea basin
- False ocean: duplicate of `MI_WaterV10_Integrated_OceanPreview` → `MI_SeaAbove_FalseOcean`, inverted plane **36 m below the waterline mask line** (borrow the JSON's `waterline_m`)
- Giant Bell proxy (engine grid sphere scaled ×80) at horizon, 12–20 s pulse driven by the *same* motif-clock as the sheep calls — one clock, whole valley sings
- Upward Niagara rain (existing petal-gust renderer proof reused, velocity flipped)
- Forbidden tonight: edits to any V9/V10 integrated instance, Substrate study-line promotion, SceneDepth on single-layer-water surface, C++, Data Channels

### 2.3 DoD checklist (adopted from handoff plan §2)

Isolated map ✓ clean PIE hero camera 16:9 ✓ normality → second-horizon → bell-pulse read in 20–30 s cinematic approach ✓ screenshot + short capture saved to `Saved/Audit/gaea_setups/sea_above/` ✓ zero production water edits ✓

---

## Sequence tonight

| # | Task | Owner lane | Gate |
|---|---|---|---|
| 1 | Sheep weight paint + FBX verify | Blender headless | 106 groups non-zero |
| 2 | SK/IK/retarget/ABP wiring | UE editor | PIE follow-camera ok |
| 3 | 12 coat MIs + `ChoralSheepVariants.json` | Python batch | 12 MIs, no master edit |
| 4 | Gaea native export + Mesh Terrain import | PowerShell script | manifest gates green |
| 5 | Substrate MI + water duplicates + Bell/Niagara | UE editor + python | handoff §2 checklist |
| 6 | Capture + commit docs/captures | all | push `main` |
