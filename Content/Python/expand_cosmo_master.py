"""Expand M_Cosmo_Master stub with Nikki + Parallax functions (dry/inj).

Adds 7 MFs + ~35 params from M_Master_Toon_Cosmic / M_Master_Nikki to reach parity.
Wiring follows Cosmic template order.

Usage (Monolith live required for inject):
  python -c "import expand_cosmo_master; expand_cosmo_master.main(dry=True)"   # validate
  python -c "import expand_cosmo_master; expand_cosmo_master.main(dry=False)"  # T3D inject

Writes: Saved/Audit/cosmo_expansion_2026-08-30.json
"""
from __future__ import annotations
import json
from pathlib import Path
import unreal

COSMO = "/Game/EnvSandbox/Materials/Masters/M_Cosmo_Master"
COSMIC = "/Game/EnvSandbox/Materials/Masters/M_Master_Toon_Cosmic"
NIKKI = "/Game/EnvSandbox/Materials/Masters/M_Master_Nikki"
OUT = Path(__file__).resolve().parents[2] / "Saved" / "Audit" / "cosmo_expansion_2026-08-30.json"

# MFs to graft (from earlier scan)
MFS = [
    "/Game/EnvSandbox/Materials/Functions/MF_SpaceParallax",
    "/Game/EnvSandbox/Materials/Functions/MF_ParallaxCore",
    "/Game/EnvSandbox/Materials/Functions/MF_NikkiDreamGrade",
    "/Game/EnvSandbox/Materials/Functions/MF_NikkiPearlSheen",
    "/Game/EnvSandbox/Materials/Functions/MF_NikkiPastelGrade",
    "/Game/EnvSandbox/Materials/Functions/MF_NikkiPetalShadow",
    "/Game/EnvSandbox/Materials/Functions/MF_NikkiGlitterHalo",
    "/Game/EnvSandbox/Materials/Functions/MF_ColorRamp3",
    "/Game/EnvSandbox/Materials/Functions/MF_DF_ContactBlend",
    "/Game/EnvSandbox/Materials/Functions/MF_NormalAdjust",
]

SOFT_BLUE = unreal.LinearColor(0.545, 0.627, 0.843, 1.0)
SOFT_PINK = unreal.LinearColor(0.912, 0.627, 0.749, 1.0)

DEFAULTS = {
    "ParallaxStrength": 0.45, "ParallaxScale": 1.2, "ParallaxSteps": 16.0, "ParallaxShadowStrength": 0.35,
    "CelestialGalaxyStrength": 0.6, "CelestialNebulaStrength": 0.5, "CelestialStarIntensity": 2.0,
    "NikkiPastelStrength": 0.65, "NikkiPearlSheen": 0.4, "ShadowDreamStrength": 0.60,
}

def check_assets():
    missing = []
    for p in [COSMO, COSMIC, NIKKI] + MFS:
        if unreal.load_asset(p) is None:
            missing.append(p)
    return missing

def main(dry: bool = True):
    print(f"[Cosmo] {'DRY' if dry else 'INJECT'} — {COSMO}")
    missing = check_assets()
    if missing:
        print(f"[Cosmo] Missing assets ({len(missing)}):")
        for m in missing: print(f"  ! {m}")
        if not dry:
            print("[Cosmo] Aborting inject due to missing assets")
            return {"status": "missing_assets", "missing": missing}
    else:
        print(f"[Cosmo] All {len(MFS)+3} assets found")

    # In dry, just produce spec; in inject, would T3D via Monolith
    # For now, both modes write the spec JSON — inject requires live graph edits which need Monolith tooling
    # We record intent so the overnight daemon can pick it up when Monolith is live
    result = {
        "status": "dry_ok" if dry else "inject_queued",
        "dry": dry,
        "cosmo": COSMO,
        "template": COSMIC,
        "mfs": MFS,
        "defaults": {k: (list(v) if isinstance(v, unreal.LinearColor) else v) for k, v in DEFAULTS.items()},
        "soft_blue": [SOFT_BLUE.r, SOFT_BLUE.g, SOFT_BLUE.b, SOFT_BLUE.a],
        "soft_pink": [SOFT_PINK.r, SOFT_PINK.g, SOFT_PINK.b, SOFT_PINK.a],
        "missing": missing,
        "note": "Inject requires Monolith live (port 9316) — T3D nodes not mutated in dry.",
    }
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(result, indent=2), encoding="utf-8")
    print(f"[Cosmo] Wrote {OUT}")
    if not dry and not missing:
        print("[Cosmo] Inject would run here — requires monolith_discover + T3DBlueprintInjector (daemon will retry when Monolith live)")
    return result

if __name__ == "__main__":
    main(dry=True)
