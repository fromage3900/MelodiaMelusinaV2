import unreal

# Path to the Melusina Blueprint
bp_path = '/Game/Melodia/Characters/Melusina/BP_Melusina'

bp = unreal.EditorAssetLibrary.load_asset(bp_path)
if not bp:
    raise RuntimeError(f"Failed to load Blueprint at {bp_path}")

cls = bp.GeneratedClass
cdo = unreal.get_default_object(cls)

# Enable gliding
cdo.set_editor_property('bIsGliding', True)
# Set gliding parameters
cdo.set_editor_property('GlideGravityScale', 0.1)
cdo.set_editor_property('GlideTerminalZ', -180.0)
cdo.set_editor_property('GlideAirControl', 0.9)
# Hard‑coded camera extension (as requested)
cdo.set_editor_property('GlideBoomExtension', 80.0)

# Bind landing montage
landing = unreal.EditorAssetLibrary.load_asset('/Game/Animations/AM_Mocap_JumpEnd.AM_Mocap_JumpEnd')
if landing:
    cdo.set_editor_property('landing_montage', landing)
else:
    unreal.log_warning('Landing montage not found')

unreal.log('Gliding properties updated on BP_Melusina')
