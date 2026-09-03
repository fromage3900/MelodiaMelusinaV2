"""Probe UE's live Python RVT class names/properties without modifying assets."""
import unreal

print("RVT classes:", [x for x in dir(unreal) if "VirtualTexture" in x])
print("RVT material enum:", [x for x in dir(unreal.RuntimeVirtualTextureMaterialType) if not x.startswith("_")])
print("RVT quality enum:", [x for x in dir(unreal.RuntimeVirtualTextureMaterialQuality) if not x.startswith("_")])
print("RVT volume enum:", [x for x in dir(unreal.RuntimeVirtualTextureMainPassType) if not x.startswith("_")])
for name in ("RuntimeVirtualTexture", "RuntimeVirtualTextureFactory", "RuntimeVirtualTextureVolume", "RuntimeVirtualTextureComponent", "RuntimeVirtualTextureMaterialType"):
    cls = getattr(unreal, name, None)
    print(name, cls)
    if cls:
        try:
            print("  properties:", cls.static_class().get_name())
        except Exception as exc:
            print("  class probe failed:", exc)
