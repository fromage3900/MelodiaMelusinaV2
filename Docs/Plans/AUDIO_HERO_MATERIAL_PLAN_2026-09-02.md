# AUDIO-REACTIVE HERO MATERIAL — UPDATED PLAN (2026-09-02)

Reusable, long-term audio-reactive HERO ASSET for BS_GodFile. One audio->material
"brain" (neural onnx) + one polished cymatic hero-gem PBR family, both driven by the
project's SINGLE audio writer, staged into the hero's own level per standing directives.

Supersedes-as-plan: the 08-31 spike fragment for "reusable hero asset." Keep the
Emerging-Toolchain Master Index (08-31) as the SSOT for what is PRESENT/SCAFFOLDED.

## 1. Research deepen (2026-09-02) — Infinity Nikki + cymatics

### Infinity Nikki (official UE interview + companion coverage)
- **Versatile master material** that merges fabric textures, reduces variants, portable
  across platforms -> repo already mirrors this (M_Master_Nikki / M_Master_Toon_Universal,
  single audio MPC writer).
- **Jewellery/accessory material (the HERO GEM recipe):** opaque, Cubemap-based
  refraction/reflection + subsurface scattering (3S) + highlights. This is the hero-gem
  target: low roughness facets, high reflection, subsurface glow, specular highlights.
- **OIT** redeployed for sheer/silk semi-transparency (Fairytale Swan) — relevant when the
  hero gem is set in a sheer fabric.
- **Standardized PBR inputs** + modified ambient boxes for Lumen consistency — validates
  feeding the hero gem from a normalized PBR set, not bespoke properties.
- **WPO for lightweight reactive motion; Chaos for precision** — the gem uses WPO (emissive
  displacement) so no heavy sim.

### Cymatics (physics-accurate sources: cymatrix, wavefield, cymatics-labs, schladni)
- **Frequency->mode law** `m = round(sqrt(f/220)*3), n = round(sqrt(f/220)*5)` couples
  pitch to Chladni complexity. Adopted: the hero gem's chladni_modes run bass->treble.
- **Lorentzian forced-damped resonance** — figure only forms at eigenfrequency; a purer
  future mode-selector (drive (m,n) from the MPC band peaks).
- **FFT band partition -> bass/mid/treble** maps directly onto the existing
  MPC_Melodia_Palette (BassIntensity / BeatIntensity / BeatPhase / BeatPulse / BeatTracker).
- **Multi-oscillator interference + standing-wave phase crawl** = the 8-frame flipbook loop.

## 2. Architecture contract (single-writer preserved)

```
MusicClock -> UMelodiaAudioReactivePresentationSubsystem   (THE single MPC *audio* writer)
                  -> MPC_Melodia_Palette: BassIntensity, BeatIntensity, BeatPhase,
                                          BeatPulse, BeatTracker   [verified names]
                          |  read-only (no second writer)
                          v
   UMelodiaNeuralHeroMaterialSubsystem (SCAFFOLDED, needs closed-editor build)
     hero_material_controller.onnx  (5 MPC features -> 5 hero params, VERIFIED 7/7)
     -> writes computed hero params to subsystem-owned MPC_Hero_Material
        (EmissiveStrength / EmissiveTint / SubsurfaceScatter / Displacement / SpecBoost)
                          |
                          v
   Hero gem material (M_Master_Toon_Universal MI) + cymatic PBR maps (MelodiaHeroGem)
```

- The onnx is the REUSABLE brain: any hero asset (crystal, fabric, water-glass) shares it.
- The single MPC audio writer is unchanged; cymatics + neural are READ-ONLY consumers.

## 3. Built & VERIFIED tonight

| Piece | Path | Proof |
|---|---|---|
| Hero-material controller onnx (5->16->12->5 MLP) | `Tools/Audio/models/hero_material_controller.onnx` | `hero_neural_material_verify.py` **7/7 PASS** (deterministic, [0,1], responsive Δ0.358) |
| Controller builder | `Tools/Audio/hero_neural_material_controller.py` | seed-locked; graph stable; retrain by config |
| Verifier harness | `Tools/Audio/hero_neural_material_verify.py` | real onnxruntime 1.29 inference gate |
| Native runtime seam (SCAFFOLD) | `Source/.../MelodiaNeuralHeroMaterialSubsystem.h/.cpp` | read-only; needs closed-editor build |
| **MelodiaHeroGem** cymatic PBR variant (added to existing Copernicus generator) | `Tools/Houdini/copernicus/copernicus_cymatic_parallax.py` | cooked **9/9 maps PASS** (facets low-rough, gold metallic, nodal emissive, nacre irid) |

Output: `Saved/Audit/copernicus_cymatic/MelodiaHeroGem/T_Cymatic_MelodiaHeroGem_{9 maps}.png` +
`Saved/Audit/qa_herogem_2026-09-02.json`.

