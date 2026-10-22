# MelodiaMelusina: Palette + M_Poitou_Master spec (Material Artist, v1 proposal)
Paper spec only. No Unreal assets were touched. Every value is a **proposal pending the reference board**.
Note: the contract names the master `M_MelusinaFrench_Master`; this spec calls it `M_Poitou_Master`. Treat these as the same asset and pick one name.

Research notes that drive the choices (from [S1]–[S3]):
- Walls: limestone rubble with a full lime render ("enduit plein") flush to the dressed quoins, in clear sand tone. Beige and écru inland, whiter on the coast. Smooth render bands frame the openings. [S1][S2]
- Roofs: low-pitch canal tiles ("tige de botte") made from local bri clay, in mixed ocre-rosé tones. The guide explicitly says to avoid dark tiles. Slate only on the costly bourgeois logis. [S1]
- Shutters: one colour per house. Vert d'eau / tender green is the cited traditional choice. Blue is iconic but, per the Inventaire, "not characteristic of the region". [S1][S2]
- Plinth: a darker base band (soubassement) is a real practice, so the damp waterline is grounded, not just a game effect. [S1]
- Ruin: Maillezais is a Romanesque west massif plus nave bays, with a Gothic remodel of the last 3 of 7 bays, on a Jurassic limestone island. [S3]

## 5. Palette slots (FILLED: Material Artist proposal v1, PENDING REFERENCE BOARD)
> Every value below is a **proposal**. Hex values are sRGB albedo targets for a toon/stylized master (displayed sRGB, not measured). Lock them only after checking against the photo reference board. Where a row says "no source fetched", the value is art direction, not research.

| # | Slot | Proposed sRGB hex | Roughness | Real-world reference | Zones / systems |
|---|---|---|---|---|---|
| 1 | P_LimeWash_Base | #E6DFCC (var ±4% value, ±2° hue) | 0.88 | Full lime render / lime-milk wash on limestone rubble. The PNR guide asks for "enduit de teinte sable clair" and inland beiges and écrus, whiter toward the coast [S1] | village_buildings (houses, logis), mist_marsh_reeds cabane |
| 2 | P_LimeWash_Patina | #C9BFA6 | 0.92 | Weathered and dirtied lime render; the PNR notes how "la patine et la texture des matériaux nuancent les couleurs" [S1] | All RoomShell walls (AO/top-edge grime), quéreux walls |
| 3 | P_Limestone_Quoin | #D9C9A3 | 0.75 | "Pierre blonde calcaire" from quarries on the marsh edge (Benet, Nalliers) [S1]. Maillezais sits on Jurassic limestone [S3] | Quoins and openings (RoomShell), whole church, abbey ruin, stone bief bridge |
| 4 | P_Roof_Terracotta | #C07A57 new / #9A6450 aged (per-instance lerp) | 0.80 | Canal tiles ("tige de botte") made from local bri clay, in mixed ocre-rosé tones. The guide says to avoid dark tiles [S1]. "Tuile creuse" on the Maison aux volets bleus [S2] | Houses, balais barns, hay barns, cabane |
| 5 | P_Roof_Slate | #4E555C | 0.55 dry / 0.30 wet | Slate on the bourgeois logis built from costly imported materials [S1] | Logis only, church spire/tower roof |
| 6 | P_Shutter_Green | #9DB8A5 (alt #7FA08C) | 0.60 paint / 0.85 peeled | "Nuances vert d'eau" and "vert tendre" painted wood shutters, one colour per house; the PNR's most-cited shutter colour [S1] | RoomShell shutters/doors (default hue, ~60% of houses) |
| 7 | P_Shutter_Blue | #8FAAC0 (tonic alt #5F86A8) | 0.60 / 0.85 | Pastel blue (Le Mazeau) and more tonic blue (Coulon) [S1]; Maison aux volets bleus, Sansais/Coulon [S2]. Note: [S2] says blue is *not* traditional to the region, so use it sparingly (~25%) | RoomShell shutters (~25%), remaining ~15% grey-blue / brown-red per [S1] |
| 8 | P_Wood_Tarred (black keys) | #26221E | 0.65 dry / 0.35 wet | Tarred (coal-tar/pitch) boat and landing timbers. *No source fetched; art direction* | Piano walkways: black-key boards, pile tops, barque hulls |
| 9 | P_Wood_Oak (white keys) | #A58A66 fresh → #9C9890 silvered | 0.80 | Oak deck planks weathering to silver-grey. The PNR notes local poplar for cladding ("gris argenté des bardages") [S1]; poplar board variant #B3A68C is allowed for barn cladding | Walkway decks, rails, jetties, barn cladding (poplar variant), Trim_Wood |
| 10 | P_Waterline_Damp | multiply #7A746A at 0.65 (≈ −35% value); band 0–0.8 m above WaterLevelZ, soft 0.15 m falloff | +(-0.25) roughness (wetter) | Darker plinth band ("soubassement de teinte plus foncée") that seats the building and hides dirt; historically a lime render redone regularly against rising damp [S1] | Plinths (MS_Plinth_DampStone), balais steps, quéreux bases, piles, bief bridge, ruin base |
| 11 | P_Moss | #5F6B3B (lichen accent #A9A77A) | 0.95 | Moss and grey-green lichen on north-facing limestone and tiles in a humid marsh. *No source fetched; art direction* | Roof lichen, wall tops, ruin (with ivy), waterline proximity |
| 12 | P_Duckweed | #84A83C | 0.40 (wet sheen) | Duckweed (lentilles d'eau) covering still conches. *No source fetched; art direction* | Water-surface decal on conches and ditches; never on the bief |
| 14 | P_Stone_Weathered (church/ruin) | #9A9384 | 0.85 | Reference board swatches 4_church_square #999083 and 7A_maillezais #928E81 (/workspace/poitou_board/swatches.json) | Church walls at mid/far distance, abbey ruin, ruin_rise landscape layer |
| 13 | P_Mist_Tint | #DCE3E4 | n/a (fog) | Marsh morning light, "lumière douce et claire du marais", blues and greys [S1] | Fog volume and mist_volume; also the far-band desaturation target |

