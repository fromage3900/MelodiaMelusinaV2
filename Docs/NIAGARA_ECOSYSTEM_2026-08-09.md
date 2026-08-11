# Melodia Niagara Ecosystem — contract, driver, pipelines (2026-08-09)

One parameter language for every owned Niagara system. Systems are not one-off
effects: they declare a common User.* surface, a project-wide BP fans the same
live signals into all of them, and new systems are built from the proven
pipelines below.

## 1. The parameter contract

Every owned reusable system declares these User parameters (neutral defaults).
The master driver is the only writer; systems consume what their graph uses.

| Param | Type | Source (live bus) |
|---|---|---|
| `User.Intensity` | float | MPC_Melodia_Palette.GlobalReactivity |
| `User.Reaction01` | float | MPC_Melodia_Palette.BeatIntensity (TD audio) |
| `User.AudioLow` | float | MPC_Melodia_Palette.Bass (TD /audio/band/sub,low) |
| `User.AudioMid` | float | MPC_Melodia_Palette.Mid (TD /audio/band/mid) |
| `User.AudioHigh` | float | MPC_Melodia_Palette.Treble (TD /audio/band/high,air) |
| `User.BeatPulse` | float | MPC_Melodia_Palette.BeatPulse (reactivity C++) |
| `User.RhythmPulse` | float | MPC_Melodia_Palette.RhythmPulse (player hit) |
| `User.PlayerProximity` | float | driver-computed `clamp(1 - dist/range)` per component |
| `User.DreamVisibility` | float | MPC_SakuraDream.DreamVisibility |
| `User.DreamIntensity` | float | MPC_SakuraDream.DreamIntensity (fold-in) |
| `User.DreamTwinkleSpeed` | float | MPC_SakuraDream.DreamTwinkleSpeed (fold-in) |
| `User.WindStrength` | float | WindMPC.WindStrength (fold-in) |
| `User.WindVector` | vec3 | driver: (WindStrength, 0, 0) |
| `User.ImpactPosition` | vec3 | driver: player location |
| `User.ReactionColor` | vec4 | driver: white (neutral) |
| `User.Seed` | float | driver: 0 (deterministic variation) |
| `User.TargetPosition` | vec3 | reserved (neutral 0) |
| `User.QuantumChoice` | float | MPC_Melodia_Palette.QuantumChoice (draw winner, 0..1) |
| `User.QuantumSeed` | float | MPC_Melodia_Palette.QuantumSeed (normalized draw seed) |
| `User.QuantumBackend` | float | MPC_Melodia_Palette.QuantumBackend (provider id, 0..1) |
| `User.QuantumChoiceInv` | float | driver-computed `1 - QuantumChoice` (collapse loser) |
| `User.QuantumPulse` | float | MPC QuantumPulse (1.0 on each draw, driver-decayed ~5/s) |
| `User.ReactionColor` | vec4 | MPC QuantumReactionColor — **winner tint**: the draw colors every system |

**Winner palette** (`Tools/quantum_niagara_bridge.py`): Arc=soft coral,
Splash=aqua, Glint=champagne gold, Sigil=lavender, Dust=pearl, Ripple=teal,
EyeSparkle=starlight blue. On every draw the bridge writes the winner color +
a 1.0 pulse; the driver decays the pulse and fans both out project-wide, so
the whole effect set tints to the draw and `NS_Melusina_EntropyDust` poofs the
entropy moment (its SpawnRate is bound to `User.QuantumPulse`).

**Components** (both actors): `VFX_EntropyDust` (root), `VFX_ChaosDrift`
(root), `VFX_Superposition` (hand_r), `VFX_ProviderSigil` (foot_l); relay
BeginPlay attaches them. Latent fix: the JRPG relay's inherited-mesh parent
links are now wired via `Self → GetComponentByClass(SkeletalMeshComponent) →
Cast` (the tool cannot resolve inherited native components as variable gets).

## 6a. Quantum/chaos/entropy VFX systems (2026-08-09)

Four systems themed on the decision-service flavors, all driven by the
Quantum* contract params (quiet at rest; `melodia.Rhythm.Disable 1` unaffected):

