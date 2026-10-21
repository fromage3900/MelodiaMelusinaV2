# MelodiaMelusina: "Musical but French" Style Contract v0
Reuse rule: §3 drives EXISTING builders (gn_parisian_audit.md). Scope: Marais Poitevin level ("Melusina's Morning"). Applies to the systems BP_MelusinaRoomShell (PCGEx), Resonant Cathedral generator, and Piano walkways. This document is read-only with respect to Unreal and does not change any assets.

## 1. Identity rule
**Silhouette is French. Music lives in rhythm and ornament.** From 50 m away or more, every structure must read as plausible Poitevin vernacular or Romanesque architecture. That means no instrument shapes, no clefs and no floating forms. Music shows up only in (a) spacing and repetition (openings, planks, arcades follow bar or measure patterns), (b) small-scale carving or ironwork motifs seen up close, and (c) existing sound/press feedback (piano-walkway keys, bell resonance). If a musical element changes the outline, it is banned.

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

### 3a. Houses and barns: REUSE MEL_nikki_quarter (Townhouse) + MEL_wall_* + MEL_half_timber_wall + GN_PARIS_WallDetail
Use exteriors from the existing GN builders (see gn_parisian_audit.md). Do not design a new house builder.

| Builder | Role | Poitou values |
|---|---|---|
| **MEL_nikki_quarter**, Mode 0 Townhouse | House massing + roof | Floors 1–2 (default 3 → cap 2); Floor Height 2.7 (GF override to 3.0 if exposed); Width 7.2–14.4 / Depth 5.4–8.4 (snap 0.6, bay 2.4); Window Count = bays × openings from the bar pattern (below); Roof Mode 0 = Hip (modes 1–3 onion/pagoda/clerestory banned); Roof Pitch ≈0.5 terracotta (~27°) / 0.8 slate (~39°, logis only); Eave Overhang 0.3–0.5; Variation/Seed per plot; Bay Window / Balcony / Lantern / Trim Cornice = OFF; Chimney / Porch / Flower Boxes = ON |
| **MEL_wall_straight / _corner / _with_door / _with_window / _multi_window / _t_join** | Quéreux walls, enclos, balais façades, gable fills | Length 6–30 m; Height 1.8–2.4 (walls) / 3.0–5.0 (barns); Thickness 0.5–0.7; opening count from the bar pattern (set via PROPS) |
| **MEL_retaining_wall** | Quays and levees along canals | Height 0.6–1.5 above the water |
| **MEL_half_timber_wall** | Balais barns and jetty sheds (timber upper or gable only) | Barn W 4.8–9.6, H 3.0–5.0, step drop 0.6–1.2 toward water |
| **GN_PARIS_WallDetail** | Trim pass on all of the above | Show Cornice / String / Wainscot / Panels = OFF; Show Baseboard = ON (= damp plinth, 0.4–0.6 m); Apply Trim UV = ON (quoin/trim slot); CORNICE_STYLE unused |
| GN_PARIS_SlabTrim | Optional plain lime string band on the logis | 1 band max |
| MEL_wall_arched_window | Logis / church-adjacent only | Round arch only, no ogive |

- **Banned from the audit's C list:** MEL_raycast_facade, curved/radial buildings, the Paris day-night façade, the Escher ladder, and baroque/bifora/ogee/venetian elements.
- **Openings rhythm** (unchanged): one bay = one 4-beat bar. Allowed patterns are `– W – W`, `W – D – W`, `D – W –`. At most 40% of the façade is open, corners stay solid, and the same bar repeats at most 3 times. Window Count and wall opening counts are derived from the pattern.
- **Interiors:** use UE **BP_MelusinaRoomShell** (its exposed vars are not yet audited; see open questions) or GN **MEL_music_room_shell** with Room Length/Width/Height to match the exterior minus the wall thickness, Wall Thickness 0.5, and Cut Door/Cut Window aligned to the exterior bar pattern. Dado Staff Band = OFF (it breaks the far/mid motif rule); it is allowed in hero interiors only. MEL_mh6_room_shell is a fallback.
- **Material slots** (M_Poitou_Master instances, per palette_and_master_MA.md): lime render, limestone quoins, terracotta or slate roof, painted shutters, damp plinth, wood trim.