Sources: [S1] PNR Marais poitevin, Carnet d'architecture "Habiter dans le Parc", https://pnr.parc-marais-poitevin.fr/wp-content/uploads/Carnet-habiter-parc-marais-poitevin-Interactif-Planche.pdf · [S2] Patrimoine Nouvelle-Aquitaine, "Ferme dite la Maison aux volets bleus" (IA79005824), https://www.patrimoine-nouvelle-aquitaine.fr/default/doc/Dossier/2d511238-6edb-4234-950b-ef3f366c7371/ferme-dite-la-maison-aux-volets-bleus?_lg=fr-FR · [S3] Département de la Vendée, "L'abbatiale cathédrale de Maillezais", https://nossites.vendee.fr/abbaye-de-maillezais/explorer-le-site/une-architecture-unique/labbatiale-cathedrale-de-maillezais

---
# M_Poitou_Master (SUPERSEDED, kept for reference)
> **v2 decision (2026-10-20):** no new master. All props/buildings are MIs of `/Game/EnvSandbox/Materials/Masters/M_Master_Toon_Universal`; the layer stack below is design intent only and maps onto existing toon params (see "v2 mapping" at the end).
One opaque master for walls, roofs, wood and stone, driven by **trim sheets + tileable textures** (UV0 = trim/tile, UV1 = lightmap/unique AO optional). It is toon-friendly: albedo stays flat and readable, the layers are mask-driven (no high-frequency PBR noise at Far band), and its outputs feed the project's toon universal master as a material function `MF_Poitou_Surface` (BaseColor, Roughness, Normal, AO, ToonBandBias) so the toon lighting model is untouched.

