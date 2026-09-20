# Materials clean-loop fold-in — 2026-09-17 ~5:48pm ET

Source: New Bot `MATERIALS_CLEAN_LOOP_2026-09-17_1745` (read-only on fromage Monolith 0.20.3; box :9316 down). Full receipt: `C:\EnvironmentPortfolio\BS_GodFile\Saved\Audit\MATERIALS_CLEAN_LOOP_2026-09-17_1745.md`.

## Deltas vs 2:52pm fold-in
- Dirty packages: **19** (was 0 post-crash earlier) → **owner Ctrl+S**
- Nikki master: **0 hard** (cleared; was 1 hard at 2:52pm) / 152 warn
- SDF Enhanced: still **2 hard** QUARANTINE
- HeightBlend Toon parent `M_Master_Toon_Landscape_HeightBlend`: **27** MIs (matches 2:52pm; morning 35 still needs LABEL_MAP reconcile; #158 owns)
- Melodia Flipbook master **EXISTS**: sheep BeatStar → `/Game/Melodia/_PROJECT/VFX/Materials/M_Niagara_MelodiaFlipbook` (afternoon "MISSING" is stale)
- WoolMote → Melodia `MI_Niagara_Melodia_Static_Glint`; that MI still depends_on Content `M_Niagara_MelodiaFlipbook` → Content Static_Glint = DUPLICATE candidate
- Stubs live at `/Game/Melodia/Materials/Lookdev/MI_Melodia_Stub_Toon` + `Stub_Fabric`
- 12 Copernicus Melodia* tex folders still lack MI hints (AmethystVein, AuroraGlass, ForestEmerald, GoldSilk, Moonlace, MotherPearl, SapphireGlass, MoonlitMoss, PrismaticObsidian, RoyalVelvetBrocade, SingingDune, WeepingWillow)
- No mutations

## Ask Melodia study bot
1. Fold Nikki hard→0 into leftover/#158 docs
2. LABEL_MAP: HeightBlend 27; Enhanced QUARANTINE; Melodia Flipbook SHIP provisional; Content VFX Static_Glint/Flipbook twin DUPLICATE once Melodia Static_Glint drops Content depends_on
3. Any other docs/PR fold-ins? New Bot will not steal #158 Nikki leftover ownership
