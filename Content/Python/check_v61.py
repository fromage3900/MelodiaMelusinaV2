"""Verify V6.1 state."""
import unreal
MEL = unreal.MaterialEditingLibrary
m = unreal.load_asset("/Game/EnvSandbox/Materials/PostProcess/Candidates/M_PP_StorybookOutline_Premium_Candidate")
c = [e for e in MEL.get_material_expressions(m) if type(e).__name__ == "MaterialExpressionCustom"][0]
code = c.get_editor_property("code")
print(f"LEN: {len(code)}")
print(f"NO_FRAME: {str('StateFrameIndex' not in code)}")
print(f"NO_JITTER: {str('jitterPx' not in code)}")
print(f"RADIAL: {'radOff' in code}")
print(f"STABLE: {'12.9898' in code}")
print(f"STORYBOOK: {'paperHash' in code}")
print(f"SUBSURFACE: {'PPI_SubsurfaceColor' in code}")
