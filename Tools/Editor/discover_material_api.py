"""
One-shot API discovery for UE 5.8 material-instance editing, plus cleanup of the
mis-named instances created by the first Enchanted Interiors attempt.

Prints:
  * the MaterialEditingLibrary functions that set parameters
  * the MaterialInstanceBasePropertyOverrides struct surface
  * the MaterialParameterInfo construction that works
  * the BlendMode enum member names

Then deletes any /Game/EnchantedInteriors/Materials/KB3D_ECI_KB3D_ECI_* assets
(double-prefixed, created by the buggy first run) and reports what remains.

Run: UnrealEditor-Cmd <proj> -run=pythonscript -script=<this file> -unattended -nullrhi
"""

from __future__ import annotations

import unreal

OUT = []
OUTFILE = r"C:\Users\froma\AppData\Local\Temp\opencode\api_discovery.txt"


def say(*args):
    msg = " ".join(str(a) for a in args)
    OUT.append(msg)
    unreal.log("[DISC] " + msg)
    # flush immediately: a later exception must not lose what we already learned
    try:
        with open(OUTFILE, "w", encoding="utf-8") as fh:
            fh.write("\n".join(OUT))
    except Exception:
        pass


def main():
    mel = unreal.MaterialEditingLibrary
    fns = sorted(p for p in dir(mel) if not p.startswith("_"))
    say("MaterialEditingLibrary set/get functions:")
    for f in fns:
        if any(k in f for k in ("set_material_instance", "get_all_material_instance",
                                "get_material_instance", "set_material_instance_parent")):
            say("   ", f)

    say("")
    say("MaterialInstanceBasePropertyOverrides type:",
        hasattr(unreal, "MaterialInstanceBasePropertyOverrides"))
    if hasattr(unreal, "MaterialInstanceBasePropertyOverrides"):
        props = [p for p in dir(unreal.MaterialInstanceBasePropertyOverrides)
                 if not p.startswith("_")]
        say("   members:", ", ".join(props))

    say("")
    say("BlendMode members:",
        ", ".join(p for p in dir(unreal.BlendMode) if not p.startswith("_")))

    say("")
    say("MaterialParameterInfo members:",
        ", ".join(p for p in dir(unreal.MaterialParameterInfo) if not p.startswith("_")))
    try:
        say("MaterialParameterAssociation members:",
            ", ".join(p for p in dir(unreal.MaterialParameterAssociation) if not p.startswith("_")))
    except Exception as exc:
        say("no MaterialParameterAssociation:", exc)

    # live probe on one real instance
    master = unreal.EditorAssetLibrary.load_asset(
        "/Game/EnvSandbox/Materials/Masters/M_Master_Toon_Universal")
    say("")
    say("master loaded:", master is not None)

    probe = unreal.EditorAssetLibrary.load_asset(
        "/Game/KitBash_EnchantedVehicles/M_KB3D_ECV_BrickStoneGray")
    say("probe instance loaded:", probe is not None)
    if probe is not None:
        try:
            bpo = probe.get_editor_property("base_property_overrides")
            say("   bpo type:", type(bpo))
            say("   bpo dir:", ", ".join(p for p in dir(bpo) if not p.startswith("_")))
            for cand in ("blend_mode", "two_sided", "b_use_opacity_map", "use_opacity_map"):
                try:
                    v = bpo.get_editor_property(cand)
                    say(f"   get_editor_property({cand}) ->", v)
                except Exception as exc:
                    say(f"   get_editor_property({cand}) FAILED: {exc}")
        except Exception as exc:
            say("bpo read failed:", exc)

        try:
            infos = mel.get_all_material_instance_texture_parameter_info(probe)
            say("   texture param infos:", [str(i.get_editor_property("name")) for i in infos])
        except Exception as exc:
            say("   get_all_material_instance_texture_parameter_info failed:", exc)

        try:
            val = mel.get_material_instance_texture_param_value(
                probe, unreal.MaterialParameterInfo(name="Albedo"))
            say("   get_material_instance_texture_param_value ->", val)
        except Exception as exc:
            say("   get_material_instance_texture_param_value failed:", exc)

        try:
            infos = mel.get_all_material_instance_scalar_parameter_info(probe)
            say("   scalar param infos:", [str(i.get_editor_property("name")) for i in infos][:12])
        except Exception as exc:
            say("   scalar infos failed:", exc)

    # cleanup of the mis-named first attempt
    say("")
    ar = unreal.AssetRegistryHelpers.get_asset_registry()
    bad = [a for a in ar.get_assets_by_path("/Game/EnchantedInteriors/Materials", recursive=True)
           if "KB3D_ECI_KB3D_ECI_" in str(a.asset_name)]
    say("mis-named instances to delete:", len(bad))
    for a in bad:
        p = f"{str(a.package_name)}"
        try:
            unreal.EditorAssetLibrary.delete_asset(p)
        except Exception as exc:
            say("   delete failed", p, exc)
    left = [str(a.asset_name) for a in
            ar.get_assets_by_path("/Game/EnchantedInteriors/Materials", recursive=True)]
    say("remaining in Materials folder:", len(left))
    say("names:", ", ".join(sorted(left)[:10]))

    with open(r"C:\Users\froma\AppData\Local\Temp\opencode\api_discovery.txt", "w", encoding="utf-8") as fh:
        fh.write("\n".join(OUT))


if __name__ == "__main__":
    main()
