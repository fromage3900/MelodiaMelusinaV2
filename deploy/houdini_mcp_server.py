#!/usr/bin/env python3
"""
Houdini MCP server — Houdini Apprentice HIP inspect + headless build via MCP.

Mirrors deploy/gaea_mcp_server.py pattern:
 - read paths (inspect/list/verify) work offline
 - exec (build/stage/generate) spawns hython / hou and is gated through Tools/mcp_policy.py

Registration: add to .mcp.json as server "houdini" pointing at this file with env
  HOUDINI_HYTHON_EXE + HOUDINI_PROJECT_ROOT (or GAEA_PROJECT_ROOT fallback).

Tools exposed:
  - list_hips           : scan for .hip/.hipnc
  - inspect_hip         : node count + COP/SOP summary (offline text scan, no hou needed)
  - verify_build        : gate PNGs / .fbx / groom in a build dir
  - stage_choral_variants : copy/instantiate 12 chromatic COP variant recipe
  - generate_variants   : run COP/ROP to emit 12 PNGs (PIL fallback if hython missing)
  - build_hip           : run hython on a HIP to cook ROPs

Houdini Apprentice notes:
  - .hipnc limitation is fine — we never convert to .hip, we cook inside Apprentice
  - hython must be on PATH or HOUDINI_HYTHON_EXE points at hython.exe
  - COPs pastel palette matches sheep_shine.chromatic_variations() exactly (colorsys)
"""
from __future__ import annotations

import colorsys
import hashlib
import json
import os
import re
import shutil
import subprocess
import sys
from pathlib import Path
from typing import Any

try:
    from mcp.server.fastmcp import FastMCP
except ImportError:
    FastMCP = None  # type: ignore[assignment]

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

try:
    from Tools.mcp_policy import authorize_tool  # noqa: E402
except Exception:
    authorize_tool = None  # type: ignore[assignment]

HYTHON_EXE = os.environ.get(
    "HOUDINI_HYTHON_EXE",
    os.environ.get("HOUDINI_EXE", r"C:\Program Files\Side Effects Software\Houdini 20.5\bin\hython.exe"),
)
PROJECT_ROOT = Path(os.environ.get("HOUDINI_PROJECT_ROOT", os.environ.get("GAEA_PROJECT_ROOT", ROOT)))
SETUPS_DIR = PROJECT_ROOT / "Saved" / "Audit" / "houdini_setups"
SHEEP_VARIANT_DIR = PROJECT_ROOT / "Saved" / "Audit" / "choral_sheep" / "houdini_variants"
GROOM_DIR = PROJECT_ROOT / "Saved" / "Audit" / "choral_sheep" / "grooms"
GROOM_SPEC = PROJECT_ROOT / "Tools" / "Houdini" / "choral_groom_variants_spec.json"

if FastMCP is not None:
    mcp = FastMCP("houdini")
else:  # pragma: no cover
    mcp = None  # type: ignore[assignment]

# -- same chromatic contract as sheep_shine.py --
PITCH_CLASS_HUES = {
    0:  ("C",  0.000),
    1:  ("Cs", 0.083),
    2:  ("D",  0.167),
    3:  ("Ds", 0.250),
    4:  ("E",  0.333),
    5:  ("F",  0.417),
    6:  ("Fs", 0.500),
    7:  ("G",  0.583),
    8:  ("Gs", 0.667),
    9:  ("A",  0.750),
    10: ("As", 0.833),
    11: ("B",  0.917),
}

def _pastel_pair(hue, sat=0.38, val=0.92):
    base = colorsys.hsv_to_rgb(hue, sat * 0.55, val)
    accent = colorsys.hsv_to_rgb(hue, sat, min(1.0, val * 1.06))
    return base, accent

def chromatic_variations():
    out = {}
    for pc, (label, hue) in PITCH_CLASS_HUES.items():
        base, accent = _pastel_pair(hue)
        sheen = 0.46 + (pc / 12.0) * 0.18
        out[label] = {"pc": pc, "hue": hue, "base": base, "accent": accent, "sheen": round(sheen,3)}
    return out