### 3b. Church and ruin: REUSE MEL_math_gothic_cathedral (lowered) + UE SM_Cathedral_* kit
- **GN MEL_math_gothic_cathedral** (recursive_castle.py), driven to a squat Romanesque form:
  - Nave Length 20–30
  - Nave Width 8–10
  - Vault Height lowered to 7–9 (walls), about 12 at the ridge
  - Buttress Reach small, 0.6–0.9 (flat pilaster buttresses)
  - Rose Window Radius 0, or ≤1.2 as a west oculus only
  - Petal Count 6–8 if the oculus is used
  - No flying buttresses or pointed arches. Arches are semicircular.
- **UE kit, placed or swapped onto GN sockets:**
  - SM_Cathedral_Portal (3 archivolts, the "chord")
  - SM_Cathedral_Buttress (scaled down)
  - SM_Cathedral_Pier (nave arcade, ruin bays)
  - SM_Cathedral_Crypt (optional undercroft)
  - SM_Cathedral_Spire used only as a low stone or pyramidal cap on the 25–35 m tower
  - SM_Cathedral_LancetWindow and RoseWindow are allowed only on the ruin (≤2 Gothic instances)
  - Escher/Orb/Bifrost variants are banned
  - Materials: MI_Cathedral_Stone (walls) and MI_Cathedral_Rock (ruin base), to be reparented as M_Poitou_Master children when the Material Artist lands it
- Music elements (unchanged): organ-pipe louvres (×0.94 length step) inside the tower bay, instrument capitals, a musicians' corbel table.
- **Abbey ruin variant (Maillezais-style):** the same builder plus decay params (Ruin_Integrity 0.2–0.5, TopEdgeNoise 0.5–2.5 m, MissingRoof, ArchCollapseChance 0.2–0.35, never on landmark-facing arches, IvyCoverage 0.3–0.6). RubbleSpawn feeds `ruin_rise`. **Gap:** MEL_math_gothic_cathedral has no decay inputs. Add a post-process GN modifier (boolean or noise trim on the top edge), or break the ruin by hand in UE.

### 3c. Piano walkways: EXISTS, REUSE. Only new item: a `DA_PianoWalkway_Poitou` variant
The system already exists in UE. This contract adds **no new features**; it only supplies Poitou values for a new data-asset variant.

| Piece | Status |
|---|---|
| C++ `Source/BS_GodFile/Piano/PCGPianoKeyboard.h/.cpp`: per-key actor (KeyIndex, MidiNote, FirstMidiNote 21 … LastMidiNote 108), StepTrigger box, HandleStepBegin/End, OnKey events `FPCGPianoKeyEvent(KeyIndex, MidiNote, SteppingActor)`, PressSound pitch-shifted from PressSoundRootMidi, press animation and visual params | exists, reuse (step → note → sound → press anim already covered) |
| PCG `Content/Melodia/PCG/Walkways/PCG_PianoWalkway_WestRim`, `PCG_PianoWalkway_InfiniteScore_PianoRoll` | exists, reuse (WestRim as the template for bank-following runs) |
| PCG `EnvSandbox/PCG/Musical/PCG_PianoKeyRun_2Oct` + `DA_PianoKeyRun_2OctProfile` | exists, reuse (short 2-octave footbridges) |
| DA `DA_PianoWalkway_MorningMeadow` / `_FarawayFabric` | exists, reuse; **duplicate MorningMeadow → `DA_PianoWalkway_Poitou`** |
| Mesh `Melodia/Meshes/PianoKey_AAA` | exists, reuse (scaled to plank dims) |
| Python `Content/Python/pcg_piano_walkway.py`, `build_pcg_piano.py` | exists, reuse for (re)building runs |
| MIs `MI_PianoKey_MorningMeadow_{Ivory,Ebony}` | exists; duplicate to `MI_PianoKey_Poitou_Oak` / `_Tarred` (M_Poitou_Master children: P_Wood_Oak / P_Wood_Tarred) |

