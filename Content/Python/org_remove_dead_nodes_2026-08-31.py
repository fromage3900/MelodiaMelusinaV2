import unreal

# Remove all orphaned SetNiagaraVariableFloat nodes from BP_MelusinaJRPGCharacter EventGraph
# (verified orphaned: chain 43-57 has no exec feed; node 43 execute input connected_to=[])
TARGET = '/Game/MelodiaIntegration/Blueprints/BP_MelusinaJRPGCharacter'

bp = unreal.load_asset(TARGET)
removed = 0
failed = []

for graph in bp.graphs:
    if graph.get_name() != 'EventGraph':
        continue
    for n in list(graph.nodes):
        cname = n.get_class().get_name()
        fname = n.get_function_name() if hasattr(n, 'get_function_name') else ''
        if cname == 'K2Node_CallFunction' and fname == 'SetNiagaraVariableFloat':
            try:
                graph.remove_node(n, False)
                removed += 1
            except Exception as ex:
                failed.append('%s :: %s' % (n.get_name(), ex))

unreal.log_warning('DEADNODE_REMOVE target=%s removed=%d failed=%d' % (TARGET, removed, len(failed)))
for f in failed[:5]:
    unreal.log_warning('DEADNODE_FAIL %s' % f)

# Recompile to confirm clean
try:
    unreal.KismetSystemLibrary.flush_rendering_commands() if False else None
except Exception:
    pass
unreal.log_warning('DEADNODE_REMOVE done')