## Static switches (keep permutations low)
| Switch | Default | Notes |
|---|---|---|
| bUseLimeWash | true | off for bare-stone church/ruin/oak |
| bUseDampBand | true | |
| bUseMoss | true | |
| bUseRoofTileVariation | false | on for roof MIs only |
| bUseWoodSilvering | false | on for wood MIs |
| bUsePeelMask | false | shutters/trim |
| bToonQuantizeAlbedo | true | posterizes layer blends to 3 steps for toon read |

## Layer stack (bottom → top)
| # | Layer | Mask source | Key parameters (default) |
|---|---|---|---|
| L0 | **Base surface** (stone / render / tile / wood) | trim sheet or tile texture, UV0 | `Base_Tex` (T_Trim_Poitou_Stone_A), `Base_Tint` (P_Limestone_Quoin #D9C9A3), `Base_TileScale` 1.0 (= 2.4 m per tile, one bay), `Base_Roughness` 0.75, `Base_NormalStrength` 0.6, `Base_AlbedoVar` 0.04, `Base_VarNoiseScale` 0.002 (world-space macro noise) |
| L1 | **Lime-wash** | **Vertex paint R** × `LW_HeightMask` (from stone height map: wash pools in mortar joints first) | `LW_Color` P_LimeWash_Base #E6DFCC, `LW_PatinaColor` P_LimeWash_Patina #C9BFA6, `LW_Coverage` 1.0, `LW_EdgeContrast` 0.5, `LW_Roughness` 0.88, `LW_FlattenNormal` 0.7 (render hides rubble), `LW_PatinaAO_Strength` 0.5, `LW_PatinaTopEdge` 0.3 |
| L2 | **Damp waterline** | **World-Z band**: `saturate(1 - (WorldZ - WaterLevelZ)/DB_Height)` with noise-broken top edge, **max** with **Vertex paint G** (manual extra damp / rain streaks) | `WaterLevelZ` (MPC_Poitou global, cm), `DB_Height` 80, `DB_EdgeSoftness` 15, `DB_EdgeNoiseAmp` 10, `DB_Darken` 0.35, `DB_Tint` #7A746A, `DB_RoughnessDelta` −0.25, `DB_GreenAlgae` 0.15 (lerp toward P_Moss at the very bottom 20 cm) |
| L3 | **Moss / lichen** | **Vertex paint B** × world-up mask `saturate((N·Z − MS_UpMin)/(1−MS_UpMin))` + north bias `(N·−Y)` × `MS_NorthBias` + damp-band proximity | `MS_Color` P_Moss #5F6B3B, `MS_LichenColor` #A9A77A, `MS_Amount` 0.4, `MS_UpMin` 0.35, `MS_NorthBias` 0.3, `MS_WaterProx` 0.25, `MS_Roughness` 0.95, `MS_BreakupTex` T_Noise_Moss, `MS_BreakupScale` 0.01 |
| L4 | **Roof tile tint variation** | **PerInstanceRandom** (ISM/HISM roofs) + per-tile cell ID from trim UV (`floor(UV*TileCount)` hash) | `RT_NewColor` #C07A57, `RT_AgedColor` #9A6450, `RT_InstanceAgeRange` (0.2, 0.9), `RT_PerTileHueJitter` 0.03, `RT_PerTileValueJitter` 0.08, `RT_TileCount` (8, 4), `RT_LichenBoost` 0.2 (adds to L3 on aged instances) |
| L5 | **Weathering grime** | AO (baked/trim) × gravity streak tex (world-down aligned) + cavity | `GR_Color` #5A5248, `GR_Amount` 0.25, `GR_StreakTex` T_Streak_Poitou, `GR_StreakScale` 0.004, `GR_AOPower` 1.5, `GR_UnderSillBoost` 0.3 (trim sheet row ID), `GR_Roughness` 0.9 |
| L6 (opt) | **Wood silvering / tar** | `WD_Silvering` scalar (+ PerInstanceRandom ±0.15), wetness from MPC | `WD_FreshColor` #A58A66, `WD_SilverColor` #9C9890, `WD_Silvering` 0.4, `WD_TarColor` P_Wood_Tarred #26221E, `WD_TarRoughDry` 0.65, `WD_TarRoughWet` 0.35 |
| L7 (opt) | **Paint + peel** (shutters/doors) | peel tex × `PP_Peel` + edge wear | `PP_PaintColor` (P_Shutter_Green / Blue), `PP_Peel` 0.15 (range 0–0.3), `PP_UnderColor` = P_Limestone_Quoin or oak, `PP_Roughness` 0.6 |
| Final | **Toon / distance** | camera distance | `TN_FarDesat` 0.25 toward P_Mist_Tint beyond 150 m, `TN_QuantizeSteps` 3, `TN_RimTint` #DCE3E4 |

Global MPC `MPC_Poitou`: `WaterLevelZ`, `Wetness` (0–1, morning mist = 0.3), `MistTint` (#DCE3E4), `SunDir` (if the toon master needs it).
Vertex paint convention: **R = lime-wash, G = extra damp, B = moss, A = reserved (ivy on ruin / peel override)**. PCG/RoomShell can write default vertex colours per building seed (e.g. R = 1 on houses, 0.6 on barns).

## Material instances
### RoomShell (houses, balais barns, quéreux)
| MI | Parent switches | Overrides |
|---|---|---|
| MI_Poitou_Wall_LimeRender | LW on, Damp, Moss | Base_Tex = rubble trim; LW_Coverage 1.0 |
| MI_Poitou_Wall_LimeRender_Coastal | same | LW_Color #EDE9DD (whiter coast per [S1]) |
| MI_Poitou_Wall_BarnRubble | LW on, Damp, Moss | LW_Coverage 0.5, GR_Amount 0.35 |
| MI_Poitou_Quoin_Limestone | LW off | Base_Tint #D9C9A3, Base_Roughness 0.75 |
| MI_Poitou_Plinth_DampStone | Damp | DB_Height 80, DB_Darken 0.40 |
| MI_Poitou_Roof_TigeDeBotte | RoofTileVar, Moss | RT_* defaults, MS_Amount 0.3 |
| MI_Poitou_Roof_Slate_Logis | Moss | Base_Tint #4E555C, Base_Roughness 0.55, MS_Amount 0.15 |
| MI_Poitou_Shutter_VertDeau / _Bleu / _GrisBleu / _BrunRouge | Peel | PP_PaintColor #9DB8A5 / #8FAAC0 / #8C98A0 / #7A4A3E (last two: proposals from [S1] mentions) |
| MI_Poitou_Trim_Wood | WoodSilvering | WD_Silvering 0.5 |
| MI_Poitou_Cladding_Poplar (barns) | WoodSilvering | WD_FreshColor #B3A68C, WD_Silvering 0.7 |
| MI_Poitou_Wall_Quereux | LW on, Damp, Moss | LW_Coverage 0.7, coping uses the Quoin MI |

### Resonant Cathedral (church + ruin)
| MI | Overrides |
|---|---|
| MI_Poitou_Church_Ashlar | LW off, Base = ashlar trim, Base_Tint #D9C9A3, GR_Amount 0.3, MS_Amount 0.25 |
| MI_Poitou_Church_Carved (capitals, corbels, archivolts) | NormalStrength 1.0, GR_AOPower 2.0 (cavity reads the carving in toon) |
| MI_Poitou_Church_SpireSlate | Slate MI values |
| MI_Poitou_Church_Louvres | Oak MI, WD_Silvering 0.8, darkened by GR 0.4 (reads as dark stripes far band) |
| MI_Poitou_Ruin_Limestone | Base_Tint #D2C29E, GR_Amount 0.45, MS_Amount 0.6, MS_UpMin 0.2, vertex A = ivy, DB_Height 40 (rise is dry) |
| MI_Poitou_Ruin_BrokenEdge | MS_Amount 0.8 on top-edge mask (TopEdgeNoise geometry) |
| MI_Poitou_Ruin_GothicTracery | Ruin_Limestone, NormalStrength 0.9 (max 2 instances per contract) |

### Piano walkways
| MI | Overrides |
|---|---|
| MI_Poitou_Walk_OakDeck (white keys) | WoodSilvering, WD_Silvering 0.35 + PerInstanceRandom ±0.15 per plank, Damp on (piles/underside) |
| MI_Poitou_Walk_TarredKey (black keys / octave board) | WD_Tar, Roughness 0.65 → 0.35 via MPC Wetness; no albedo variation (keep the rhythm clean) |
| MI_Poitou_Walk_Rail | Oak, WD_Silvering 0.6 |
| MI_Poitou_Walk_Pile | Tar below DB_Height, oak above, Moss B at waterline |
| MI_Poitou_Bridge_StoneBief | Quoin values + Damp + Moss |
| (Water decal) MI_Poitou_Duckweed | separate translucent/decal material, colour #84A83C, not part of this master |

## Texture budget (proposal)
- T_Trim_Poitou_Stone_A (rubble, ashlar, quoin, sill rows), T_Trim_Poitou_Wood_A (planks, shutters, louvres), T_Tile_Poitou_Canal, T_Tile_Poitou_Slate: 2K, packed BC / N / ORH (Occlusion-Roughness-Height).
- Shared noise textures: T_Noise_Moss, T_Streak_Poitou, T_Peel_Mask.

## Open items for the reference board
1. Check the shutter-hue ratio against village photos (Coulon, Arçais, Le Vanneau-Irleau).
2. Measure tile colour from real tige-de-botte roofs. The current hex is a guess from "ocre-rosé".
3. Tar black: confirm the slight warm cast vs. pure neutral for the toon ramp.
4. Unsourced slots (8, 11, 12) need photo references.

---
# v2 mapping onto M_Master_Toon_Universal (read-only inspection, 2026-10-20)
Parent: opaque Surface, DefaultLit, used_with_nanite=True, used_with_instanced_static_meshes=False. It has no landscape layer nodes (no LandscapeLayerBlend), so it **cannot be the landscape material**. The landscape gets a separate `M_Poitou_Landscape`.
Toon params used: `BaseTint` (vec), `Roughness` (scalar), `MossColor`, `MistColor`, `DawnLowColor`, `DawnHighColor`, `DreamRimColor`. Strengths (`MossConcavityStrength`, `MistStrength`, `DawnStrength`, `DreamRimStrength`, `WetnessStrength`) stay at parent defaults until TAL/AD tune them.
Concept → toon param: lime-wash/stone/tile/wood base → BaseTint; moss layer → MossColor + MossConcavityStrength; damp waterline → WetnessStrength/WetnessDarken (no world-Z band in the parent; the band is a future request); grime → MacroVariationStrength; mist → MistColor/MistStrength.

| MI (/Game/EnvSandbox/Poitou/Materials/) | BaseTint | Roughness |
|---|---|---|
| MI_Poitou_LimeWash | #E6DFCC | 0.88 |
| MI_Poitou_Tile | #C07A57 | 0.80 |
| MI_Poitou_Slate | #4E555C | 0.55 |
| MI_Poitou_Oak | #A58A66 | 0.80 |
| MI_Poitou_Tar | #26221E | 0.65 |
| MI_Poitou_RuinStone | #9A9384 | 0.85 |
Shared on all: MossColor #5F6B3B (not on Tar), MistColor #DCE3E4, DawnLowColor #AAB8AF, DawnHighColor #EAEFF6, DreamRimColor #DCE3E4. Hexes are sRGB; the script converts them to linear.

Landscape layers (names = Houdini mask channels): wet_meadow_grass #68735D, canal_banks #555D38, village_buildings #A08F6C, ruin_rise #9A9384, tree_rows_poplar_ash #44513E, mist_marsh_reeds #93A179, mist_volume #7E8770, water #2F3A2C. Script: ma_poitou_materials.py.
