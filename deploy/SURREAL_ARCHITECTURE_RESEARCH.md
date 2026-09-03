# Surreal Architecture — Research & Overhaul Notes

**Version:** 2.75.0  
**Deploy:** `deploy/surreal_architecture_gen.py` + `deploy/surreal_arch/` + `deploy/surreal_greybox/` + `deploy/surreal_os/`  
**Live:** copy all four to Blender 5.1 `scripts/addons/`

## v2.75 — Surreal Architecture OS (Zen pilot)

| Layer | Module | Notes |
|-------|--------|-------|
| Style Genome | `surreal_os/genome.py` | `zen_shrine_v1` — floats, sacred_sequence, default_graph |
| Atoms | `surreal_os/schema/architectural_atoms.yaml` | Kit ↔ trim/snap contracts for all `GB_ZEN_*` |
| Grammar | `surreal_os/grammar/zen_shrine_axis.yaml` | `ZEN_SHRINE_AXIS` graph (torii → sando → kairo → karesansui) |
| Rules | `surreal_os/rules_engine.py` | snap_compat, compose_roles, surreal transforms |
| Taxonomy | `surreal_os/schema/procedural_taxonomy.yaml` | Generator I/O contracts + verify tier |
| UI | `surreal_arch/os_ops.py` | Level Design panel — Apply Genome, Spawn Graph |

### Human research (repo root)

Structured studies live under [`research/`](../research/README.md) — deploy docs no longer duplicate long glossaries:

| Study | Path |
|-------|------|
| Roji sequence | `research/zen/01_roji_sequence.md` |
| Shrine axis | `research/zen/02_shrine_axis.md` |
| Karesansui grammar | `research/zen/03_karesansui_grammar.md` |
| Surreal transforms | `research/surreal/01_non_euclidean_transforms.md` |

### New kits (v2.74)

| Type | Module | Atom |
|------|--------|------|
| `GB_ZEN_SANDO` | `zen_kit.py` | `sando_approach` |
| `GB_ZEN_KAIRO` | `zen_kit.py` | `kairo_cloister` |

### New room graph (OS grammar)

| Graph | Composition |
|-------|-------------|
| `ZEN_SHRINE_AXIS` | Torii → sando ×2 → kairo → karesansui → machiai → lantern |

## v2.73 — Sakura path kits

| Type | Notes |
|------|-------|
| `GB_ZEN_STONE_BRIDGE` | Arched deck + bank snaps |
| `GB_ZEN_CHERRY_ALLEE` | Blossom canopy path |
| `GB_ZEN_WATER_EDGE` | Stream bank + bridge landing |
| `ZEN_SAKURA_WALK` | Graph chaining sakura modules |

## v2.66 — UE trim pipeline + kit registration

| Feature | Module | Notes |
|---------|--------|-------|
| Trim vertex bake | `surreal_arch/trim_bake.py` | `trim_id` vertex color + face attribute for UE material assignment |
| Kit registration API | `surreal_arch/kit_registration.py` | `register_kit(monolith, arch_id, builder, snap_fn=...)` |
| Greybox extract | `surreal_greybox/primitives.py` | `_gb_box`, `_gb_join`, `_gb_bool_diff` bound at register |

## Trim group convention (UE)

Trim metadata on `obj['surreal_trim_groups']` maps to vertex color `trim_id` layer on bake.

Export sidecar JSON via **Export Snap JSON** or automatically on **Bake & Export UE5** includes snaps + trim_groups + `ue_export_hints`.

## Verify

```text
powershell deploy/run_verify.ps1 -Mode all
```

Tiers: `overhaul`, `world`, `os` (Style Genome, grammar, atoms, taxonomy).
