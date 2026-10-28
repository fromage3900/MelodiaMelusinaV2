# Environment Material Layout Contract (2026-08-14)

This is the folder/naming contract for the EnvSandbox material system. It exists so the
500+ instance library stays maintainable long-term. Trust this over older docs where they
conflict.

## Master spine canon (2026-10-28)

The six production masters are canon: `M_Master_Nikki_Landscape` (terrain), `M_Master_Nikki`
(fabric/character), `M_Master_Toon_Universal` (generalist), `M_Master_Toon_Character`
(Choral Sheep/presentation), `M_Water_Oceanology_Melodia` (single-layer water authority),
and `Masters/SDF/M_Master_SDF_Toon` (SDF toon lane — the subfolder copy only). Machine form:
`specs/materials/master_spine_canon.v1.json`; re-derivable census:
`Tools/masters_spine_census.py`; graph baselines:
`Docs/T3D_Baseline/materials/master_spine/*.graph.json`.

- **No parallel masters.** New looks are instances or new columns on a spine master; a new
  master needs a demonstrated blocker plus owner sign-off. (`M_Master_Impressionist_Toon`
  listed in the pre-reorg table below no longer loads and is NOT spine — do not reference it.)
- **Group canon.** Every parameter lives in exactly one numbered family ("NN | Name");
  shared spine 01–18 where present, appends >= 19 (fabric/landscape: 19 Extended Layers,
  20 Snow Layer, 21 Gaea Pipeline, 22 Rock Triplanar Detail, 23 Snow Coverage Detail,
  24 Snow Distance Field, 25 Landscape Cymatics, 26 Glitter Pile, 27 Atmosphere; fabric:
  19 Glitter Pile, 20 Gouache Wash, 21 Nikki SDF Iris, 22 Character Extensions, 23 Toon
  Ramp, 24 Audio & Cymatics), Toon_Universal appends 41–46, Character/Water/SDF carry
  fresh 01–13/24/26/… schemes. Ungrouped parameters on a spine master are a defect.
- **Identity rule.** Parameter identity is ParameterName + GUID: group renames are
  instance-safe (verified 2026-10-28 on MI_Poitou_Landscape_Nikki, MI_Melusina_Nikki_Hair,
  water + SDF instances). Stale `MELODIA_COLUMN:` comment prefixes are retired — headers
  read "NN | Name".
- **Mutating-batch law.** Backup duplicate first, save exact packages only, expression-count
  parity + clean recompile + zero new validation issues + instance-override smoke before
  claiming done. Receipts: `Saved/Audit/MastersSpine_20261028/`.

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
