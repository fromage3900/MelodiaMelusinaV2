# Sol Work Package — Cosmic Orrery Corridors: Architecturally Sound Houdini + PCG

**To:** Sol (Houdini) · **From:** build lane, 2026-10-14 · **Status authority:** `CURRENT_STATE.md`
**Order (live Jev `jev-1.13.0`, all conf 1.0):** 1) foyer portal → 2) massing arrangement → 3) resonance readout.
While you author in Houdini, I keep the UE side (GameMode, nav, cymatics, materials, PIE proof).

## 1. Live state notes (measured today, UE 5.8, all cm)

- **Level:** `/Game/EnvSandbox/Environments/WP/L_WP_CosmicOrrery` · GameMode `BP_MelodiaJRPGGameMode` (canonical pawn possessed in PIE ✓) · navmesh covers full route 5/5 waypoints → deck Z=110 ✓ · RecastNavMesh + `HS1_Cathedral_NavMeshBounds` live.
- **PCG:** `PCG_SeaAbove_OceanCathedral`, 16 branches, **3,141 instances**, all spawners pack 1 custom float (`$Steepness` harmonic Resonance 0.22–0.98). `MelodiaCymatic` on 8 musical/cosmic/silk spawners (329 inst); floors STATIC. PCG ISM collision is live in PIE (blocking hits verified).
- **Blocker:** `SM_OceanCathedral_foyer` at (-1200,0,100) is **~50×32×35 m solid, X -6200..-1130, Y ±1600, Z 0..3568**. Hollow interior (pawn walked 4.7 m inside from the east), **west wall at X≈-6200 is solid** — nave/cloister/apse unreachable on foot (PIE sweep trace evidence). PlayerStart (-1350,0,212) sits *inside* the foyer.
- **Route chain (UE cm):** entrance -1650 → foyer center -3665 → **portal wall -6200** → nave axis (Y=0) → bridge row (Y=1310) → cloister courts (X -10600/-15000/-19400, Y ±5570) → apse orrery (-20984,0,100).
- **Orrery nodes (7):** 6 cloister courts above + grand apse hero at (-20984,0,100). `SM_OceanCathedral_orrery` = 13 m wide, collision complex-as-simple (walkable ✓).
- **Cymatic volumes cover their nodes** (bounds read live): NaveAndApse X -24500..-2500; North/South cloister boxes 6500×4500×600 at (-15000,±5570). Field owner: `UMelodiaCymaticFieldComponent` (Chladni standing wave + ripples, presentation-only).
- **Materials (all 9 MIs verified saved, clean Copernicus maps, Nikki palettes):**

| MI | Albedo map | Glow/InnerGlow | Rough/Metal |
|---|---|---|---|
| pearl_shell | PearlWeave | 0.52/0.38 | 0.18/0.05 |
| pearl_ruffle | SingingSilk | 0.58/0.42 | 0.20/0.02 |
| trim_gold | FarawayGildedRidge (+Height/Emissive) | 0.68/0.45 | 0.15/0.72 |
| sea_crystal | CrystalCathedral | 0.88/0.50 | 0.08/0.18 |
| crystal_glass | CrystalCathedral | 0.85/0.48 | 0.12/0.14 |
| rose_glass | FractalCathedral | 0.68/0.38 | 0.12/0.12 |
| floor_stone | ChoirStone | 0.45/0.35 | 0.18/0.04 |
| col_stone | ChoirStone | 0.42/0.34 | 0.18/0.04 |
| wall_plaster | FarawayCelestialSilk | 0.40/0.32 | 0.20/0.02 |

- **Module slots (keep stable):** nave crystal_glass/wall_plaster/trim_gold · rose rose_glass · bay col_stone/trim_gold/wall_plaster/crystal_glass · deck floor_stone/trim_gold · bridge floor_stone/trim_gold/crystal_glass/col_stone · pipe trim_gold/crystal_glass/col_stone · court floor_stone/trim_gold/crystal_glass · foyer (same as court) · orrery floor_stone/trim_gold/crystal_glass · shell pearl_shell/trim_gold/sea_crystal · ruffle pearl_ruffle/trim_gold/pearl_shell · crown crown_pearl/trim_gold/sea_crystal · ribbon ribbon_silk.
- **Conventions:** UE = (-HoudiniY,-HoudiniX,HoudiniZ)×100, q=(qy,qx,-qz,qw). Anchors carry `bay_index/story_index/wing_index/pitch_class/module_id/midi_note`. Reimport over existing mesh paths (`.../Modules_20261014/SM_OceanCathedral_*`); PCG regenerates unchanged. New branches = CreatePoints + StaticMeshSpawner pair wired to Output.
- **Hard bans:** Apprentice/EngineEducation license (in-editor Engine cooks blocked — export FBX, UE imports). Never touch `M_Master_Toon_Universal` or any `Config/`. `OUT_Collision` = architecture **minus** decoration (existing rule: vault prisms must not block a character — the foyer is exactly that defect class at building scale).

## 2. Escher research (repo-real, applicable)

