# MelodiaMelusina: "Musical but French" Style Contract v0
Scope: Marais Poitevin level ("Melusina's Morning"). Applies to the systems BP_MelusinaRoomShell (PCGEx), Resonant Cathedral generator, and Piano walkways. This document is read-only with respect to Unreal and does not change any assets.

## 1. Identity rule
**Silhouette is French. Music lives in rhythm and ornament.** From 50 m away or more, every structure must read as plausible Poitevin vernacular or Romanesque architecture. That means no instrument shapes, no clefs and no floating forms. Music shows up only in (a) spacing and repetition (openings, planks, arcades follow bar or measure patterns), (b) small-scale carving or ironwork motifs seen up close, and (c) sound or VFX feedback (note-on-step, bell resonance). If a musical element changes the outline, it is banned.

## 2. Global module grid and proportions (metric, 1 uu = 1 cm)
- **Base module M = 0.6 m.** Bay = 4M = 2.4 m (one "bar" of 4 beats). Storey = 5M = 3.0 m (ground floor 3.0 m, upper floor 2.7 m).
- Snap grid: 0.3 m (half beat) for openings, 0.6 m for walls, 2.4 m for bay rhythm.
- Walls are 0.5–0.7 m thick (limestone rubble). Plinths are 0.4–0.6 m above the bank.
- Heights from layout_plan.md:
  - eaves 4–6.5 m, ridge 7–10 m
  - barns 5–8 m
  - church nave about 12 m, steeple 25–35 m
  - ruin keep or abbey 18–25 m, on a rise of 15–25 m
- Waterways: ditch under 4 m, conche 4–8 m, bief 18 m. Walkway clearance is 0.6–1.2 m above water level so barques can pass.
- Proportions:
  - House façade H:W is about 1:1.5 to 1:2.5 (long and low).
  - Window opening H:W is 1.6–2:1.
  - Church nave W:H is about 1:1.3.
  - Romanesque arches are semicircular only (rise = span/2).

## 3. Per-system specs

### 3a. BP_MelusinaRoomShell becomes village houses, stepped barns ("balais") and quéreux walls
| Param | House (maison maraîchine) | Balais barn (stepped toward water) | Quéreux / enclos wall |
|---|---|---|---|
| Module | 0.6 m (bay 2.4) | 0.6 m (bay 3.0, wide doors) | 0.6 m |
| W (façade) | 7.2–14.4 m (3–6 bays) | 4.8–9.6 m | 6–30 m runs |
| D | 5.4–8.4 m | 6–10 m | 0.5 m |
| H (eaves) | 4.0–6.5 m (1–2 storeys) | 3.0–5.0 m, each step −0.6 to −1.2 m toward water | 1.8–2.4 m |
| Roof | Gable, pitch 25–35° (canal tile, "tige de botte"), slate allowed only on the bourgeois "logis" at 40–45° | Gable or lean-to, 20–30° | Coping stone |
| Door_* | Door_Count 1–2, Door_W 1.0–1.2, Door_H 2.1–2.4, Door_Arch {flat, segmental} | Door_W 2.4–3.0 (cart/boat door), Door_Arch {flat, segmental} | Gate 1.2–3.0 |

**Openings rhythm as a musical bar.** Each storey is a measure of 4 beats per bay. Each beat is either a window (W), a door (D), blank wall (–), or a small oculus (o).
- Allowed patterns: `– W – W`, `W – D – W` (3/4 waltz bay), `D – W –`. The upper floor keeps the same downbeats as the ground floor, offset at most a half beat.
- No more than 40% of the façade may be open. Corners are always solid (quoins).
- Shutters always come in pairs. The pattern seed is stored per building so a street "plays" a phrase without repeating the same bar more than 3 times in a row.

**Material slots** (see §5):
- MS_Wall_LimeRender
- MS_Quoin_Limestone
- MS_Roof_TerracottaCanal / MS_Roof_Slate
- MS_Shutter_Painted (marsh palette: celadon green, light blue, grey-blue; one hue per building)
- MS_Plinth_DampStone
- MS_Trim_Wood

### 3b. Resonant Cathedral generator becomes a squat Romanesque church, with a Maillezais-style abbey ruin as a variant
**Church (village, landmark A)**
- Single nave 8–10 m wide, 20–30 m long, walls 7–9 m, ridge about 12 m. Apse is semicircular.
- Square crossing or west bell tower 5–6 m square, total height 25–35 m (low stone spire or pyramidal roof).
- Openings:
  - semicircular arches only
  - nave windows narrow (0.8–1.0 × 2.4–3.0 m), placed every bay of 4.8 m (2 bars)
  - west portal: 3 stepped archivolts (arch-ring bands) = a "chord" of 3 rings
