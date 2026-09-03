import unreal

s = unreal.CollectionScalarParameter.static_struct()
props = []
for i in range(s.num_props()):
    p = s.get_property(i)
    props.append(p.get_name())
print("CollectionScalarParameter props:", props)

vs = unreal.CollectionVectorParameter.static_struct()
props_v = []
for i in range(vs.num_props()):
    p = vs.get_property(i)
    props_v.append(p.get_name())
print("CollectionVectorParameter props:", props_v)