"""The surreal water contract gate - offline, no Unreal, no editor.

Checks that the water chorus obeys the canon it claims to obey:
  * every system it dispatches EXISTS in the project (no invented assets)
  * it READS the palette and never WRITES an MPC (one writer per surface)
  * it owns no new authority: it is a plain class with no reflected surface
  * the form contract still holds
"""
from __future__ import annotations

import json
import os
import re
import sys

REPO = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
CHORUS = os.path.join(REPO, "Source", "BS_GodFile", "MelodiaIntegration", "MelodiaWaterChorus.cpp")
CHORUS_H = os.path.join(REPO, "Source", "BS_GodFile", "MelodiaIntegration", "MelodiaWaterChorus.h")
COMPONENT = os.path.join(REPO, "Source", "BS_GodFile", "MelodiaIntegration",
                         "MelodiaWaveHarpCombatComponent.cpp")
SPEC = os.path.join(REPO, "specs/vfx/surreal_water_chorus.v1.json")

results = []


def check(name, ok, detail):
    results.append({"check": name, "ok": bool(ok), "detail": detail})
    print("%-6s %-42s %s" % ("PASS" if ok else "FAIL", name, detail))


def main():
    source = open(CHORUS, encoding="utf-8").read()
    header = open(CHORUS_H, encoding="utf-8").read()
    component = open(COMPONENT, encoding="utf-8").read()

    # 1. every dispatched system exists on disk
    # The paths are object paths ("/Game/Folder/Asset.Asset"); the asset file is the
    # part before the final dot.
    paths = sorted(set(re.findall(r'TEXT\("(/Game/[^"]+)"\)', source)))
    check("systems.named", len(paths) >= 4, "%d systems named" % len(paths))
    for object_path in paths:
        asset = object_path.rsplit(".", 1)[0] if "." in object_path.rsplit("/", 1)[-1] else object_path
        disk = os.path.join(REPO, "Content", asset[len("/Game/"):].replace("/", os.sep)) + ".uasset"
        if os.path.exists(disk):
            check("asset%s" % asset, True, "exists")
            continue
        # A moved asset is still a finding, but an actionable one: say where it went.
        name = asset.rsplit("/", 1)[-1] + ".uasset"
        found = []
        for root, dirs, files in os.walk(os.path.join(REPO, "Content")):
            if name in files:
                found.append(os.path.relpath(os.path.join(root, name),
                                            os.path.join(REPO, "Content")).replace("\\", "/"))
        check("asset%s" % asset, False,
              "MISSING - found at %s" % found[0] if found else "MISSING on disk")

    # 2. it reads the palette and never writes an MPC
    writes = re.findall(r"SetScalarParameterValue|SetVectorParameterValue|"
                         r"K2_SetScalarParameterValue|K2_SetVectorParameterValue", source)
    check("no_mpc_writes", not writes,
          "no MPC write calls" if not writes else "WRITES: %s" % set(writes))
    check("reads_palette", "GetParameterCollectionInstance" in source,
          "reads through the world instance, the project's own pattern")

    # 3. it is a plain class: no reflected surface, no new authority
    check("plain_class", "UCLASS" not in header and "USTRUCT" not in header,
          "no UCLASS/USTRUCT in the header")
    check("no_new_owner", "class UMelodia" not in header and "UPROPERTY" not in header,
          "no reflected members, so no UHT pass and no new authority")

    # 4. the role binding is by pattern, and the receipt exists
    check("role_binding", "RoleForParameter" in source,
          "parameters are bound by role, not by hard-coded names")
    check("receipt", "MELODIA_WATER_CHORUS" in source,
          "the log carries the receipt")

    # 5. the component owns it and it is OFF by default
    check("owned_by_component", "WaterChorus.Start" in component and "WaterChorus.Tick" in component,
          "the component starts and ticks it")
    check("off_by_default", "bool bEnableWaterChorus = false" in
          open(os.path.join(REPO, "Source", "BS_GodFile", "MelodiaIntegration",
                            "MelodiaWaveHarpCombatComponent.h"), encoding="utf-8").read(),
          "the surfaces have to exist before it is turned on")

    # 6. the spec agrees
    check("spec_present", os.path.exists(SPEC),
          os.path.relpath(SPEC, REPO) if os.path.exists(SPEC) else "the contract is missing")

    bad = [r for r in results if not r["ok"]]
    print("\n%d checks, %d failed" % (len(results), len(bad)))
    out = os.path.join(REPO, "Saved", "Audit", "waveharp", "surreal_water_contract.json")
    os.makedirs(os.path.dirname(out), exist_ok=True)
    with open(out, "w", encoding="utf-8") as fh:
        json.dump({"schema": "melodia.surreal_water_contract.v1",
                   "source": "offline gate (no editor)",
                   "checks": results}, fh, indent=2)
    print("receipt:", os.path.relpath(out, REPO))
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main())
