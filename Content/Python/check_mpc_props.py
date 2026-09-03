import unreal

# Check properties on instance
csp = unreal.CollectionScalarParameter()
print("CollectionScalarParameter properties:")
for attr in dir(csp):
    if not attr.startswith('_'):
        try:
            val = getattr(csp, attr)
            if not callable(val):
                print(f"  {attr} = {val}")
        except:
            pass

cvp = unreal.CollectionVectorParameter()
print("\nCollectionVectorParameter properties:")
for attr in dir(cvp):
    if not attr.startswith('_'):
        try:
            val = getattr(cvp, attr)
            if not callable(val):
                print(f"  {attr} = {val}")
        except:
            pass