- **Existing:** `Content/EnvSandbox/PCG/Styles/Escher/` (Belvedere, GravityShiftCorridor, PenroseLoop, RecursiveRoom, RelativityRoom) · `MI_Baroque_EscherOrnament`, `MI_Escher_ImpossibleTile`, `MI_Escher_Woodcut` · `M_SDF_Penrose_Staircase`, `M_SDF_EscherGeometry_Enhanced` · `SM_PENROSE1` · hero render H08/`11_TD_04` escher sanctuary.
- **Applicable item 1 — regular-division pavements (Escher's Alhambra source):** cloister court + apse floors in periodic tilings. Hexagonal `p6m`: regular hexagon side `s`, width `2s`, height `s√3`, area `(3√3/2)s²`; square `p4m` forbay fields. Gild the grout lines (trim_gold) — reads as sacred geometry, costs zero collision.
- **Applicable item 2 — hyperbolic medallion (Circle Limit source):** apse floor medallion as Poincaré-disk tiling `{7,3}` or `{8,3}` (need `1/p+1/q<1/2`). Hyperbolic distance `d` from center maps to Euclidean `r=tanh(d/2)` — ring bands compress toward the rim exactly like an orrery diagram. Optional flourish, floor-only.
- **Gameplay ban:** Belvedere/Penrose impossibility stays in materials/SDF, never in walkable geometry. Every stair must satisfy §3 stair math and every corridor the §4 chain widths, or PIE sweep rejects it.

## 3. Corridor plan v2

1. **Foyer west portal (first):** opening in wall plane **X=-6200**, centered **Y=0**, sill at local deck top (~Z 190–220, confirm in-editor against deck instances). Clear **700 wide**, springing **900 above sill**, **equilateral head r=700 → rise ≈606** (§3), total ≈1500. Wall thickness per measured mesh. Keep east face/doorway as-is (pawn entered cleanly). Fallback if the solid resists a clean portal: PCG-only bypass branch around the north/south flank with existing bridge/deck meshes (Jev runner-up, 0.28).
2. **Massing (second, PCG-only per Jev 0.55):** thin bay/deck/ruffle counts + vary per-point scale/rotation through authored ScaleBias; keep hero cadence (crown 16 / ribbon 8 / orrery 7) dominant. No new meshes.
3. **Resonance (third, UE-side, mine):** bind packed `$Steepness` to emissive pulse on sea_crystal/rose children.
4. **Proof standard (mine, after each drop):** editor ISM readback → swept PIE walk entrance→apse (assert Z≈deck, no blocking hit) → cymatic overlap check → 2560×1440 stills from the 3 HS1 cams.

## 4. Real-architecture math formulary (all units convertible; UE cm = m×100)

**A. Two-centered pointed arch (the Gothic module — replaces fractal-profile arches).**
Span `s`, chosen radius `r ≥ s/2`, centers on the springing line offset `a = r − s/2` each side. Rise above springing:
`h = √(r² − a²)`. Equilateral: `r = s` → `h = s√3/2 ≈ 0.866s`. Lancet example: `r = 1.5s` → `a = s`, `h ≈ 1.118s`.
Portal worked example: `s = 700`, equilateral → springing 900, head rise 606, total ≈ 1506.

**B. Vault bay (the actual Gothic solution — different arcs, one crown).**
Square bay `s×s`, crown height `H` fixed. Transverse arches span `s` (pointed per A). **Diagonal ribs** span `c = s√2` as *segmental* arcs: `R = (H² + (c/2)²) / (2H)`. Never force diagonals pointed — that is why real vaults work and fake ones look wrong.

**C. Proportion rules.** Aisle width ≈ `S/2` (S = nave span); bay length ≈ `S`; arcade opening ≈ 0.5–0.6 bay. Plan squares by *ad quadratum*: `s, s√2, 2s…`. Cloister courts stay **square**; reserve φ (1.618) for portal/panel rectangles, not courts.

**D. Rose window / orrery tracery (12-fold, Apostles number).**
Bars at `360°/12 = 30°`. `n` tangent foils on ring radius `Rc`: foil radius `r = Rc·sin(π/n)` (n=12 → `r ≈ 0.259Rc`). Chladni tie-in (precedent: existing rose used Chladni-(8,6) displacement): foil/petal count = `m+n` of the node's field mode — ornament *is* the local resonance diagram.

**E. Spiral stair (Blondel + winders).**
`2R + G ≈ 63` (R riser, G going at walkline, human scale; scale up only by explicit heroic factor). `N` steps/turn → winder angle `θ = 360°/N`; going at walkline radius `Rw`: `g = 2πRw/N`. Keep the existing spiral's story rhythm; apply Blondel to riser/going.

**F. Harmonic orrery rings (Kepler + music — the cosmic orrery's own math).**
Kepler III: `a ∝ T^(2/3)`. Periods in harmonic ratio `1:2:3:4` (fundamental + harmonics):

| ring | T ratio | a factor | a (a₀=6.5 m) | ω (rel) |
|---|---|---|---|---|
| 1 | 1 | 1.000 | 6.5 m | 1.000 |
| 2 | 2 | 1.587 | 10.3 m | 0.500 |
| 3 | 3 | 2.080 | 13.5 m | 0.333 |
| 4 | 4 | 2.520 | 16.4 m | 0.250 |

`a₀ = 6.5 m` = half the orrery module width; ring 4 lands inside the 55 m court. Alternative consonant stack (octaves): periods `1:2:4:8` → radii `1, 1.587, 2.520, 4.000`. Drive ring speeds at `ω = 2π/T`; consonant motion *is* the music made visible.

**G. Human anchors (already repo law, restated so Houdini honors them):** corridor 300 cm · clear height 240 cm · hall/processional 1200 cm. Portal 700 wide sits between corridor and hall — processional, not domestic.

## 5. Deliverables & acceptance

- Per module: versioned `.hipnc` + `.hdanc`, FBX re-exported over existing paths, anchors JSON with the §1 metadata fields, updated module JSON (points/prims/materials/anchors).
- Collision: `OUT_Collision` = architecture minus decoration; every corridor/portal/stair passes swept-capsule walk + nav projection (my PIE proof).
- No new masters, no new solvers, no license-gated cooks; machine-local paths stay gitignored until owner P4-promotes.
