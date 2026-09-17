# Twin cleanup — Static_Glint + MelodiaFlipbook — 2026-09-17

**Package:** A — Materials org  
**Machine:** fromage `6402dab1-6635-4abb-8220-27a07354b444`  
**Repo tip (owner):** `C:\EnvironmentPortfolio\BS_GodFile` (MelodiaMelusinaV2)  
**Stamp:** 2026-09-17 ~18:25 EDT (America/Toronto)  
**Mode:** Docs / org only. **No** Monolith `save_packages` / `recompile_material`. **No invented saves.**  
**Sources:** LABEL_MAP 2026-09-09 · MATERIALS_CLEAN_LOOP fold-in 1745 · MELODIA_CLOSEOUT_HANDOFF · offline WorldGrid/Flipbook receipt

## Decision (SHIP vs DUPLICATE)

| Role | Soft path | Label |
|------|-----------|-------|
| **SHIP (authority)** | `/Game/Melodia/_PROJECT/VFX/Materials/M_Niagara_MelodiaFlipbook` | **SHIP** |
| **SHIP (authority)** | `/Game/Melodia/_PROJECT/VFX/Materials/MI_Niagara_Melodia_Static_Glint` | **SHIP** |
| **DUPLICATE → redirect / archive** | `/Game/_PROJECT/VFX/Materials/M_Niagara_MelodiaFlipbook` | **DUPLICATE** |
| **DUPLICATE → redirect / archive** | `/Game/_PROJECT/VFX/Materials/MI_Niagara_Melodia_Static_Glint` | **DUPLICATE** |

**Rationale:** Melodia/_PROJECT is the production VFX root. Live 2026-09-17 17:45 fold-in confirmed Melodia Flipbook **EXISTS** and sheep BeatStar already parents there. Content `/_PROJECT` twins remain on disk/git as the old fork — label DUPLICATE and redirect remaining consumers before archive.

Disk / git note: Melodia Flipbook+Static_Glint are **on fromage disk** (live). Git `main` still lists the Content `/_PROJECT` twin set; Melodia VFX materials may be local-only / fat-branch until a Content PR (out of Package A scope — **do not push Content** from this docs lane).

## Inventory — exact soft paths

### Melodia/_PROJECT (SHIP tree)

| Asset | Soft path | Kind |
|-------|-----------|------|
| Flipbook master | `/Game/Melodia/_PROJECT/VFX/Materials/M_Niagara_MelodiaFlipbook` | Master |
| Static glint MI | `/Game/Melodia/_PROJECT/VFX/Materials/MI_Niagara_Melodia_Static_Glint` | MI |
| Companion textures (when present) | `/Game/Melodia/_PROJECT/VFX/Textures/` (e.g. `T_Alpha_diamond_glint_alpha`) | Texture |

### Content/_PROJECT (DUPLICATE tree)

| Asset | Soft path | Kind |
|-------|-----------|------|
| Flipbook master | `/Game/_PROJECT/VFX/Materials/M_Niagara_MelodiaFlipbook` | Master |
| Static glint MI | `/Game/_PROJECT/VFX/Materials/MI_Niagara_Melodia_Static_Glint` | MI |
| Related Content MIs (same parent family) | `/Game/_PROJECT/VFX/Materials/MI_Niagara_MelodiaFlipbook_Water` | MI |
| | `/Game/_PROJECT/VFX/Materials/MI_Niagara_Melodia_SplashFlip` | MI |
| | `/Game/_PROJECT/VFX/Materials/MI_Niagara_Melodia_Static_Arc` | MI |
| | `/Game/_PROJECT/VFX/Materials/MI_Niagara_Melodia_Static_Chaos` | MI |
| | `/Game/_PROJECT/VFX/Materials/MI_Niagara_Melodia_Static_DropletRing` | MI |
| | `/Game/_PROJECT/VFX/Materials/MI_Niagara_Melodia_Static_Dust` | MI |
| | `/Game/_PROJECT/VFX/Materials/MI_Niagara_Melodia_Static_GlobuleCluster` | MI |
| | `/Game/_PROJECT/VFX/Materials/MI_Niagara_Melodia_Static_Provider` | MI |
| | `/Game/_PROJECT/VFX/Materials/MI_Niagara_Melodia_Static_Ripple` | MI |
| | `/Game/_PROJECT/VFX/Materials/MI_Niagara_Melodia_Static_Sigil` | MI |
| | `/Game/_PROJECT/VFX/Materials/MI_Niagara_Melodia_Static_SplashBurst` | MI |
| | `/Game/_PROJECT/VFX/Materials/MI_Niagara_Melodia_Static_StarGold` | MI |
| | `/Game/_PROJECT/VFX/Materials/MI_Niagara_Melodia_Static_StateB` | MI |
| Twin textures | `/Game/_PROJECT/VFX/Textures/` | Texture |