- Buttresses are flat pilaster strips, 0.6 m wide, aligned with the bay.
- Music:
  - Bell-tower louvres (abat-sons) are slats sized and spaced like organ pipes. Lengths step in a scale ratio (×0.94 per slat ≈ semitone). The slats stay inside the arched bay opening, so the silhouette does not change.
  - Capitals are carved with instrument motifs (vielle, harp, viol, horn), as on real Poitevin Romanesque capitals with elders of the Apocalypse.
  - Corbel table shows musicians' heads.

**Abbey ruin variant (landmark B, on the limestone rise)**
- Base it on Maillezais: a Gothic-on-Romanesque abbey on a limestone island. Keep Romanesque arches for consistency.
- Remaining elements: west façade fragment 18–25 m, two nave arcade bays, a stair tower, curtain-wall stubs 3–8 m.
- Decay params:
  - Ruin_Integrity 0.2–0.5
  - TopEdgeNoise amplitude 0.5–2.5 m
  - MissingRoof = true
  - ArchCollapseChance 0.2–0.35 (never on landmark-facing arches)
  - RubbleSpawn → feeds the `ruin_rise` heatmap
  - IvyCoverage 0.3–0.6
  - Window tracery is Gothic only on the ruin, at most 2 instances
- Music at the ruin: broken organ-pipe louvres with gaps (missing notes), and wind-driven resonance as an audio cue.

### 3c. Piano walkways become canal footbridges (passerelles), jetties and boat landings
- **Width 1.2–1.5 m** (deck). Span 4–8 m for conches; the main canal (bief) uses a stone bridge instead (no piano).
- **Plank = key.** Pitch is 0.15 m per white plank (plank 0.14 m plus a 0.01 m gap), in the scale of a real oak deck. Black keys are tarred dark boards that run as a raised short half-plank (0.09 m wide, 60% of deck width) in the 2-3 groups pattern. An alternative is a full-width dark board placed every 7 white planks (one octave).
- Rails: wood, 1.0 m high, posts every 2.4 m (one bar). An optional rail-less "passerelle" type has a 0.3 m curb.
- Jetty / landing: 1.5–2.4 m wide, 4–12 m long, on piles every 2.4 m. A mooring post sits every 7th plank.
- Note-on-step: a plank's index sets its pitch in a scale (default D dorian, modal and "folk"). Velocity comes from player speed. Arpeggios fire only on jetties at landmark beats 1 and 3. There is a 0.12 s debounce so footsteps don't spam notes.
- Ban: keyboard-length bridges with literal white and black stripes across the whole span (the silhouette would read as a piano). Max 1 octave of visible contrast per span.

## 4. Musical motif allow/ban list by distance band
| Band | Allowed | Banned |
|---|---|---|
| Far (>150 m) | Rhythm only: regular bay spacing, poplar spacing (6–7 m) as a metre, bell-tower louvres reading as dark stripes | Any instrument silhouette, giant clefs/notes, floating or spiral forms, colour coding by note |
| Mid (20–150 m) | Façade bar patterns, archivolt "chords", rail posts at bar spacing, octave dark boards on bridges, organ-pipe louvre gradation | Literal staff lines on walls, piano-stripe bridges, signage with notes, glowing emissives in daylight |
| Near (<20 m) | Carved capitals (instruments), corbel musicians, ironwork shutter hinges as clef scrolls, door knockers, painted note on boat names, note-on-step VFX ripple (water-blue, under 0.5 s) | Holographic UI notes, neon, motifs on more than 1 in 5 elements, modern typography |

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
| 13 | P_Mist_Tint | #DCE3E4 | n/a (fog) | Marsh morning light, "lumière douce et claire du marais", blues and greys [S1] | Fog volume and mist_volume; also the far-band desaturation target |

Sources: [S1] PNR Marais poitevin, Carnet d'architecture "Habiter dans le Parc", https://pnr.parc-marais-poitevin.fr/wp-content/uploads/Carnet-habiter-parc-marais-poitevin-Interactif-Planche.pdf · [S2] Patrimoine Nouvelle-Aquitaine, "Ferme dite la Maison aux volets bleus" (IA79005824), https://www.patrimoine-nouvelle-aquitaine.fr/default/doc/Dossier/2d511238-6edb-4234-950b-ef3f366c7371/ferme-dite-la-maison-aux-volets-bleus?_lg=fr-FR · [S3] Département de la Vendée, "L'abbatiale cathédrale de Maillezais", https://nossites.vendee.fr/abbaye-de-maillezais/explorer-le-site/une-architecture-unique/labbatiale-cathedrale-de-maillezais

