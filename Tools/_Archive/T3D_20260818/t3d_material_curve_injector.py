#!/usr/bin/env python3
"""
T3D Material Curve Injector — inject material parameter curves, scalars, colors,
and textures via Monolith MCP.

Two-tier dispatch:
  - Material instances (UMaterialInstance) → material_query:set_instance_parameter
  - Toon profiles / Blueprint-based assets → editor_query:run_python

CLI:
    python t3d_material_curve_injector.py --asset <path> --set-scalar <name>=<value>
    python t3d_material_curve_injector.py --asset <path> --set-color <name>=<r,g,b,a>
    python t3d_material_curve_injector.py --asset <path> --curve <name> --points <json>
    python t3d_material_curve_injector.py --spec specs/toon_profiles/tp_melusina.json
"""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path

from mcp_client import monolith


class T3DMaterialCurveInjector:
    """Inject material parameter curves, scalars, colors, and textures via Monolith MCP."""

    # ------------------------------------------------------------------
    # Curve read / write  (Toon-Profile RuntimeCurveLinearColor)
    # ------------------------------------------------------------------

    def read_curve_from_asset(self, asset_path: str, curve_name: str) -> list[dict] | None:
        """Export asset T3D text and extract curve keys.

        Returns  [{"time": float, "color": {"r": ..., "g": ..., "b": ..., "a": ...}}, ...]
        or None when the server is unreachable or the curve is not found.
        """
        raw = monolith("project_query", {
            "action": "export_asset_text",
            "asset_path": asset_path,
            "grep_pattern": curve_name,
        })
        if not raw or raw.startswith("ERROR"):
            return None
        return self._parse_color_curve(raw, curve_name)

    @staticmethod
    def _parse_color_curve(t3d: str, curve_name: str) -> list[dict] | None:
        """Reconstruct colour keys by merging the four per-channel curves.

        T3D format for a RuntimeCurveLinearColor stored inside a struct property::

            DiffuseRamp=(ColorCurves[0]=(Keys=((Time=0.0,Value=0.034),...),...),
                         ColorCurves[1]=(Keys=((Time=0.0,Value=0.022),...),...), ...)

        Each ColorCurves[N] is a scalar curve for one RGBA channel.
        """
        # Locate the block that belongs to the requested curve property
        m = re.search(rf'\b{curve_name}=\(', t3d)
        if not m:
            return None

        # Collect per-channel key tables  channel → [(time, value)]
        channels: dict[int, list[tuple[float, float]]] = {}
        pattern = re.compile(
            r'ColorCurves\[(\d+)\]='  # channel index
            r'\(Keys=\(('             # open Keys
            r'(?:\([^)]*\),?)*'       # one or more key tuples
            r')\)'                     # close Keys
        )
        for ch_match in pattern.finditer(t3d, m.end()):
            ch_idx = int(ch_match.group(1))
            keys_body = ch_match.group(2)
            key_pairs = re.findall(r'\(Time=([\d.e+-]+)(?:,Value=([\d.e+-]+))?\)', keys_body)
            for time_str, val_str in key_pairs:
                t = float(time_str)
                v = float(val_str) if val_str else 0.0
                channels.setdefault(ch_idx, []).append((t, v))

        if not channels:
            return None

        # Merge all unique time samples across the 4 channels
        all_times = sorted({t for ch in channels.values() for (t, _v) in ch})
        points: list[dict] = []
        for t in all_times:
            rgba: list[float] = [0.0, 0.0, 0.0, 1.0]
            for ch_idx in range(4):
                table = channels.get(ch_idx, [])
                # linear interpolation between the two nearest keys
                rgba[ch_idx] = _eval_scalar_curve(table, t)
            points.append({
                "time": round(t, 6),
                "color": {
                    "r": round(rgba[0], 6),
                    "g": round(rgba[1], 6),
                    "b": round(rgba[2], 6),
                    "a": round(rgba[3], 6),
                },
            })
        return points

    def write_curve_to_asset(
        self,
        asset_path: str,
        curve_name: str,
        curve_points: list[dict],
    ) -> bool:
        """Write a colour curve (RuntimeCurveLinearColor) to a toon-profile asset."""
        keys_lines: list[str] = []
        for pt in curve_points:
            c = pt["color"]
            keys_lines.append(
                f"c.add_key({pt['time']}, unreal.LinearColor({c['r']}, {c['g']}, {c['b']}, {c['a']}))"
            )
        keys_body = "\n            ".join(keys_lines)

        code = f"""import unreal
tp = unreal.EditorAssetLibrary.load_asset("{asset_path}")
if not tp:
    print("ERROR:load_failed")
else:
    s = tp.get_editor_property("Settings")
    c = unreal.RuntimeCurveLinearColor()
    {keys_body}
    s.set_editor_property("{curve_name}", c)
    tp.set_editor_property("Settings", s)
    unreal.EditorAssetLibrary.save_asset("{asset_path}")
    print("SUCCESS")
"""
        result = monolith("editor_query", {"action": "run_python", "command": code})
        return bool(result and "SUCCESS" in result)

    # ------------------------------------------------------------------
    # Scalar / colour / texture parameters  (dual dispatch)
    # ------------------------------------------------------------------

    def set_scalar_parameter(
        self, asset_path: str, param_name: str, value: float,
        is_material_instance: bool = False,
    ) -> bool:
        if is_material_instance:
            return self._mi_set(asset_path, parameter_name=param_name, scalar_value=value)
        return self._tp_set_scalar(asset_path, param_name, value)

    def set_color_parameter(
        self, asset_path: str, param_name: str, color_dict: dict,
        is_material_instance: bool = False,
    ) -> bool:
        r, g, b, a = (color_dict.get(k, 0.0) for k in ("r", "g", "b", "a"))
        if is_material_instance:
            return self._mi_set(asset_path, parameter_name=param_name, vector_value=[r, g, b, a])
        return self._tp_set_color(asset_path, param_name, r, g, b, a)

    def set_texture_parameter(
        self, asset_path: str, param_name: str, texture_path: str,
        is_material_instance: bool = False,
    ) -> bool:
        if is_material_instance:
            return self._mi_set(asset_path, parameter_name=param_name, texture_value=texture_path)
        return self._tp_set_texture(asset_path, param_name, texture_path)

    def _mi_set(self, asset_path: str, **kw) -> bool:
        result = monolith("material_query", {
            "action": "set_instance_parameter",
            "asset_path": asset_path,
            "parameter_name": kw.pop("parameter_name"),
            **kw,
        })
        return not (isinstance(result, str) and "ERROR" in result)

    def _tp_set_scalar(self, _asset_path: str, _param_name: str, _value: float) -> bool:
        code = f"""import unreal
a = unreal.EditorAssetLibrary.load_asset("{_asset_path}")
if a:
    s = a.get_editor_property("Settings")
    s.set_editor_property("{_param_name}", {_value})
    a.set_editor_property("Settings", s)
    unreal.EditorAssetLibrary.save_asset("{_asset_path}")
    print("SUCCESS")
"""
        result = monolith("editor_query", {"action": "run_python", "command": code})
        return bool(result and "SUCCESS" in result)

    def _tp_set_color(self, _asset_path: str, _param_name: str, r: float, g: float, b: float, a: float) -> bool:
        code = f"""import unreal
a = unreal.EditorAssetLibrary.load_asset("{_asset_path}")
if a:
    s = a.get_editor_property("Settings")
    s.set_editor_property("{_param_name}", unreal.LinearColor({r}, {g}, {b}, {a}))
    a.set_editor_property("Settings", s)
    unreal.EditorAssetLibrary.save_asset("{_asset_path}")
    print("SUCCESS")
"""
        result = monolith("editor_query", {"action": "run_python", "command": code})
        return bool(result and "SUCCESS" in result)

    def _tp_set_texture(self, _asset_path: str, _param_name: str, tex_path: str) -> bool:
        code = f"""import unreal
a = unreal.EditorAssetLibrary.load_asset("{_asset_path}")
t = unreal.EditorAssetLibrary.load_asset("{tex_path}")
if a and t:
    s = a.get_editor_property("Settings")
    s.set_editor_property("{_param_name}", t)
    a.set_editor_property("Settings", s)
    unreal.EditorAssetLibrary.save_asset("{_asset_path}")
    print("SUCCESS")
"""
        result = monolith("editor_query", {"action": "run_python", "command": code})
        return bool(result and "SUCCESS" in result)

    # ------------------------------------------------------------------
    # Compile / verify
    # ------------------------------------------------------------------

    def compile_and_verify(self, asset_path: str) -> tuple[bool, str]:
        result = monolith("material_query", {
            "action": "recompile_material",
            "asset_path": asset_path,
        })
        stats = monolith("material_query", {
            "action": "get_compilation_stats",
            "asset_path": asset_path,
        })
        if isinstance(result, str) and "ERROR" in result:
            return False, stats or result
        has_errors = bool(stats and "error" in stats.lower() and "0 errors" not in stats.lower())
        return (not has_errors, stats or "ok")

    def get_instance_parameters(self, asset_path: str) -> dict | str | None:
        result = monolith("material_query", {
            "action": "get_instance_parameters",
            "asset_path": asset_path,
        })
        if isinstance(result, str) and result.startswith("ERROR"):
            return None
        try:
            return json.loads(result)
        except (json.JSONDecodeError, TypeError):
            return result

    # ------------------------------------------------------------------
    # Batch helpers
    # ------------------------------------------------------------------

    def set_instance_parameters_batch(self, asset_path: str, params: list[dict]) -> bool:
        normalised: list[dict] = []
        for p in params:
            entry = {"name": p["name"], "type": p["type"]}
            if p["type"] == "vector" and isinstance(p["value"], dict):
                c = p["value"]
                entry["value"] = [c.get("r", 0), c.get("g", 0), c.get("b", 0), c.get("a", 1.0)]
            else:
                entry["value"] = p["value"]
            normalised.append(entry)
        result = monolith("material_query", {
            "action": "set_instance_parameters",
            "asset_path": asset_path,
            "parameters": normalised,
        })
        return not (isinstance(result, str) and "ERROR" in result)

    # ------------------------------------------------------------------
    # Spec-driven toon-profile application
    # ------------------------------------------------------------------

    def apply_toon_profile_spec(self, spec: dict) -> dict:
        settings = spec["settings"]
        asset_path = spec["asset_path"]
        applied: list[dict] = []
        errors: list[str] = []

        for key, value in settings.items():
            if key in ("DiffuseRamp", "SpecularRamp"):
                ok = self.write_curve_to_asset(asset_path, key, value)
                applied.append({"param": key, "type": "curve", "ok": ok})
                if not ok:
                    errors.append(f"curve {key}")
            elif key == "ShadowHatchingPattern":
                ok = self.set_texture_parameter(asset_path, key, value)
                applied.append({"param": key, "type": "texture", "ok": ok})
                if not ok:
                    errors.append(f"texture {key}")
            elif isinstance(value, (int, float)):
                ok = self.set_scalar_parameter(asset_path, key, value)
                applied.append({"param": key, "type": "scalar", "ok": ok})
                if not ok:
                    errors.append(f"scalar {key}={value}")
            elif isinstance(value, dict) and all(k in value for k in ("r", "g", "b")):
                ok = self.set_color_parameter(asset_path, key, value)
                applied.append({"param": key, "type": "color", "ok": ok})
                if not ok:
                    errors.append(f"color {key}")

        return {"asset": asset_path, "applied": applied, "errors": errors, "ok": len(errors) == 0}


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def _main() -> int:
    import argparse

    p = argparse.ArgumentParser(description="T3D Material Curve Injector")
    p.add_argument("--asset", help="Asset path")
    p.add_argument("--curve", help="Curve property name")
    p.add_argument("--points", help="JSON array of curve points")
    p.add_argument("--set-scalar", help="Name=value")
    p.add_argument("--set-color", help="Name=r,g,b,a")
    p.add_argument("--set-texture", help="Name=path")
    p.add_argument("--compile", action="store_true", help="Recompile + verify")
    p.add_argument("--spec", help="Apply spec from JSON file")
    p.add_argument("--read-curve", help="Read curve and print keys")
    p.add_argument("--get-params", action="store_true", help="Read instance params")
    p.add_argument("--material-instance", action="store_true", help="Target is MI")

    args = p.parse_args()
    inj = T3DMaterialCurveInjector()

    if args.spec:
        with open(args.spec) as f:
            spec = json.load(f)
        result = inj.apply_toon_profile_spec(spec)
        print(json.dumps(result, indent=2))
        return 0 if result["ok"] else 1

    if not args.asset:
        p.print_help()
        return 1

    ap = args.asset

    if args.curve and args.points:
        pts = json.loads(args.points)
        ok = inj.write_curve_to_asset(ap, args.curve, pts)
        print(f"curve {args.curve}: {'OK' if ok else 'FAIL'}")

    if args.set_scalar:
        name, val = args.set_scalar.split("=", 1)
        ok = inj.set_scalar_parameter(ap, name, float(val), args.material_instance)
        print(f"scalar {name}={val}: {'OK' if ok else 'FAIL'}")

    if args.set_color:
        name, vals = args.set_color.split("=", 1)
        parts = [float(x) for x in vals.split(",")]
        colour = {"r": parts[0], "g": parts[1], "b": parts[2], "a": parts[3] if len(parts) > 3 else 1.0}
        ok = inj.set_color_parameter(ap, name, colour, args.material_instance)
        print(f"color {name}={colour}: {'OK' if ok else 'FAIL'}")

    if args.set_texture:
        name, tex_path = args.set_texture.split("=", 1)
        ok = inj.set_texture_parameter(ap, name, tex_path, args.material_instance)
        print(f"texture {name}={tex_path}: {'OK' if ok else 'FAIL'}")

    if args.read_curve:
        pts = inj.read_curve_from_asset(ap, args.read_curve)
        if pts:
            print(f"  {len(pts)} keys:")
            for pt in pts:
                print(f"    t={pt['time']:.4f}  {pt['color']}")
        else:
            print("  curve not found")

    if args.get_params:
        params = inj.get_instance_parameters(ap)
        print(json.dumps(params, indent=2) if params else "  no params / error")

    if args.compile:
        ok, stats = inj.compile_and_verify(ap)
        print(f"compile: {'OK' if ok else 'ERRORS'}")
        print(stats)

    return 0


def _eval_scalar_curve(table: list[tuple[float, float]], t: float) -> float:
    """Linear interpolate within a sorted (time, value) table."""
    if not table:
        return 0.0
    table.sort(key=lambda x: x[0])
    if t <= table[0][0]:
        return table[0][1]
    if t >= table[-1][0]:
        return table[-1][1]
    for i in range(1, len(table)):
        if t <= table[i][0]:
            t0, v0 = table[i - 1]
            t1, v1 = table[i]
            if t1 == t0:
                return v0
            f = (t - t0) / (t1 - t0)
            return v0 + f * (v1 - v0)
    return table[-1][1]


if __name__ == "__main__":
    sys.exit(_main())
