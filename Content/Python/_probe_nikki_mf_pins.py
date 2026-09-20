import unreal, json
EAL=unreal.EditorAssetLibrary; MEL=unreal.MaterialEditingLibrary
paths=[
 '/Game/EnvSandbox/Materials/Functions/MF_NikkiRimGlow',
 '/Game/EnvSandbox/Materials/Functions/MF_NikkiSparkle',
 '/Game/EnvSandbox/Materials/Functions/MF_NikkiPearlSheen',
 '/Game/EnvSandbox/Materials/Functions/MF_NikkiDreamGrade',
]
out={}
for p in paths:
  mf=EAL.load_asset(p)
  if not mf:
    out[p]={'missing':True}; continue
  # create temp call to read inputs? Or inspect function inputs via expressions
  inputs=[]
  try:
    for e in MEL.get_material_expressions(mf) or []:
      if 'FunctionInput' in e.get_class().get_name():
        try: inputs.append(str(e.get_editor_property('input_name')))
        except:
          try: inputs.append(str(e.get_editor_property('InputName')))
          except: inputs.append('?')
  except Exception as ex:
    inputs=['ERR:'+str(ex)]
  outputs=[]
  try:
    for e in MEL.get_material_expressions(mf) or []:
      if 'FunctionOutput' in e.get_class().get_name():
        try: outputs.append(str(e.get_editor_property('output_name')))
        except: outputs.append('?')
  except Exception as ex:
    outputs=['ERR:'+str(ex)]
  out[p.split('/')[-1]]={'inputs':inputs,'outputs':outputs}
print('MFPINS', json.dumps(out))