## 4. STAGING (standing directive — stage all UE work in its own level)

Land the hero gem in the hero's OWN level, not as a loose asset:
- **Level / host:** `L_PCG_Hero_CrystalHarpGrove` + `APCGHeroMusicGraphHost`, the existing
  heroic music level (PCG_Hero_CrystalHarpGrove graph, DA_Hero_CrystalHarpGroveProfile).
- **PCG placement:** scatter the hero gem via the existing PCG hero-music graph/control
  family (`pcg_hero_music_*`), height-aware on the level's CanonicalLandscape — never a new
  landscape.
- **Cymatic integration:** gem map/tiles placed where cymatic field (`WorldField.Resonance`/
  `Tension`, from `UMelodiaCymaticsSubsystem` read-only) is strongest; nodal emissive rides
  the standing-wave amplitude.
- **Landscape-aware heatmap:** place gems using the project's heatmap-threshold placement
  discipline (match `PCG_HEATMAP_AUDIT` and Sea Above/Faraway Mother conventions) so density
  follows moisture/resonance fields, not eyeballing.
- **Polished PBR + MIs:** import the 9 MelodiaHeroGem PNGs (BaseColor sRGB, Normal/ORM/Height
  non-sRGB), create MIs on `M_Master_Toon_Universal`, wire Emissive/Iridescence/Height (parallax)
  + the MPC_Hero_Material param lanes.

## 5. Build sequence (phased, no editor yet)

- [x] Phase A: neural controller onnx + verifier (7/7) — DONE
- [x] Phase B: MelodiaHeroGem PBR variant cook (9/9) — DONE
- [ ] Phase C: closed-editor Build.bat (adds MelodiaNeuralHeroMaterialSubsystem; build while
      editor CLOSED; verify DLL writable first per AGENTS rule 14)
- [ ] Phase D: editor import of MelodiaHeroGem PNGs + MI on M_Master_Toon_Universal
- [ ] Phase E: stage into L_PCG_Hero_CrystalHarpGrove (PCG + cymatic + heatmap + MIs)
- [ ] Phase F: live PIE — beat reacts: gem emissive pulses through the neural seam.

## 7. Physics-accurate Chladni eigenmode lane (advanced by daemon 2026-09-02)

Closed-form simply-supported rectangular-plate eigenmodes power the *resonant*
(nodal) drive for the hero gem — the exact alternative to the heuristic
`m=round(sqrt(f/220)*3)` rule from §1.

- **Math substrate** `Tools/Houdini/copernicus/chladni_eigen.py`:
  `omega_mn = pi^2 * sqrt(D/(rho*h)) * ((m/Lx)^2 + (n/Ly)^2)`, exact mode
  `phi_mn(x,y)=sin(m*pi*x/Lx)*sin(n*pi*y/Ly)`, Lorentzian-nearest resonance picker.
  Verifier `chladni_eigen_verify.py` **9/9 PASS** (closed-form f(1,1..3,3) exact,
  non-decreasing order, thin→lower fundamental, nearest-resonance, nodal zero-count).
- **4 physical plates** (brass/steel/glass/crystal) with real E, rho, nu, h, L.
- **Baked eigenplate map library** `Saved/Audit/eigenplate/` — 8 maps, **8/8 QA PASS**
  (PNG 1024x1024, non-blank):
  - `T_EigenPlate_4_3_brass_Height/Normal` (existing)
  - `T_EigenPlate_1_2_{steel,glass,crystal}_Height/Normal`
- **Lane target (editor, Phase D/E):** per live audio frequency → nearest (m,n) →
  pick the matching eigenplate Height (parallax relief on nodal lines) + Normal into
  the `M_Master_Toon_Universal` hero-gem MI; nodal emissive rides the standing-wave
  amplitude (follows `WorldField.Resonance`, §4). Read-only consumer of
  MPC_Melodia_Palette (single-writer preserved).
- **Identity check per plate:** brass resonant at 440 Hz → (1,2) 423.7 Hz (96.3%
  match), crystal → (1,1) 404.5 Hz (91.9%). Test bake used anharmonic (1,2) maps to
  preserve a stable relief set; the lane picks the truly-catalog-nearest (m,n) live.

## 6. Open items / gates
- Closed-editor build required before the C++ seam compiles (two editor processes were up —
  HOLD until one editor, 9316).
- onnx runtime in UE: NNERuntimeORT integration TODO in the subsystem (API confirm on build).
- Master-index SSOT: promote the neural scaffold + hero gem to §2 when build lands.
- Free-model note: daemon crons back on free deepseek-v4-flash (git-health pair was 404-
  transient; revert to free honoured the standing directive).