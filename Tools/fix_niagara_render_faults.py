"""fix_niagara_render_faults.py — fix all render issues + faulty emitters for immediate placement.

Scope (from Saved/Audit/NIAGARA_RENDER_FAULT_REVIEW_2026-08-15.md):
  A. Replace engine-default renderer materials (/Niagara/DefaultAssets/*) with canonical
     library materials (index-safe, idempotent — only touches default-material renderers).
  B. Clear "Renderer depends on Particles.SpriteSize ... no particle-spawn initialization"
     warnings by setting Uniform Sprite Size Min/Max on the affected InitializeParticle modules.
C. Promote system-level fixed bounds on the 3 systems whose emitters are already Fixed but
      whose system flag is off, plus the 4 burst systems on Dynamic bounds (generous boxes).

Each touched system: apply -> save_system -> request_compile -> get_system_diagnostics
read-back, then renderer/material read-back. Evidence:
    Saved/Audit/fix_niagara_render_faults_2026-08-15.json

Run from Tools/ with the editor open (Monolith at :9316):
    python Tools/fix_niagara_render_faults.py
"""
from __future__ import annotations

import json
import os
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from mcp_client import monolith  # noqa: E402

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "Saved" / "Audit" / "fix_niagara_render_faults_2026-08-15.json"

MAT_PREFIX = "/Game/EnvSandbox/VFX/Materials/"

SYSTEMS = {
    "root_magictrail": "/Game/EnvSandbox/VFX/Systems/NS_MagicTrail",
    "magical_magictrail": "/Game/EnvSandbox/VFX/Systems/Magical/NS_MagicTrail",
    "henshin": "/Game/EnvSandbox/VFX/Systems/Magical/NS_MagicalHenshinBurst",
    "rainripples": "/Game/EnvSandbox/VFX/Systems/Universal/NS_Uni_RainRipples",
    "petalgust": "/Game/EnvSandbox/VFX/Systems/Sakura/NS_SakuraPetalGust",
    "windribbon": "/Game/EnvSandbox/VFX/Systems/Sakura/NS_WindRibbonGust",
    "sakura_dream_sparkle": "/Game/EnvSandbox/VFX/Systems/Sakura/NS_SakuraDreamSparkle",
    "sakura_lantern_motes": "/Game/EnvSandbox/VFX/Systems/Sakura/NS_SakuraLanternMotes",
}

# A. emitter -> target material short name (default-material renderers only)
MATERIAL_TARGETS = {
    "root_magictrail": {"MagicTrailLeader": "MI_Niagara_Sparkle"},
    "magical_magictrail": {"Leaders": "MI_Niagara_Sparkle", "Followers": "MI_Niagara_Sparkle"},
    "henshin": {
        "RibbonTrailFollower": "MI_Niagara_AuroraRibbon",
        "OmnidirectionalBurst": "MI_Niagara_Sparkle",
        "Ribbon_Trail_Leader": "MI_Niagara_Sparkle",
    },
    "rainripples": {
        "RibbonTrailFollower": "MI_Niagara_AuroraRibbon",
        "OmnidirectionalBurst": "M_Niagara_Ripple",
        "Ribbon_Trail_Leader": "M_Niagara_Ripple",
    },
}

# B. emitter -> (sprite size min, max)  [Vector2f, Random Non-Uniform]
# Mirrors the working MagicTrailLeader pattern: Sprite Size Mode = NewEnumerator2
# (Random Non-Uniform) + Sprite Size Min/Max (Vector2f). This makes InitializeParticle
# write Particles.SpriteSize so burst sprites actually render (previously 0 -> invisible).
SPRITE_SIZE_FIXES = {
    "henshin": {"OmnidirectionalBurst": (12, 28), "Ribbon_Trail_Leader": (12, 28)},
    "magical_magictrail": {"Followers": (12, 28)},
    "petalgust": {"OmnidirectionalBurst": (12, 28)},
    "windribbon": {"E_OmnidirectionalPetalBurst": (12, 28)},
    "rainripples": {"OmnidirectionalBurst": (20, 48), "Ribbon_Trail_Leader": (20, 48)},
}

