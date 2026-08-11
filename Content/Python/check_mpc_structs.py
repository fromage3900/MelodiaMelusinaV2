import unreal

# Check CollectionScalarParameter properties
csp_struct = unreal.CollectionScalarParameter.static_struct()
print("CollectionScalarParameter fields:")
for i in range(csp_struct.num_properties):
    prop = csp_struct.get_property(i)
    if prop:
        print(f"  {prop.get_name()}")

# Check CollectionVectorParameter properties
cvp_struct = unreal.CollectionVectorParameter.static_struct()
print("\nCollectionVectorParameter fields:")
for i in range(cvp_struct.num_properties):
    prop = cvp_struct.get_property(i)
    if prop:
        print(f"  {prop.get_name()}")