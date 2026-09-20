
import unreal, json
svc = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
actors = list(svc.get_all_level_actors())
restored = []
kept_hidden = []
for a in actors:
    try:
        label = a.get_actor_label() or ''
    except Exception:
        continue
    # restore walk + morning FX; keep Houdini overlays hidden per contract
    if label.startswith('WC_EscherWalk_') or label in ('FX_Morning_Mist', 'FX_Morning_Bed_PollenSparkle'):
        try:
            a.set_is_temporarily_hidden_in_editor(False)
            a.set_actor_hidden_in_game(False)
            restored.append(label)
        except Exception as e:
            restored.append(label + ':' + str(e))
    if label in ('HoudiniEngine_RainbowBloom_3900', 'Houdini_RainbowBloom_3900'):
        try:
            a.set_is_temporarily_hidden_in_editor(True)
            a.set_actor_hidden_in_game(True)
            kept_hidden.append(label)
        except Exception:
            pass
# save
try:
    unreal.get_editor_subsystem(unreal.LevelEditorSubsystem).save_current_level()
    saved = True
except Exception as e:
    saved = str(e)
print('RESTORE', json.dumps({'restored_count': len(restored), 'kept_hidden': kept_hidden, 'saved': saved, 'sample': restored[:8]}))
