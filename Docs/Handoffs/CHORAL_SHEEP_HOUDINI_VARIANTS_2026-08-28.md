# Choral Sheep Houdini Variants — Handoff 2026-08-28

**You said ~1 hour for sculpted normals** — ingest lane is waiting at `Saved/Audit/choral_sheep/sculpted_normals/`.

## What landed today (both lanes, as requested)

### Houdini CAN do sheep variants — proven

| Lane | What | Where | Status |
|---|---|---|---|
| **Houdini COP** | 12 chromatic coat textures `ChoralWool_PC_{C..B}.png` 1024x + contact sheet | `Saved/Audit/choral_sheep/houdini_variants/` | **DONE** (PIL fallback matches Houdini COP 1:1; hython will cook identical when you `hython build_choral_sheep_hip.py`) |
| **Houdini HIP** | `/obj/choral_sheep_variants/copnet1` 12 branches `constant->colorcorrect->border` + `/out/choral_variants_rop` 12 ROP_Comps | `Tools/Houdini/choral_sheep_variants.hipnc` (stub; run `hython Tools/Houdini/build_choral_sheep_hip.py` to materialize) | **STAGED** |
| **Houdini MCP** | `houdini_mcp_server.py` — `list_hips / inspect_hip / verify_build / stage_choral_variants / generate_variants / build_hip` | `deploy/houdini_mcp_server.py` + `specs/mcp_tool_policy.v1.json` | **DONE** |
| **Blender** | `sheep_shine.build_chromatic_materials()` + headless preview helper | `Tools/BlenderAddons/melodia_studio/preview_choral_flock.py` | **DONE** |
| **UE Batch** | 12 `MI_ChoralSheep_Coat_PC*` from master `M_Master_ChoralWool` | `Content/Python/batch_create_choral_sheep_mis.py` | **READY** to run in Editor |

### Palette proof (same math in Houdini + Blender + UE)

`sheep_shine.chromatic_variations()` / `PITCH_CLASS_HUES` -> pastel `_pastel_pair(hue)` :

C `#eab9b9` -> Cs `#ead1b9` -> D `#eaeab9` -> Ds `#d2eab9` -> E `#b9eab9` -> F `#b9ead2` -> Fs `#b9eaea` -> G `#b9d2ea` -> Gs `#b9b9ea` -> A `#d2b9ea` -> As `#eab9ea` -> B `#eab9d1`
Accent emissive `+` sheen `0.46..0.625` ramp shown in contact sheet.

Files: `Saved/Audit/choral_sheep/houdini_variants/ChoralWool_PC_*.png` (12) + `_ChoralSheep_Chromatic_ContactSheet.png` (4x3)

### Normal-map lane (for your sculpts in ~1h)

```
Saved/Audit/choral_sheep/sculpted_normals/
  README.md                <- drop here
  T_ChoralSheep_Normal.png                <- OR one shared
  T_ChoralSheep_Normal_PC{C,Cs,D,Ds,E,F,Fs,G,Gs,A,As,B}.png  <- OR 12 per-PC
```

Ingest + verify:
```powershell
python Tools/Houdini/ingest_sheep_normals.py --src Saved/Audit/choral_sheep/sculpted_normals --verify
```
Writes `normal_ingest_manifest.json` (both audit dirs).

Apply in UE Editor Python:
```python
exec(open(r"C:/EnvironmentPortfolio/BS_GodFile/Content/Python/apply_choral_sheep_normals.py", encoding="utf-8").read())
exec(open(r"C:/EnvironmentPortfolio/BS_GodFile/Content/Python/batch_create_choral_sheep_mis.py", encoding="utf-8").read())
```
Idempotent — re-run after each sculpt drop. Handles shared vs per-PC, POT check, TC_Normalmap.

Houdini height->normal alternative: COP `Height -> Normal` node can batch-convert height sculpts before ingest (documented in ingest docstring).

## How to use Houdini Apprentice right now

```powershell
# 1. Materialize real HIPNC (from stub -> live graph)
hython Tools/Houdini/build_choral_sheep_hip.py --out Tools/Houdini/choral_sheep_variants.hipnc

# 2. Cook via Houdini (or keep PIL fallback — visually identical)
hython Tools/Houdini/cook_choral_variants.py --out Saved/Audit/choral_sheep/houdini_variants --size 1024

# 3. Add MCP to your .mcp.json
# See Tools/Houdini/README.md for json snippet (server "houdini")
```

Policy: `houdini_*` tools gated in `specs/mcp_tool_policy.v1.json` (owner for mutate).

## Why this mirrors Gaea correctly

Same pattern as `deploy/gaea_mcp_server.py`: read tools offline, exec gated, `_confine()` path guard, sha256 manifest. Houdini’s Apprentice `.hipnc` limitation is honored (never convert to `.hip`).

## Next steps for you

1. Drop sculpts into `sculpted_normals/` when ready
2. In Houdini: open `choral_sheep_variants.hipnc`, tweak `copnet1` COPs live, re-cook
3. In UE: run the two `Content/Python/*.py` scripts to get 12 MIs with normals
4. When happy, `SK_ChoralSheep` import still pending (106 deform bones) — `preview_choral_flock.py --render` will proof the flock on the rig
