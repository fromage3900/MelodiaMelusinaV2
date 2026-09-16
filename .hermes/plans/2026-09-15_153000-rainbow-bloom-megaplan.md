# RAINBOW BLOOM MEGAPLAN — Melusina's Morning flower field (2026-09-15)

Fit for a queen: a FULL floral carpet ringing the pond, seven rainbow bands
by radius, breathing with the music. No live cooking, no new authorities.

## Why it works (proven, not promised)

- Toon master ALREADY reads the music: binary scan of
  `M_Master_Toon_Universal.uasset` confirms `Cymatic_BeatPulse`,
  `Cymatic_BassIntensity`, `Cymatic_MidIntensity`,
  `Cymatic_EmissiveScale`, `Cymatic_IridescenceShift`,
  `Cymatic_UVDistortion`, plus `BeatPulse`, `BaseTint`, `DreamTint`,
  `EmissiveColor`, `EmissiveMapTint`. Contract: `MelodiaCymaticsWriterSubsystem.h`
  (palette -> driver mapping), published by
  `UMelodiaAudioReactivePresentationSubsystem` (presentation ONLY — rhythm
  authority untouched, Quartz timing untouched).
- Petals exist: `M_GhostPetalInner/Mid/Outer` + maps
  (`T_Surreal_GhostLotus_Albedo/Emissive/Normal/Roughness/Translucency`).
- Placement pattern proven today: phyllotaxis scatter + trace-ground +
  save + reload-recount (house dell 71/71).

## Design

- Center: pond centroid (computed from dell manifest at runtime, never guessed).
- 7 bands, radius-stepped: red, orange, gold, green, blue, indigo, violet.
  One MI per band (`MI_RainbowPetal_B0..B6`), parent toon master, differing
  ONLY in `BaseTint` (+ shared GhostLotus maps). No master edits, freeze-safe.
- Audio reaction is FREE: master's Cymatic wiring pulses emissive on the beat,
  shifts iridescence with bass. If `BaseTint` won't take vectors via Monolith,
  fallback: numpy-tinted albedo variants (offline bake, house rule safe).
- Field: ~700-1000 instances, 7 ISM actors (`RainbowBloom_B0..B6`),
  golden-angle spiral, density falling with radius, trace-grounded, random
  yaw + scale breath per instance.
- Synergy: Dawnmotes drift above; brook stones + bells remain the banks.

## Execution order

1. Forge 7 MIs + set BaseTint per band (this script batch).
2. Place field (phyllotaxis, grounded, saved, reload-proven).
3. PIE capture 25s + brightness/color bill.
4. Scoped commit: MIs + actors + proofs. Strangers' dirt untouched.

## Gates

- Beauty: owner viewport. Telemetry: instance counts per band, PIE means
  steady, zero errors. Ledger: manifest JSON next to frames.