Related Content Static_* MIs should eventually reparent to Melodia Flipbook SHIP (owner batch; not this stamp).

## Live parents that need retarget (do-not-save)

**Hard rule:** document intended retargets only. If Monolith is used, **read-only verify**. Owner **Ctrl+S** after any live retarget.

| Consumer | Current (last known) | Intended authority | Notes |
|----------|----------------------|--------------------|-------|
| `/Game/Melodia/Companions/ChoralSheep/VFX/MI_NS_ChoralSheep_WoolMote` | Melodia `MI_Niagara_Melodia_Static_Glint` (MI path) | Keep Melodia Static_Glint | Already on Melodia glint MI |
| Melodia `MI_Niagara_Melodia_Static_Glint` **parent** | Still **depends_on** Content `/Game/_PROJECT/VFX/Materials/M_Niagara_MelodiaFlipbook` (1745) | Reparent → Melodia `/Game/Melodia/_PROJECT/VFX/Materials/M_Niagara_MelodiaFlipbook` | **Primary twin break** |
| `/Game/Melodia/Companions/ChoralSheep/VFX/MI_NS_ChoralSheep_BeatStar` | Melodia `/Game/Melodia/_PROJECT/VFX/Materials/M_Niagara_MelodiaFlipbook` | Keep Melodia Flipbook | Already SHIP; verify FlipbookTexture/grid |
| Any other MI still parenting Content Flipbook / Content Static_Glint | Content `/_PROJECT/...` | Melodia `/_PROJECT/...` | Live Asset Registry search when Monolith up |
| Niagara systems using Content twin MIs | Content Static_* | Melodia Flipbook SHIP + Melodia textures | Fix A: material owns scrub; SubUV off |

### Sheep soft paths (for owner Ctrl+S after retarget)

- `/Game/Melodia/Companions/ChoralSheep/VFX/MI_NS_ChoralSheep_WoolMote`
- `/Game/Melodia/Companions/ChoralSheep/VFX/MI_NS_ChoralSheep_BeatStar`
- `/Game/Melodia/_PROJECT/VFX/Materials/MI_Niagara_Melodia_Static_Glint` (after parent drop off Content Flipbook)

## Redirect sequence (owner / later Content PR — not agents)

1. Live verify Melodia Flipbook + Static_Glint load (0 hard preferred).
2. Reparent Melodia Static_Glint off Content Flipbook → Melodia Flipbook.
3. Reparent any remaining Content-parented sheep / NS MIs → Melodia SHIP.
4. Owner **Ctrl+S** dirty packages only.
5. Fix Up Redirectors Melodia←Content twins; archive Content `/_PROJECT/VFX` Flipbook+Static_Glint (+ twin textures) in a dedicated Content PR.
6. Never cold-delete while soft refs remain.

## Do not

- Call Monolith `save_packages` / `recompile_material`.
- Invent Melodia saves if asset missing on a given machine tip — document intended path only.
- Push Content from this docs branch.
- Touch `cleanup/pbr-twin-landing-2026-09-10` tip for this work.

## Related

- `Docs/Materials/LABEL_MAP_2026-09-09.md` (DUPLICATE / SHIP rows)
- `Docs/Audits/PHASE_C_STAMP_2026-09-17.md`
- `Docs/VFX/MELODIA_CLOSEOUT_HANDOFF_2026-09-17.md` (PR #228)
- `Saved/Audit/PACKAGE_A_MATERIALS_ORG_2026-09-17.md`
