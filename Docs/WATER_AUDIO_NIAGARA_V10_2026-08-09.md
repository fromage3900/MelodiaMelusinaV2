# Water v10 audio + Niagara integration — 2026-08-09

## Implemented

- Added `UMelodiaWaterAudioBridgeComponent` as a gameplay-owned consumer of the normalized water contact bus.
- Added bounded MetaSound routing for surface movement, surface entry, underwater bubble, impact, and re-emergence.
- Added per-profile audio event/voice budgets, project-owned concurrency, and 3D attenuation.
- Added runtime parameters for intensity, immersion, velocity, and depth; event volume/pitch are derived from the water packet.
- Added a 0.28 s default movement cadence while swimming. It emits normalized `Ripple` contacts only while moving, so surface strokes and underwater bubble motion are audible continuously without per-frame spam. Underwater ripples resolve to `MS_Water_UnderwaterBubble`; surface ripples resolve to `MS_Water_SurfaceMovement`.
- Added an opt-in quantum/Nikki Niagara overlay to the Water bridge. It reads the shared `MPC_Melodia_Palette` values (`QuantumReactionColor`, `QuantumPulse`, `QuantumChoice`, `QuantumSeed`, and `QuantumBackend`) and writes them to existing conformed systems.
- Ordinary contact/ripple/splash presentation remains independent. `NS_Melusina_ChaosDrift` and `NS_Melusina_EntropyDust` are only spawned during a live quantum pulse and are capped at two reactions per second by default.

## Project-owned assets

Water audio assets live under `/Game/EnvSandbox/Water/v10/Audio/`:

- `MS_Water_SurfaceMovement`
- `MS_Water_SurfaceEntry`
- `MS_Water_UnderwaterBubble`
- `MS_Water_Impact`
- `MS_Water_Reemergence`
- `SC_WaterV10_AudioConcurrency`
- `SA_WaterV10_3D_Attenuation`

The MetaSounds wrap existing project-approved water source waves and are saved as project assets. The source waves are not edited. The quantum overlay references the existing project-owned systems `/Game/Melodia/VFX/NS_Melusina_ChaosDrift` and `/Game/Melodia/VFX/NS_Melusina_EntropyDust`.

## Text-injection seam

`Content/Python/bind_water_v10_audio_niagara_profile.py` is a guarded profile manifest. It validates every asset and every reflected property before saving `DA_WaterV10_Default`. It must be run after a normal editor restart because the currently attached editor still has pre-rebuild reflection; runtime C++ also seeds the same defaults as a compatibility fallback.

## Validation status

- UHT/non-unity build: passed in `Saved/Logs/WaterSwimCadenceBuildFix_20260809.log`.
- MetaSound graph authoring: five sources built successfully through `MetaSoundEditorSubsystem.build_to_asset`.
- Concurrency/attenuation authoring: both assets created and saved successfully.
- Quantum Niagara source integration: compiled successfully; runtime PIE proof is pending the controlled editor restart and profile bind.
- Full entry/swim/dive/impact/re-emergence audio capture, device playback confirmation, gameplay-map performance, and Tier 3/4 FLIP promotion remain open gates.

## Safety boundary

No engine plugin assets, third-party Water/UDS assets, general BGM/UI audio assets, or the other editor instance were modified or terminated.
