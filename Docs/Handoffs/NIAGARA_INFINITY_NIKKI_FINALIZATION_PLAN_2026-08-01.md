# Niagara Finalization Plan — Living Sakura / Infinity Nikki Lens

Status: proposed production plan. This is candidate-first work based on the post-upgrade library audit. It does not authorize overwriting active Niagara systems, maps, landscape, lighting, PCG, hair, or gameplay authority.

## Outcome

The library becomes one authored living-sakura language:

- Petals have mass, direction, life cycle, and readable cause-and-effect.
- Surreal focal effects stay rare and expressive; ambient effects stay quiet and inexpensive.
- Landing, gathering, gusting, and magic reactions happen as layered beats.
- SDF effects become reusable visual instruments instead of invisible prototypes.
- Gameplay sends presentation requests only; Niagara never owns save, battle, quest, collision, or rhythm decisions.

## Approved mesh lanes

| Lane | Mesh | Use | Constraint |
| --- | --- | --- | --- |
| Hero focal petals | /Game/Melodia/Meshes/VFX/SM_SakuraPetal | Close camera, transformations, hero gusts, curated piles | Nanite; 798 triangles; tightly capped |
| Standard petals | /Game/EnvSandbox/Meshes/Sakura/SM_SakuraPetal | Drift, ground scatter, distant gusts | 310 triangles; GPU mesh lane |
| Far density | Existing petal sprite material family | Background only | Never the hero silhouette |

Do not use the imported PolySphere/proxy meshes as petals: they are spherical proxies, not the authored Sakura form.

## 0. Freeze baseline and work in candidates

1. Keep the current upgraded systems as approved runtime baseline.
2. Leave NS_SakuraPetals_v2 untouched while its event chain is repaired in a candidate.
3. Work in versioned candidate folders:
   - VFX/Candidates/Petals
   - VFX/Candidates/SDF
   - VFX/Candidates/Materials
4. Capture fixed-camera before frames for Zen Forest, Morning, and one close pile shot.
5. Keep a manifest for each system: role, mesh lane, material, bounds, warmup, sim target, user parameters, budget, placement owner, sign-off frame.

Promotion is a deliberate replacement only after visual A/B and performance evidence.

## 1. Shared material-loop system

Build one reusable function, MF_MelodiaPetalLifecycle, rather than copied loops.

Inputs:

- normalized particle age
- engine time
- per-particle random / seed
- vertex color and particle color
- particle velocity magnitude
- optional world position
- User.Intensity, User.Reaction01, User.AudioLow, User.AudioMid, User.AudioHigh

Outputs:

- alpha/fade envelope
- hue and value lift
- emissive cap
- UV flutter / rotation offset
- edge sheen
- optional iridescence and contact-darkening weights

The loop must be phase-stable: per-particle offset plus time, never a synchronized global sine.

Create one parent per renderer intent:

1. M_Niagara_PetalMesh_Loop: two-sided mesh petal material with particle color, age, random, and velocity.
2. M_Niagara_PetalSprite_Loop: far-field density card only.
3. M_Niagara_PetalPile: opaque/masked pile material with gentle per-instance hue and roughness variation.
4. M_Niagara_SDF_Loop: shared SDF wrapper, using MF_Niagara_SDF_Sample where appropriate.

Instances expose only art tokens: Palette A/B, opacity, emissive cap, loop speed, flutter, sheen, reaction gain, audio gain, wind gain, density.

## 2. Gameplay-reactivity contract

Every reusable system exposes:

| Parameter | Role |
| --- | --- |
| User.Intensity | Overall authored strength, 0–1 |
| User.Seed | Deterministic variation |
| User.WindVector | External wind direction/speed |
| User.Reaction01 | Short response envelope |
| User.ReactionColor | Palette lift |
| User.ImpactPosition | Optional impact location |
| User.TargetPosition | Optional attraction/destination |
| User.AudioLow/Mid/High | Presentation-only audio bands |
| User.DreamVisibility | Global quality/capture visibility |

Existing authority sends these values after an already-decided interaction, collectible, quest milestone, battle presentation impact, Quill beat, trigger, or audio event. The adapter never grants rewards, changes collision, releases turns, advances quests, or decides rhythm success.

Later, use a small Melodia VFX request payload: profile/system, transform, seed, intensity, reaction color, optional target, lifetime. This keeps future Niagara, sound, and UI reactions aligned without a second game controller.

