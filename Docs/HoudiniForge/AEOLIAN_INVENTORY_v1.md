# AEOLIAN INVENTORY v1 (read-only scan, 2026-10-15 ~1:10 PM ET)
Retargeted from riverbed to the Aeolian cliff. Nothing was modified. GP = Saved/Staging/GrokPrep, C = Content.

## TouchDesigner
- No .toe/.tox file or .tdn network mentions "aeolian". Searched Documents and Desktop (G:\ and C:\EnvironmentPortfolio were not searched for TD).
- TD files found: Documents\Codex\worktrees\melusina-airi-bridge-p0\_TouchDesigner\grandmaster_melodia\grandmaster_melodia(.2).toe (compressed, so no readable strings); networks\*.tdn (text); exports\nikki_sanctuary.fbx + world.json, nikki_gazebo_viewport.png; components\nikki_particles.py.
- TouchEngine tox files in ue_export_sandbox\Content\Melodia\TouchEngine: melodia_te_canary_v1, melodia_te_cathedral_field_v1, melodia_te_chladni_field_v1. The Chladni tox fits Aeolian thematically.

## Hero geometry (GP/aeolian_cliff, FBX, NOT imported into UE)
- weingarten/fbx/SM_GPX_Weingarten_Facade.fbx: pass 3 = final. 91 pipes, 283k tris, 277x64x187 m, 2 slots (MI_GP_Body/Accent), 1uu=1cm. Contains 16 bells, pearls, shells, finials and staff bars. No LODs or collision, planar UVs (use triplanar).
- weingarten/fbx/SM_GPX_Weingarten_RoseTracery.fbx: 65k tris, Chladni-bar tracery for the 5 windows. Shares the facade origin.
- weingarten/fbx/SM_GPX_Weingarten_Facade_v2.fbx: archive, do not import. There is no separate v3 FBX; v3 exists only as look renders (look/v3_*.png, identical to front/hero/top).
- organ_kit/fbx: SM_GP_OrganFront_Cmaj15 + 15 SM_GP_OrganPipe_{A..G}{2,3}, C4.
- singing_tree/fbx/SM_GPX_SingingTree_Organ.fbx (hero, top and side renders).
- houdini_cliff: cliff_rock_only_col.obj (53k tris, rock collision with window recesses and tunnel bore), windows.json (15 windows + 2 portals), facade_sites.json (3 sites: S0_Amin7, S2_Dmin, S4_Gdom7, with yaw and scale), erosion_A/harmony_height.r16 (picked terrain).
## Textures / VFX data
- houdini/out: T_Aeolian_ChladniRipple_8x8, GlassShimmer_4x4, StaffInk_8x8 flipbooks; T_SDF_Aeolian_ChladniNodal (8/16-bit), OrganPipeMouth, WeingartenTowers.
- houdini_wind/out_houdini/export: VF_AeolianWind_{Facade, CentreOpening60m, InnerOpeningL60m, MouthC0_500cm}.fga vector fields + pipe_speak_table.csv/json.
- chladni_paths/aeolian: chord-pad paths for Amin7, Fmaj7, Dmin, Bdim, Gdom7 (csv/json/png + transitions).
- aeolian_fx_pack.v1.json, layout/aeolian_layout_preview.json, aeolian_cliff_harmony.proposal.json.

## In UE: C/Staging/Aeolian (imported)
- Systems (NS_*): WindRibbonGust, SakuraPetalGust, Uni_{DustShafts, Fireflies, GroundWisps, LeafDrift, MistSheet, PollenSparkle, WaterMist, RainRipples}, ConstellationTwinkle/Draw, FairyDust, EmberMotes, MagicTrail, SDF_Foliage_{Grass, Bush, Vine}, SDF_Parallax*, Melodia_PetalEndlessLoop/LeafPileLoop, plus *_Candidate variants.
- Materials: MI_Niagara_Gust, AuroraRibbon, Melodia_MusicStaff, Melodia_NoteBeam, LanternFiligree, MistGrain, Stardust, Morning_DustShaft, and others.
- SDF textures: T_SDF_MusicNote, Sparkle6, SparkleHalo, StarGlitter, Rosette, and others. Flipbooks: BrassPatina, CelestialSilk, CymaticPulse atlases.
- No Aeolian .umap anywhere in Content. No Weingarten, organ or singing-tree uasset.

