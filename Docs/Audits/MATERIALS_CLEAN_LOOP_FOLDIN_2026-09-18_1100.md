# Materials clean-loop fold-in — 2026-09-18 ~11:00am ET

Source: New Bot standing routine `Melodia materials clean loop` (weekday 10:32).
Mode: **offline only** — no live validate / no MI mutations.

## Connectivity
- Box Monolith `http://127.0.0.1:9316`: **connection refused**
- Owner machine `fromage` (`6402dab1-6635-4abb-8220-27a07354b444`): **disconnected** (no MachineShell / no remote :9316)
- Hard rules honored: no `save_packages` / no `recompile_material`

## Deltas vs last live fold-in (2026-09-17 ~5:48pm ET)
Live Monolith sample **not run** this pass. Carry-forward from 1745 + overnight Toon reconvert memory:

| Item | Status |
|------|--------|
| Nikki landscape master / 9 MIs | Last live: **0 hard** / 152 warn — re-validate when Monolith up |
| `M_SDF_OrnamentLayer_Enhanced` | Still **QUARANTINE** (2 hard) — do not ship |
| HeightBlend Toon parent MIs | **27** — Melodia study bot **#158** owns; do not steal |
| Melodia Flipbook | SHIP provisional at `/Game/Melodia/_PROJECT/VFX/Materials/M_Niagara_MelodiaFlipbook` |
| Content `_PROJECT` VFX twins | **DUPLICATE** candidates (Static_Glint still depends_on Content Flipbook) |
| SurrealFabric | Master + 3 lookdev MIs exist (`M_SurrealFabric_Flipbook`); Normal/ORM still PearlWeave statics — atlas wire later |
| Stubs | `/Game/Melodia/Materials/Lookdev/MI_Melodia_Stub_Toon` + `Stub_Fabric` |
| Copernicus Melodia* folders without MI hints | **12** (AmethystVein, AuroraGlass, ForestEmerald, GoldSilk, Moonlace, MotherPearl, SapphireGlass, MoonlitMoss, PrismaticObsidian, RoyalVelvetBrocade, SingingDune, WeepingWillow) |
| TextureWeight=0 EnvSandbox MIs | Queue open — needs live set_instance_parameter when Monolith up |
| WorldGrid/None SM slots | Queue open → Stub_Toon / Stub_Fabric |

## Overnight / post-1745 lane (memory + PR #236 closeout)
- Megascans → Toon/Custom path: **237/237**
- Quixel leftovers: **2/2**
- Enchanted Vehicles: **73** Melodia MI wrappers on disk under `/Game/Melodia/Imported/EnchantedVehicles/`; mesh slots still stock `M_KB3D_ECV_*` (Monolith can't set asset material slots — **manual owner assign**)
- Brushify Floating Islands: **98** → Toon, **13** FX skipped, **0** fail
- Docs closeout merged **PR #236**; remote git clean; **~1000 local dirty UE assets** likely → **owner Ctrl+S**
- Receipt path (owner disk): `Saved/Audit/TOON_RECONVERT_CLOSEOUT_2026-09-17.md`

## Expanded deprecate / label share (for LABEL_MAP / clean-env)
Concrete paths for Melodia study bot fold-in (label only; no cold-delete):

### SHIP (authority — reaffirm)
- `/Game/EnvSandbox/Materials/Masters/M_Master_Nikki_Landscape`
- `/Game/EnvSandbox/Materials/Masters/M_Master_SDF_Toon`
- `/Game/EnvSandbox/Materials/Masters/M_Toon_SDF`
- `/Game/EnvSandbox/Materials/Masters/SDF/M_SDF_OrnamentLayer`
- `/Game/EnvSandbox/Materials/Masters/SDF/M_SDF_GildedFiligree`
- `/Game/Melodia/_PROJECT/VFX/Materials/M_Niagara_MelodiaFlipbook`
- `/Game/Melodia/_PROJECT/VFX/Materials/MI_Niagara_Melodia_Static_Glint`
- `/Game/Melodia/Materials/Masters/M_SurrealFabric_Flipbook`
- `/Game/Melodia/Materials/Lookdev/MI_Melodia_Stub_Toon`
- `/Game/Melodia/Materials/Lookdev/MI_Melodia_Stub_Fabric`
- `/Game/Melodia/Materials/Masters/M_Master_Toon_Universal` (Toon reconvert target)

### LEGACY
- `/Game/EnvSandbox/Materials/Masters/M_Master_Toon_Landscape_HeightBlend` (+ **27** MIs) — **#158**
- False ocean: `M_Water_Master_Grand_v7` / `v9` / `v10_*`, `MI_Water_v10_HeroFLIP`

### QUARANTINE
- `/Game/EnvSandbox/Materials/Masters/SDF/M_SDF_OrnamentLayer_Enhanced`

### DUPLICATE
- Keep Melodia/_PROJECT Flipbook + Static_Glint; archive `Content/_PROJECT/VFX/Materials/M_Niagara_MelodiaFlipbook` (+ twin Static_* family) once Melodia Static_Glint drops Content depends_on

### SCRATCH
- EnvSandbox `_Scratch` Nikki master; `MI_Orphan_*`; SeaAbove Box + DemoRoom `*_BS` packages

### Post-Toon follow-ups (not label steal)
- ECV mesh slots still stock `M_KB3D_ECV_*` → manual retarget to Melodia wrappers
- Brushify dirty packs → owner Ctrl+S
- KitBash Atlantis / BlingVol3 / Magician Library remain Study Melodia convergence queue (P0/P1 after Megascans/Brushify)

## Mutations this pass
**None** (Monolith down).

## Ask Melodia study bot
1. Ping: morning clean-loop pass plan was live Nikki/SDF/VFX validate + TextureWeight=0 / WorldGrid stub queue + Copernicus MI gaps — **blocked** on Monolith.
2. Fold Toon reconvert closeout (#236) + dirty Ctrl+S / ECV mesh-slot note into LABEL_MAP / clean-env docs if useful.
3. Any other docs/PR fold-ins needed? New Bot will **not** steal #158 Nikki leftover / HeightBlend ownership.
4. When fromage + Monolith are up, New Bot will resume live validate + safe MI param / stub assigns only.
