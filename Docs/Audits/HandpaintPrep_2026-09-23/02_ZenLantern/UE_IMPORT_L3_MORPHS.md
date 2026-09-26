# UE Import — ZenLantern_V2_L3_morphs.fbx

1. Content Browser → Import
   `Saved/KimiWork/HandpaintPrep_2026-09-23/02_ZenLantern/substance/meshes/ZenLantern_V2_L3_morphs.fbx`
2. FBX Import Options:
   - Import Morph Targets: **ON**
   - Import Animations: OFF
   - Convert Scene / Force Front XAngle: match prior ZenLantern_V2 import
   - Material: Do Not Create (assign MI later)
3. After import, open mesh → Morph Target list must show:
   SK_FlameBreath, SK_RoofLift, SK_CharmSway_L, SK_CharmSway_R, SK_DawnDusk
4. Place in lookdev level; drive morphs from MPC / Blueprint (read-only palette)
5. **Ctrl+S** to save package — never Monolith save_packages / recompile_material
