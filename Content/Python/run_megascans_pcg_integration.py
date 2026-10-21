"""Master runner for Megascans PCG integration into L_MelusinaMorning biome graphs.

Executes all integration steps in order:
  1. Reparent Megascans MIs onto M_Master_Toon_Universal
  2. Integrate Megascans rocks into PCG_Biome_RockScatter
  3. Integrate Megascans plants into PCG_Biome_MorningMeadow
  4. Integrate Megascans crystal/rock into PCG_Biome_CrystalGarden
  5. Verify integration

Run inside UE editor via Monolith run_python:
    import run_megascans_pcg_integration as rmpi
    rmpi.run()
"""

from __future__ import annotations

import integrate_megascans_reparent as imr
import integrate_megascans_rock_scatter as irs
import integrate_megascans_meadow as imm
import integrate_megascans_crystal_garden as icg
import verify_megascans_pcg_integration as vmpi


def run() -> dict:
    results = {}

    results["step1_reparent"] = imr.run()
    unreal.log(f"[INTEGRATE] step1_reparent: {results['step1_reparent']}")

    results["step2_rock_scatter"] = irs.run()
    unreal.log(f"[INTEGRATE] step2_rock_scatter: {results['step2_rock_scatter']}")

    results["step3_meadow"] = imm.run()
    unreal.log(f"[INTEGRATE] step3_meadow: {results['step3_meadow']}")

    results["step4_crystal_garden"] = icg.run()
    unreal.log(f"[INTEGRATE] step4_crystal_garden: {results['step4_crystal_garden']}")

    results["step5_verify"] = vmpi.run()
    unreal.log(f"[INTEGRATE] step5_verify overall: {results['step5_verify']['overall']}")

    return results


if __name__ == "__main__":
    print(run())