| System | Flavor | Driver | Look |
|---|---|---|---|
| `NS_Melusina_EntropyDust` | entropy — unreproducible | rate = `User.QuantumSeed` | sparkle-cluster dust; a new draw is a new pattern |
| `NS_Melusina_ChaosDrift` | chaos — re-seedable | rate = `User.QuantumChoice` | Ghibli wind-swirl motes; the winner re-seeds the drift |
| `NS_Melusina_Superposition` | quantum collapse | StateA rate = `QuantumChoice`, StateB = `QuantumChoiceInv` | diamond star vs 4-point ghost — the collapse IS the pick |
| `NS_Melusina_ProviderSigil` | commit-reveal / provider | rate = `User.QuantumBackend` | harmonic-staff rune; activity maps to the provider id |

Run a draw and the whole set reacts:
`python Tools/quantum_niagara_bridge.py --backend entropy --seed 42`

Conformance (what `Tools/niagara_ecosystem_audit.py --contract` enforces):
fixed bounds, zero warmup, zero compile errors/warnings, contract params
declared. Third-party zones (UltraDynamicSky, _ThirdParty, ArtOfShader,
HairStrands, /Niagara) are reported but out of scope.

## 2. The master driver — `BP_MelodiaNiagaraDriver`

`/Game/Melodia/VFX/BP_MelodiaNiagaraDriver` (Actor, placed in levels that need
ambient VFX reactivity; currently placed in `MelodiaIntegrationMap`).

- **BeginPlay**: cache `PlayerRef` + `ActorCache` (typed actor array).
- **Tick**: chain 11 MPC reads → branch on a 3 s refresh timer (re-caches
  actors — replaces, never appends) → nested ForEachLoop (actors →
  `GetComponentsByClass(NiagaraComponent)`) → per component: proximity math +
  16 param pushes (13 floats, 2 vec3, 1 LinearColor).
- **Sakura fold-in**: `BP_SakuraDreamDriver`'s exact four pushes
  (`DreamIntensity`, `DreamTwinkleSpeed`, `DreamVisibility`, `WindStrength`)
  are preserved inside the master. `BP_SakuraDreamDriver` is superseded,
  kept on disk, unreferenced — do not delete without owner sign-off.
- Per-actor relays (`BP_MelusinaJRPGCharacter`, `BP_MelusinaSwordsman_Presentation`)
  remain for character-attached effects; the driver covers world/ambient systems.
  Pushing the same values twice is idempotent.

## 3. Reference pipelines (the "top" architectures)

Proven stacks to copy when authoring new systems.

**Ambient sprite scaffold** (Universal tier, all Sakura ambient):
`EmitterState → SpawnRate → InitializeParticle → ShapeLocation → AddVelocity →
ParticleState → Gravity/Drag/CurlNoise → ScaleColor → SolveForcesAndVelocity`
CPU or GPU; fixed bounds; warmup 0.

**Event-driven ribbon receiver** (`NS_WindRibbonGust`, `NS_SakuraCosmicAurora`,
`NS_Melusina_SwingTrail`): `EmitterState → InitializeParticle → ParticleState →
CurlNoiseForce → SolveForcesAndVelocity → ReceiveLocationEvent` — deliberately
no spawn module; the "no spawn module" validator warning is a false positive for
event-spawned receivers.

**Death-event receiver** (`NS_SakuraPetals_v2.EM_PondRipple`): local shape +
`ReceiveDeathEvent` on the same stack.

**Character-attached burst set** (Melusina, 2026-08-08): single-emitter CPU
systems, spawn rate bound to a per-system `User.<Rate>` param, ShapeLocation
zero (bone alignment via component socket attach), flipbook/alpha MI material,
fixed bounds, warmup 0. Quiet at rest: default rate 0.

## 4. Audio/OSC data flow (TD ↔ UE)

- **TD → UE, UDP 8000** (`Content/Python/osc_server.py`): `/audio/band/{sub,low,mid,high,air}`
  → `MPC_Melodia_Palette.Bass/BassIntensity/Mid/Treble/TrebleIntensity` +
  `GlobalAudioReactivity`; `/audio/beat` → BeatIntensity; `/time/beat` → BeatPhase;
  `/material/*`, `/niagara/*`, `/melusina/*` → Sakura/Magical MPC toon params.
  Thread-safety rule (documented in the script): OSC thread only stages values;
  a Slate post-tick flush writes them on the game thread.