**`DA_PianoWalkway_Poitou` values** (use the matching fields of the existing DA; names follow that DA, not new fields):
- Key width / pitch **0.24 m** (10 keys = 2.4 m = 1 bar/bay; 0.24 = 0.6/2.5). The MorningMeadow-style default of 0.22 is acceptable if the DA can't change it.
- Key length = deck width **1.2–1.5 m**; key height 0.04–0.06 m (oak plank look).
- Spans 4–8 m (conches, about 17–34 keys) and jetties 4–12 m. MIDI range stays within the existing FirstMidiNote 21…LastMidiNote 108; pick a mid-register window per run.
- Black keys (tarred boards) are visible across **one octave per span** max, mid-span (contract ban: no full-span piano stripes). If the DA/PCG has no way to limit this, flag it as an open question rather than adding a feature.
- Visuals: Oak / Tarred MIs; press animation and sound use the existing defaults (PressSound and visual params unchanged unless the audio lead says otherwise).
- Deck substructure, piles and rails: whatever the existing PCG graphs place. Clearance target 0.6–1.2 m above water, posts every 2.4 m where the graph exposes spacing. (The GN MEL_mother_walkway_* / MEL_pergola_walkway builders are only an optional fallback for hand-made hero jetties.)

Placement: footbridges where the route crosses canal_banks water; landing jetties at beats 1 and 3 (see §6).

## 4. Musical motif allow/ban list by distance band
| Band | Allowed | Banned |
|---|---|---|
| Far (>150 m) | Rhythm only: regular bay spacing, poplar spacing (6–7 m) as a metre, bell-tower louvres reading as dark stripes | Any instrument silhouette, giant clefs/notes, floating or spiral forms, colour coding by note |
| Mid (20–150 m) | Façade bar patterns, archivolt "chords", rail posts at bar spacing, octave dark boards on bridges, organ-pipe louvre gradation | Literal staff lines on walls, piano-stripe bridges, signage with notes, glowing emissives in daylight |
| Near (<20 m) | Carved capitals (instruments), corbel musicians, ironwork shutter hinges as clef scrolls, door knockers, painted note on boat names, existing piano-key press animation (PCGPianoKeyboard) | Holographic UI notes, neon, motifs on more than 1 in 5 elements, modern typography |

## 5. Palette and material placeholder slots (for the Material Artist's master material M_Poitou_Master)
| Slot | Placeholder value (sRGB) | Param notes |
|---|---|---|
| P_LimeWash_Base | #E9E3D3 | Albedo variation ±4%, roughness 0.85 |
| P_LimeWash_Patina | #CFC6B0 | Grime mask from AO and top edges |
| P_Limestone_Quoin | #D8CBAE | Roughness 0.75 |
| P_Roof_Terracotta | #B56A4A / aged #8E5A45 | Lichen mask |
| P_Roof_Slate | #4B5157 | Logis and church spire only |
| P_Shutter_Green | #8FAE9B | Peeling mask 0–0.3 |
| P_Shutter_Blue | #8AA4B8 | Same |
| P_Wood_Tarred (black keys) | #2A2622 | Roughness 0.5 when wet |
| P_Wood_Oak (white keys) | #A88D6A | Silvered weathering 0–1 |
| P_Waterline_Damp | Height band 0–0.8 m above water, darken 35% | World-Z driven; global WaterLevel param |
| P_Moss | #5E6B3A | Mask from normal·up, waterline proximity, north-facing |
| P_Duckweed | #7FA33A | Water-surface decal |
| P_Mist_Tint | #DDE4E6 | Shared with the fog volume |

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

// Piano walkway: NOT in this DA. Use DA_PianoWalkway_Poitou (variant of existing DA_PianoWalkway_MorningMeadow); see §3c.
TSoftObjectPtr<UDataAsset> PianoWalkwayProfile;   // -> DA_PianoWalkway_Poitou

// Materials
TSoftObjectPtr<UMaterialInterface> MasterMaterial;
TMap<FName, FLinearColor> PaletteSlots;    // keys = §5 slot names
TMap<FName, UTexture2D*>  ZoneHeatmaps;    // village_buildings, canal_banks, ...
```

## Open questions
1. Do the existing RoomShell `Door_*` params support arch type, or does that need a new enum?
2. Does the Resonant Cathedral generator support a single-nave squat mode, or only tall Gothic forms?
3. Which MIDI register or window should each walkway run use (within the existing 21–108)? Can DA_PianoWalkway limit black keys to one octave per span?
4. Should the ruin read as Maillezais (abbey) or Lusignan (keep)? This contract assumes an abbey.
5. Canal tile vs slate: some Marais roofs are mixed. Keep slate for the logis and church only?

6. BP_MelusinaRoomShell exposed vars are still unaudited (editor needed). Confirm a mapping onto MEL_music_room_shell params.
7. Can PianoKey_AAA be scaled to a 0.24 × 1.4 m plank without the press animation breaking?
