import unreal
abp=unreal.load_object(None,'/Game/Melodia/Characters/Melusina/Hair/ABP_Melusina_WaterHair')
print('graphs',abp.get_animation_graphs())
print('nodes',abp.get_nodes_of_class(unreal.AnimGraphNode_CopyPoseFromMesh))
print('modify',abp.modify())
