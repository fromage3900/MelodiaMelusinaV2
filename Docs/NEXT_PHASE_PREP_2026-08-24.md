# Next Phase Prep — P0 Vertical Slice Completion — 2026-08-24

## Goal
Close the remaining P0 gates so the Melodia/Melusina vertical slice is
playable: rhythm combat feels responsive, the HUD is coherent, and musical
world-gen has real visual variety.

## Current commit
`b8f5b10f` — docs: review and expand Melodia Melusina pipeline

## Open gates from last review
- `hud_single_writer`
- `rhythm_grade_to_result`
- `music_world_key`
- `wardrobe_equip_roundtrip`
- `wardrobe_gameplay_hook`
- `rhythm_owner`
- D7: preset divisors ignored
- D14: v5 renders not visually validated
- D16: 37 GeneratedScenes missing material/UVs
- D17: only 1 substantive MIDI asset

---

## Phase priority

### P1 — Fix the blockers that are cheap and proven

1. **D7: expose preset divisors in `midi_voxel_v3.generate()`**
   - Add optional `surface_div`/`cave_div` kwargs defaulting to 32/40
   - Update `midi_bridge.py` to pass preset divisors through
   - Update `test_height_divisors_are_honoured` from expectedFailure to real test
   - Evidence: `test_height_divisors_are_honoured` passes

2. **Merge HUD writers**
   - Merge `MelodiaJRPGBattleOverlaySubsystem` into `MelodiaUIBridgeSubsystem`
   - Keep all widget creation on one owner
   - Evidence: grep for `CreateWidget` in both files drops to zero in battle overlay

3. **Add render verification harness**
   - Capture per-preset SHA + bounding-box stats
   - Prove D7 fix produced visually distinct outputs
   - Evidence: new `Docs/Evidence/midi_preset_sha_<date>.json`

### P2 — Wire the rhythm combat feel

4. **Rhythm grade -> effect request**
   - Port `MelodiaGlobalEconomy` clamp/chain rules from `deploy/melodia_economy.py` to C++
   - Start with `cast_utility_debuff` (mana drain)
   - Add parity tests: Python oracle vs C++ must match for identical inputs
   - Evidence: `MelodiaRhythmCombatTests.cpp` covers grade boundaries

5. **Stock resolver handshake**
   - Rhythm adapter emits exactly one `FMelodiaRhythmEffectRequest`
   - Stock skill resolver applies it exactly once
   - Evidence: dev log includes skill ID, session ID, grade, magnitude

### P3 — World-gen quality of life

6. **Author 2+ substantive MIDI assets**
   - Target 200+ notes with clear phrases
   - Place in `Content/MelodiaIntegration/MIDI/`
   - Evidence: `128BPMarpeggiomelody.mid` is 192 notes; new asset >= 200

7. **Gaea heightfield export**
   - Export v4 walkable field as 16-bit PNG
   - Verify `Gaea.Build.exe` CLI contract
   - Evidence: `Saved/Audit/gaea_heightfield_<date>.png` + CLI log

### P4 — Polish and validation

8. **Owner visual review of v5 renders**
9. ** wardrobe equip roundtrip + gameplay hook**
10. ** Full PIE acceptance loop**

---

## Immediate next actions

1. Fix D7 in `Tools/midi_to_voxel/midi_voxel_v3.py`
2. Update `melodia_studio/midi_bridge.py` to pass divisors through
3. Remove expectedFailure from `test_height_divisors_are_honoured`
4. Run: `python3.11 -B -m unittest discover -s Tools/BlenderAddons/melodia_studio/tests -v`
5. Merge HUD writers in `Source/BS_GodFile/MelodiaIntegration/`
6. Start economy parity test scaffold

---

## Evidence to collect

| Action | Evidence file | Gate |
|---|---|---|
| Fix D7 | `Docs/Evidence/midi_preset_sha_<date>.json` | preset variety measurable |
| Merge HUD writers | grep `CreateWidget` in battle overlay -> 0 | single writer |
| Economy parity | `MelodiaRhythmCombatTests.cpp` new test | C++ matches Python |
| Rhythm wiring | dev log sample with skill/session/grade | resolver handshake |
| Gaea export | `Saved/Audit/gaea_heightfield_<date>.png` | heightfield valid |

---

## Files to touch

- `Tools/midi_to_voxel/midi_voxel_v3.py`
- `Tools/BlenderAddons/melodia_studio/midi_bridge.py`
- `Tools/BlenderAddons/melodia_studio/tests/test_midi_bridge.py`
- `Source/BS_GodFile/MelodiaIntegration/MelodiaUIBridgeSubsystem.cpp/.h`
- `Source/BS_GodFile/MelodiaIntegration/MelodiaJRPGBattleOverlaySubsystem.cpp/.h`
- `deploy/melodia_economy.py` (reference)
- `Source/BS_GodFile/MelodiaIntegration/MelodiaRhythmCombatSubsystem.cpp/.h`
- `Source/BS_GodFile/MelodiaIntegration/MelodiaRhythmCombatTests.cpp`

---

## Out of scope for this phase

- Gaea erosion graph authoring
- Geometry-Nodes scatter at 10k+ density
- UE5 landscape/PCG import pipeline
- Oceanology plugin investigation
- Portfolio website updates
