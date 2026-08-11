# Harmonix MIDI Rhythm Contract — 2026-07-29

## Decision

Harmonix is enabled as Melodia's **authored musical-time and MIDI-asset
layer**. MIDI Device Support is also enabled for optional external-controller
prototyping. Both are presentation/input systems: the stock JRPG template
continues to own command validation, damage, targets, terminal battle result,
turn release, party state, and save state.

Harmonix is experimental in UE 5.8. Treat this as a controlled content lane:
one authored song at a time, with an explicit fallback to normal stock skill
execution.

## Authoring flow

1. Import a `.mid` file into `/Game/Melodia/Audio/MIDI/`.
2. Create a Harmonix MetaSound music source using that MIDI asset, a Music
   Clock, and a musical transport.
3. Expose beat/bar events to a dedicated presentation actor/widget.
4. Associate the source with one stock skill presentation profile:
   montage, VFX cue, UI timing ring, and optional SFX stems.
5. Test the skill with the timing layer disabled. It must still execute the
   normal stock attack once.
6. Enable the timing layer and verify it can only decorate an already-valid
   stock command; it may never issue damage or advance a turn itself.

## MIDI boundaries

| MIDI type | Use | Forbidden use |
| --- | --- | --- |
| Imported MIDI file | authored tempo, bars, note lanes, VFX/UI timing | authoritative damage timing |
| Music Clock | presentation beat/bar callbacks, animation/VFX alignment | battle completion / result routing |
| External MIDI Device | optional accessibility/prototype input | bypassing the stock command UI or save flow |
| MetaSound/Fusion | music playback, instrument layers, reactive stems | quest, inventory, party, or travel state |

## First proof asset

Create one `DA_MelodiaRhythmProfile_PetalSever` with:

- one `.mid` source at a fixed BPM;
- one bar and one obvious downbeat;
- `AM_Mocap_BasicAttack` as its visual presentation;
- a UI pulse and petal VFX on the downbeat;
- no gameplay multiplier until stock battle and presentation timing are
  visually signed off.

## External MIDI safety

MIDI Device Support streams live device messages. Bind external notes only to
the existing input action for a currently available stock command, and make
keyboard/controller input remain fully functional. Do not make a hardware
device required for a normal playthrough.

## Required evidence before promotion

- Imported MIDI asset plays through a Harmonix music source.
- Music Clock drives one visible UI/VFX beat accurately enough for capture.
- A stock battle skill still works with Harmonix disabled.
- With Harmonix enabled: one command, one montage, one stock impact, one
  target/result, one turn release.
- No MIDI route writes canonical save, quest, inventory, party, or combat
  state directly.
