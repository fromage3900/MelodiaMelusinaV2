# AAA Anime / Gacha Character Pipelines in Unreal Engine — Research Brief

**Date:** 2026-08-15
**Scope:** Infinity Nikki (Infold/Papergames, UE5), Wuthering Waves (Kuro Games, UE4.26), Genshin Impact / HoYoverse where publicly documented, plus Epic first-party documentation.
**Purpose:** Inform character-integration decisions for *Melodia* / Melusina (UE 5.8, Blender + Auto-Rig Pro + Rigify face + Faceit).

---

## Evidence grading used throughout

Every claim below is tagged:

- **[DOCUMENTED]** — stated by the developer, by Epic, by Apple, or in a first-party conference deck.
- **[COMMUNITY]** — derived from datamining, reverse-engineering, or widely-reproduced practitioner tutorials. Directionally reliable, not authoritative.
- **[INFERENCE]** — my reasoning from the above. Not sourced. Treat as a hypothesis.

**Two research limitations you should know before acting on this:**

1. `unrealengine.com` returned HTTP 403 to every direct fetch attempt in this session. The Epic developer interview *"Behind the Scenes of Infinity Nikki"* ([canonical URL](https://www.unrealengine.com/en-US/developer-interviews/behind-the-scenes-of-infinity-nikki-tracing-a-glamorous-turn-to-an-unreal-open-world)) was therefore reconstructed from search-engine extraction of that page plus a **directly fetched, heavily overlapping** Apple Developer article ([developer.apple.com/news/?id=9mgkwjnm](https://developer.apple.com/news/?id=9mgkwjnm)). Where a claim appears in the Apple article I cite that as primary. Where it appears only via search extraction of the Epic page, I mark it **[DOCUMENTED — via search extraction, verify against the live page]**. **You should open the Epic page in a browser and confirm the quoted specifics before making a production decision on them.**
2. There is **no** publicly available Kuro Games or Infold document describing their outline algorithm, their face-shadow algorithm, their bone counts, or their LOD budgets. Sections that would need those are explicitly marked as gaps rather than filled with plausible-sounding detail.

---

## Executive summary

**The single most important finding is a negative one.** Across every genuinely authoritative source found — Epic's Infinity Nikki interview, Apple's Infold feature, and Kuro Games' Unreal Fest Tokyo 2025 deck — *none* of these studios describe an exotic character-authoring pipeline. What they describe is: a **conventional skinned-mesh character**, plus an **enormous amount of custom engine C++/HLSL work** layered on top. The differentiator is not the rig. It is the renderer and the simulation solver.

Concretely:

1. **Infinity Nikki's cloth is the actual technical achievement, and it is not stock Chaos Cloth.** Infold replaced collision-based cloth resolution with **constraint-based** solvers and proprietary skeletal-chain algorithms, and — critically — added a **preprocessing "soft-driven constraint" stage** that guarantees garments start in a non-clipping state before any simulation runs ([Apple Developer](https://developer.apple.com/news/?id=9mgkwjnm)). This is the answer to "how do they ship hundreds of swappable outfits without interpenetration": **it is solved at bake time, not at runtime.**
2. **Kuro Games' Wuthering Waves is a masterclass in *not* upgrading your engine.** They stayed on **UE4.26** and back-ported a Lumen-equivalent GI system by hand rather than migrating to UE5 ([Unreal Fest Tokyo 2025 deck, Xin Wang / KURO GAMES](https://www.docswell.com/s/EpicGamesJapan/58W89L-UE_UFT2025_KUROGAMES)). Their toon-shading work is expressed as *modifications to how lighting reaches the toon shader*, not as a separate art pipeline.
3. **The SDF face shadow map is real, is the genre signature, and is entirely reproducible by a solo dev.** It is a baked 2-channel texture plus roughly ten lines of material math. This is the highest visual-return-per-hour item on this list, by a wide margin. **[COMMUNITY]** — HoYoverse has never published it; it is universally reconstructed from datamined assets.
4. **ARKit's 52 blendshapes are the de facto standard and Epic has standardized on them.** ARKit maps facial geometry onto 52 blend-shape coefficients, and Epic built the MetaHuman facial rig against that same set, so Live Link Face data maps on without a retargeting step ([Apple ARKit docs](https://developer.apple.com/documentation/arkit/arfaceanchor/blendshapelocation), [MoCap Online](https://mocaponline.com/blogs/mocap-news/face-capture-game-dev-iphone-arkit-live-link-metahuman)). Faceit's core value proposition is that it generates exactly this set. **Use it. This is a solved problem — do not invent a face rig.**
5. **A 465-bone control rig must not reach Unreal.** A standard humanoid game rig is 50–80 body bones, 100–120 with fingers, and 150–200 for a AAA character with a full facial rig ([MoCap Online](https://mocaponline.com/blogs/mocap-news/character-rigging-game-dev-guide)); the stock UE5 skeleton is 67 bones. 465 is a *Blender authoring* number — controls, mechanism bones, IK targets, and drivers — and is defensible **only** if the exported deform skeleton is a fraction of it. See §6.

**Bottom line for Melodia:** copy the SDF face shadow (§3) and the ARKit-52 face (§4) more or less exactly. Copy Infold's *architectural principle* on garments (§5) — precompute the non-clipping state — but implement it with the cheap version, not their custom solver. Do **not** attempt to copy Kuro's or Infold's engine-fork strategy (§1, §2); for a solo dev that is a project-killing decision, and both studios explicitly describe it as costly.

---

## 1. Infinity Nikki — UE5 technical practice

### 1.1 Engine branch strategy

**[DOCUMENTED — via search extraction, verify against the live page]** Infinity Nikki was Infold/Papergames' first project after switching to Unreal Engine, and the move enabled the shift from the confined dress-up scenes of earlier Nikki titles to an open world ([Epic developer interview](https://www.unrealengine.com/en-US/developer-interviews/behind-the-scenes-of-infinity-nikki-tracing-a-glamorous-turn-to-an-unreal-open-world); corroborated by [Wikipedia](https://en.wikipedia.org/wiki/Infinity_Nikki)).

**[DOCUMENTED — via search extraction]** Epic's announcement of the UE5 Fortnite build was cited as the trigger that "solidified Infold Games' resolve to upgrade to 5.0." The upgrade **required extensive modifications to the engine** and prompted internal debate over risk versus reward ([Epic developer interview](https://www.unrealengine.com/en-US/developer-interviews/behind-the-scenes-of-infinity-nikki-tracing-a-glamorous-turn-to-an-unreal-open-world)).

**Gap — say so plainly:** I could not find a stated *specific* engine version, custom-branch name, or upgrade cadence for Infinity Nikki. Claims circulating about a precise UE 5.x point release are not supported by any source I could verify. Community CVar documentation exists ([gist](https://gist.github.com/DiceTsuki/e3ee44aeecc0daeb2c05f5f9d75aacfd)) but does not establish a version.

**Scale context — [DOCUMENTED]:** approximately **800 people, six years** of development ([Apple Developer](https://developer.apple.com/news/?id=9mgkwjnm)). Every technique below carries that price tag. This is the number to hold in mind when deciding what to replicate.

### 1.2 Cloth: skeletal physics + Chaos Cloth, heavily modified

This is the best-documented part of the entire brief. **[DOCUMENTED]**, all from [Apple Developer](https://developer.apple.com/news/?id=9mgkwjnm) and corroborated by search extraction of the Epic interview:

- They **categorize fabric types** and apply "a combination of skeletal physics and ChaosCloth simulations" — i.e. **not everything is cloth-simulated.** Stiff or structural garment elements ride on bone chains; only genuinely soft material gets a cloth solver.
- They use **proprietary skeletal chain algorithms** and **enhanced cloth solvers**.
- They explicitly **replaced "costly and unstable traditional collision-based algorithms with more stable and controllable constraint-based algorithms."**
- Their custom algorithms handle **collision between different garment types and across multiple clothing layers**, which is what "enables free outfit combinations without sacrificing stability."
- Stated design goal: preserve the **artist-intended silhouette** while achieving physical plausibility. Simulation is subordinate to art direction.

**[INFERENCE]** The hybrid split — bone-chain for structure, cloth for softness — is the single most transferable idea here for a solo dev, and it needs no custom engine code. UE ships `AnimDynamics` and `RigidBody` AnimGraph nodes that cover the bone-chain half natively.

### 1.3 Authored / precomputed clipping rules

**[DOCUMENTED]** — the key sentence, from [Apple Developer](https://developer.apple.com/news/?id=9mgkwjnm):

> a flexible and soft-driven constraint stage during preprocessing, ensuring that even under dramatic movements, the initial garment avoids clipping the body

Read carefully, this says the anti-clipping guarantee is **established during preprocessing**, before runtime simulation — the garment's rest/initial state is constrained out of the body, so the simulator never has to dig itself out of a penetrating start state. Runtime layer-vs-layer collision is then handled by their custom solver.

**[INFERENCE]** This is architecturally the same insight as a shrinkwrap/push-out bake: *fix penetration at author time; let the simulator only handle motion.* A solo dev can get most of this with a Blender Shrinkwrap modifier pass, applied per outfit against the body mesh, before export. That costs hours, not engineer-years.

### 1.4 Materials

**[DOCUMENTED]** ([Apple Developer](https://developer.apple.com/news/?id=9mgkwjnm)):

- **Fabric:** a re-engineered fabric algorithm using **four-layer UV blending textures**, driven with "minimal parameter adjustments," able to express cotton/linen coarseness, silk and satin sheen, and velvet/flannel tactility. Note the design intent: *one master material, few exposed parameters, many fabrics.*
- **Jewelry/gemstone:** a dedicated material system with complex refraction, **3S (sub-surface scattering) light transmission**, and highly variable specular response — cited on the *Fairytale Swan* outfit's pearls and diamonds.
- **Animated patterns:** UE5's native motion blur was **interfering with UV-scrolling animations**; Infold built a workaround to keep UV-animated patterns crisp. Shipped on the *Threads of Reunion* outfit with three independent orbital systems, customizable planetary shapes, angular velocities and trajectories, asteroid belts, and lunar phase changes.

**Actionable for Melodia — [INFERENCE]:** the motion-blur/UV-animation conflict is a real UE5 behavior and will bite you the moment you put a scrolling pattern on a garment. Velocity output from World Position Offset and UV animation is a known source of smearing; budget time for it if Melusina has animated fabric patterns.

### 1.5 Character lighting and shadows

**[DOCUMENTED — via search extraction]** From the Epic interview: *"For character lighting, we developed high-quality shadows specifically for characters to achieve detailed self-shadowing."* The described architecture uses **three shadow passes**:

1. one for all objects and NPCs,
2. one for Nikki specifically (which can fade in/out),
3. one for character self-shadowing, covering Nikki and all NPCs.

They also describe **modified ambient boxes** used to adjust scaling parameters, which let them tune the art look and address semi-transparent rendering issues ([Epic developer interview](https://www.unrealengine.com/en-US/developer-interviews/behind-the-scenes-of-infinity-nikki-tracing-a-glamorous-turn-to-an-unreal-open-world)).

**Why this matters:** a **dedicated, separable character shadow pass** is the recurring pattern across both studios (compare Kuro's approach in §2.3). Anime characters need shadow behavior that is decoupled from environment shadow behavior, because environment-correct shadowing makes stylized faces look wrong.

**Gap:** an independent RenderDoc-based breakdown of Nikki's shadow drop exists at [simonschreibt.de/gat/infinity-nikki-shadow](https://simonschreibt.de/gat/infinity-nikki-shadow/), but the host refused connection during this session. Worth reading directly — it is the only frame-level analysis I located.

### 1.6 Physics interactions and performance

**[DOCUMENTED — via search extraction]** Interactive world objects (wind-blown flags, roadside bottles, breakable boxes) are split by cost: **simple interactions use World Position Offset (WPO)**; interactions needing precision go through **Chaos** ([Epic developer interview](https://www.unrealengine.com/en-US/developer-interviews/behind-the-scenes-of-infinity-nikki-tracing-a-glamorous-turn-to-an-unreal-open-world)). This is the same cost-tiering philosophy as the cloth split in §1.2.

**[DOCUMENTED]** The game ships on PS5, Windows, iOS and Android ([Wikipedia](https://en.wikipedia.org/wiki/Infinity_Nikki)), with native iPhone/iPad optimization and Global Illumination in the lighting pipeline ([Apple Developer](https://developer.apple.com/news/?id=9mgkwjnm)).

**Gap:** no published triangle budgets, bone budgets, LOD counts, draw-call targets, or frame budgets for Nikki characters. Anyone quoting such numbers to you is guessing.

### 1.7 The GDC talk is not a technical talk

Infold presented **"How 'Infinity Nikki' Turns Outfits into Fantasy (And Why It Works)"** at GDC 2026 — speaker **Dodie Gong, Art Director, Infold Games**, Wednesday March 11, 1:50–2:50pm, Room 2006 West Hall ([GDC schedule](https://schedule.gdconf.com/session/how-infinity-nikki-turns-outfits-into-fantasy-and-why-it-works/915309)). Coverage indicates it is about **narrative and symbolism in outfit design**, not implementation ([AUTOMATON WEST](https://automaton-media.com/en/news/you-cant-touch-peoples-hearts-by-just-piling-together-visual-information-infinity-nikki-art-director-explains-how-outfits-are-designed-to-express-narrative-and-sym/)). Valuable as portfolio-framing context for an Infold application; **not** a source of pipeline detail.

---

## 2. Wuthering Waves — Kuro Games

### 2.1 Engine strategy — the headline finding

**[DOCUMENTED]** Kuro Games presented at **Unreal Fest Tokyo 2025**, speaker **Xin Wang (KURO GAMES)**, on ray tracing in an anime-styled open world. The deck is hosted by Epic Games Japan: [docswell.com/s/EpicGamesJapan/58W89L-UE_UFT2025_KUROGAMES](https://www.docswell.com/s/EpicGamesJapan/58W89L-UE_UFT2025_KUROGAMES). **This is the strongest primary source in this brief.** Key claims from it:

- **Engine: Unreal Engine 4.26.** They did not migrate to UE5.
- **Performance target: RTX 4060, 2K resolution, 60 fps.**
- They implemented three hardware-RT features: **ray-traced reflections, probe-based diffuse GI, and ray-traced shadows.**
- They chose a **Hardware-Lumen-style approach over ReSTIR path tracing** for flexibility, and rebuilt Lumen's components inside UE4.26: **Screen Probe Gather** (octahedral map, 8×8 pixels per probe storing radiance and hit distance, adaptive probe placement, importance sampling combining BRDF and lighting PDFs, spatial/temporal reuse) and a **Radiance Cache** (four-layer world-space clipmap, 32×32 atlas pixels per probe, sphere-parallax-corrected connecting rays).
- Their own extension, a **Clipmap Irradiance Cache**, is decoupled from a surface cache to support effectively infinite bounces at resolution-independent cost — **~2 ms for GI at 2K**.

**[COMMUNITY]** A datamining-based analysis reports the UE4.26 base is confirmed in the shipped `Engine.ini`, and that Kuro stayed on UE4 deliberately due to live-service stability risk ([ToonXD analysis](https://pqmlmaoxd.github.io/gamedev/analysis/2026/04/12/wuthering-waves-performance-issues.html)). The same analysis lists custom plugins extracted from shipping config — `KuroDynamicMeshBatch`, `KuroWorldPartition`, `KuroPSOTools`, `KuroPerfCat`, `FastGeoStreaming`, `OpacityMicroMap` — plus Tencent's `MagicDawn` research plugin (neural GI/probe/lightmap compression) and a Puerts/V8 TypeScript scripting layer. **Treat all of this as unofficial**; it is binary-string and config extraction, not a developer statement. It is however internally consistent with the Unreal Fest deck.

**[COMMUNITY]** Editorial coverage frames the tradeoff bluntly: extensive engine modification means **losing official Epic support** and owning every bug yourself ([AUTOMATON WEST](https://automaton-media.com/en/column/even-from-a-developers-perspective-wuthering-waves-use-of-unreal-engine-is-borderline-perverse-a-ue4-game-decked-out-in-custom-technology/), [Vortex Gaming](https://vortexgaming.io/en/postdetail/736367)).

### 2.2 Toon shading integrated with ray-traced GI

**[DOCUMENTED]** ([Unreal Fest Tokyo 2025 deck](https://www.docswell.com/s/EpicGamesJapan/58W89L-UE_UFT2025_KUROGAMES)) — this is the genuinely novel contribution, and it is worth understanding even if you never write a ray tracer. Physically-correct GI *breaks* anime shading, so Kuro added a **three-stage conditioning of GI before it reaches the toon shader**:

1. **Spherical normal processing for hair and face regions** — i.e. the shading normal is replaced with a smoothed/spherical approximation on exactly the two regions where real geometric normals produce ugly stylized results.
2. **HSV colour-space conversion that clamps saturation and value**, keeping bounced light from oversaturating or blowing out the flat colour regions.
3. **AO multiplication with a skin mask applied**, reducing GI influence specifically on skin tones.

**Reflective surfaces:** roughness is **clamped to 0.0–0.399** to avoid the SSR transition band; metallic above 0.9 is treated as a mirror; results are blended with **MatCap-based** additions.

**[INFERENCE]** Point 1 — spherical/smoothed normals on hair and face — is the same underlying insight as the SDF face-shadow technique in §3 and the long-standing anime practice of transferring face normals from a sphere. Two independent AAA studios converging on "the face must not use its real normals" is a strong signal. **This is the highest-confidence takeaway in the whole brief.**

### 2.3 Shadows, including character self-shadowing

**[DOCUMENTED]** ([same deck](https://www.docswell.com/s/EpicGamesJapan/58W89L-UE_UFT2025_KUROGAMES)):

- **Hybrid shadows:** Cascaded Shadow Maps handle billboards/impostors; ray-traced shadows handle the rest, using `RAY_FLAG_CULL_FRONT_FACING_TRIANGLES` so one-sided plane geometry behaves.
- **Character self-shadowing is deliberately special-cased:** characters are **excluded from the RT instance masks** and given **dedicated shadow rays**, while retaining rasterized per-object shadows.
- **Volumetric fog** uses pre-generated 3D shadow volumes from ray traces, decoupling precision from performance so lower-end devices can scale.

Again: **characters get their own shadow path.** Same conclusion as Infold (§1.5).

### 2.4 Performance engineering

**[DOCUMENTED]** ([same deck](https://www.docswell.com/s/EpicGamesJapan/58W89L-UE_UFT2025_KUROGAMES)):

| Optimization | Result |
|---|---|
| Ray payload compression, 64 → 32 bytes | ~15% GPU trace improvement |
| Opacity Micro-Maps (OMM) | removes per-pixel alpha evaluation in any-hit shaders |
| CPU culling (distance + solid angle) | frame time 19.8 ms → 16.6 ms |
| Async task distribution (BuildAS / BindSBT) | 14.5 ms → 10.5 ms |
| Skybox as per-frame-updated 512×512 cubemap (one face/frame) | ~25% reflection improvement |

They also use **NRD** (NVIDIA Real-Time Denoisers) spatio-temporally and **SER** (Shader Execution Reordering) for ray divergence. Stated future work: console and mobile ports, inline ray tracing, RT direct lighting, GPU-driven/Nanite-like pipelines.

### 2.5 Explicit gaps — outline, face shadow, rigging, LOD

**I could not find any authoritative Kuro Games source on:**

- their **outline method** (inverted hull vs. post-process depth/normal edge detection vs. both),
- their **face shadow** technique (whether they use an SDF map at all),
- **hair rendering** specifics,
- any **rigging, bone-count, blendshape, or LOD** practice.

**[COMMUNITY] only:** datamined-model analysis reports that WuWa "shadows are generated using a gradient texture, each level of gray represents a degree of shadow from left-right" and that model construction is conventional for the genre — "identical to the kind you'd find when ripping open Genshin Impact, or Tower of Fantasy" — with hair specifically modelled to minimise clipping ([t/suki forum](https://forum.tsuki.games/t/a-surface-level-dive-into-wuthering-waves-character-models/149)). The author self-describes this as surface-level. **The "left-right gradient" description is consistent with an SDF-style face shadow map (§3), but this is not confirmation.**

**[COMMUNITY]** The **inverted hull** outline method — render back faces only, requiring two-sided rendering with front faces alpha-clipped away — is the standard genre approach and works well on rounded forms, less well on flat surfaces ([Daniel Ilett](https://danielilett.com/2023-04-07-tut6-5-10-shaders-quickly/)). Reconstruction shaders for datamined WuWa assets exist ([HoyoToon](https://github.com/Hoyotoon/HoyoToon) for miHoYo titles; WuWa-targeted equivalents circulate similarly). Practitioner attempts to replicate WuWa's look in UE5 are active but **unresolved** — a representative Epic forum thread asking whether the look lives in the master material or a custom shading model contains **no answer** ([UE forums](https://forums.unrealengine.com/t/deconstructing-replicating-wuthering-waves-post-process-anime-shader-model-in-ue5/2739985)).

---

## 3. The SDF face shadow map

This is the signature technique of high-end anime rendering and the **highest-value item for Melodia**. Note carefully: **HoYoverse has never published this.** Every description below is community reconstruction from datamined assets, and I am labelling it accordingly.

### 3.1 The problem it solves

**[COMMUNITY]** Anime faces look wrong under normal-based lighting. A nose casts a real shadow that reads as a blob; cheeks and brows self-shadow in ways no 2D animator would draw. miHoYo's own GDC 2021 talk states that character shadow is driven primarily by **one single light source**, with the shadow transition **artificially set** from material settings, light intensity and mass curvature to get the best transition ([miHoYo GDC 2021, as transcribed](https://mihoyo.fandom.com/wiki/Game_Developers_Conference_2021)) — note the word *artificially*. **[DOCUMENTED, weakly]** — this is a fan-wiki transcription of a real GDC talk; the talk is real, the transcription is not first-party.

The fix is to **stop deriving the face shadow from geometry at all** and instead look it up from an artist-authored texture indexed by light angle.

### 3.2 How it works

**[COMMUNITY]** The mechanism, consistent across independent sources:

1. An artist authors a **series of face shadow masks**, one per light angle, covering the light's rotation around the head. One widely-cited description divides **0–180° into 9 angles with 9 hand-drawn textures**; the map covers 0–180° on one side of the face rather than 0–90° ([search-surfaced description of the Genshin approach](https://github.com/NoiRC256/URPSimpleGenshinShaders)).
2. Each mask is converted to a **signed distance field**, and the SDFs are **interpolated** to produce a single continuous **shadow threshold map** ([akasaki1211/sdf_shadow_threshold_map](https://github.com/akasaki1211/sdf_shadow_threshold_map)). That tool's documented pipeline is: compute SDF per input image → build a mask from each input pair → take the gradient from the SDF pair → lerp with the gradient and masked image. It supports 8- or 16-bit output and explicitly notes **16-bit gives smoother shadow boundaries than 8-bit**.
3. The result is packed into **two channels: the original SDF in R, and a horizontally flipped copy in G**, for the two sides of the face ([Victor Lu, "UE5 Anime Face Shading"](https://medium.com/@Donkey/ue5-anime-face-shading-d38ba298ffdf)).
4. At runtime, the shader picks/blends the channel by which side the light is on, and **compares the sampled threshold against the light angle** to produce a hard binary shadow.

### 3.3 UE implementation specifics

**[COMMUNITY]** From the most directly relevant UE5 write-up ([Victor Lu, Medium](https://medium.com/@Donkey/ue5-anime-face-shading-d38ba298ffdf)):

- Masks were painted in **Substance Painter** and exported as a series.
- Packed texture flipped, channel-duplicated, and upscaled to **2048×2048**.
- The core material math is a **Custom node**, with the blend expressed as `shadow += lerp(TexR, TexG, Direction);`
- A **3×3 blur kernel** (9 taps, offset by `texelsize = 1./BlurIntensity*Dither`) softens the boundary.
- The author states a **custom shading model** is needed for final shadow falloff and colour control, and publishes a modified engine branch (`Anime_Rendering`).

**[COMMUNITY]** Texture import settings matter: disable **sRGB** and/or set the texture type appropriately (a Unity-side writeup specifies "Directional Lightmap"); the map is data, not colour ([AnimeShadingPlus manual](https://github.com/EricHu33/AnimeShadingPlus-Anime-Toon-Shader/blob/main/Anime%20Shading%20Plus(%2B)%20User%20Manual%20e9875988ae1e41caa5198370d9cc963d/Face%20Shadow%20Map-%20Creation%20&%20Baking%20Workflow%20d3b8769021e04683a2f2ae4cf16ac810.md)). **In UE the equivalent is: uncheck sRGB, and it is worth evaluating a 16-bit / higher-precision format given the source tool's explicit note about boundary smoothness.**

**[COMMUNITY]** The technique's stated advantage over the alternative — hand-editing face normals — is that it is **highly controllable by artists and far less time-consuming than manual normal editing**, per the AnimeShadingPlus workflow documentation.

**Tooling that exists today:** `sdf_shadow_threshold_map` ([GitHub](https://github.com/akasaki1211/sdf_shadow_threshold_map), documents UE5 and Blender as target consumers), and Face_SDF_Generator ([itch.io](https://dincairwen.itch.io/face-sdf-generator)), which generates SDF textures from PNG sequences. **You do not need to write the baker.**

**[INFERENCE]** A realistic solo-dev budget for this: one day authoring the angle masks for Melusina's face, a few hours baking with an existing tool, and a day on the material graph. It can be done **without** forking the engine if you accept a material-based rather than shading-model-based falloff — the custom shading model buys quality, not feasibility.

### 3.4 Relationship to normal smoothing

**[INFERENCE, moderate confidence]** SDF face shadow and Kuro's "spherical normal processing for hair and face" (§2.2) are two solutions to the same problem. SDF replaces the lighting *result*; spherical normals replace the lighting *input*. Spherical/transferred normals are far cheaper to author and are the sensible **first** step; SDF is the upgrade when you want the crisp, art-directed shadow shapes that read as hand-drawn. **Do the normals first.**

---

## 4. UE facial animation for anime characters

### 4.1 The ARKit-52 standard

**[DOCUMENTED]** ARKit's `ARFaceAnchor.BlendShapeLocation` is Apple's dictionary of named coefficients describing facial expression ([Apple developer documentation](https://developer.apple.com/documentation/arkit/arfaceanchor/blendshapelocation)). *(Note: the docs page returned only its title shell to automated fetch; the 52-coefficient figure below is corroborated by multiple secondary sources rather than read directly off Apple's page.)*

**[DOCUMENTED, secondary]** ARKit maps facial geometry onto **52 blend-shape coefficients**, and this is **the same set Epic's MetaHuman standard uses** ([MoCap Online](https://mocaponline.com/blogs/mocap-news/face-capture-game-dev-iphone-arkit-live-link-metahuman)). The set is **FACS-based** (Facial Action Coding System) with documented muscle-anatomy correspondence ([Pooya de Person's artist guide](https://pooyadeperson.com/the-ultimate-guide-to-creating-arkits-52-facial-blendshapes/)). Names are camelCase and region-grouped — `eyeBlinkLeft`, `jawOpen`, etc.

### 4.2 What Epic's tools expect

**[DOCUMENTED, secondary]** **Live Link Face** is Epic's free iOS app that streams ARKit face capture into Unreal over Wi-Fi, in two modes: live streaming for real-time preview/recording, and file export for offline use. Requirements: an iPhone with Face ID, UE5 with the Live Link plugin, and a MetaHuman or a skeletal mesh carrying **ARKit's 52 blend shapes** ([yelzkizi](https://yelzkizi.org/live-link-face-with-metahuman/); Epic's own doc on [recording face animation on iOS](https://dev.epicgames.com/documentation/unreal-engine/recording-face-animation-on-ios-device-in-unreal-engine?lang=en-US)).

**The critical consequence — [DOCUMENTED, secondary]:** because Epic built the MetaHuman facial rig against the ARKit set, **no retargeting step and no new morph targets are required** — the rig already listens for the ARKit blendshape names, so a value for `eyeBlinkLeft` or `jawOpen` drives the corresponding shape directly ([MoCap Online](https://mocaponline.com/blogs/mocap-news/face-capture-game-dev-iphone-arkit-live-link-metahuman), [yelzkizi](https://yelzkizi.org/live-link-face-with-metahuman/)).

**[DOCUMENTED, secondary]** **MetaHuman Animator** is the higher-quality, **non-real-time** sibling: it processes recorded iPhone or stereo-headcam video offline and produces near-film-quality facial animation, capturing nuance Live Link Face misses ([yelzkizi](https://yelzkizi.org/metahuman-mocap-workflow/)).

**Important caveat — [COMMUNITY]:** MetaHuman Animator outputs **MetaHuman control-rig curves, not raw ARKit curves**. Driving a non-MetaHuman ARKit-blendshape mesh from MHA output requires a **remapping layer**; a community tool exists specifically for this ([Dylanyz/ARKitRemap](https://github.com/Dylanyz/ARKitRemap)). **This is a real trap for Melodia: an ARKit-52 Melusina will work seamlessly with Live Link Face but will *not* natively consume MetaHuman Animator output.**

### 4.3 Blendshape vs. bone-driven faces

**[DOCUMENTED, secondary]** Production facial systems are typically **hybrid**: Faceware's system drives "primarily blendshapes (morph targets) and some bone rotations" for MetaHumans, and head/neck **rotations** are applied as bones via the face animation blueprint ([yelzkizi, Faceware workflow](https://yelzkizi.org/metahuman-facial-motion-with-faceware/)).

**[INFERENCE]** The tradeoff, stated plainly:

| | Blendshapes / morph targets | Bone-driven face |
|---|---|---|
| Expression fidelity | High — arbitrary sculpted deformation | Limited to what rigid transforms can express |
| Industry interop | **Very high** — ARKit-52 is a lingua franca | Low — every studio's bone face is bespoke |
| Runtime cost | Vertex-buffer memory; morph evaluation cost | Cheap; rides existing skinning |
| LOD behaviour | Strippable via morph-target settings (§6) | Strippable via bone removal (§6) |
| Mobile | Heavier | Lighter |
| Anime suitability | **Better** — anime faces need non-anatomical, stylized shapes (`>_<` eyes, shape-changing mouths) that bones cannot produce | Poor for extreme stylization |

**For Melodia this is not a close call.** Anime expression vocabulary is fundamentally non-anatomical, and ARKit-52 is the interop standard both Epic and the wider industry have converged on. **Faceit generating the ARKit set is the correct choice; keep bones only for jaw, eye look-at, head/neck, and tongue.**

---

## 5. Garment / outfit layering in UE

### 5.1 The AAA answer: precompute the non-clipping state

Infinity Nikki is the canonical example and §1.3 is the load-bearing citation: **[DOCUMENTED]** the anti-clipping guarantee is established in a **preprocessing constraint stage**, with runtime multi-layer garment collision handled by a custom solver ([Apple Developer](https://developer.apple.com/news/?id=9mgkwjnm)).

**[COMMUNITY]** The complementary trick is *modelling* discipline: WuWa's hair is reported as specifically designed to minimise clipping ([t/suki](https://forum.tsuki.games/t/a-surface-level-dive-into-wuthering-waves-character-models/149)). **Cheap silhouettes that cannot clip beat expensive solvers that fix clipping.**

### 5.2 Epic's official modular-character options

**[DOCUMENTED]** Epic documents three approaches ([Working with Modular Characters in Unreal Engine](https://dev.epicgames.com/documentation/en-us/unreal-engine/working-with-modular-characters-in-unreal-engine)):

| Method | Setup cost | Game thread | Render thread | Notes |
|---|---|---|---|---|
| **Leader Pose Component** | Minimal | Minimal | High | Parents child skeletal meshes to a parent mesh; animation runs **only** on the parent. Children **cannot** run independent animation or simulate physics. Children must be an **exact subset** of the parent skeleton. |
| **Copy Pose From Mesh** | Medium | High | High | AnimGraph node; each child evaluates its own anim graph — Epic states this is "more performance expensive than using the Leader Pose Component system." Enables per-child physics via **RigidBody / AnimDynamics**. |
| **Skeletal Mesh Merge** | High | Medium | **Low** | Merges to a single skeletal mesh at runtime — lowest recurring render cost. Requires the main mesh component to contain "a full skeleton with all of the character's animations." |

All three require a **shared/matching bone structure**, and Epic notes the general benefit: constructing a character from swappable skeletal meshes at runtime "performs more efficiently than swapping an entire mesh."

**Critical for Melodia — [INFERENCE from Epic's own table]:** **Leader Pose Component is incompatible with per-garment cloth simulation**, because child meshes cannot simulate physics. If Melusina's outfits need Chaos Cloth, the choice is **Copy Pose From Mesh** (paying the anim-graph cost per garment) or driving cloth from the merged mesh. This is the fork in the road and it should be decided early — it is expensive to reverse.

### 5.3 The three anti-clipping techniques, ranked

**[COMMUNITY]**, from practitioner sources:

1. **Per-outfit body-part hiding via a mask texture.** Keep the body as one mesh; author a mask per outfit marking hidden regions; the master material reads the mask and clips those areas ([tutorial](https://www.youtube.com/watch?v=S1Ixei0OJ-o); [yelzkizi, Dressing MetaHumans](https://yelzkizi.org/clothes-for-metahuman/)). **Advantage over cutting the body into pieces: no seams, no extra draw calls, one body asset.** This is the pragmatic default.
2. **Cut-body / modular body chunks.** Swap out torso/arms/legs sections. Classic, robust, but multiplies assets and can seam.
3. **Morph-based shrinkwrap.** Author a per-outfit morph that shrinks the body inward beneath the garment. Handles cases masking cannot (partial transparency, thin garments).

**[COMMUNITY]** General guidance: combining body-mesh management, physics collision setup, and skin-weight tweaks is what actually prevents clipping in practice — no single technique suffices ([yelzkizi](https://yelzkizi.org/clothes-for-metahuman/)).

**Gap:** I found **no** authoritative source describing how Infold specifically implements body hiding (mask vs. cut vs. morph). Their documented contribution is the *preprocessing constraint stage*, not a published body-hiding scheme.

---

## 6. Skeleton and LOD standards — and the 465-bone question

### 6.1 Bone counts

**[COMMUNITY]** Practitioner reference figures ([MoCap Online, rigging guide](https://mocaponline.com/blogs/mocap-news/character-rigging-game-dev-guide) and [skeleton hierarchy guide](https://mocaponline.com/blogs/mocap-news/skeleton-hierarchy-animation-guide)):

- Standard humanoid body, **no fingers: 50–80 bones**
- **With fingers: 100–120 bones**
- **AAA with full finger and facial rigs: 150–200 bones**
- The **UE5 skeleton is 67 bones** (`root`, `pelvis`, `spine_01`–`spine_03`, `neck_01`, `head`, …)
- **Mixamo** uses a **65-bone** standard

**[COMMUNITY]** **Twist bones are non-negotiable:** most game skeletons carry at least one twist bone per forearm, and forearm/upper-arm twist bones exist specifically to prevent the **"candy wrapper"** collapse that occurs when a single bone absorbs all the roll ([MoCap Online](https://mocaponline.com/blogs/mocap-news/character-rigging-game-dev-guide)). Auto-Rig P"ro generates these; **keep them in the export skeleton.**

### 6.2 Is a 465-bone control rig defensible?

**Yes — but only as a Blender authoring artifact, and only if it does not export.** [INFERENCE, high confidence, from the bone-count data above]

Auto-Rig Pro + Rigify face + Faceit produces a rig whose bone list is dominated by **control bones, mechanism/helper bones, IK targets, pole targets, and driver bones**. None of those deform anything. ARP's own export process exists precisely to emit a clean deform-only game skeleton.

The defensibility test is a single question: **how many bones are in the exported `USkeleton` that Unreal sees?**

- **Under ~200 exported deform bones (incl. twists, jaw, eyes, tongue, and any physics/jiggle chains):** entirely normal for a AAA character. Defensible.
- **465 bones arriving in Unreal:** **not defensible.** It inflates every animation asset, every pose evaluation, and every bone-transform upload, and — since ARKit-52 handles expression via morph targets (§4) — a large facial *bone* count would be redundant with the blendshapes. If a portfolio reviewer at Infold opens the skeleton and sees 465 bones, it reads as "did not understand the export step," which is precisely the wrong signal for a technical-artist application.

**Action:** verify the exported skeleton's bone count in Unreal's Skeleton Tree. If it is inflated, fix the ARP export definition — not the Blender rig. The Blender rig being complex is a feature.

### 6.3 LOD bone reduction — Epic's actual mechanisms

**[DOCUMENTED]** ([Skeletal Mesh LODs in Unreal Engine, UE5.8 docs](https://dev.epicgames.com/documentation/unreal-engine/skeletal-mesh-lods-in-unreal-engine?lang=en-US)):

- **Bones to Remove** (under LOD Info) — a manually defined array of bones stripped at a given LOD. Epic notes this "requires the manual definition of the bones you wish to remove," and that removed bones still appear in the Skeleton Tree marked with a **dot icon** instead of a bone icon. Epic's own suggested use: at distance, **remove facial expressions, tongue movement, even fingers or toes**.
- **Bones to Prioritize** + **Weight of Prioritization** (**recommended value: 5,000**) — "any geometry skinned to the bones in the list will not be optimized," protecting important deformation areas from the simplifier.
- **Morph Target Position Error Tolerance** (microns) — higher values cut memory at the cost of quality. **This is the LOD lever for an ARKit-52 face.**
- **Remap Morph Targets** — remaps base-LOD morph targets onto the reduced LOD so deformation survives simplification.
- **LOD Hysteresis** — prevents LOD-transition flicker.
- **Bake Pose** — freezes an animation frame into a static pose at a given LOD.
- **Skin Cache Usage** — Auto / Disabled / Enabled per LOD.
- Reduction **Termination Criterion**: triangle or vertex percentage, max triangle/vertex count, or hybrid.
- **Volumetric Correction** default **1.0** — Epic states "typically the default setting (a value of 1.0) will give the best results."
- **Lock Mesh Edges** maintains boundary structure but **increases triangle count**; **Enforce Bone Boundaries** helps articulated segments but "may cause issues under extreme simplification."

**[INFERENCE]** The clean LOD strategy for Melusina: strip **face bones + all 52 morph targets** at LOD1 or LOD2 (nobody reads micro-expressions at distance), strip **fingers/toes** by LOD2–3, prioritize **shoulders, hips, and chest** so silhouette deformation survives, and keep **twist bones** through mid-LODs since they exist to prevent visible collapse.

**Gap — state it clearly:** neither Infold nor Kuro has published bone counts, LOD counts, triangle budgets, or morph-target budgets. The reduction *mechanisms* above are documented by Epic; the *budgets* are not documented by anyone.

---

## 7. What Melodia should adopt / explicitly not adopt

| # | Practice | Verdict | Rationale & evidence grade |
|---|---|---|---|
| 1 | **SDF face shadow map** | **ADOPT — highest priority** | The genre's visual signature. Bakers already exist ([akasaki1211](https://github.com/akasaki1211/sdf_shadow_threshold_map), [Face_SDF_Generator](https://dincairwen.itch.io/face-sdf-generator)) and the UE material math is ~10 lines ([Victor Lu](https://medium.com/@Donkey/ue5-anime-face-shading-d38ba298ffdf)). Days of work, transformative result. **[COMMUNITY]** but overwhelmingly corroborated. |
| 2 | **Smoothed / spherical normals on face and hair** | **ADOPT — do this before #1** | Kuro explicitly does "spherical normal processing for hair/face" **[DOCUMENTED]** ([Unreal Fest deck](https://www.docswell.com/s/EpicGamesJapan/58W89L-UE_UFT2025_KUROGAMES)). Hours of work in Blender. Fixes the ugliest stylization failures on its own. |
| 3 | **ARKit-52 blendshape face via Faceit** | **ADOPT** | Industry lingua franca; Epic's MetaHuman rig is built to the same set, so Live Link Face maps with no retargeting **[DOCUMENTED, secondary]**. Faceit already generates it. Do not invent a face rig. |
| 4 | **Keep the deform skeleton ≤ ~200 bones; keep twist bones** | **ADOPT** | AAA norm is 150–200 with full finger + face rigs; UE5 stock is 67 **[COMMUNITY]**. 465 must stay a Blender-side authoring number. Verify in UE's Skeleton Tree. |
| 5 | **Dedicated, separable character shadow pass** | **ADOPT (principle)** | Both studios independently special-case character shadows — Infold's three-pass scheme **[DOCUMENTED, via search extraction]**, Kuro excluding characters from RT instance masks with dedicated shadow rays **[DOCUMENTED]**. Implement the cheap version: control character self-shadowing separately from world shadowing. |
| 6 | **Precompute the non-clipping garment rest state (shrinkwrap bake)** | **ADOPT (principle, cheap implementation)** | This is Infold's actual architectural insight — anti-clipping is solved in **preprocessing**, not at runtime **[DOCUMENTED]** ([Apple](https://developer.apple.com/news/?id=9mgkwjnm)). Implement with Blender Shrinkwrap per outfit. Do **not** implement their custom constraint solver. |
| 7 | **Per-outfit body hiding via mask texture in the master material** | **ADOPT** | Avoids seams and extra draw calls versus cutting the body **[COMMUNITY]** ([yelzkizi](https://yelzkizi.org/clothes-for-metahuman/)). Pragmatic default for swappable outfits. |
| 8 | **Hybrid cloth: bone chains for structure, Chaos Cloth only for genuinely soft material** | **ADOPT** | Infold categorize fabric types and split between skeletal physics and ChaosCloth **[DOCUMENTED]**. UE ships `AnimDynamics`/`RigidBody` natively — **zero engine modification required.** Biggest performance win available. |
| 9 | **UE LOD bone/morph stripping (Bones to Remove, Bones to Prioritize @ 5000, Morph Target Position Error Tolerance)** | **ADOPT** | Fully documented first-party mechanisms **[DOCUMENTED]** ([UE5.8 docs](https://dev.epicgames.com/documentation/unreal-engine/skeletal-mesh-lods-in-unreal-engine?lang=en-US)). Strip face bones + morphs at LOD1/2. |
| 10 | **Budget for the UE5 motion-blur vs. UV-animation conflict** | **ADOPT (awareness)** | Infold built a bespoke workaround for exactly this **[DOCUMENTED]** ([Apple](https://developer.apple.com/news/?id=9mgkwjnm)). It will bite you on any scrolling fabric pattern. |
| 11 | **Choose Copy Pose From Mesh over Leader Pose *if* garments need cloth sim** | **DECIDE EARLY** | Epic states Leader Pose children **cannot simulate physics** and cost more on the render thread; Copy Pose costs more on the game thread **[DOCUMENTED]** ([Epic modular characters](https://dev.epicgames.com/documentation/en-us/unreal-engine/working-with-modular-characters-in-unreal-engine)). Expensive to reverse later. |
| 12 | **Forking the engine / custom shading model** | **DO NOT ADOPT (for now)** | Kuro's fork cost them official Epic support and full ownership of every bug **[COMMUNITY]** ([AUTOMATON](https://automaton-media.com/en/column/even-from-a-developers-perspective-wuthering-waves-use-of-unreal-engine-is-borderline-perverse-a-ue4-game-decked-out-in-custom-technology/)); Infold's UE5 upgrade "required extensive modifications" and internal risk debate **[DOCUMENTED, via search extraction]**. Get 90% of the look from materials + post-process first. Revisit only if a specific effect is provably unreachable. |
| 13 | **Custom constraint-based cloth solver / proprietary skeletal-chain algorithms** | **DO NOT ADOPT** | Real, documented, and the correct AAA answer **[DOCUMENTED]** — but it is a specialist-engineering programme inside an **~800-person, 6-year** project ([Apple](https://developer.apple.com/news/?id=9mgkwjnm)). Stock Chaos Cloth plus item #6 is the solo-dev path. |
| 14 | **Ray-traced GI / Lumen back-port / NRD / SER / OMM** | **DO NOT ADOPT** | Kuro's entire deck is graphics-engineering R&D targeting RTX 4060 @ 2K/60 **[DOCUMENTED]** ([deck](https://www.docswell.com/s/EpicGamesJapan/58W89L-UE_UFT2025_KUROGAMES)). Read it to speak the language in an interview; do not build it. UE5.8 ships Lumen — just use it. |
| 15 | **MetaHuman Animator as the facial capture path** | **DO NOT ADOPT without a remap plan** | MHA outputs MetaHuman control-rig curves, not raw ARKit curves; driving an ARKit-52 non-MetaHuman mesh needs a remapping layer **[COMMUNITY]** ([ARKitRemap](https://github.com/Dylanyz/ARKitRemap)). **Live Link Face is the frictionless path for Melusina.** |

### The career-target angle

Infold's GDC 2026 presence is **art-direction-led** — Dodie Gong, Art Director, on outfit narrative and symbolism ([GDC schedule](https://schedule.gdconf.com/session/how-infinity-nikki-turns-outfits-into-fantasy-and-why-it-works/915309), [AUTOMATON](https://automaton-media.com/en/news/you-cant-touch-peoples-hearts-by-just-piling-together-visual-information-infinity-nikki-art-director-explains-how-outfits-are-designed-to-express-narrative-and-sym/)). Combined with the technical picture above, the portfolio signal Infold most plausibly rewards is **"garments that read as designed, integrated cleanly and cheaply"** — i.e. items #1, #2, #6, #7, #8 — rather than raw rendering-engineering depth. **[INFERENCE]**

---

## Source index

**Primary / first-party**
- [Kuro Games, Unreal Fest Tokyo 2025 — ray tracing in Wuthering Waves (Xin Wang), hosted by Epic Games Japan](https://www.docswell.com/s/EpicGamesJapan/58W89L-UE_UFT2025_KUROGAMES) — **strongest source in this brief**
- [Apple Developer — How Infold Games fashioned an open world for Infinity Nikki](https://developer.apple.com/news/?id=9mgkwjnm)
- [Epic — Behind the Scenes of Infinity Nikki](https://www.unrealengine.com/en-US/developer-interviews/behind-the-scenes-of-infinity-nikki-tracing-a-glamorous-turn-to-an-unreal-open-world) — **403 to automated fetch; verify quoted specifics manually**
- [Epic — Exploring the Post-Apocalyptic Charm of ASG Open Worlds in Wuthering Waves](https://www.unrealengine.com/en-US/developer-interviews/exploring-the-post-apocalyptic-charm-of-asg-open-worlds-in-wuthering-waves) — **403; not read**
- [Epic — Skeletal Mesh LODs in Unreal Engine (UE5.8)](https://dev.epicgames.com/documentation/unreal-engine/skeletal-mesh-lods-in-unreal-engine?lang=en-US)
- [Epic — Working with Modular Characters in Unreal Engine](https://dev.epicgames.com/documentation/en-us/unreal-engine/working-with-modular-characters-in-unreal-engine)
- [Epic — Recording Face Animation on iOS Device](https://dev.epicgames.com/documentation/unreal-engine/recording-face-animation-on-ios-device-in-unreal-engine?lang=en-US)
- [Apple — ARFaceAnchor.BlendShapeLocation](https://developer.apple.com/documentation/arkit/arfaceanchor/blendshapelocation)
- [GDC — How 'Infinity Nikki' Turns Outfits into Fantasy](https://schedule.gdconf.com/session/how-infinity-nikki-turns-outfits-into-fantasy-and-why-it-works/915309) — **403; details via search extraction**

**Secondary / editorial**
- [AUTOMATON WEST — Wuthering Waves' use of Unreal Engine is borderline perverse](https://automaton-media.com/en/column/even-from-a-developers-perspective-wuthering-waves-use-of-unreal-engine-is-borderline-perverse-a-ue4-game-decked-out-in-custom-technology/)
- [AUTOMATON WEST — Infinity Nikki art director on outfit design](https://automaton-media.com/en/news/you-cant-touch-peoples-hearts-by-just-piling-together-visual-information-infinity-nikki-art-director-explains-how-outfits-are-designed-to-express-narrative-and-sym/)
- [Vortex Gaming — Wuthering Waves: a technical marvel pushing UE4 to its limits](https://vortexgaming.io/en/postdetail/736367)
- [Wikipedia — Infinity Nikki](https://en.wikipedia.org/wiki/Infinity_Nikki) · [Wuthering Waves](https://en.wikipedia.org/wiki/Wuthering_Waves)

**Community / datamining / practitioner — treat as unverified**
- [ToonXD — Wuthering Waves performance & engine architecture analysis](https://pqmlmaoxd.github.io/gamedev/analysis/2026/04/12/wuthering-waves-performance-issues.html)
- [t/suki — a surface-level dive into Wuthering Waves' character models](https://forum.tsuki.games/t/a-surface-level-dive-into-wuthering-waves-character-models/149)
- [Victor Lu — UE5 Anime Face Shading](https://medium.com/@Donkey/ue5-anime-face-shading-d38ba298ffdf)
- [akasaki1211/sdf_shadow_threshold_map](https://github.com/akasaki1211/sdf_shadow_threshold_map)
- [EricHu33/AnimeShadingPlus — Face Shadow Map creation & baking workflow](https://github.com/EricHu33/AnimeShadingPlus-Anime-Toon-Shader)
- [NoiRC256/URPSimpleGenshinShaders](https://github.com/NoiRC256/URPSimpleGenshinShaders) · [Hoyotoon/HoyoToon](https://github.com/Hoyotoon/HoyoToon) · [Dylanyz/ARKitRemap](https://github.com/Dylanyz/ARKitRemap)
- [Face_SDF_Generator](https://dincairwen.itch.io/face-sdf-generator)
- [miHoYo GDC 2021 talks, fan-wiki transcription](https://mihoyo.fandom.com/wiki/Game_Developers_Conference_2021)
- [MoCap Online — character rigging guide](https://mocaponline.com/blogs/mocap-news/character-rigging-game-dev-guide) · [skeleton hierarchy](https://mocaponline.com/blogs/mocap-news/skeleton-hierarchy-animation-guide) · [face capture for game dev](https://mocaponline.com/blogs/mocap-news/face-capture-game-dev-iphone-arkit-live-link-metahuman)
- [yelzkizi — Dressing MetaHumans in UE5](https://yelzkizi.org/clothes-for-metahuman/) · [Live Link Face with MetaHuman](https://yelzkizi.org/live-link-face-with-metahuman/) · [Faceware facial motion](https://yelzkizi.org/metahuman-facial-motion-with-faceware/) · [MetaHuman mocap workflow](https://yelzkizi.org/metahuman-mocap-workflow/)
- [Pooya de Person — ARKit 52 blendshapes artist guide](https://pooyadeperson.com/the-ultimate-guide-to-creating-arkits-52-facial-blendshapes/)
- [Daniel Ilett — 10 shaders explained quickly (inverted hull outlines)](https://danielilett.com/2023-04-07-tut6-5-10-shaders-quickly/)
- [Simon Schreibt — Infinity Nikki: Mysterious Shadow Drop](https://simonschreibt.de/gat/infinity-nikki-shadow/) — **connection refused during research; recommended follow-up read**
- [UE forums — Deconstructing/replicating WuWa's anime shader in UE5](https://forums.unrealengine.com/t/deconstructing-replicating-wuthering-waves-post-process-anime-shader-model-in-ue5/2739985) — unanswered question thread
