# ARCH_CATH_T3D_BATCH_SPEC_2026-08-31.md

## MI_Arch_Cath_T3D_Batch — Task Spec

### Source
- `Saved/Audit/arch_toon_conversion.json` (generated 2026-08-30)
- `Saved/Audit/_arch_toon_missing_mi.json` (cathedral_truly_missing: 41)

### Scope
First 10 Cathedral meshes → T3D MI spec for editor Monolith pass

| # | Mesh Stem | MI Path | Slot | Rough | Metallic | Tint | ShadowDream | SD Strength |
|---|-----------|---------|------|-------|----------|------|-------------|-------------|
| 1 | SM_Cathedral_Altar | MI_Arch_Cath_SM_Cathedral_Altar | Marble_Altar | 0.25 | 0.0 | blue | yes | 0.55 |
| 2 | SM_Cathedral_BeatMedallion | MI_Arch_Cath_SM_Cathedral_BeatMedallion | Gold_Medallion | 0.35 | 0.85 | — | no | — |
| 3 | SM_Cathedral_Bed | MI_Arch_Cath_SM_Cathedral_Bed | Wood_Bed | 0.7 | 0.0 | — | no | — |
| 4 | SM_Cathedral_BifrostBridge | MI_Arch_Cath_SM_Cathedral_BifrostBridge | Rainbow_Bridge | 0.7 | 0.0 | — | no | — |
| 5 | SM_Cathedral_Buttress | MI_Arch_Cath_SM_Cathedral_Buttress | Stone_Buttress | 0.85 | 0.0 | — | no | — |
| 6 | SM_Cathedral_Chandelier | MI_Arch_Cath_SM_Cathedral_Chandelier | Glass_Chandelier | 0.08 | 0.0 | blue | yes | 0.55 |
| 7 | SM_Cathedral_Chapel | MI_Arch_Cath_SM_Cathedral_Chapel | Stone_Chapel | 0.85 | 0.0 | — | no | — |
| 8 | SM_Cathedral_ChapterHouse | MI_Arch_Cath_SM_Cathedral_ChapterHouse | Stone_ChapterHouse | 0.85 | 0.0 | — | no | — |
| 9 | SM_Cathedral_CombatFloor | MI_Arch_Cath_SM_Cathedral_CombatFloor | Stone_Floor | 0.85 | 0.0 | — | no | — |
| 10 | SM_Cathedral_Crypt | MI_Arch_Cath_SM_Cathedral_Crypt | Stone_Heavy | 0.85 | 0.0 | — | no | — |

### ShadowDream Tinting
- **Blue #8AA0D6**: Marble, Glass, Rose → applied to slots 1, 6
- **Pink #E8A0BF**: Rose → none in this batch (next batch: SM_Cathedral_Garland)
- **None**: Wood, Stone, Gold, Rainbow

### Parent Material
`Content/EnvSandbox/Materials/Masters/M_Master_Toon_Universal`

### Naming Convention
`MI_Arch_Cath_<MeshStem>` (PascalCase, no underscores within stem)

### T3D Format Spec
Each entry writes as T3D in format:
```
Begin Object Name="MI_Arch_Cath_SM_Cathedral_Altar" Class=/Script/Engine.MaterialInstanceConstant
   Parent=MaterialInstanceConstant'/Game/EnvSandbox/Materials/Masters/M_Master_Toon_Universal_MI'
   ScalarParameterValues(...)
   VectorParameterValues(...)
   TextureParameterValues(...)
End Object
```

### Batch 2 Remaining
31 Cathedral meshes remaining after this batch (next batch: SM_Cathedral_CryptVault through SM_Cathedral_WallParapet)

### Lane
`audit` (qwen3:8b or nemotron-free)

### Priority
2

### Notes
- 41 total Cathedral meshes need MIs
- 333 Atlantis meshes need MIs (separate task)
- Editor Monolith pass applies T3D injection
- No .uasset writes — spec-only
