# Melodia Opening — Implementation Handoff

## Current playable route

`L_Melodia_Dreamstate` is the project entry map. The player starts on the
floating bridge and can cross the `Dreamstate_WakePortal` to open
`L_MelusinaMorning`. `ZenForestTest` remains the isolated combat smoke-test
map; it is no longer the game entry point.

The authoring script deliberately uses the existing Unreal house kit, not the
placeholder Blender scenes. Its ownership is limited to the two new opening
maps and labelled actors so it is safe to rerun.

## State already wired

- `AMelodiaOpeningStateAnchor` owns a Resonance Bond and Dissonance component.
- The bond starts **Absent**: songcraft is not empowered until Sir Melodious is
  reunited and resonant.
- Dreamstate has `SongcraftScalar = 0.75`, making the opening’s emotional
  strain mechanically inspectable before a visual Dissonance binding exists.
- The bedroom contains `Morning_SirMelodiousPerch_PROXY_REPLACE`; replace only
  that labelled proxy when the cockatoo skeletal mesh is imported.

## Sir Melodious import gate

1. Import the cockatoo skeletal mesh, skeleton, materials, and animations into
   `/Game/Melodia/Characters/SirMelodious` without changing the source asset.
2. Create `BP_SirMelodious` from the imported mesh and place it at the perch.
3. On the reunion beat, call `SetBondState(Resonant)` on the active opening
   state anchor. Do not silently set the state from **Absent** at level load.
4. Add the future human/bird switching component only after foot traversal and
   the reunion encounter are play-tested; the vertical slice introduces the
   companion but does not falsely promise flight immediately.

## First visible Dissonance beat

The next authored task is a short trigger near the bridge midpoint:

1. Set Dissonance to **Strain** and keep SongcraftScalar at 0.75.
2. Drive a post-process material/audio layer from the component’s state-change
   event: slight chromatic separation, unstable sky light, and detuned ambience.
3. Restore visual stability only after the bedroom/reunion beat; do not turn
   the first 90 seconds into horror spectacle.

## Required manual acceptance test

In PIE or a packaged Development build:

1. Launch the project; it should begin on `L_Melodia_Dreamstate`.
2. Walk across the bridge and enter the Wake portal.
3. Confirm it opens `L_MelusinaMorning`, spawns safely in the room, and the
   cockatoo perch marker is visible.
4. Confirm Songcraft cannot be treated as empowered while the bond is Absent.

The structural map verification is automated by
`Content/Python/verify_melodia_opening_levels.py`; the traversal remains a
human play-test because it depends on the current Melusina animation/controller
work.
