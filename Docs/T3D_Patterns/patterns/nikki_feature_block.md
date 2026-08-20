# Nikki Feature Block — T3D / Builder Pattern

The Nikki feature expansion is NOT hand-injected T3D — it is rebuilt by
`Content/Python/expand_nikki_features.py` (idempotent, tagged `NikkiFeat:`),
the same pattern as `expand_nikki_masters.py` (`NikkiX:`). This file documents
the block so it can be recreated by hand OR via T3D if a future agent needs a
snippet.

## The block (7 gates, all default OFF)

Chain (all read the PASTEL switch output, never the ShadowDream switch — cycle risk):

```
PastelOut ──► [bNikkiSDFRibbon_Active] MF_NikkiSDFRibbon
           ──► [bNikkiPearlSheen_Active] MF_NikkiPearlSheen
           ──► [bNikkiDreamWatercolor_Active] MF_NikkiDreamWatercolor
           ──► [bNikkiStickerEdge_Active] MF_NikkiStickerEdge
           ──► [bNikkiGlitterHalo_Active] MF_NikkiGlitterHalo
           ──► [bNikkiPetalShadow_Active] MF_NikkiPetalShadow
           ──► ShadowDream lerp (A input)
WPO: [bNikkiSquishWPO_Active] MF_NikkiSquishWPO ──► StaticSwitch ──► MP_WORLD_POSITION_OFFSET
```

## Per-gate parameter sets

| Gate | Scalars | Vectors |
|---|---|---|
| bNikkiSDFRibbon_Active | NikkiSDFRibbon_Scale/Sharpness/Strength/EdgeFalloff/EdgeStrength | NikkiSDFRibbon_Color |
| bNikkiPearlSheen_Active | NikkiPearl_Frequency/SecondFrequency/Strength | NikkiPearl_Tint |
| bNikkiDreamWatercolor_Active | NikkiWatercolor_Bleed/Jitter/Strength | NikkiWatercolor_BleedColor |
| bNikkiStickerEdge_Active | NikkiStickerEdge_Width/Bands/Softness/Strength | NikkiStickerEdge_Color |
| bNikkiGlitterHalo_Active | NikkiGlitterHalo_Scale/Amount/Intensity/HaloStrength/HaloPower/TwinkleSpeed | NikkiGlitterHalo_Color |
| bNikkiPetalShadow_Active | NikkiPetal_Scale/Radius/Softness/Strength/BloomSpeed | NikkiPetal_Tint |
| bNikkiSquishWPO_Active | NikkiSquish_Amount/Speed | NikkiSquish_Direction |

## T3D shape (per gate, schematic)

```
Begin Object Class=/Script/Engine.MaterialExpressionStaticSwitchParameter
  ParameterName={{GATE}}
  DefaultValue=False
  Desc=NikkiFeat:{{GATE}}
End Object
Begin Object Class=/Script/Engine.MaterialExpressionMaterialFunctionCall
  MaterialFunction=MF_Nikki{{FUNC}}
  Desc=NikkiFeat:{{FUNC}}Call
End Object
```

## Rebuild commands (canonical — prefer these over hand-editing)

```python
import expand_nikki_features as e; e.main(rebuild_functions=False)  # surgery only
import expand_nikki_features as e; e.main(rebuild_functions=True)   # rebuild MFs too
```

## Traps

1. Read the pre-stage color from `bNikkiPastelGrade_Active`, NEVER
   `bShadowDream_Active` (graph cycle → "Expression is part of a cycle").
2. WPO: MF output → StaticSwitchParameter → MP_WORLD_POSITION_OFFSET. Connecting
   the MF call directly to the material property crashes the editor.
3. Cleanup only removes nodes tagged `NikkiFeat:` — the original chain is `NikkiX:`.