## 6. Zone to system mapping (heatmap channels in /heatmaps)
| Zone / channel | RoomShell | Cathedral | Piano walkway | Notes |
|---|---|---|---|---|
| village_buildings | Houses + balais (density = plot probability; >0.8 → 2 storeys) | Church fixed at landmark A | Jetties where village meets canal | Quéreux walls fill gaps |
| canal_banks | Balais steps toward water only | — | Footbridges where a route or path crosses water; landings where value >0.7 and near a beat | Exclusions: open water |
| wet_meadow_grass | Isolated hay barns (≤1 per parcel, value 0.4–0.7) | — | Ditch planks (1.2 m, 3–4 m span) | — |
| tree_rows_poplar_ash | — | — | — | Foliage only; acts as the far-band "metre" |
| ruin_rise | — | Abbey ruin variant (landmark B); rubble from ruin_rise | — | — |
| mist_marsh_reeds | Possible single fisherman's hut (cabane) | — | Start jetty (beat 1) | — |
| mist_volume | — | — | — | Atmosphere only |

## 7. Data asset field sketch: `DA_MelusinaFrench_Style` (UPrimaryDataAsset)
```
// Global
float   ModuleM = 60.f;            // cm
int32   BeatsPerBar = 4;
float   BayWidth = 240.f;          // = ModuleM*BeatsPerBar
float   StoreyHeight = 300.f;
float   WaterLevelZ;
FName   MusicalScale = "D_Dorian";
TMap<EDistanceBand, FMotifRules> MotifRules;   // Far/Mid/Near allow/ban flags + max ratio

// RoomShell
FFloatRange House_W {720,1440}, House_D {540,840}, House_H {400,650};
FFloatRange Barn_W {480,960},  Barn_D {600,1000}, Barn_H {300,500}, Barn_StepDrop {60,120};
FFloatRange RoofPitch_Tile {25,35}, RoofPitch_Slate {40,45};
TArray<FString> BarPatterns { "-W-W", "W-D-W", "D-W-" };
float   MaxOpeningRatio = 0.4f;
int32   MaxBarRepeats = 3;
FFloatRange Door_W {100,120}, Door_H {210,240}, BarnDoor_W {240,300};
TArray<FLinearColor> ShutterPalette;

// Cathedral
FFloatRange Nave_W {800,1000}, Nave_L {2000,3000}, Nave_WallH {700,900};
FFloatRange Tower_H {2500,3500};
int32   PortalArchivolts = 3;
float   LouvreSemitoneRatio = 0.94f;
TArray<TSoftObjectPtr<UStaticMesh>> CapitalMotifs;   // vielle, harp, viol, horn
FRuinParams Ruin { Integrity {0.2,0.5}, TopEdgeNoise {50,250}, ArchCollapse {0.2,0.35}, Ivy {0.3,0.6}, bMissingRoof=true };

// Piano walkway
FFloatRange Deck_W {120,150};
float   KeyPitch = 15.f, KeyGap = 1.f, BlackKeyWidth = 9.f, BlackKeyDeckFrac = 0.6f;
float   RailH = 100.f, PostSpacing = 240.f, WaterClearance {60,120};
float   NoteDebounce = 0.12f;
int32   MaxVisibleOctavesPerSpan = 1;

// Materials
TSoftObjectPtr<UMaterialInterface> MasterMaterial;
TMap<FName, FLinearColor> PaletteSlots;    // keys = §5 slot names
TMap<FName, UTexture2D*>  ZoneHeatmaps;    // village_buildings, canal_banks, ...
```

## Open questions
1. Do the existing RoomShell `Door_*` params support arch type, or does that need a new enum?
2. Does the Resonant Cathedral generator support a single-nave squat mode, or only tall Gothic forms?
3. Should piano notes play D dorian (folk / vielle à roue) or follow Melusina's leitmotif key?
4. Should the ruin read as Maillezais (abbey) or Lusignan (keep)? This contract assumes an abbey.
5. Canal tile vs slate: some Marais roofs are mixed. Keep slate for the logis and church only?
