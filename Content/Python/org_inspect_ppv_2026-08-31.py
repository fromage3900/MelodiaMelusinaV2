import unreal

# Inspect PPV_NikkiDream PostProcessVolume blendable stack in L_KaleidoNave
actors = unreal.EditorActorSubsystem().get_all_level_actors()
ppv = [a for a in actors if a.get_actor_label() == 'PPV_NikkiDream']
unreal.log_warning('PPV_COUNT=%d' % len(ppv))
if not ppv:
    raise SystemExit

actor = ppv[0]
comp = actor.get_component_by_class(unreal.PostProcessVolumeComponent)
unreal.log_warning('PPV_COMP=%s' % (comp.get_name() if comp else 'NONE'))
if not comp:
    raise SystemExit

unreal.log_warning('PPV_PRIORITY=%s' % comp.priority)
unreal.log_warning('PPV_UNBOUND=%s' % comp.unbound)
s = comp.settings
unreal.log_warning('PPV_HAS_SETTINGS=%s' % (s is not None))
if s:
    wb = s.weighted_blendables
    unreal.log_warning('PPV_WEIGHTED_COUNT=%d' % len(wb.array))
    for i, item in enumerate(wb.array):
        try:
            mi_path = item.object.get_path_name() if item.object else 'NONE'
            unreal.log_warning('PPV_BLENDABLE[%d] %s weight=%s' % (i, mi_path, item.weight))
        except Exception as e:
            unreal.log_warning('PPV_BLENDABLE[%d] ERR %s' % (i, e))