## Bells / notes / clefs / Nikki
- C/Staging/HoudiniForge/Carillon: creatures BellSpirit (v1), ChandelierWraith (v2), BellGolem (v3), InvertedTower (v5), each in Arch and Awake poses; ~65 parts (Bell_A5..C6 and variants, Halo, Filigree, Crown, Plinth, Post, Yoke, Canopy, Spire); SKM_Carillon_Cords.
- C/Staging/HoudiniForge/Gaudy: ChimeSnail, PearlJellybell (+Queen), NPC_Dingle. LittleGuys/MusicBoxMimic v3. NPC/Dingle LOD.
- C/EnvSandbox/Meshes/OrnamentMusical: SM_Orn_TrebleClef, SM_Orn_NoteHead, SM_Orn_NoteBeam. EnvSandbox/Meshes/Environment: Bell_Art, BellStructure_Art.
- C/Melodia/Meshes/MusicRail_AAA: Notes_2m/8m, ClefCap_2m.
- SDF materials: MI_SDF_TrebleClef_Ornament, MI_SDF_FloatingNotes_Default, MI_SDF_Rock_Stembell.
- PCG: EnvSandbox/PCG/Musical/Hero/PCG_Hero_BellTreeGarden (+ L_PCG_Hero_BellTreeGarden.umap), PCG_Nikki_DreamStones, MandalaBloom, PhyllotaxisGarden(_Walkable), PCG_SeaAbove_BellTreeGarden.
- Nikki builders (Content/Python): pcg_nikki_scene_dressing.py, build_pcg_ornamental.py, setup_ornament_demo_level.py, musical_ornament_kitbash_catalog.py, generate_wp_setdress_handoff.py, build_nikki_masters.py. Nikki materials: M_Master_Nikki, MI_NikkiHero_*, MI_Nikki_Tier_*, MF_Nikki*.

## Referenced but missing
- Weingarten facade, RoseTracery, organ kit and singing tree have not been imported to /Game/Staging/Aeolian.
- MI_GP_Body / MI_GP_Accent are named as slots; not found in Content by name.
- No merged cliff+facade collision (cliff_collision.obj is not created yet).
- The facade has not been refit to the real houdini_cliff/windows.json.
- The FBX Y-flip/yaw has not been verified in engine.
- Known issues: the Gdom7 recesses intersect the tunnel, and the facades float 8-54 m above the ground.
- Some weingarten_tuning.csv entries still say 82 pipes (pass-1 data).

## Suggestions (presentation)
1. Import Facade + RoseTracery (scale 1, triplanar gold) at site S0_Amin7 from facade_sites.json, against cliff_rock_only_col.obj. This is the hero shot.
2. Set the Carillon creatures (BellSpirit/BellGolem Awake) and Bell parts on the cliff ledges or plinths, using the 16 bell anchors in bake_report decor.bells as placement hints.
3. Wind read: NS_WindRibbonGust + NS_SakuraPetalGust + NS_Uni_DustShafts through the windows; optionally drive with VF_AeolianWind_Facade.fga.
4. Path dressing along the Amin7 chord-pad path: run PCG_Hero_BellTreeGarden / pcg_nikki_scene_dressing with SM_Orn_TrebleClef/NoteHead and MusicRail Notes_8m, plus MI_SDF_FloatingNotes.
5. Ambient: ChimeSnail and PearlJellybell, SingingTree_Organ as a midground landmark, NS_Uni_Fireflies/PollenSparkle, and T_Aeolian_ChladniRipple on the ground decals.
