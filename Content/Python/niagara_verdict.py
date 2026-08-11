"""Analyze live_niagara_audit.json -> per-system verdict table + default-emitter flags."""
from __future__ import annotations
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
AUDIT = ROOT / "Saved" / "Audit" / "live_niagara_audit.json"

DEFAULT_MARKERS = (
    "niagara/defaultassets",
)


def renderer_materials(detail) -> list:
    mats = []
    rnd = detail.get("renderers") if isinstance(detail, dict) else None
    if isinstance(rnd, list):
        for r in rnd:
            if isinstance(r, dict):
                typ = r.get("type")
                mat = r.get("material") or ""
                mats.append({"type": typ, "material": mat})
    return mats


def analyze():
    data = json.loads(AUDIT.read_text(encoding="utf-8"))
    rows = []
    for e in data:
        sysn = e["system"]
        sumy = e.get("summary") or {}
        sp = sumy.get("system_properties") or {}
        warmup = sp.get("warmup_time")
        fixed = sp.get("fixed_bounds")
        diag = e.get("diagnostics") or {}
        err = diag.get("error_count", "?")
        warn = diag.get("warning_count", "?")
        n_emit = len(sumy.get("emitters") or []) if isinstance(sumy.get("emitters"), list) else 0
        # default flags
        default_mats = []
        sim_targets = set()
        renderer_types = set()
        for ed in e.get("emitter_detail") or []:
            detail = ed.get("detail") or {}
            sim_targets.add(str(detail.get("sim_target")))
            for r in renderer_materials(detail):
                mat = (r["material"] or "").lower()
                if not mat:
                    continue
                if any(dm in mat for dm in DEFAULT_MARKERS):
                    default_mats.append(r["material"])
                renderer_types.add(r["type"])
        init_burst_missing = False
        init_size_missing = False
        for ed in e.get("emitter_detail") or []:
            detail = ed.get("detail") or {}
            mods = detail.get("modules") or {}
            spawn = mods.get("particle_spawn") or []
            names = [m.get("name") for m in spawn if isinstance(m, dict)]
            if "InitializeParticle" not in names:
                init_size_missing = True
            if not names:
                init_burst_missing = True
        rows.append({
            "system": sysn, "emitters": n_emit, "warmup": warmup, "fixed_bounds": fixed,
            "sim_targets": sorted(sim_targets), "err": err, "warn": warn,
            "default_materials": sorted(set(default_mats)),
            "renderer_types": sorted(renderer_types),
            "init_particle_ok": not init_size_missing,
            "has_spawn_stack": not init_burst_missing,
        })
    return rows


def main():
    for r in analyze():
        flag = ""
        if r["default_materials"]:
            flag += " [DEFAULT-MAT]"
        if not r["init_particle_ok"]:
            flag += " [NO-InitParticle]"
        if r["warmup"] and r["warmup"] > 3:
            flag += " [WARMUP>3]"
        if not r["fixed_bounds"]:
            flag += " [DYNAMIC-BOUNDS]"
        if r["warn"]:
            flag += f" [warn={r['warn']}]"
        if r["err"]:
            flag += f" [err={r['err']}]"
        print(f"{r['system']:<24} em={r['emitters']:<2} sim={','.join(r['sim_targets']):<12} "
              f"rend={','.join(x.split('.')[-1] for x in r['renderer_types'][:2]):<28} "
              f"mat={'/'.join(r['default_materials']) or 'ok'}{flag}")


if __name__ == "__main__":
    main()