import unreal
for p in ['/Game/Melodia/Characters/Melusina/BP_Melusina','/Game/Melodia/Characters/Melusina/Hair/SK_Melusina_Hair_Skeleton']:
 for fn in [lambda:unreal.load_object(None,p),lambda:unreal.load_asset(p)]:
  try: print(p,fn())
  except Exception as e: print(type(e),e)
