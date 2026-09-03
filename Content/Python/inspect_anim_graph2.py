import unreal
abp=unreal.load_object(None,'/Game/Melodia/Characters/Melusina/Hair/ABP_Melusina_WaterHair')
print('nodes',len(abp.get_nodes_of_class(unreal.AnimGraphNode_CopyPoseFromMesh)))
for n in abp.get_nodes_of_class(unreal.AnimGraphNode_CopyPoseFromMesh):
 print('node props', n.get_editor_property('Node'))
 for p in n.list_all_pins():
  print('pin',p, type(p), [x for x in dir(p) if x in ['name','direction','linked_to','default_value','pin_type']])
print('compile lib',hasattr(unreal,'BlueprintEditorLibrary'))