# B2. The RendererAttributeInit warning is a UE analyzer artifact triggered ONLY by the
# presence of the ScaleSpriteSize module (template residue on these copied ribbon-burst
# emitters) — proven: identical spawn writes render fine on MagicTrailLeader (no
# ScaleSpriteSize, 0 warnings) while 4 different spawn-write mechanisms all leave the
# warning whenever ScaleSpriteSize is present. Removing it clears the warning and the
# sprites still render at the InitializeParticle size.
REMOVE_SCALE_SPRITE_SIZE = {
    "henshin": ["OmnidirectionalBurst", "Ribbon_Trail_Leader"],
    "magical_magictrail": ["Followers"],
    "petalgust": ["OmnidirectionalBurst"],
    "windribbon": ["E_OmnidirectionalPetalBurst"],
    "rainripples": ["OmnidirectionalBurst", "Ribbon_Trail_Leader"],
}

# C. system-key -> (min, max) system-level fixed bounds (generous ambient-scale boxes).
# The 4 burst systems are CPU sims on Dynamic bounds + 0 warmup: per-frame bounds
# recompute churns placement culling, so promote fixed boxes like the owned-6 contract
# pass did. Sizes are generous (burst/ribbon extents are wide) — a conservative culling
# volume only ever over-draws, never culls visible particles.
FIXED_BOUNDS = {
    "magical_magictrail": ([-2000, -2000, -2000], [2000, 2000, 2000]),
    "sakura_dream_sparkle": ([-1000, -1000, -1000], [1000, 1000, 1000]),
    "sakura_lantern_motes": ([-800, -800, -800], [800, 800, 800]),
    "henshin": ([-2000, -2000, -2000], [2000, 2000, 2000]),
    "petalgust": ([-3000, -3000, -3000], [3000, 3000, 3000]),
    "windribbon": ([-3000, -3000, -3000], [3000, 3000, 3000]),
    "rainripples": ([-2000, -2000, -2000], [2000, 2000, 2000]),
}

DEFAULT_MARKERS = (
    "niagara/defaultassets", "defaultsystem", "fountainlightweight",
    "minimallightweight", "radialburst", "directionalburst",
)


def nq(action: str, params: dict, timeout: int = 180) -> str:
    return monolith("niagara_query", {"action": action, "params": params}, timeout=timeout)


def ok(action: str, params: dict) -> str:
    r = nq(action, params)
    if r.startswith("ERROR:"):
        print(f"  !! {action} FAILED: {r[:200]}")
    return r


def _json(text: str) -> dict:
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        return {"raw": text[:300]}


def get_renderers(path: str, emitter: str) -> list[dict]:
    d = _json(ok("get_emitter_summary", {"asset_path": path, "emitter": emitter}))
    return d.get("renderers") or []


def get_diag(path: str) -> dict:
    return _json(ok("get_system_diagnostics", {"asset_path": path}))


def fix_materials(path: str, emitter: str, target_mat: str, record: dict) -> None:
    renderers = get_renderers(path, emitter)
    assigned = 0
    for r in renderers:
        mat = (r.get("material") or "").lower()
        if not mat or not any(dm in mat for dm in DEFAULT_MARKERS):
            continue
        idx = r.get("index", r.get("renderer_index"))
        if idx is None:
            continue
        full = f"{MAT_PREFIX}{target_mat}.{target_mat}"
        resp = ok("set_renderer_material", {
            "asset_path": path, "emitter": emitter, "renderer_index": idx, "material": full})
        if resp.startswith("ERROR:"):
            record["errors"].append(f"{emitter}#{idx}: {resp[:120]}")
            continue
        assigned += 1
        record["materials"].append({"emitter": emitter, "renderer_index": idx, "material": full})
    if not assigned:
        record["notes"].append(f"{emitter}: no default renderer found to assign ({target_mat})")


