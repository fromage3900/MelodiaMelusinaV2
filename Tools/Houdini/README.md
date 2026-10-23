# Houdini Apprentice Lane — BS_GodFile

> **READ FIRST — long-term reference:** `Docs/Production/HOUDINI_CREATIVE_PIPELINE_REFERENCE_2026-08-28.md`
> — verified environment facts (hython 22.0.368, Apprentice export restrictions: FBX and Alembic
> ROPs are BLOCKED; File-SOP write mode is the geometry path), proven code patterns, and the
> evidence workflow for all Houdini creative work.
>
> **Corrections to this README (2026-08-28):** installed Houdini is **22.0.368** (not 20.5 —
> the MCP env path below is stale); Apprentice **cannot export Alembic via ROP**, so the groom
> claim below ("grooms export as `.abc`") has never actually cooked — real-ABC groom work needs
> Core/Indie, or strands baked to meshes/cards via the File-SOP path. The overnight learn loop
> ran in demo mode only. The newest lane lives in `Tools/Houdini/sea_above_reef/` (textures +
> meshes, all proven and manifest-backed).

Houdini Apprentice 20.5+ is live on this workstation. This lane mirrors the Gaea MCP pattern but for Houdini.

## Quick start

```powershell
# 1. Build the choral sheep HIP (inside Houdini or via hython)
hython Tools/Houdini/build_choral_sheep_hip.py --out Tools/Houdini/choral_sheep_variants.hipnc

# 2. Stage 12 chromatic variants (creates recipe + COP params)
python -m deploy.houdini_mcp_server  # or via MCP: houdini_stage_choral_variants

# 3. Generate PNGs — tries hython COP cook, falls back to PIL
python Tools/Houdini/generate_choral_variants.py --size 1024
# -> Saved/Audit/choral_sheep/houdini_variants/ChoralWool_PC_*.png + contact sheet

# 4. When sculpted normals arrive (you said ~1h):
python Tools/Houdini/ingest_sheep_normals.py --src Saved/Audit/choral_sheep/sculpted_normals/ --verify
# UE import:
# In Editor Python: exec(open("Content/Python/apply_choral_sheep_normals.py").read())
```

## Files

| File | Role |
|---|---|
| `build_choral_sheep_hip.py` | `hou` script — builds `/obj/choral_sheep_variants/copnet1` with 12 pastel COPs + `/out/choral_variants_rop` |
| `cook_choral_variants.py` | hython cooker — iterates PC 0..11, sets COP hue, cooks ROP |
| `cook_hip.py` | generic HIP ROP cooker used by MCP `build_hip` |
| `generate_choral_variants.py` | standalone PIL fallback (matches Houdini output 1:1, no Houdini required) |
| `ingest_sheep_normals.py` | validates + renames sculpted normal maps into ingest dir, prepares UE import manifest |
| `choral_sheep_variants.hipnc` | generated HIPNC (Apprentice, never convert to .hip) |

## Why Houdini CAN do sheep variants

- **COPs**: one COPnet drives 12 hue-shifted coat textures off a single wool base — same `_pastel_pair()` math as `sheep_shine.py`, but GPU-cooked 2K in seconds.
- **Groom**: `Guide Groom SOP + Hair Generate` — 12 groom variations via attribute-driven `wool_clump_scale`, `density`, `curl` per PC. Apprentice grooms export as `.abc` / cards.
- **Karma/ROP**: contact sheet + per-variant `ROP Composite Output` bakes straight to `Saved/Audit/...`
- **VEX**: bell emissive pulse = `chramp` over `pitch_class` for Resonant World call-response.

Normal maps you sculpt in the next hour slot into `Saved/Audit/choral_sheep/sculpted_normals/` as either one shared `T_ChoralSheep_Normal.png` or 12 per-PC `T_ChoralSheep_Normal_PC{C...B}.png` — ingest script handles both and wires `MI_ChoralSheep_Coat_PC*` Normal slots in UE.

## MCP registration

Add to `.mcp.json` (or global `~/.config/Code/User/mcp.json`):

```json
"houdini": {
  "command": "python",
  "args": ["C:/EnvironmentPortfolio/BS_GodFile/deploy/houdini_mcp_server.py"],
  "env": {
    "HOUDINI_HYTHON_EXE": "C:/Program Files/Side Effects Software/Houdini 20.5/bin/hython.exe",
    "HOUDINI_PROJECT_ROOT": "C:/EnvironmentPortfolio/BS_GodFile"
  }
}
```

Policy gated via `specs/mcp_tool_policy.v1.json` — `houdini_*` tools.
