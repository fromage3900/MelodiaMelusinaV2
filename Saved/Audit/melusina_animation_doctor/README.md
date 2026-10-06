# Melusina Animation Doctor — staging area index (2026-10-06 college session)

Status lives in `CURRENT_STATE.md` (repo root). This folder holds the day's
working evidence. Nothing here is production; `STAGING_ONLY` throughout.

## Run it (any python3, read-only)
`python Content/Python/melusina_animation_doctor.py [--trend] [--compare OLD NEW]`
Reports land here as `doctor_report_*.json` (schema v1→v2 inside).

## Pipeline scripts (keep at top level)
| Script | Does |
|---|---|
| `audit_shirt_weights.py` | Shirt capture audit (KineFX interleave parse) |
| `fix_shirt_weights.py` | Leg→torso remap + top-4 + renormalize + clearance + winding audit |
| `verify_shirtfix.py` / `verify_lab_hip.py` | Independent re-reads of staged outputs |
| `repoint_lab_hip.py` | Repoint staged lab hips at real sources |
| `verify_groomhip.py` / `prove_groom.py` | Groom hip verification |
| `render_prove.py` | Headless-GL prove-out (keep working before changing render path) |
| `render_one.py` / `render_dress.py` | Single-angle turntable frames (one process per angle — Vulkan) |
| `render_turntable.py` / `render_loop.py` / `render_final.py` / `render_iso.py` / `render_plain.py` / `render_bisect.py` | Turntable iterations (superseded; kept for provenance) |
| `assemble_sheet.py` / `assemble_dress_sheet.py` | PIL contact sheets (needs hython, not UE python) |

## Evidence dirs (DO NOT rename — referenced by manifests/doctor/docs)
- `rig/` — `rig_manifest_{melusina,sheep,shorewake_dress}.json`
- `shirt_fix/` — fixed `.bgeo`, weight deltas, manifests
- `turntable/` — `shirt_fix_*.png`, `dress_*.png`, contact sheets
- `stage_*.log` — per-run process logs
- `probes/` — 30 one-off diagnostics (superseded questions, kept for method)

## Naming for next time
- Reports: `doctor_report_YYYYMMDD_<topic>.json`
- Manifests: `<thing>_manifest.json` with a `schema` key + `status`
- One process per render; explicit group names (never `@attr` patterns);
  SHOP colors via `basecolorr/g/b`; filmboxfbx can't round-trip SOP skin.
