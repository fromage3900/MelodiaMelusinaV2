# Untracked File Triage — 2026-08-28

**Author:** Melusina (Hermes agent, z-ai/glm-5.2)
**Date:** 2026-08-28
**Status:** Complete — based on live git status

---

## Summary

| Category | Count | Action |
|----------|-------|--------|
| SAFE_TO_ADD (committed this session) | 21 | Already committed in 4 commits |
| SAFE_TO_ADD (remaining) | ~15 | Ready to commit — docs, Python tools, Source |
| EDITOR_BOUND | ~40 | Leave untracked — .uasset, .fbx, .png, .umap |
| JUNK | 0 | None found — zero-byte root files already cleaned |

---

## Already Committed This Session (4 commits)

| Commit | Files | Content |
|--------|-------|---------|
| `92af496b` | 5 | Crash fix + profiler traces + MelodiaShader wiring |
| `47eb208a` | 16 | Docs, config, Python tools, task ledger |
| `1dd37870` | 13 | Fixtures manifest + model entries |
| `7b00aa81` | 9 | MelodiaShader module source (6 .ush + .h + .cpp + .Build.cs) |

**Total: 43 files committed**

---

## Remaining Modified Tracked Files (editor-bound — do NOT commit)

These 5 modified .uasset files are editor-managed. They should be committed only after a clean editor session verifies them:

| File | Size | Modified |
|------|------|----------|
| Content/EnvSandbox/Materials/Instances/Atlantis/MI_TerracottaTileB.uasset | — | Yes |
| Content/EnvSandbox/Materials/Instances/Landscape/MI_Landscape_CliffGrass.uasset | — | Yes |
| Content/EnvSandbox/Materials/Instances/Landscape/MI_Landscape_CoastalCliff.uasset | — | Yes |
| Content/Melodia/Characters/Melusina/ABP_Melusina_Current.uasset | 680KB | Yes |
| Content/Melodia/Characters/Melusina/Hair/ABP_Melusina_WaterHair.uasset | — | Yes |

**Recommendation:** Leave these uncommitted. They are editor state. Committing them without a clean editor save risks saving inconsistent state. The editor should be opened, these assets should be saved cleanly, and then they can be committed.

---

## Untracked Files — Categorized

### SAFE_TO_ADD (source, docs, Python — should be tracked)