- **UE → TD, UDP 9000** (`UMelodiaRhythmReactivitySubsystem::SendOSCFloat`):
  `/rhythm/beat_pulse`, `/rhythm/beat_phase`, `/rhythm/combo_normalized`,
  `/rhythm/crescendo_normalized`, `/rhythm/command_energy`, `/rhythm/victory_pulse`.
- The contract's Audio bands + BeatPulse are therefore already live in
  `MPC_Melodia_Palette` whenever TD is running (C1 lane owns TD persistence:
  Embody/Envoy re-toggle after TD restart).
- `melodia.Rhythm.Disable 1` silences beat/rhythm-driven params — the Decision
  016 A/B applies to the whole ecosystem.

## 5. Standing rules

- New owned systems: declare the contract surface, fixed bounds, warmup 0,
  quiet at rest; place under `Content/Melodia/VFX/` or a VFX family folder.
- The driver is the only writer of the contract params (per-actor relays may
  write per-role rate params like `SplashRate`).
- Run `python Tools/niagara_ecosystem_audit.py --contract` after touching
  systems; JSON review at `Saved/Audit/niagara_ecosystem_review.json`.
- Out of scope: UltraDynamicSky/_ThirdParty weather, HairStrands, engine
  `/Niagara` defaults, ArtOfShader glitch systems (audit-reported only).

## 6. Quantum / exotic decision service → Niagara (2026-08-09)

`Tools/quantum_niagara_bridge.py` links the quantum decision service
(`Content/Python/quantum/`, FastAPI port 8008 or in-process) to the ecosystem.

- **What it draws**: the authored reaction-pattern set (Arc, Splash, Glint,
  Sigil, Dust, Ripple, EyeSparkle — difficulty/spacing weighted). Picking the
  leading pattern before a session is the approved "choose among authored
  patterns" use; hit detection/grading stay classical in UE.
- **Providers** (the exotic zoo, all in `draw_providers.py`): `qsharp-simulator`
  (honest 2-candidate amplitude collapse), `qiskit-aer`, `pbit`, `entropy`
  (OS hardware RNG — "physics decides"), `cellular` (Game of Life survivor),
  `commit-reveal` (SHA-256 verifiable fair draw), `chaos`, `swarm`, `oracle`
  (local Ollama), `classical-baseline` (always-available fallback).
- **Path**: draw → `MPC_Melodia_Palette.QuantumChoice/QuantumSeed/QuantumBackend`
  → `BP_MelodiaNiagaraDriver` fans out to `User.Quantum*` on every system →
  `NS_Melusina_Sigil` consumes `User.QuantumChoice` as its spawn rate (the rune
  ring pulses with the draw). Other systems declare the params for future wiring.
- **Fallbacks**: provider failure degrades to classical-baseline (service-side);
  service/Monolith unreachable → the bridge reports and MPC neutral defaults
  (0) keep every system quiet at rest. `melodia.Rhythm.Disable 1` unaffected.
- Run: `python Tools/quantum_niagara_bridge.py --backend entropy --seed 42`
  (add `--patterns Arc,Sigil` for the honest 2-candidate Q# collapse).

## 7. Known flags (2026-08-09)

- `NS_Uni_WaterMist` (placed, production): 3 system-script errors — stale
  "Emitter Fountain Update" called graph. Error text says a graph refresh
  fixes it; MCP cannot refresh graphs. Needs one in-editor refresh
  (open system → recompile) when convenient.
- `NS_Melodia_LaneHit` / `NS_EscherTorusKnot`: authored SpriteSize / RibbonWidth
  inits are present, but the RendererAttributeInit heuristic warning persists.
  Compile-valid; verify in preview before promotion.
- `BP_MelodiaNiagaraDriver` placement: spawn in `MelodiaIntegrationMap`
  (blueprint_query `spawn_blueprint_actor`, blueprint
  `/Game/Melodia/VFX/BP_MelodiaNiagaraDriver`). Deferred: the editor session
  was on another map, and loading the integration map would discard the
  session's open-map state.
- SDF/constellation family (legacy + candidates) are prototypes, not yet
  contract-conformed (reported at 0/15 coverage). Conform when promoted.
- `BP_SakuraDreamDriver` superseded by the master driver's fold-in; kept on
  disk, unreferenced. Do not delete without owner sign-off.