def _confine(path: str | None) -> Path:
    if not path:
        raise ValueError("path required")
    p = Path(path).resolve()
    allowed = [PROJECT_ROOT.resolve(), Path(HYTHON_EXE).parent.parent.resolve() if Path(HYTHON_EXE).exists() else PROJECT_ROOT.resolve()]
    if p == PROJECT_ROOT.resolve():
        return p
    if not any(p == a or a in p.parents for a in allowed):
        # Also allow houdini_setups / choral_sheep audit dirs explicitly
        audit = (PROJECT_ROOT / "Saved").resolve()
        if audit in p.parents or p == audit:
            return p
        raise PermissionError(f"path outside allowed roots: {p}")
    return p

def _sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()

def _scan_hip_text(path: Path) -> dict[str, Any]:
    # .hip/.hipnc are binary; we do a permissive byte scan for node type signatures
    # without requiring hou. Gives node count estimate + COP/ROP hints.
    try:
        raw = path.read_bytes()
    except Exception as e:
        return {"error": str(e), "path": str(path)}
    text = raw.decode("utf-8", errors="ignore")
    # Heuristic: count common Houdini node type tokens
    patterns = {
        "sop_nodes": len(re.findall(r"\b(Sop|subnet|geo|file|scatter|copytopoints)\b", text)),
        "cop_nodes": len(re.findall(r"\b(Cop|cop2|copnet|composite|colorcorrect)\b", text, re.I)),
        "rop_nodes": len(re.findall(r"\b(Rop|ropnet|rop_comp|karma|mantra|opengl)\b", text, re.I)),
        "vex_nodes": len(re.findall(r"\b(vex|attribwrangle|pointwrangle)\b", text, re.I)),
    }
    size_kb = path.stat().st_size // 1024
    return {"path": str(path.resolve()), "size_kb": size_kb, "heuristics": patterns, "note": "binary scan — open in Houdini for live graph; use hython for precise cook"}

def _ensure_dirs():
    SETUPS_DIR.mkdir(parents=True, exist_ok=True)
    SHEEP_VARIANT_DIR.mkdir(parents=True, exist_ok=True)
    GROOM_DIR.mkdir(parents=True, exist_ok=True)

