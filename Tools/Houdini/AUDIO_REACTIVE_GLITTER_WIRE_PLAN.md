================================================================================
AUDIO-REACTIVE GLITTER WIREING PLAN — EDITOR EXECUTION
================================================================================

STATUS: Shaders and Python build script UPDATED. Editor material connections
        PENDING execution in Unreal Editor.

--------------------------------------------------------------------------------
1. SHADER MODIFICATIONS (ALREADY DONE)
--------------------------------------------------------------------------------

1a) Source: Source/MelodiaShader/Shaders/MelodiaNikkiCommon.ush
    - Line 66: Added `float audioTwinkle` parameter
    - Lines 74-80: Audio-driven twinkle logic:
      * When audioTwinkle > 0: uses beat/treble-enhanced twinkle
      * When audioTwinkle == 0: falls back to original time-driven twinkle

1b) Source: Content/Python/expand_nikki_features.py
    - Line 214: Added `("AudioTwinkle", f1)` to the glitter _build_mf() inputs list
    - This passes the audioTwinkle scalar from the material function blueprint
      down to the HLSL shader

--------------------------------------------------------------------------------
2. EDITOR MATERIAL CONNECTIONS (PENDING — NEEDS UNREAL EDITOR)
--------------------------------------------------------------------------------

TARGET: 5 Character Material Instances + Melusina environment MIs

2a) Load each MI in the Unreal Editor and locate:

CollectionParameter nodes reading from MPC_Melodia_Palette:
- BeatPulse
- TrebleIntensity  
- BassIntensity
- GlobalReactivity

These are currently ORPHANED (exist but not connected to anything).

2b) For each MI, connect the MPC params to the glitter function inputs:

GLITTER FUNCTION INPUTS (from MF_NikkiGlitterHalo):
- Intensity       ← CONNECT BeatPulse (floats)
- Amount          ← CONNECT TrebleIntensity (floats)  
- Scale           ← CONNECT BassIntensity (floats)
- (Optional)      ← CONNECT GlobalReactivity (float, 0.0 = baseline, >0 = reactive)

CONNECTION METHOD in Editor:
- Select the Material Expression CollectionParameter node for each param
- In the Details panel, set "Collection" to MPC_Melodia_Palette (if not already)
- Add a Material Expression MaterialFunctionCall for MF_NikkiGlitterHalo
- Connect the CollectionParameter output to the function's corresponding input:
  * BeatPulse → Intensity input pin
  * TrebleIntensity → Amount input pin
  * BassIntensity → Scale input pin
  * GlobalReactivity → (optional) enable gate or multiply factor

2c) Verify the glitter function call node is present and has the right inputs:
- Look for MaterialExpressionMaterialFunctionCall named "GlitCall" or similar
- Its material_function should be MF_NikkiGlitterHalo
- Inputs should show: BaseColor, Normal, WorldPosition, Mask, Scale, Amount, 
  Intensity, GlitterColor, HaloStrength, HaloPower, TwinkleSpeed, Time, AudioTwinkle

2c) Optional: Add explicit AudioTwinkle connection:
- If the MI already has a scalar parameter named "AudioTwinkle" or similar,
  connect it to the glitter function's AudioTwinkle input
- When AudioTwinkle > 0: audio-driven twinkle activates
- When AudioTwinkle == 0: falls back to time-driven twinkle

--------------------------------------------------------------------------------
3. REBUILD MASTER MATERIALS
--------------------------------------------------------------------------------

After the connections are made, rebuild the master materials so the changes
propagate:

3a) Open M_Melusina (or whichever is the authoritative master - check the 3
      locations: Masters/, Melodia/_PROJECT/04_Materials/, _PROJECT/04_Materials/)

3b) Use "Rebuild Shaders" or "Force Recompile" on the master material

3c) The updated MF_NikkiGlitterHalo will now have the AudioTwinkle input
      available for wiring

--------------------------------------------------------------------------------
4. VERIFICATION in PIE
--------------------------------------------------------------------------------

4a) Launch PIE (Play In Editor)

4b) Play audio track or generate beat events

4c) Verify:
- Beat downbeat → Intensity spike → glitter "flash" visible
- Treble increase → Amount increase → more glitter "pop"
- Bass increase → Scale shift → world hash pattern changes
- Silence → AudioTwinkle ≈ 0 → falls back to baseline twinkle

4d) Check the Melusina character surface for visible audio-reactive glitter
    on clothing, hair, or other surface areas using the wired MIs

--------------------------------------------------------------------------------
5. ROLLBACK PLAN (if needed)
--------------------------------------------------------------------------------

5a) To revert shader changes:
- Restore MelodiaNikkiCommon.ush to original (remove audioTwinkle param)
- Restore expand_nikki_features.py glitter _build_mf() to 12 inputs (remove AudioTwinkle)

5b) To revert material connections:
- Delete the CollectionParameter→glitter function connections in each MI
- Rebuild shaders on the master

================================================================================