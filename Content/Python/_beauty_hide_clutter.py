"""Hide non-portfolio clutter that was bloating the meadow (gates, palace kit, houdini bloom)."""
import unreal

def _label(a):
    try: return a.get_actor_label() or ''
    except: return ''

HIDE_SUB = (
    'BldgLgPalace', 'gate', 'Houdini_RainbowBloom', 'Houdini_',
    'KB3D_ATL', 'greybox', 'Greybox', 'SM_Cube', 'BasicShape',
)

svc = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
hidden = []
for a in svc.get_all_level_actors():
    lab = _label(a)
    if any(s in lab for s in HIDE_SUB):
        try:
            a.set_is_temporarily_hidden_in_editor(True)
            a.set_actor_hidden_in_game(True)
            hidden.append(lab)
        except Exception:
            pass
unreal.get_editor_subsystem(unreal.LevelEditorSubsystem).save_current_level()
print('BEAUTY_HIDE', len(hidden), hidden[:30])
