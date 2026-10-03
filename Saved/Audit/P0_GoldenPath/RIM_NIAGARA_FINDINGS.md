# Rim + Niagara findings (read-only, 2026-10-02)

## 1. "Magic dream rim" = a feature of M_Master_Toon_Universal
- Docs/Production/DREAM_SYSTEM.md group 10b: fresnel x IQ thin-film palette, gated by static/bool `bDreamRim_Active`.
  Params (verified on master via material_query): DreamRimColor/Power/Cycles/Strength, plus RimColor/Power/Intensity/Width/Bias/Clamp,
  ContactRim*, Grazing_Rim_Boost/Tint. Also 10e Dream Pulse (`DreamPulseAmp`), 10j DreamHalo. All default OFF.
- Master has 12 MPC CollectionParameter nodes; GlobalEmissiveBoost (MPC_Melodia_Palette) multiplies the whole dream emissive stack
  (so rim glow is scaled level-wide by the MPC). Per-collection mapping of the 12 nodes not verified.
- Beat driver: Plugins/MelodiaCore/.../MelodiaRhythmReactivitySubsystem.cpp PublishToReactiveMaterials() (~L366) sets on registered
  MIDs: DreamPulseAmp=BeatPulse, Iridescence=BeatPulse, TemporalStrength=CommandEnergy, ParallaxStrength=BeatPulse.
  It touches MIDs only (needs component registered via the subsystem's reactive-material registration; stencil helper SetReactiveStencil exists).
  It does NOT drive DreamRimStrength; DreamPulseAmp breathes the whole emissive (rim included only when bDreamRim_Active).
- M_Nikki masters: no param named *Rim* on M_Master_Nikki (290 expr); Content/Python/annotate_master_columns.py claims a "Nikki Rim & Glow" column
  (RimColor/DreamRim variant) - applies to Toon_Universal column scheme, not M_Master_Nikki itself.
- Rim lights/PPV: Polish_Rim_* names appear only in setup scripts (melusina_lookdev_studio.py etc.); not queried in level.

## 2. M_Piano_Surface (/Game/EnvSandbox/PCG/Musical/M_Piano_Surface)
- 4 expressions only: BaseColor, Roughness, Specular, ClearCoat. Reads NO MPC, no rim, no emissive. MI_Piano_Ivory/Ebony/Keybed cannot react to beat.

## 3. Recommendation (no master edit)
- Make new MI_PianoKeyRim_* (new instances, allowed) parented to M_Master_Toon_Universal (or an existing MI under
  /Game/EnvSandbox/Materials/Instances/MelusinaReal/M_Master_Toon_Universal/ e.g. MI_..._Crystal): set bDreamRim_Active=1, DreamRimStrength/Color,
  DreamPulseAmp>0; GlobalEmissiveBoost already MPC-driven. For beat reaction either (a) register the key mesh with
  UMelodiaRhythmReactivitySubsystem (drives DreamPulseAmp/Iridescence per beat) or (b) drive DreamRimStrength per key from the piano actor MID.
  Use rim only on the key top/ring mesh; keep Ivory/Ebony body unchanged.
- Check first that the Toon master's MPC nodes include BeatPulse-type scalars (MPC_Melodia_Palette has BeatPulse/BeatPhase per the subsystem comment, writer = C++ subsystem).

## 4. Niagara <-> MPC
- Niagara cannot sample MPC. Twin: /Game/EnvSandbox/VFX/MPC/NPC_Melodia_Palette (namespace NPC.MelodiaPalette, 71 params: BeatPulse, BeatIntensity,
  BeatPhase, RhythmPulse, GlobalEmissiveBoost, GlobalSparkleIntensity, PaletteShift, PlayerProximity, DayCyclePhase, SeasonBlend, ...).
  Also NPC_SakuraDream, MPC_SakuraDream in same folder.
- Writer: BS_GodFile MelodiaAudioReactivePresentationSubsystem.cpp (AudioNpcPath ~L29, load L206, write ~L396-428) via
  UNiagaraFunctionLibrary::GetNiagaraParameterCollection -> SetFloatParameter(GlobalReactivity,Bass,Mid,Treble,BeatPhase,BeatPulse,BeatIntensity,
  ComboNormalized,CrescendoNormalized,CommandEnergy,RhythmPulse,BreakPulse,VictoryPulse,EnemyTension). Missing asset => graceful disable.
- Readers: could not confirm any system binds NPC.MelodiaPalette.* (niagara search returned none for that name). Other scripts referencing the NPC:
  Content/Python/{ppv_contract,bind_ppv_audio_contract,setup_zenforest_musical_glam,Tools/FarawayMother/faraway_cymatic_driver}.py.
- Existing systems instead expose per-component User.* floats (BeatPulse found on 34 systems); they need a component writer, not the NPC.

## 5. Reuse set for a path trail (all have User.BeatPulse, RhythmPulse, AudioLow/Mid/High, GlobalReactivity, Intensity, DreamVisibility, ReactionColor, PitchHue*, Seed)
1. /Game/Melodia/Characters/Melusina/Weapons/WaveHarp/NS_WaveHarp_ArrowTrail (+TargetPosition, ImpactPosition, ChladniDrive) - best ribbon/trail.
2. /Game/Melodia/Companions/ChoralSheep/VFX/NS_ChoralSheep_MotionTrails - trailing ribbons.
3. /Game/Melodia/VFX/NS_Melusina_SwingTrail - AudioLow/Mid/High, BeatPulse, DreamVisibility, GlobalReactivity, ImpactPosition.
4. /Game/Melodia/Companions/ChoralSheep/VFX/NS_ChoralSheep_PetalCascade (petal motes, +WindVector, WoolGlow).
5. /Game/Melodia/VFX/NS_Morning_PetalDrift (+BandHue, HueSeed, PetalSpawnMultiplier) / NS_Morning_PollenMote / NS_Melusina_StarSparkle for key-hit glints.
(*PitchHue on ChoralSheep/WaveHarp set, BandHue on Morning.) Who writes User.* : whoever spawns the component (SetVariableFloat) - per-key hit code must do it.

## 6. Missing
- A per-key hit hook feeding either NPC or a per-component User.BeatPulse/ReactionColor (PCGPianoKeyboard.cpp currently modified/uncommitted).
- Rim MIs for keys; confirmation any Niagara system reads NPC.MelodiaPalette.

## 7. Needs owner approval
- Any edit of M_Master_Toon_Universal / M_Piano_Surface (masters). Adding MIs and spawning existing NS = fine. Touching C++ (uncommitted PCGPianoKeyboard.*) and Config = owner.
