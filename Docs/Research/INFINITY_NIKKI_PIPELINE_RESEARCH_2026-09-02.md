# INFINITY NIKKI PIPELINE RESEARCH — MIs, Real-Time Cymatics, NNERuntimeORT (2026-09-02)

**Purpose:** Deep-dive feeding `Docs/Plans/AUDIO_HERO_MATERIAL_PLAN_2026-09-02.md` (Phase 1
"Research deepen"). Three sections: (1) Infinity Nikki material-instance authoring,
(2) real-time cymatics in UE 5.8, (3) NNERuntimeORT (NNE) in UE 5.8. Ends with how it
applies to the **MelodiaHeroGem + neural hero controller**.

Honesty note: every claim is backed by a cited URL, the onnx (read from disk), or the
SCAFFOLDED subsystem source in this repo. Anything unverifiable is marked
`NEEDS-CONFIRMATION-AT-BUILD`. Nothing fabricated.

---

## 1. INFINITY NIKKI — material / material-instance authoring

Primary source: official **Unreal Engine developer interview** (Weibo Xie, VP of Technology,
Infold Games),
`https://unrealengine.com/developer-interviews/behind-the-scenes-of-infinity-nikki-tracing-a-glamorous-turn-to-an-unreal-open-world`
(2024-08-23). Corroborated by Apple's 2026-04-03 developer story (lead programmer Ade et al.):
`https://developer.apple.com/news/?id=9mgkwjnm`.
Repo cross-ref: `Docs/Research/UE58_TOON_MATERIAL_INTAKE_INFINITY_NIKKI_2026-08-08.md`.

### 1.1 "One versatile master material / few variants" doctrine (VERIFIED)
- Xie: "developing a **versatile master material** that could achieve various fabric effects
  while being easy for artists … **merge multiple fabric textures efficiently, reduce material
  variants, and perform well across different platforms**."
- Apple (Ade): "a **re-engineered fabric algorithm** … **four-layer UV blending textures … with
  only minimal parameter adjustments**" to simulate cotton/silk/satin/velvet/flannel.
- **Takeaway:** one `M_Master_Toon_Universal` + few parameterized MIs (tiling, tint, roughness,
  sparkle) beats bespoke masters per asset — matches the repo's existing
  `M_Master_Nikki` / `M_Master_Toon_Universal` + single audio MPC writer.

### 1.2 Jewellery material recipe — the HERO GEM target (VERIFIED)
- Xie: "we specifically developed a **jewelry material** … although **opaque, utilizes Cubemap
  and other algorithms** to achieve the unique **refraction, reflection, subsurface scattering
  (3S), and various highlights** of jewelry materials."
- Apple: "**complex refraction, 3S light transmission, and highly variable specular highlights**,
  as seen in the pearls and diamonds of the Fairytale Swan outfit."
- **Recipe to mirror:** opaque blend → low-roughness facets → Cubemap reflection/refraction →
  subsurface glow → specular highlights. This is exactly the 5-output lane the neural controller
  drives (see §4).

### 1.3 OIT for sheer fabrics (VERIFIED)
- "semi-transparent elements, like the **Fairytale Swan** … the tech team **redeveloped
  Order-Independent Transparency (OIT)**" for transparency sorting.
- Relevance: sheer/silk around the gem needs OIT or conservative single-layer translucency. OIT
  is engine-level work — do NOT rebuild this phase; adopt standard translucency on the master MI.

### 1.4 Standardized PBR inputs + Lumen ambient boxes (VERIFIED)
- "we adhere to **standardized PBR inputs** … using **modified ambient boxes** to adjust various
  scaling parameters … to address semi-transparent rendering issues" under Lumen.
