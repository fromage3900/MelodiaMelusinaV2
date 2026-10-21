# Sonic Identity Integration Guide
1. Generate 4-hit grade set from seed in ElevenLabs Sound Effects
2. Export WAVs: SFX_Hit_Perfect.wav, SFX_Hit_Great.wav, SFX_Hit_Good.wav, SFX_Hit_Miss.wav
3. Copy to Content/Melodia/Audio/Generated/SonicIdentity/
4. Import in UE (48kHz mono, normalize to match existing)
5. Update HitMetaSound to use these or component will fallback to default
6. Test in PIE with dense phrases
