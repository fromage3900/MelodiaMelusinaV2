# Builds the reusable _Template showcase level: lighting rig + global post-process
# + CineCamera. Run in the editor Python console:  import setup_template
# (requires the "Python Editor Script Plugin")
import unreal

LEVEL = '/Game/EnvSandbox/_Template/L_Template'
les = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
eas = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)

les.new_level(LEVEL)

def spawn(cls, loc=(0, 0, 0), rot=(0, 0, 0)):
    try:
        return eas.spawn_actor_from_class(cls, unreal.Vector(*loc), unreal.Rotator(*rot))
    except Exception as e:
        unreal.log_warning(f'spawn {cls} failed: {e}')
        return None

# --- lighting rig (fully dynamic / Lumen) ---
sun = spawn(unreal.DirectionalLight, (0, 0, 600), (-40, 35, 0))
spawn(unreal.SkyLight, (0, 0, 400))
spawn(unreal.SkyAtmosphere)
spawn(unreal.ExponentialHeightFog, (0, 0, 0))

# --- global post-process volume (lock exposure so renders stay consistent) ---
ppv = spawn(unreal.PostProcessVolume, (0, 0, 0))
if ppv:
    ppv.set_editor_property('unbound', True)
    s = ppv.get_editor_property('settings')
    s.set_editor_property('b_override_auto_exposure_method', True)
    s.set_editor_property('auto_exposure_method', unreal.AutoExposureMethod.AEM_MANUAL)
    s.set_editor_property('b_override_auto_exposure_bias', True)
    s.set_editor_property('auto_exposure_bias', 10.0)   # manual EV; tweak to taste
    ppv.set_editor_property('settings', s)
    # >> Add TP_Default toon profile + M_PP_ToonOutline post-process material to this PPV by hand.
    #     Materials live under /Game/EnvSandbox/Materials/ (see Docs/MATERIAL_MIGRATION.md).

# --- portfolio camera ---
spawn(unreal.CineCameraActor, (-700, 0, 250), (0, -12, 0))

les.save_current_level()
unreal.log(f'[Template] {LEVEL} built: sun + sky + skylight + fog + unbound PPV (manual exposure) + CineCamera')
print(f'Template level built at {LEVEL}. Duplicate it per environment style.')
