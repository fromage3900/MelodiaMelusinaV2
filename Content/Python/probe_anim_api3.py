import unreal
for c in [unreal.AnimBlueprint,unreal.AnimGraphNode_CopyPoseFromMesh,unreal.AnimNode_CopyPoseFromMesh,unreal.EdGraph]:
 print('\nCLASS',c)
 print([x for x in dir(c) if any(k in x.lower() for k in ['graph','node','pin','compile','modify','pose','copy'])][:120])
