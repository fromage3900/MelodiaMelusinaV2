# GN "Parisian" builder audit → Marais Poitevin village (read-only, 2026-10-20)

## Sources found
- Box: /workspace/lookdev_regalia_v2/src/p/*.py (canonical GN builder scripts)
  - paris_wall_detail.py, paris_track_a.py, paris_escher_ladder.py, nikki_quarter.py, buildings_kit.py, walls_kit.py, euro_kit.py, melodia_house.py, music_aaa.py, music_heroes.py, mother_v3.py, recursive_castle.py, presets.py
- Box .blend (not opened; no Blender on box): lookdev_regalia_v2/v5dev/regalia_v3_final.blend, v5test/regalia_v5_boxfull.blend, earrings_rig/regalia_v4_it2_copy.blend (jewelry, likely irrelevant)
- GN dumps: /workspace/src/gn_dump_R09.json, /workspace/lookdev_melusina_deco_wings/gn_dump_R09.json
- PC fromage: Blender 4.2/4.3/4.5/5.1/5.2 installed (C:\Program Files\Blender Foundation). Filename search for paris/haussmann/mansard/etc under C:\Users\froma was too slow (interrupted); no Parisian .blend located there. Headless node-group listing NOT run (no target .blend found).

## Classification
| Builder (group) | File | Class | Key inputs → style contract |
|---|---|---|---|
| MEL_nikki_quarter (Mode 0 Townhouse) | nikki_quarter.py | **B** | Floors(3→1-2), Floor Height 2.7, Width/Depth, Window Count (rhythm), Roof Mode 0=Hip (use; 1-3 onion/pagoda/clerestory skip), Roof Pitch 0.7(→~0.5 terracotta/0.8 slate), Eave Overhang, Variation/Seed (roughness), toggles Bay Window/Balcony/Lantern/Trim Cornice→OFF, Chimney/Porch/Flower Boxes→ON |
| GN_PARIS_WallDetail | paris_wall_detail.py | **B** | BBox Min/Max, Show Cornice/String/Wainscot/Panels (→off), Show Baseboard (→on as plinth), CORNICE_STYLE int, Panel Scale, Apply Trim UV (trim material slot) |
| GN_PARIS_SlabTrim | paris_wall_detail.py | B | slab/string-course trim; use as plain lime band |
| MEL_modular_house / MEL_auto_building | buildings_kit.py | B | PROPS-dict driven (no literal sockets parsed); wall+baseboard+cornice composition, door/window walls |
| MEL_wall_straight/_corner/_with_door/_with_window/_multi_window/_t_join | walls_kit.py | **A** | wall length/height/thickness, opening count (window rhythm) via PROPS |
| MEL_retaining_wall | walls_kit.py | A | quays/levees along canals |
| MEL_half_timber_wall | walls_kit.py | B | barns/jetty sheds (timber) |
| MEL_wall_arched_window, MEL_gothic_arch | walls_kit/euro_kit | B | round-arch (Romanesque) only; set flat ogive |
| MEL_buttress | euro_kit.py | B | church |
| MEL_math_gothic_cathedral | recursive_castle.py | B | Nave Length/Width, Vault Height(→lower), Buttress Reach, Rose Window Radius, Petal Count → Romanesque church |
| MEL_raycast_facade, MEL_curved/radial_building | buildings_kit.py | C | urban/fantasy forms |
| GN_PARIS_DayNightFacade, fountain loop | paris_track_a.py | C | Facade Width/Height, Tiles X/Y, Relief (tile shader-ish) |
| GN_PARIS_EscherLadder | paris_escher_ladder.py | C | Mansard Landing, Railing; surreal |
| MEL_baroque_facade/niche/balustrade/vault, bifora, cusped/ogee/trefoil, venetian_bridge | euro_kit.py | C | ornamental city |
| MEL_wall_bay_window, arrow_slits, higgsas_colonnade | walls_kit.py | C | |

## Existing systems to reuse
### Piano key walkway
- GN **MEL_imm_piano_keys** (music_aaa.py:581): Octaves 2, Key Width 0.22, Key Depth 0.9, Key Height 0.09, Black Length Ratio 0.62, Scale. Black-key pattern implied by octave layout. No spline input / rail / sound.
- GN **MEL_music_piano_roll** (music_heroes.py:473): Key Width, Key Length, Key Height, Profile, Key Count 24, Endless, Length 4.0, Pitch Start, Black Offset, Realize for export. Best for a timber-plank jetty walkway (Key Width=plank, Length=path length).
- GN **MEL_mother_walkway_straight/curved** (mother_v3.py:45/126) + MEL_mother_walkway_pylon: Length/Radius, Angle, Width (deck), Fold Depth/Frequency, Tension. Deck only.
- GN MEL_pergola_walkway (castle_extras.py:656): rails/pergola deck.
- UE: Content\EnvSandbox\Materials\Instances\PianoPath\MI_PianoKey_{FarawayFabric,MorningMeadow}_{Ebony,Ivory}.uasset (material instances only; no Piano BP/PCG found by filename). Note/sound hookup not found in filesystem names.
### Cathedral
- GN MEL_math_gothic_cathedral (above), p4_crystal_cathedral.py (C, crystal).
- UE: Content\Dev\TouchEngineG0\BP_TE_Cathedral_Harness.uasset; Content\EnvSandbox\Meshes\Cathedral\SM_Cathedral_* (Buttress, Portal, Spire, LancetWindow, RoseWindow, Crypt, Chapel, ResonantDoor, Pier…); MI_Cathedral_Stone/Rock, MI_Env_Stone_Cathedral. Stone/Buttress/Portal/Pier/Crypt usable (B) for Romanesque church; Escher/Orb/Bifrost C.
### Room shell
- GN MEL_mh6_room_shell (melodia_house.py:59): Width 4.2, Depth, Height 3.42, Curve, Wall Thickness, Cornice Rise/Depth, Opening Columns/Rows/Scale, Voxel Size, Seed.
- GN MEL_music_room_shell (music_heroes.py:779): Room Length/Width/Height, Wall Thickness, Ceiling, Cut Door, Cut Window, Dado Staff Band, Dado Height... → good interior shell (A with Dado Staff Band off).
- UE: Content\EnvSandbox\Blueprints\House\BP_MelusinaRoomShell.uasset (exposed vars not readable without editor).