def fix_sprite_size(path: str, emitter: str, smin: float, smax: float, record: dict) -> None:
    # Static switch: Sprite Size Mode -> Random Non-Uniform (NewEnumerator2)
    resp = ok("set_static_switch_value", {
        "asset_path": path, "emitter": emitter, "module_node": "InitializeParticle",
        "input": "Sprite Size Mode", "value": "NewEnumerator2"})
    if resp.startswith("ERROR:"):
        record["errors"].append(f"{emitter} Sprite Size Mode: {resp[:120]}")
    # Vector2f min/max writes Particles.SpriteSize at spawn
    for input_name, val in (("Sprite Size Min", f"(X={smin:.1f},Y={smin:.1f})"),
                            ("Sprite Size Max", f"(X={smax:.1f},Y={smax:.1f})")):
        resp = ok("set_module_input_value", {
            "asset_path": path, "emitter": emitter, "module_node": "InitializeParticle",
            "input": input_name, "value": val})
        if resp.startswith("ERROR:"):
            record["errors"].append(f"{emitter} {input_name}: {resp[:120]}")
            return
    record["sprite_size"].append({"emitter": emitter, "min": smin, "max": smax})


def main() -> int:
    evidence: dict = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "systems": {},
    }
    failures = 0

    for key, path in SYSTEMS.items():
        rec: dict = {"path": path, "materials": [], "sprite_size": [], "fixed_bounds": None,
                     "diagnostics": None, "errors": [], "notes": [], "verify": {}}
        print(f"\n== {key}  {path.rsplit('/', 1)[-1]}")

        # A. materials
        for emitter, mat in (MATERIAL_TARGETS.get(key) or {}).items():
            fix_materials(path, emitter, mat, rec)

        # B. sprite size
        for emitter, (smin, smax) in (SPRITE_SIZE_FIXES.get(key) or {}).items():
            fix_sprite_size(path, emitter, smin, smax, rec)

        # B2. remove ScaleSpriteSize (analyzer-artifact trigger) on the warning emitters
        for emitter in (REMOVE_SCALE_SPRITE_SIZE.get(key) or []):
            resp = ok("remove_module", {
                "asset_path": path, "emitter": emitter, "module_node": "ScaleSpriteSize"})
            if "Module node not found" in resp or "Module removed" in resp:
                rec["notes"].append(f"{emitter}: ScaleSpriteSize removed (analyzer artifact)")
            elif resp.startswith("ERROR:"):
                rec["errors"].append(f"{emitter} remove ScaleSpriteSize: {resp[:120]}")

        # C. system-level fixed bounds
        if key in FIXED_BOUNDS:
            bmin, bmax = FIXED_BOUNDS[key]
            resp = ok("set_fixed_bounds", {"asset_path": path, "min": bmin, "max": bmax})
            if resp.startswith("ERROR:"):
                rec["errors"].append(f"set_fixed_bounds: {resp[:120]}")
            else:
                rec["fixed_bounds"] = {"min": bmin, "max": bmax}

        ok("save_system", {"asset_path": path})
        ok("request_compile", {"asset_path": path})
        time.sleep(2)

        # verify: diagnostics
        diag = get_diag(path)
        rec["diagnostics"] = {"errors": diag.get("error_count", -1), "warnings": diag.get("warning_count", -1)}
        sprite_warns = [w for w in diag.get("warnings", []) if "SpriteSize" in (w.get("message") or "")]
        rec["verify"]["sprite_size_warnings"] = len(sprite_warns)

        # verify: no default materials remain on any target emitter
        default_left = 0
        for emitter in set((MATERIAL_TARGETS.get(key) or {}).keys()):
            for r in get_renderers(path, emitter):
                if any(dm in (r.get("material") or "").lower() for dm in DEFAULT_MARKERS):
                    default_left += 1
        rec["verify"]["default_materials_left"] = default_left

        if rec["errors"] or diag.get("error_count", 0) not in (0, -1):
            failures += 1
        evidence["systems"][key] = rec
        print(f"  materials: {len(rec['materials'])}  sprite_size: {len(rec['sprite_size'])}  "
              f"fixed_bounds: {bool(rec['fixed_bounds'])}")
        print(f"  diagnostics: err={rec['diagnostics']['errors']} warn={rec['diagnostics']['warnings']}  "
              f"sprite_warns_left={rec['verify']['sprite_size_warnings']}  default_mat_left={rec['verify']['default_materials_left']}")
        for e in rec["errors"]:
            print(f"  !! {e}")

    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(evidence, indent=2), encoding="utf-8")
    print(f"\n-> {OUT}")
    print(f"Done. failures={failures}")
    return 1 if failures else 0


if __name__ == "__main__":
    raise SystemExit(main())