| File | Category | Notes |
|------|----------|-------|
| Content/Python/Tests/test_sea_above_t3d_contract.py | Test | New contract test |
| Content/Python/_test_headless_hello.py | Test | Headless test stub |
| Content/Python/apply_choral_sheep_grooms.py | Tool | Choral sheep grooming |
| Content/Python/apply_choral_sheep_normals.py | Tool | Choral sheep normals |
| Content/Python/author_musical_dream_mis.py | Tool | Musical dream material instances |
| Content/Python/batch_create_choral_sheep_mis.py | Tool | Batch choral sheep MIs |
| Content/Python/bind_ppv_audio_contract.py | Tool | PPV audio contract binding |
| Content/Python/build_musical_dream_kit.py | Tool | Musical dream kit builder |
| Content/Python/build_pcg_hero_orbital_rings.py | Tool | PCG hero orbital rings |
| Content/Python/create_hda_arpeggio_stair.py | Tool | HDA arpeggio stair |
| Content/Python/create_hda_space_orbital_rings.py | Tool | HDA space orbital rings |
| Content/Python/finalize_ppv_for_shipping.py | Tool | PPV finalization |
| Content/Python/finalize_ppv_hero_stack.py | Tool | PPV hero stack |
| Content/Python/fix_ppv_drift_refs.py | Tool | PPV drift fix |
| Content/Python/import_sculpted_choral_sheep.py | Tool | Choral sheep import |
| Content/Python/musical_dream_kit_spec.json | Spec | Musical dream kit spec |
| Content/Python/prune_ppv_dead_levels.py | Tool | PPV dead level pruning |
| Content/Python/setup_pcg_hero_orbital_rings_level.py | Tool | PCG hero level setup |
| Content/Python/smoke_houdini_engine_pcg.py | Tool | Houdini engine smoke test |
| Content/Python/stage_seaabove_mesh_terrain_candidate.py | Tool | Sea above terrain staging |
| Content/Python/stage_seaabove_slice.py | Tool | Sea above slice |
| Content/Python/strip_ppv_color_overrides.py | Tool | PPV color strip |
| Content/Python/musical_dream_kit_spec.uasset | EDITOR_BOUND | Actually a .uasset — leave untracked |
| Docs/Handoffs/CHORAL_SHEEP_GROOM_VARIANTS_2026-08-28.md | Doc | Choral sheep groom doc |
| Docs/Handoffs/CHORAL_SHEEP_HOUDINI_VARIANTS_2026-08-28.md | Doc | Choral sheep Houdini doc |
| Docs/Handoffs/CHORAL_SHEEP_WOOL_LAB_REVIEW_2026-08-28.md | Doc | Choral sheep wool lab |
| Docs/Handoffs/OVERNIGHT_HOUDINI_LEARN_LOOP_2026-08-28.md | Doc | Overnight Houdini loop |
| Docs/Handoffs/SESSION_REVIEW_ALL_FINDINGS_2026-08-28.md | Doc | Session review (from earlier) |
| Docs/Handoffs/UNIFIED_PPV_OCEANOLOGY_LOOKDEV_PLAN_2026-08-28.md | Doc | Unified PPV plan |
| Docs/P0_CLOSEOUT_PLAN_2026-08-28.md | Doc | P0 closeout plan |
| Docs/WorldGen/HOUDINI_ENGINE_SMOKE_SPEC_2026-08-27.md | Doc | Houdini smoke spec |
| Docs/WorldGen/WARDROBE_ORBITAL_GATE_SPEC_2026-08-27.md | Doc | Wardrobe orbital gate |
| Source/MelodiaShader/ | Source | ALREADY COMMITTED in `7b00aa81` |
| Tools/BlenderAddons/melodia_studio/preview_choral_flock.py | Tool | Blender addon |
| deploy/houdini_mcp_server.py | Deploy | Houdini MCP server |
| generated/zentrim_contact_sheet.png | Generated | Contact sheet |
| hda/ | HDA | Houdini Digital Assets |
| Plugins/HoudiniEngine/ | Plugin | Houdini Engine plugin |

### EDITOR_BOUND (leave untracked — .uasset, .fbx, .png)

These are all the ChoralSheep art assets and any .uasset/.fbx/.png:

- Content/Melodia/Companions/ChoralSheep/*.fbx (5 files)
- Content/Melodia/Companions/ChoralSheep/*.uasset (8 files)
- Content/Melodia/Companions/ChoralSheep/*.png (5 files)
- Content/Melodia/Companions/ChoralSheep/*.assbin (1 file)
- Content/Python/musical_dream_kit_spec.uasset (1 file — actually a .uasset despite .json name pattern)

The .gitignore already has `!Content/Melodia/Companions/ChoralSheep/` and `!Content/Melodia/Companions/ChoralSheep/**` — these are intentionally untracked art assets.

### JUNK

None found. The zero-byte root files (Checking, Installing, Set, uv) from the earlier session have been cleaned up.

---

## .gitignore Coverage

The .gitignore correctly:
- Ignores `Binaries/`, `DerivedDataCache/`, `Intermediate/`, `Saved/` (UE transient)
- Ignores `.bundle`, `Saved/Backups/`, `.git.backup/`
- Ignores `.ai/`, `.claude/*` (but re-includes `.claude/skills/`, `.claude/commands/`, `.claude/agents/`)
- Re-includes `Content/Melodia/Companions/ChoralSheep/` explicitly

**Missing from .gitignore:** Nothing critical. The `generated/` and `hda/` directories are untracked but not in .gitignore — if they should be ignored, add them. Otherwise they're fine as untracked.

---

## Recommended Next Actions

1. **Commit SAFE_TO_ADD files** — the docs and Python tools are ready to track
2. **Leave EDITOR_BOUND files** — they're editor state, commit after clean editor save
3. **No junk to clean** — already done
4. **Consider adding `generated/` and `hda/` to .gitignore** if they're transient
