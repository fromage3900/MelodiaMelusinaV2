# Choral Sheep Houdini Groom — 12 Wool Variants — 2026-08-28

You said **yesss** — wired.

## What Houdini is now driving for the flock

**Base contract** (from `ChoralSheepDefinition.json`):
- `wool_clump_scale: 0.65` | `sheen_response: 0.45` | LODs `NativeGroom 0-400cm / ShellCard 400-1200cm / Impostor 1200cm+`
- Assets: `Groom_ChoralSheep_Wool_Hero` / `FurShell_ChoralSheep_Wool_Mid` / `FurCards_ChoralSheep_Wool_Far`
- Groom is **optional** — missing groom never blocks `SK_ChoralSheep` follow (`groom_policy`)

**Per-PC overrides** (`Tools/Houdini/choral_groom_variants_spec.json`):

| PC | Label | wool_clump_scale | clump_size | curl | density× | len | frizz |
|---|---|---|---|---|---|---|---|
|0|C|0.62|0.45|0.30|1.00|6.2|0.12|
|1|Cs|0.63|0.46|0.32|1.02|6.3|0.13|
|2|D|0.64|0.48|0.34|1.04|6.4|0.14|
|3|Ds|0.65|0.50|0.36|1.06|6.5|0.15|
|4|E|0.66|0.52|0.38|1.08|6.6|0.16|
|5|F|0.67|0.54|0.40|1.05|6.5|0.17|
|6|Fs|0.68|0.56|0.42|1.03|6.4|0.18|
|7|G|0.66|0.55|0.41|1.01|6.3|0.16|
|8|Gs|0.65|0.53|0.39|0.99|6.2|0.15|
|9|A|0.64|0.51|0.37|1.00|6.1|0.14|
|10|As|0.63|0.49|0.35|1.02|6.2|0.13|
|11|B|0.62|0.47|0.33|1.04|6.3|0.12|

Fs is the shaggiest/most curled wedding-cake sheep. C/B are tightest. All simulation-safe.

## Files

| Path | Role |
|---|---|
| `Tools/Houdini/choral_groom_variants_spec.json` | single source of truth for groom wedges + UE binding |
| `Tools/Houdini/build_choral_groom_hip.py` | builds `choral_sheep_groom.hipnc` — `/obj/choral_sheep_groom/guide_groom1` (scatter 120 → attribwrangle pc→clump) → `hair_generate1` (9000 strands) + wedge 12 + `/out/groom_abc_rop` |
| `Tools/Houdini/cook_groom_variants.py` | cooks wedges via hython; fallback writes `Groom_ChoralSheep_PC_{C..B}.abc` placeholders + `_Groom_ContactSheet.png` so pipeline validates without Houdini |
| `Tools/Houdini/ingest_grooms.py` | validates real ABC vs placeholder (Ogawa magic), writes `groom_ingest_manifest.json` |
| `Tools/Houdini/choral_sheep_groom.hipnc` | stub until you `hython build_choral_groom_hip.py` (Apprentice .hipnc only) |
| `Saved/Audit/choral_sheep/grooms/Groom_ChoralSheep_PC_{C..B}.abc` | 12 ABCs (placeholders now; real after hython cook) |
| `Saved/Audit/choral_sheep/grooms/_Groom_ContactSheet.png` | 4×3 wool preview (circle size = clump, arc = curl) |
| `Content/Python/apply_choral_sheep_grooms.py` | Editor Python — reports groom status, auto-imports real ABCs if present |
| `deploy/houdini_mcp_server.py` | + `stage_groom_variants` / `generate_grooms` tools |
| `specs/mcp_tool_policy.v1.json` | + `houdini_stage_groom_variants` / `houdini_generate_grooms` (owner) |

`Groom_ChoralSheep_PC_{label}.json` per variant also written alongside each ABC — carries the exact clump/curl/density for UE groom override or for re-cook.

## Try it now (no Houdini needed)

```powershell
python Tools/Houdini/cook_groom_variants.py --out Saved/Audit/choral_sheep/grooms
python Tools/Houdini/ingest_grooms.py --verify
# UE Editor Python (Reports placeholder vs real; never errors):
exec(open(r"C:/EnvironmentPortfolio/BS_GodFile/Content/Python/apply_choral_sheep_grooms.py", encoding="utf-8").read())
```

## For real strands (when you're back from sculpting)

```powershell
hython Tools/Houdini/build_choral_groom_hip.py --out Tools/Houdini/choral_sheep_groom.hipnc
hython Tools/Houdini/cook_groom_variants.py --out Saved/Audit/choral_sheep/grooms
python Tools/Houdini/ingest_grooms.py --verify
# UE will now see Ogawa ABCs; apply script auto-imports to /Game/Melodia/Companions/ChoralSheep/Grooms/
```

Grooms bind to `AMelodiaChoralSheepActor` GroomComponent — same pitch-class axis as the coat COP variants, so `PC_E` material + `PC_E` groom travel together. Missing groom still lets the sheep graze/harmonize/guide.

**Previous handoff** still valid for coat COPs + normals: `Docs/Handoffs/CHORAL_SHEEP_HOUDINI_VARIANTS_2026-08-28.md` (the 1024 PNGs are at `Saved/Audit/choral_sheep/houdini_variants/`).
