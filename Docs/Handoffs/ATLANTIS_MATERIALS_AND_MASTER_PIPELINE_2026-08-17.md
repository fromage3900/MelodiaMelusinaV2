# Atlantis Materials + Master Pipeline Review — 2026-08-17

**Scope**: close-out of the Atlantis material ingest + status of the master-material pipeline, PPV dreamprint wiring, and loose ends. Read alongside `Docs/Atlantis_Ingest_Completion.md` and `Docs/Production/MATERIAL_MASTER_RECONCILIATION.md`.

---

## 1. Atlantis materials — SHIPPED (verified 2026-08-17)

| Step | Count | Evidence |
|---|---|---|
| Texture import (sRGB slot-aware) | 424/424 | `Saved/Audit/atlantis_texture_import.json` |
| Masked variant master (gated opacity) | `M_Master_Toon_Universal_Alpha` | `Saved/Audit/atlantis_opacity_master_wire.json` |
| MI authoring (+verify-by-reread) | 83/83 all_ok | `Saved/Audit/atlantis_mi_author.json` |
| Mesh resolve (prefix-strip match) | 333/333, 1213 slots, 0 unresolved | `Saved/Audit/atlantis_mesh_resolve.json` |

Key decisions worth preserving:

- **Water master correction**: canonical = `M_Water_Master_Grand_v10_Upgrade` (v6 is 6 versions old). `ingest_aaa_underwater_packs.py` `MASTER_WATER_GRAND` and `paths.py` `M_WATER` now point at v10_Upgrade.
- **Opacity path**: the OPAQUE Universal master cannot take opacity (Substrate BSDF has no opacity input), so the masked variant `M_Master_Toon_Universal_Alpha` (BLEND_MASKED + two_sided) carries the gated chain `bUseOpacityMap ? (OpacityMap × OpacityStrength) : 1.0 → MP_OPACITY_MASK` — the M_ToonFoliage route. Default-off, so 105+ existing instances are untouched.
- **Substrate quirk discovered**: masters report EMPTY `scalar_parameter_values`/`texture_parameter_values`/`static_switch_parameter_values`; parameter discovery must enumerate graph expressions. Scripts now do this (`expression_params`).
- **Switch read-back**: global overrides must be read with `MaterialParameterAssociation.GLOBAL_PARAMETER`, not LAYER_PARAMETER.
- **Crosswalk is 83 entries, not 85** (manifest is authoritative; all 83 have texture sets).

## 2. PPV dreamprint materials — wiring FIXED + VERIFIED

- Blendable restored to **After Tonemapping** (`fix_dreamprint_blendable.py`), grade `DREAMPRINT` block applied (`dreamprint_grade_upgrade.json` ok), 3 profile MIs parented, MetaSound `MSS_MelodiaMusicPulse` built 2026-08-16 17:48.
- `Saved/Audit/dreamprint_verify.json` reports `metasound_exists: false` — **stale**: the verify ran ~6 min before the MetaSound build; the build manifest (`dreamprint_metasound_build.json`, ok) supersedes it.
- Docs: `Docs/Handoffs/DREAMPRINT_STACK_BUILD_2026-08-16.md`, `Docs/Handoffs/PPV_STALE_CLEANUP_2026-08-17.md`.

### Owner actions remaining (GUI session)
1. Delete the **unlabeled** `PostProcessVolume` in `L_SakuraPath` and `L_Template` (the labeled `PPV_NikkiDream`/dreamprint volumes stay).
2. Spawn `PPV_NikkiDream` in `L_Template`: `Content/Python/setup_nikki_render_post_process.py --force`.
3. A/B the dreamprint look (PPV toggle) + approve; wire director/camera integration.

## 3. Loose ends inventory (checked 2026-08-17)

- **Stale v6 water references** (possibly current for legacy `MI_GrandWater_*` instances — NOT changed; verify before editing):
  - `Content/Python/audit_grand_water.py`, `audit_grand_water_aaa.py`, `expand_grand_water.py`
  - `material_family_manifest.py`, `material_family_manifest_full.py` (v6 lists)
  - `Docs/` water master tables
- **Editor boot fragility (machine)**: F: is a Seagate USB HDD ~53 GB free with 0.67 MB/s random reads — the DDC could not init there and the editor crash-looped. The one running editor now launches with `UE-LocalDataCachePath=G:\UE_DDC` (G: = ROG ESD-S1C USB SSD, 108.6 GB free; Zen cold start ~7 s). Keep this flag on future editor launches; F: needs free space or decommissioning.
- **Editor relaunched clean** after the crash-loop diagnosis: single editor, port 9316 open (rule: never trust a PID, verify the port).

## 4. Master pipeline — unfinished work inventory (for the next sessions)

### P0 (owner-call / risk)
- **Git tracking**: untracked water/Nikki masters + material functions + instances — decide tracking strategy (Content/ is untracked by design since f89fccd5; do not `git clean`/`checkout`).
- `extract_owner_instance_profiles.py` — written, never run.
- 59 zero-override maskers — owner decides keep/reparent.
- Stale T3D baselines in `Docs/T3D_Baseline/` — regenerate after any master edit.

### P1 (planned, needs owner approval before touching masters)
- Universal ↔ TriplanarPro parity pass.
- Universal overhaul Stages A–C (from reconciliation doc).
- Nikki BaseTint dedupe.
- SDF conversion track (M_Master_Toon_Universal SDF seams work).
- Water v11 — blocked on 9 gates documented in the water handoff.

### P2/P3
- Presentation pass, instance lockdown, DissonanceGore materials.

### Owner calls queued
- 773 `Textures_Shared` copies (dedupe/relink).
- 12 `_Scratch` zero-reference assets.
- 24 runtime duplicate instances.
- `material_family_manifest_full.py` capture run (audit data, not destructive).

## 5. Scripts created/updated (Content/Python)

| Script | Purpose |
|---|---|
| `probe_atlantis_material_surface.py`, `probe_atlantis_surface2.py` | Reflection probes (blend/BSDF/params) |
| `import_atlantis_textures.py` | 424-PNG import, slot-aware sRGB, dot-name sanitize |
| `fix_atlantis_refraction_srgb.py` | one-off sRGB fix for refraction_inverted |
| `wire_atlantis_opacity_master.py` | masked variant + gated opacity chain |
| `author_atlantis_mis.py` | 83 MI authoring, conventions, verify-by-reread |
| `resolve_atlantis_meshes.py` | 333-mesh slot resolution |
| `ingest_aaa_underwater_packs.py`, `paths.py` | water constant → v10_Upgrade |

## 6. Next steps

1. (Owner) visual smoke of Atlantis meshes in a level — opaque + masked sets.
2. (Owner) dreamprint A/B + PPV_NikkiDream spawn + stale PPV deletion.
3. (Agent) P0/P1 master work per reconciliation doc after owner approval.