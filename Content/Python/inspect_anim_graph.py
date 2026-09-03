import unreal
abp=unreal.load_object(None,'/Game/Melodia/Characters/Melusina/Hair/ABP_Melusina_WaterHair')
for n in abp.get_nodes_of_class(unreal.AnimGraphNode_CopyPoseFromMesh):
 print('node',n.get_path_name())
 print('props',[(p,getattr(n,p,None)) for p in ['node','Node','copy_pose','UseAttachedParent','use_mesh_pose']])
 print('pins',n.list_all_pins())
for gpath in abp.get_animation_graphs():
 g=unreal.load_object(None,gpath)
 print('graph',g, [x.get_class().get_name() for x in g.get_editor_property('nodes')])
