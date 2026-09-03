# Environment Material Layout Contract (2026-08-14)

This is the folder/naming contract for the EnvSandbox material system. It exists so the
500+ instance library stays maintainable long-term. Trust this over older docs where they
conflict.

## Folder map (live)

```
EnvSandbox/Materials/
├── Masters/                    # PRODUCTION masters only (62 after 2026-08-14 reorg)
│   ├── M_Master_Toon_Universal         (the big generalist)
│   ├── M_Master_Toon_Landscape_HeightBlend
│   ├── M_Master_Nikki / M_Master_Nikki_Landscape
│   ├── M_Water_Master_Grand_v10_Upgrade
│   ├── M_Master_Toon_Character
│   ├── M_Master_Impressionist_Toon (+_Landscape)
│   └── SDF/                    # experimental SDF family (53 masters, redirector-safe)
├── Functions/                  # canonical MF_* only; retired MFs move to _Scratch
├── Instances/
│   ├── Environment/            # per-family curated instances
│   │   ├── FlatColors/         # shared flat-tint family (MI_Flat_<material>)
│   │   ├── Zen/  Sakura?       # curated sets (Zen, Stylized, Magical, Baroque, Triplanar, Cathedral, House, World, Cinematic, Escher)
│   │   ├── ImportedPacks/      # pack-level shared MIs (MI_Env_<Pack>)
│   │   ├── RetroTextures/      # Kenney RetroTexturesFantasy materialized kit (117)
│   │   ├── PatternsExtra/      # Kenney PatternPackExtra materialized kit (84)
│   │   └── _Library/           # (reserved) bulk materialized pack kits
│   ├── Landscape/  Water/  Foliage/  Character/  Melusina/  Showcase/
│   ├── NikkiHero/  NikkiIntegrated/
│   └── _Legacy/                # (reserved) owner-triage orphans
├── SDF/                        # SDF family: Instances/ (173) + Textures/ (106)
├── ToonProfiles/               # TP_* toon profiles
├── PostProcess/  Niagara/  Landscape/  Impressionist/
├── _Scratch/                   # experiments, quarantine/backup masters, retired MFs
└── _Archive/                   # policy no-delete
```

## Naming rules

| Prefix | Kind | Example |
|---|---|---|
| `M_` | Master material | `M_Master_Toon_Universal` |
| `MI_` | Material instance | `MI_Flat_wood` |
| `MF_` | Material function | `MF_NikkiPastelGrade` |
| `T_` | Texture | `T_Box_Base` |
| `TP_` | Toon profile | `TP_Gold` |
| `MPC_` | Material parameter collection | `MPC_Portfolio_Palette` |

Instance short name = `MI_<Family>_<Look>` (family = folder or prefix).

## Who may write

- `Masters/` and `Functions/` — only via the Python builders (`setup_master_universal.py`,
  `expand_nikki_masters.py`, `setup_material_functions.py`), never hand-edited in a way that
  drifts from the script.
- `Instances/Environment/` — the routing scripts (`route_*`, `fix_*`, `assign_*`) and
  curated passes.
- `SDF/` — the SDF family scripts only.
- `_Scratch/` — anything experimental; never referenced by shipping meshes.
- `_Archive/` — no deletes, policy.

## Rules of thumb

1. A mesh slot must reference an instance that resolves: real maps, neutral maps, or flat
   tint — never the master's noise defaults (audit: `audit_layer_a_state.py`).
2. Every instance param must provably exist on its parent master (grounding rule).
3. Owner overrides are never clobbered (policy applicator `already_overridden` skip).
4. New pack imports materialize under `Instances/Environment/<Family>/` with the pack's
   own textures; shared instances are preferred over per-mesh duplicates.
5. `_Loose/` under `Meshes/Environment/` is NOT a routing location — distribute into
   `<prop>/Materials/` or shared instances.
6. Never `git clean` / `checkout -- .`; never `delete_asset` without zero-referencer proof
   and owner sign-off.

## Reorg history (2026-08-14)

- 53 experimental `M_SDF_*` masters → `Masters/SDF/` (redirector-safe, instances verified 0 broken parents).
- 10 landscape quarantine/work masters (`*_20260729`, `_BACKUP_`, `_QUARANTINE_`, …) → `_Scratch/`.
- `Masters/` root: 125 → 62 production assets.
- SDF instances: 0 broken parents post-move (verified by re-read).