## 3. Surreal Sakura candidate family

### NS_SakuraPetals_v3_Candidate

Repair v2 topology first:

1. PetalDrift: GPU standard mesh petals with wind, curl, tumble, and lifecycle material.
2. PetalHeroAccents: low-count Nanite petals only for close/focal shots.
3. PetalLandingEvent: source generates real collision/death events and passes position, normal, velocity.
4. PondRippleReceiver: event-spawned ripple that applies event position; no accidental local-shape fallback.
5. PetalPileReceiver: event-spawned settled mesh petals, low count, controlled fade.

Desired beat: wind/player/burst -> airborne petals -> landing event -> ripple or pile -> quiet settle/dissolve.

### NS_SakuraPetalPiles_Candidate

Transient, art-directed piles rather than physics:

- 6–24 petals by quality tier
- orient to surface normal
- randomize yaw, scale, hue, and material phase
- conservative radius so piles read as accumulated flowers
- no per-particle collision after spawn

Long-lived decorative piles remain authored static/HISM dressing under Claude’s environment lane. Niagara piles are transient landing, quest, spell, skill, and shrine moments.

### NS_SurrealSakuraGust_Candidate

Hero-only layered gust:

1. broad GPU mesh-petal arc
2. sparse Nanite petals crossing the camera silhouette
3. restrained ribbon/shimmer wake

Use for transformations, shrine arrival, major skill punctuation, and rare milestones—not ordinary walking.

## 4. Universal SDF candidate family

Treat the six current SDF systems as prototypes, not in-place patch targets:

- NS_SDF_Pulse_Candidate
- NS_SDF_Geometry_Candidate
- NS_SDF_Fish_Candidate
- NS_SDF_Foliage_Bush_Candidate
- NS_SDF_Foliage_Grass_Candidate
- NS_SDF_Foliage_Vine_Candidate

Each candidate must define:

1. spawn count/rate, lifetime, size, color, motion, renderer material, bounds, and warmup
2. GPU sim when no CPU event dependency exists
3. fixed bounds that match the intended volume
4. shared SDF loop material and explicit parameters
5. one real visual role; no generic sprite fallback for fish or foliage

Roles:

- Pulse: short magical ground/architecture response.
- Geometry: shrine, collectible, or combat-readable glyph response.
- Fish: stylized pond-school illusion driven by flow direction, not random sphere bursts.
- Bush/grass/vine: localized magical flutter or wake, never a PCG replacement.

Keep SDF material work camera-safe and bounded; do not raymarch broad ambient particle fields.

## 5. Quality lanes

| Tier | Ambient petals | Hero petals | Piles | SDF |
| --- | --- | --- | --- | --- |
| Fast | Sprite/card or sparse standard mesh | Off | Off | Single simple pulse lane |
| Standard | GPU standard mesh | Limited | 6–12 transient | GPU, simple loop |
| Hero | GPU mesh plus curated Nanite crossings | Focal only | 12–24 transient | Rich loop, capped audio response |

Rules:

- Nanite petals are a composition tool, not a density tool.
- New GPU systems require fixed bounds.
- Warmup defaults to zero; any exception needs written justification.
- No promotion without isolated preview, fixed in-level camera, shader/GPU sample, and clean diagnostics.
- Preserve ENV_StorybookAmbientVFX for ambient systems; use a separate hero effect type only for capture/focal needs.

## 6. Promotion order

1. Build and prove candidate petal material parents/instances.
2. Repair NS_SakuraPetals_v3_Candidate and prove one landing -> ripple/pile loop.
3. Build/validate pile and surreal gust candidates.
4. Repair map-referenced NS_ConstellationDraw and reduce/validate NS_SakuraDreamSparkle warmup.
5. Rebuild SDF candidates one role at a time.
6. Claude places/composes approved systems; Codex does not edit maps.
7. Promote one candidate at a time, retain dated recovery copies, then quarantine only proven superseded systems after reference checks.

## Sign-off

- Silhouette reads at close, traversal, and wide camera ranges.
- One landing creates exactly one intended secondary response.
- No duplicated bursts, local-origin receiver spawns, or real event defects.
- Material loop feels varied and restrained; no synchronized pulsing.
- Presentation adapter only consumes authoritative events.
- Standard tier stays affordable at the fixed Zen Forest camera.
- Hero/Nanite petals stay capture-critical or authored focal.
- Every replacement has before/after capture and rollback asset.
