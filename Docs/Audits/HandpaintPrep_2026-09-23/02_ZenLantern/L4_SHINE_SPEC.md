# L4 Shine Stack — ZenLantern V2

Date: 2026-09-24
Depends on: L1+L2 (done) · L3 morph FBX (done) · handpaint base (owner Painter / Substance)

## Goal
Layered, audio-reactive shine on `MI_Handpaint_ZenLantern` (or Melodia Toon/Nikki equivalent),
all read-only consumers of `MPC_Melodia_Palette`. No second audio writer.

## Stack (bottom → top)
1. **Handpainted base** — Substance pass on V2 / showcase (stone body, Nikki palette per paint_guide).
2. **Cymatic emissive** — `T_Cymatic_FrozenFracture_Emissive` × vcol A (fire box); intensity = BeatPulse × vcol B.
3. **Iridescence rim** — FrozenFracture_Iridescence on roof ribs + charm bevels only.
4. **Warm core light** — point light at fire box; intensity f(BeatPulse); color from audio palette.
5. **Niagara micro-sparkles** — G-zone (eaves) emit 2–3 petal-sparkles on beat (`NS_Melodia_PetalLoop` family).
6. **Night lookdev** — L_FallenMoon dusk vs `W_Melodia_FadeDayNight`; lantern = cymatic beacon.

## Morph ↔ shine coupling (from L3)
| Morph | Shine coupling |
|---|---|
| SK_FlameBreath | Scale emissive + core light with same BeatPulse |
| SK_RoofLift | One-shot inner-glow reveal when morph > 0.5 |
| SK_CharmSway_L/R | Sparkle spawn rate × BassIntensity |
| SK_DawnDusk | Lerp warm/cool emissive tint with FadeDayNight |

## Owner gates (cannot finish headless)
- Import `ZenLantern_V2_L3_morphs.fbx` with morph targets enabled
- Apply / create `MI_Handpaint_ZenLantern` (Ctrl+S only — never Monolith save_packages)
- Wire MPC + Niagara in editor lookdev level
- Painter: finish SMS apply + Create smart material → real `.spsm`

## Agent-deliverable this pass
- This SPEC
- L5 evidence checklist with L3 morph reimport proof filled in
- Import notes for morph FBX

## Paths
- Morph FBX: `Saved\KimiWork\HandpaintPrep_2026-09-23\02_ZenLantern\substance\meshes\ZenLantern_V2_L3_morphs.fbx`
- L3 receipt: `...\02_ZenLantern\L3_MORPH_RECEIPT.md`
