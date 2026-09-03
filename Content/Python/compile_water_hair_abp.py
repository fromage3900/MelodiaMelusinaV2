import unreal
p='/Game/Melodia/Characters/Melusina/Hair/ABP_Melusina_WaterHair'
abp=unreal.load_object(None,p)
print('compile',unreal.BlueprintEditorLibrary.compile_blueprint(abp))
unreal.EditorAssetLibrary.save_asset(p,only_if_is_dirty=False)
print('saved')