- Confirms: feed the hero gem from a **normalized PBR set** (BaseColor / NOR / ORM / Height), not
  bespoke properties. Lighting stays PBR even for the stylized look ("our lighting calculations
  follow PBR standards" — Xie).

### 1.5 WPO for lightweight reactivity; Chaos for precision (VERIFIED)
- "Simple interactions are implemented using **World Position Offset (WPO)** … precision-demanding
  interactions are calculated using the **Chaos** system."
- Takeaway: the gem's reactive motion (Displacement/emissive wobble) rides **WPO**, no heavy sim —
  the plan's stated approach.

Secondary corroboration: Archyde summary (16 ms frame budget on A17 Pro, compute-shader jewellery/
fabric offload) — `https://archyde.com/infinity-nikki-wins-apple-design-award-for-stunning-visuals-and-graphics-in-2025/`

---

## 2. REAL-TIME CYMATICS in UE

Physics bases (cited): standing-wave nodal lines and eigenmodes (COMSOL), Chladni's law
(Wikipedia; AIP), forced-damped resonance (McMaster), plate reconstruction (NCTU/ASA).

### 2.1 Frequency → mode law (VERIFIED scaling)
- Chladni's law (circular plates): `f = C·(m + 2n)^p`, `p≈2` → mode number grows **~`sqrt(f)`**.
  `https://en.wikipedia.org/wiki/Chladni%27s_law` · `https://doi.org/10.1119/1.12866`
- Square Kirchhoff plate: `f_mn ∝ (m² + n²)` → `(m,n) ∝ sqrt(f)`.
  `https://novasolver.jp/en/tools/chladni-figures.html`
- **Adopted recipe** (plan §1, sources `cymatrix/wavefield/cymatics-labs/schladni`, tuned
  in-repo — NOT a universal law): `m = round( sqrt(f/220) * 3 )`, `n = round( sqrt(f/220) * 5 )`.
  The `sqrt(f)` scaling is physics-consistent; the 220 Hz reference and 3/5 weights are a
  stylistic dial in the Copernicus generator. Result: bass → low (m,n), treble → high (m,n);
  `chladni_modes` run bass→treble.

### 2.2 Lorentzian forced-damped resonance — mode selection (VERIFIED math)
- A driven damped oscillator peaks at eigenfrequency ω₀; the resonance line is **Lorentzian**
  with width from damping γ, and off-resonance amplitude collapses — so a figure only forms
  at/near an eigenfrequency. `https://physics.mcmaster.ca/~mckay/1d3/pdf/lecture37.pdf` ·
  `https://docs.mantidproject.org/v6.5.0/fitting/fitfunctions/Lorentzian.html`
- **Use:** weight each candidate (m,n) band by `L(ω) = γ²/((ω−ω₀)² + γ²)` against FFT band peaks →
  the mode that "locks" is the one whose eigenfrequency the audio energy is closest to. Nodal
  lines appear where `|φ| < ε` (NovaSolver/COMSOL principle).

### 2.3 Driving from audio in UE 5.8 (pattern)
- Single audio writer → `MPC_Melodia_Palette` scalars (**BassIntensity / BeatIntensity /
  BeatPhase / BeatPulse / BeatTracker**, verified in
  `MelodiaAudioReactivePresentationSubsystem.cpp`).
- Material **Chladni** in the gem MI (Material Function or inline `Sin` products):
  `u = WorldPos·ChladniScale; φ = BeatPhase·2π; w = Sin(mπu.x+φ)·Sin(nπu.y+φ)`;
  `emissive += NodalGain·smoothstep(1-k,1,1-|w|)` (nodal-line emissive);
  `WPO += Normal·Displacement·w` (parallax/height wobble). O(1) per-pixel pure material math — no
  sim, matches §1.5. `m,n` and `NodalGain` are MI scalars the controller / MPC_Hero_Material feeds.
- **FFT band → bass/mid/treble** maps onto the palette lanes (bass=BassIntensity, onset=
  BeatIntensity); the frequency→mode law converts a band's representative frequency into (m,n).
  Banding is project-adopted (plan §1) — FFT lives in the existing audio/reactivity writer.

---

## 3. NNERuntimeORT / NNE in UE 5.8

Authoritative: Epic **Neural Network Engine (NNE)** overview (UE 5.8):
`https://dev.epicgames.com/documentation/unreal-engine/neural-network-engine-overview-in-unreal-engine?lang=en-US`
Microsoft onnx-runtime UE sample: `https://github.com/microsoft/OnnxRuntime-UnrealEngine`
Epic forum course (runtime names + DirectML): `https://forums.unrealengine.com/t/course-neural-network-engine-nne/1162628`

### 3.1 Architecture (VERIFIED, Epic 5.8 doc)
- **NNE** = common API over multiple runtimes/"execution providers". **Beta** — caution shipping.
- **Assets:** import `*.onnx` in Content Browser → engine creates a `UNNEModelData` asset
  (toggle which runtimes use it; unneeded runtimes grow cook/package size).
- **Interfaces** (the lane): `INNERuntimeCPU` (sync/async game thread; caller owns tensors),
  `INNERuntimeGPU` (CPU tensors in/out, GPU executes outside frame), `INNERuntimeRDG`
  (in-frame FRDGBuilder GPU, RDG-buffer I/O).
- **Runtimes** (the provider): plugin `NNERuntimeORT` registers **`NNERuntimeORTCpu`** (ONNX
  Runtime CPU) and **`NNERuntimeORTDml`** (DirectML GPU, DX12, ships *inside* the plugin, no CUDA/
  cuDNN install). `NNERuntimeORTCuda` **removed in 5.4** (needed manual CUDA/cuDNN). **GPU provider
  = DirectML; CUDA backend gone.**
- Get runtime: `UE::NNE::GetRuntime<INNERuntimeCPU>("NNERuntimeORTCpu")` (weak ptr; null-check).
  List: `UE::NNE::GetAllRuntimeNames()`.
- **Build wiring:** add module `NNE` to the `.Build.cs`; includes `NNE.h`, `NNERuntimeCPU.h`,
  `NNEModelData.h`.

### 3.2 CPU inference pattern (VERIFIED, Epic doc + forum)
```cpp
TObjectPtr<UNNEModelData> ModelData = LoadObject<UNNEModelData>(GetTransientPackage(),
    TEXT("/Game/Models/HeroMaterialController.HeroMaterialController"));
TSharedPtr<UE::NNE::IModelCPU> Model =
    UE::NNE::GetRuntime<INNERuntimeCPU>("NNERuntimeORTCpu")->CreateModelCPU(ModelData);
TSharedPtr<UE::NNE::IModelInstanceCPU> Inst = Model->CreateModelInstanceCPU();
Inst->SetInputTensorShapes(InputShapes);          // re-call if any input shape changes
Inst->RunSync(InputBindings, OutputBindings);     // caller owns tensor memory for full call
```
- Tensors: `UE::NNE::FTensorBindingCPU{ Data = float*, SizeInBytes = N*sizeof(float) }`.
- Run once/frame sync or as **async task**; **batch** multiple calls per tick; keep I/O memory
  alive across the call (thread-safety is caller's job).

### 3.3 CPU vs GPU for OUR model (recommendation)
The hero controller is a **5→16→12→5 MLP** (`hero_material_controller.onnx`, 1845 bytes, input
`audio [?,5]`, output `hero`, opset 17, IR 9 — read from disk this session). 5 float inputs/frame
is negligible for the **CPU runtime**, avoiding GPU-photon + RDG complexity and frame sync.
**Recommendation: `NNERuntimeORTCpu`, synchronous on game thread.** GPU/DirectML only if a future
model is far heavier or in-frame post → then `INNERuntimeRDG` (Dml).
`NEEDS-CONFIRMATION-AT-BUILD`: exact `CreateModelCPU`/`CreateModelInstanceCPU`/tensor-binding
signatures, runtime registration strings, and opset-17 Gemm/Relu/Sigmoid/Identity coverage in the
shipped ONNX Runtime — confirm against 5.8 headers at build.

### 3.4 How to load the onnx
- **Preferred (asset):** import `Tools/Audio/models/hero_material_controller.onnx` → `UNNEModelData`
  (keep only `NNERuntimeORTCpu` enabled) → `LoadObject` by path in `Initialize()`. Robust, packages
  correctly, matches Epic doc.
- **Manual bytes** (`NNERuntimeORTCpu::CreateModelData(...)` from a loaded file) exists but is
  runtime-specific / forum-documented — `NEEDS-CONFIRMATION-AT-BUILD`; prefer the asset route.

---

## 4. HOW THIS APPLIES — MelodiaHeroGem + neural hero controller

Repo ground truth (this session): onnx at `Tools/Audio/models/hero_material_controller.onnx`
(input `audio [?,5]` = BassIntensity/BeatIntensity/BeatPhase/BeatPulse/BeatTracker; output `hero`
= EmissiveStrength/EmissiveTint/SubsurfaceScatter/Displacement/SpecularBoost, sigmoid → [0,1]),
and scaffold `Source/BS_GodFile/MelodiaIntegration/MelodiaNeuralHeroMaterialSubsystem.{h,cpp}`
(UGameInstanceSubsystem, FTSTicker-driven; already reads the audio MPC read-only and writes the
subsystem-owned `MPC_Hero_Material`; `RunInference()` is the marked NNERuntimeORT TODO seam).
`NNERuntimeORT` is already in `BS_GodFile.uproject` (verified in plugins list); module dep `NNE`
must be added to the `.Build.cs`.

### 4.1 Direct mapping
- **§1 hero-gem recipe** == the 5 neural outputs: low-roughness facets + Cubemap reflection/
  refraction (EmissiveTint), subsurface 3S glow (SubsurfaceScatter), specular highlights
  (SpecularBoost), WPO/emissive displacement (Displacement), radiant glow (EmissiveStrength).
  MI authored on `M_Master_Toon_Universal` fed from `MPC_Hero_Material` — one master, few
  parameterized MIs (the Nikki doctrine).
- **§2 cymatic weave** drives the same WPO/emissive lanes: Chladni `(m,n)=sqrt(f/220)·(3,5)` from
  the FFT band, Lorentzian mode-weighting, nodal-line emissive. `chladni_modes` run bass→treble
  via `Displacement`/`EmissiveStrength`, so neural + physics-driven cymatic field agree on one
  read-only MPC.

### 4.2 Concretely at build (Phases C–F)
1. Add module `NNE` to `MelodiaIntegration.Build.cs` (`NNERuntimeORT` already on in `.uproject`).
   **NEEDS-CONFIRMATION-AT-BUILD** on signatures.
2. Import the onnx as `UNNEModelData` (editor, Phase D).
3. `RunInference()`: pack 5 palette scalars → `FTensorBindingCPU` → `SetInputTensorShapes({1,5})`
   → `RunSync` → read 5 floats → write `MPC_Hero_Material` scalars (existing fallback path is the
   current non-neural behavior; neural path replaces it, single writer to MPC_Hero_Material unchanged).
4. Gem MI reads `MPC_Hero_Material` + Chladni function; stage in `L_PCG_Hero_CrystalHarpGrove` (plan §4).

### 4.3 Open items / risks
- NNE is Beta; one-sync-call-per-frame CPU inference is within the game-thread budget but must be
  proven in PIE, not assumed (Phase F gate).
- `NNERuntimeORTCuda` is gone in 5.8 — do not plan around it; GPU = DirectML (`NNERuntimeORTDml`).
- The 220 Hz / (3,5) weights are stylistic in-repo dials, physics-consistent (sqrt) but not a
  universal law; keep them as MPC/MI scalars, retrainable onnx unchanged (§2.1).

*Prepared 2026-09-02. Sources cited inline; uncertain NNE API details marked
NEEDS-CONFIRMATION-AT-BUILD.*