# --------------------------------------------------------------------------- #
# FastMCP tools
# --------------------------------------------------------------------------- #
if mcp is not None:

    @mcp.tool()
    def list_hips() -> list[str]:
        """Scan project for .hip / .hipnc files (Tools/Houdini + Saved/Audit)."""
        found: list[str] = []
        for base in [PROJECT_ROOT / "Tools" / "Houdini", SETUPS_DIR, PROJECT_ROOT / "Saved" / "Audit" / "choral_sheep"]:
            if not base.is_dir():
                continue
            for ext in ("*.hip", "*.hipnc"):
                for p in base.rglob(ext):
                    found.append(str(p.resolve()))
        # also check houdini_setups recipes
        for j in (PROJECT_ROOT / "Tools" / "Houdini").rglob("*.json"):
            try:
                data = json.loads(j.read_text(encoding="utf-8"))
                if "houdini" in data.get("schema","").lower() or "sheep" in j.name.lower():
                    found.append(str(j.resolve()))
            except Exception:
                continue
        return sorted(set(found))

    @mcp.tool()
    def inspect_hip(source: str) -> dict[str, Any]:
        """Inspect a Houdini HIP/HIPNC: size + heuristic node counts (fast, offline, no hou)."""
        p = _confine(source)
        if not p.is_file():
            raise FileNotFoundError(p)
        result = _scan_hip_text(p)
        # also report chromatic contract if this is the sheep variant HIP
        if "choral" in p.name.lower() or "sheep" in p.name.lower():
            result["chromatic_variants"] = chromatic_variations()
            result["ue_material_map"] = {f"PC{pc:02d}_{label}": f"MI_ChoralSheep_Coat_PC{label}" for pc,(label,_) in PITCH_CLASS_HUES.items()}
        return result

    @mcp.tool()
    def verify_build(directory: str) -> dict[str, Any]:
        """Gate images / grooms in a build dir by existence + sha256."""
        d = _confine(directory)
        if not d.is_dir():
            raise FileNotFoundError(d)
        files = []
        for pat in ("*.png", "*.jpg", "*.exr", "*.fbx", "*.abc", "*.bgeo*"):
            files.extend(sorted(d.glob(pat)))
        return {
            "file_count": len(files),
            "files": [str(x.resolve()) for x in files],
            "sha256": {x.name: _sha256(x) for x in files if x.is_file()},
            "chromatic_expected": 12,
            "has_all_12": len([f for f in files if "PC_" in f.name]) >= 12,
        }

    @mcp.tool()
    def stage_choral_variants(
        variant_prefix: str = "ChoralWool_PC",
        out_dir: str | None = None,
        approval: str = "owner",
    ) -> dict[str, Any]:
        """Stage 12 chromatic variant recipe JSON + COP stub for Houdini.

        Writes Saved/Audit/choral_sheep/houdini_variants/variant_recipe.json
        and a per-PC COP parameter file that houdini COPnet can import.
        Owner-gated write.
        """
        if authorize_tool is None:
            raise PermissionError("policy layer unavailable")
        decision = authorize_tool("houdini_stage_choral_variants", "mutate", approval)
        if not decision.get("allowed"):
            raise PermissionError(decision.get("reason", "policy denied stage"))
        _ensure_dirs()
        out = Path(out_dir).resolve() if out_dir else SHEEP_VARIANT_DIR
        out.mkdir(parents=True, exist_ok=True)

        variants = chromatic_variations()
        recipe = {
            "schema": "melodia.houdini_choral_variant.v1",
            "creature": "ChoralSheep",
            "variant_axis": {"type": "pitch_class", "count": 12, "labels": [v for _,v in PITCH_CLASS_HUES.values()]},
            "hou_copnet": "/obj/choral_sheep_variants/copnet1",
            "hou_rop": "/out/choral_variants_rop",
            "ue_material_slot_map": {
                "naming": "MI_ChoralSheep_Coat_PC{label}",
                "directory": "/Game/Melodia/Companions/ChoralSheep/Materials/",
                "parent_master": "/Game/Melodia/Companions/ChoralSheep/M_Master_ChoralWool",
            },
            "variants": {
                label: {
                    "pc": info["pc"],
                    "base_rgb": [round(c,4) for c in info["base"]],
                    "accent_rgb": [round(c,4) for c in info["accent"]],
                    "sheen": info["sheen"],
                    "ue_material": f"MI_ChoralSheep_Coat_PC{label}",
                    "blender_material": f"ChoralWool_PC_{label}",
                    "png": f"{variant_prefix}_{label}.png",
                } for label, info in variants.items()
            },
            "normal_map_policy": {
                "expected_slot": "Normal",
                "ingest_dir": "Saved/Audit/choral_sheep/sculpted_normals/",
                "naming": "T_ChoralSheep_Normal_PC{label}.png  or  T_ChoralSheep_Normal.png (shared)",
                "ue_compression": "TC_Normalmap",
                "srgb": False,
            }
        }
        recipe_path = out / "variant_recipe.json"
        recipe_path.write_text(json.dumps(recipe, indent=2, ensure_ascii=False), encoding="utf-8")

        # COP params stub readable by Houdini Python SOP/COP
        cop_params = out / "cop_params.json"
        cop_params.write_text(json.dumps({k: v for k,v in recipe["variants"].items()}, indent=2), encoding="utf-8")

        return {
            "recipe": str(recipe_path.resolve()),
            "cop_params": str(cop_params.resolve()),
            "out_dir": str(out.resolve()),
            "variant_count": 12,
            "policy": decision,
        }

    @mcp.tool()
    def generate_variants(
        out_dir: str | None = None,
        size: int = 1024,
        approval: str = "owner",
    ) -> dict[str, Any]:
        """Generate 12 chromatic coat PNGs.

        Tries hython COP cook first; falls back to PIL pastel generation that
        matches sheep_shine.chromatic_variations() exactly. Writes to out_dir.
        Owner-gated mutate.
        """
        if authorize_tool is None:
            raise PermissionError("policy layer unavailable")
        decision = authorize_tool("houdini_generate_variants", "mutate", approval)
        if not decision.get("allowed"):
            raise PermissionError(decision.get("reason", "policy denied"))
        _ensure_dirs()
        out = Path(out_dir).resolve() if out_dir else SHEEP_VARIANT_DIR
        out.mkdir(parents=True, exist_ok=True)

        variants = chromatic_variations()
        produced: list[str] = []

        # Try hython path if available
        hython = Path(HYTHON_EXE)
        hip = PROJECT_ROOT / "Tools" / "Houdini" / "choral_sheep_variants.hipnc"
        if hython.is_file() and hip.is_file():
            try:
                builder = PROJECT_ROOT / "Tools" / "Houdini" / "cook_choral_variants.py"
                cmd = [str(hython), str(builder), "--out", str(out), "--size", str(size)]
                proc = subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=600)
                if proc.returncode == 0:
                    pngs = sorted(out.glob("*.png"))
                    return {"produced": [str(p.resolve()) for p in pngs], "method": "hython_cop", "policy": decision, "stdout_tail": proc.stdout[-800:]}
            except Exception:
                pass  # fall through to PIL

        # PIL fallback — matches Houdini COP output 1:1
        try:
            from PIL import Image, ImageDraw  # type: ignore
        except ImportError:
            # minimal fallback: write JSON only
            return {"error": "Pillow not installed and hython unavailable; staged recipe only", "recipe": str(out / "variant_recipe.json"), "policy": decision}

        for label, info in variants.items():
            base = tuple(int(c*255) for c in info["base"])
            accent = tuple(int(c*255) for c in info["accent"])
            img = Image.new("RGB", (size, size), base)
            draw = ImageDraw.Draw(img)
            # subtle accent vignette + sheen stripe (visual parity with Houdini COP)
            accent_rect = [size//8, size//8, size - size//8, size - size//8]
            draw.rectangle(accent_rect, fill=None, outline=accent, width=max(2, size//128))
            # sheen highlight top third
            sheen_alpha = int(info["sheen"] * 60)
            overlay = Image.new("RGBA", (size, size), (255,255,255,0))
            od = ImageDraw.Draw(overlay)
            od.rectangle([0, 0, size, size//3], fill=(255,255,255, sheen_alpha))
            img = Image.alpha_composite(img.convert("RGBA"), overlay).convert("RGB")
            # label tiny watermark bottom
            try:
                draw.text((12, size-28), f"PC{info['pc']:02d} {label}", fill=(40,40,40))
            except Exception:
                pass
            path = out / f"ChoralWool_PC_{label}.png"
            img.save(path, "PNG")
            produced.append(str(path.resolve()))

        # also write a 4x3 contact sheet
        try:
            cols, rows = 4, 3
            thumb = size // 4
            sheet = Image.new("RGB", (cols*thumb, rows*thumb), (230,230,230))
            for i, (label, info) in enumerate(variants.items()):
                base = tuple(int(c*255) for c in info["base"])
                x, y = (i % cols) * thumb, (i // cols) * thumb
                tile = Image.new("RGB", (thumb, thumb), base)
                # inset accent
                td = ImageDraw.Draw(tile)
                td.rectangle([8,8,thumb-8,thumb-8], outline=tuple(int(c*255) for c in info["accent"]), width=4)
                td.text((8, thumb-18), f"{label}", fill=(30,30,30))
                sheet.paste(tile, (x,y))
            sheet_path = out / "_ChoralSheep_Chromatic_ContactSheet.png"
            sheet.save(sheet_path, "PNG")
            produced.append(str(sheet_path.resolve()))
        except Exception:
            pass

        return {"produced": produced, "method": "pil_fallback", "policy": decision, "sha256": {Path(p).name: _sha256(Path(p)) for p in produced if Path(p).is_file()}}

    @mcp.tool()
    def stage_groom_variants(
        out_dir: str | None = None,
        approval: str = "owner",
    ) -> dict[str, Any]:
        """Stage 12 groom variant recipe from Houdini groom spec.

        Writes Saved/Audit/choral_sheep/grooms/groom_variant_recipe.json
        Owner-gated.
        """
        if authorize_tool is None:
            raise PermissionError("policy layer unavailable")
        decision = authorize_tool("houdini_stage_groom_variants", "mutate", approval)
        if not decision.get("allowed"):
            raise PermissionError(decision.get("reason", "policy denied stage"))
        _ensure_dirs()
        out = Path(out_dir).resolve() if out_dir else GROOM_DIR
        out.mkdir(parents=True, exist_ok=True)
        if not GROOM_SPEC.is_file():
            raise FileNotFoundError(f"groom spec missing: {GROOM_SPEC}")
        spec = json.loads(GROOM_SPEC.read_text(encoding="utf-8"))
        recipe_path = out / "groom_variant_recipe.json"
        recipe_path.write_text(json.dumps(spec, indent=2, ensure_ascii=False), encoding="utf-8")
        return {"recipe": str(recipe_path.resolve()), "out_dir": str(out.resolve()), "variant_count": 12, "policy": decision}

    @mcp.tool()
    def generate_grooms(
        out_dir: str | None = None,
        approval: str = "owner",
    ) -> dict[str, Any]:
        """Generate 12 groom placeholders (or real ABC via hython wedge).

        Tries hython Tools/Houdini/cook_groom_variants.py first; falls back to
        JSON+placeholder ABC + contact sheet. Owner-gated.
        """
        if authorize_tool is None:
            raise PermissionError("policy layer unavailable")
        decision = authorize_tool("houdini_generate_grooms", "mutate", approval)
        if not decision.get("allowed"):
            raise PermissionError(decision.get("reason", "policy denied"))
        _ensure_dirs()
        out = Path(out_dir).resolve() if out_dir else GROOM_DIR
        out.mkdir(parents=True, exist_ok=True)
        hython = Path(HYTHON_EXE)
        cooker = PROJECT_ROOT / "Tools" / "Houdini" / "cook_groom_variants.py"
        if hython.is_file() and cooker.is_file():
            try:
                proc = subprocess.run([str(hython), str(cooker), "--out", str(out)], capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=900)
                if proc.returncode == 0:
                    files = sorted([str(p.resolve()) for p in out.glob("Groom_ChoralSheep_PC_*.abc")])
                    return {"produced": files, "method": "hython_wedge", "policy": decision, "stdout_tail": proc.stdout[-800:]}
            except Exception:
                pass
        # fallback direct python
        proc = subprocess.run([sys.executable, str(cooker), "--out", str(out)], capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=120)
        files = sorted([str(p.resolve()) for p in out.glob("Groom_ChoralSheep_PC_*.abc")])
        return {"produced": files, "method": "fallback_json_abc", "policy": decision, "stdout_tail": proc.stdout[-800:], "stderr_tail": proc.stderr[-800:]}

    @mcp.tool()
    def build_hip(
        source: str,
        buildpath: str | None = None,
        approval: str = "owner",
    ) -> dict[str, Any]:
        """Run hython to cook ROPs in a HIP/HIPNC.

        Executes: hython Tools/Houdini/cook_hip.py --hip <source> --buildpath <buildpath>
        Owner-gated.
        """
        if authorize_tool is None:
            raise PermissionError("policy layer unavailable")
        decision = authorize_tool("houdini_build_hip", "mutate", approval)
        if not decision.get("allowed"):
            raise PermissionError(decision.get("reason", "policy denied build"))
        src = _confine(source)
        if not src.is_file():
            raise FileNotFoundError(src)
        hython = Path(HYTHON_EXE)
        if not hython.is_file():
            raise FileNotFoundError(f"hython not found at {HYTHON_EXE}; set HOUDINI_HYTHON_EXE")
        cooker = PROJECT_ROOT / "Tools" / "Houdini" / "cook_hip.py"
        if not cooker.is_file():
            raise FileNotFoundError(f"cooker script missing: {cooker}")
        dst = _confine(buildpath) if buildpath else SETUPS_DIR / src.stem / "build"
        dst.mkdir(parents=True, exist_ok=True)
        proc = subprocess.run(
            [str(hython), str(cooker), "--hip", str(src), "--buildpath", str(dst)],
            capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=1800,
        )
        produced = [p.name for p in dst.glob("*") if p.is_file()]
        return {
            "exit": proc.returncode,
            "stdout_tail": proc.stdout[-1200:] if proc.stdout else "",
            "stderr_tail": proc.stderr[-800:] if proc.stderr else "",
            "produced": produced,
            "buildpath": str(dst.resolve()),
            "policy": decision,
        }

if __name__ == "__main__":
    if mcp is None:  # pragma: no cover
        raise SystemExit("mcp SDK not importable; cannot start houdini server")
    mcp.run()
