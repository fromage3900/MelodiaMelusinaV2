# Cross-System Integration Map — 2026-09-01

> **Purpose:** How the five Melodia pillars — **Cymatics**, **Faraway Mother**, **Rhythm**, **Wardrobe**, **Water/Sea Above** — interconnect via shared fields, materials, and level systems.
> **Companions:** `grand_review_document.md` (§3 = 7-rec matrix) · `onboarding_guide.md` (§7 = ownership table) · `Docs/Research/EMERGING_TOOLCHAIN_MASTER_INDEX_2026-08-31.md` (§5 = field contracts, §7 = synesthesia)
> **State:** 2026-09-01 — P0 8/8 pass, 21 cymatic variants + 16 Faraway GN builders baked, editor gate MODAL_OPEN.

---

## 1. Authority & Boundaries (Do Not Cross)

| Subsystem | Writer / Owner | Contract |
|-----------|---------------|----------|
| Audio reactivity (MPC `MPC_Melodia_Palette`) | `MelodiaAudioReactivePresentationSubsystem` — **sole MPC writer** | Tiers 1–3 are PRESENT: `MelodiaMusicClockSubsystem` → MPC BeatPulse/Phase/Intensity → MetaSounds/PPV/Niagara. Never add a second writer. |
| Audio → geometry | `UMelodiaCymaticsSubsystem` — **read-only consumer** of the MPC above | Chladni mapping only; never writes back into MPC. |
| Rhythm combat | `BP_BattleController` (JRPG template) + `MelodiaRhythmCombatSubsystem` | Rhythm rides **on top of** JRPG decisions (Attack/Skill/Item/Flee) — same turn, timed scalar. |
| Rhythm grade | `EMelodiaSkillGrade` (Perfect/Great/Good/Miss) via Q/W/O/P lanes | Monotonic multipliers into stock JRPG damage; `rhythm_grade_to_result` gate. |
| Wardrobe equip / save / gameplay hook | `MelodiaWardrobeSubsystem` + `MelodiaTraversalCapabilityRegistry` | Canonical slot; `capability.melodia.glide` is the first-slice hook; `IsTraversalUnlocked` / `RequestTraversalMode(Glide)` are the API. |
| World music challenge | `UMelodiaPCGNarrativeChallengeBridgeComponent` | One Piano phrase → one idempotent `challenge.first_resonance_echo` → one visible route (portal unlock). Component must be placed on `PCGHeroMusicNode_0`. |
| Portal / traversal gating | `MelodiaTraversalCapabilityRegistry` + `BP_MelodiaPortal_Hub` | Capability false→true transition; live prompt refresh; `TryInteract` success. |
| Water / ripples / membrane | `MelodiaWaterSimulationZone` (WaterBody + spline) · Niagara fluids | `M_Water_Master_Grand_v7` · membrane 16.0s pulse; oceanology lane is HOLD (vendor inputs missing). |
| Materials / PPV / Niagara | Masters under `Content/EnvSandbox/Materials/` | `M_Master_Toon_Universal` / `M_Master_Toon_Landscape_HeightBlend` / `M_Water_Master_Grand_v7`; `Source/MelodiaShader` PostConfigInit. |

All cross-system flows below **consume** these authorities; none replace them.

---

## 2. Cymatics ↔ Rhythm (Standing Wave → Combat Scalar)

```
Houdini Copernicus (21 variants, 1665 PNGs)
  → 5 PBR maps/frame (BC/N/R/Height/AO) + flipbook frames
    → UMelodiaCymaticsSubsystem (reads MPC BeatPulse/Phase)
      → rhythmic standing-wave field (World Field Bus: Resonance/Tension/Reaction)
        → rhythm grade lane pattern (Q/W/O/P timing windows scale with cymatic frequency)
          → EMelodiaSkillGrade → stock JRPG damage scalar (rhythm_grade_to_result)
```

- **Pillar bridge:** Cymatic spatial frequency maps to rhythm lane density. `SingingConstellations` / `GoldenSpiralGrove` → sparse, high-value Perfect windows; `FrozenFracture` / `VoronoiSacredGeometry` → dense, comb-like timing.
- **Field contract:** Master Index §5b World Field Bus — `Resonance`, `Tension`, `Reaction` carry the cymatic field to rhythm. Do not invent a parallel field name.
- **Gate:** `rhythm_grade_to_result` — monotonic damage multipliers proven 2026-08-28; cymatic-driven windowing must preserve monotonicity.
- **Toolchain:** `melodia-copernicus-parallax` skill (9→21 variants); `Tools/Houdini/flipbook_aaa.py --frames {8,16}`; future 4K hero sets for strongest 2–3 variants.
- **Recs:** Rec 1 (PRESENT) + Rec 5 (ecosystem) + Rec 7 (user-facing cymatic browser).

---

## 3. Cymatics ↔ Water (Standing Wave → Ripple Animation)

```
Cymatic height/AO maps (185 height PNGs)
  → displacement + normal injection into M_Water_Master_Grand_v7
    → MelodiaWaterSimulationZone_SeaAbove ripple grid (Niagara)
      → visible membrane pulse (16.0s) + shoreline standing-wave dress
```

- **Pillar bridge:** Cymatic `Height` → water displacement scale; `Normal` → wave-normal perturbation; `AO` → foam-line mask. Same 5-map PBR set feeds both the toon ribbon and the water surface — one asset, two consumers.
- **Field contract:** World Field Bus `Moisture` / `Residue` / `Contact` / `FilterFlow` (Master Index §5b) + SpeedTree bridge `melodia_moisture` (downstream foliage responds to same wetness).
- **Level instance:** `BP_MelodiaWaterSimulationZone_SeaAbove` in `MelodiaIntegrationMap` / `LV_SeaAbove_Prototype`; reef dressing is PCG-placed, water owns motion (see `LEVEL_DESIGNER_ONBOARDING.md` ownership rule).
- **Recs:** Rec 5 mapping "cymatic patterns → water ripple animation"; Rec 7 cymatic params surface in water tuning (designer slider, not player by default).

---

## 4. Faraway Mother ↔ Wardrobe (Fabric Texture → Garment Authority)

```
Copernicus fabric PBR (6 suites + 12 V3 assets)
  → GN builders (16: fabric_ridge, pleat, lace, silk, …)
    → baked meshes (MotherSilhouette 66177pts, EyeLandmark, Lantern, ClothMountains 8.8MB)
      → fabric textures (T_FM_PleatDetail_N, SeamMask, 3 × 1024² tilechecked)
        → MI on M_Master_Toon_Universal (e.g., MI_Melusina_Dress_Shorewake)
          → MelodiaWardrobeSubsystem equip → MelodiaTraversalCapabilityRegistry (Glide)
            → player traversal (RequestTraversalMode) + cosmetic visible
```

- **Pillar bridge:** Every Faraway Mother texture is authored as wardrobe fabric, not just look-dev. Equipping a Faraway garment must flow through `MelodiaWardrobeSubsystem` — no invented slots, no bypass (P0 `wardrobe_equip_roundtrip` contract: equip→save→restart→load→restore).
- **Constants reuse:** `BASE_H 140 / PLEAT_AMP 60 / SEAM_DEPTH 90 / MOTIF_*` — the same Houdini constants drive both PBR and GN builder pleat geometry. Change the constant once; both update.
- **V3 expansion:** 8 new builders (walkway straight/curved, frill rock/arch, lace tree, pearl bush, silk vine, brocade flower) feed the same wardrobe pipeline — plus structural columns (Doric/Ionic/Corinthian/Fluted/Twisted, 9 PBR maps each) as architectural wardrobe context.
- **Gate:** `wardrobe_gameplay_hook` — one equipped item = one capability (`Glide` first slice; `Swim`/`SeaAboveResonance` horizon). Duplicate check `faraway_v3_cymatic_bridge_gap_analysis_2026-09-01.md` audits this lane.
- **Recs:** Rec 2 (Faraway P1) + Rec 5 (texture→wardrobe mapping) + Rec 7 (Faraway outfit selector UI).

---

## 5. Faraway Mother ↔ Level / PCG (Cloth Mountain → World Population)

```
Faraway GN builders (16) + columns (5 × 9 PBR)
  → baked hero meshes (Silhouette, ClothMountains, Eye, Lantern)
    → Nanite import → PCG population (PCGExtendedToolkit)
      → world scatter (valley depression, fabric ridges, shoulder folds)
        → player-gated visibility (portal unlock / traversal mode)
```

- **Pillar bridge:** Faraway Mother is not just wardrobe — it is **landscape sculpture**. `MEL_mother_valley_depression` / `fabric_ridge` / `moonlight_rig` become PCG-spawnable meshes. `PCGExtendedToolkit` is PRESENT (Master Index §1) — extend it, don't rebuild.
- **Field contract:** World Field Bus `AnchorStability` / `Residue` / `Contact` + SpeedTree bridge `melodia_soil_depth` / `melodia_molt_age` / `melodia_ecological_density` gate where ridges/valleys accept foliage scatter.
- **Level map:** Faraway assets populate `L_KaleidoNave` (tracked PCG proving surface) and `LV_SeaAbove_Prototype`; greybox predecessors are level-local and replaced via reviewed asset refs, not shared-kit rewiring.
- **Recs:** Rec 2 (GN taxonomy integration) + Rec 5 (mesh→PCG mapping).

---

## 6. Full Interconnect — All Five Pillars on One Map

```
                          ┌─────────────────────────────────┐
                          │   MelodiaMusicClockSubsystem     │
                          │   (BPM / phrase / BeatPhase)    │
                          └──────────────┬──────────────────┘
                                         │ BeatPulse / BeatPhase / BeatIntensity
                                         ▼
               ┌──────────────────────────────────────────────┐
               │ MelodiaAudioReactivePresentationSubsystem    │  ← sole MPC writer
               │        MPC_Melodia_Palette                   │
               └──────┬──────────────────────┬────────────────┘
                      │ read-only            │ read-only
         ┌────────────▼──────┐  ┌────────────▼────────────┐
         │ UMelodiaCymatics  │  │ PPV / Niagara / MetaSounds │
         │  Subsystem        │  │ (tiers 1–3 PRESENT)        │
         │  21 variants      │  └───────────┬────────────────┘
         │  Chladni field    │              │ Resonance / Tension
         └────┬──────────────┘              └─────────┬──────┘
              │ Height/N/AO                   ┌───────▼────────┐
     ┌────────▼────────┐                      │ MelodiaWater   │
     │  Rhythm Combat   │  Q/W/O/P → Grade   │ SimulationZone │
     │  BP_BattleCtrl   │◄───────────────────┤ M_Water_Master │
     │  grade→damage    │  cymatic window    │ ripples/membrane│
     └────────┬────────┘                      └───────┬────────┘
              │ typed result                          │ 16s pulse
              │ (victory/defeat/fled/unavail)        ▼
              │                              ┌─────────────────┐
              │                              │  WBP / Quill    │
              │                              │  dialogue + HUD │
              └──────────────┐               │ (sole writers)  │
                             │               └────────┬────────┘
                             ▼                        │
              ┌──────────────────────────────────────▼──────┐
              │     UMelodiaPCGNarrativeChallengeBridge     │
              │     PCGHeroMusicNode_0 (Piano phrase)       │
              │     → challenge.first_resonance_echo        │
              └──────────────────────┬──────────────────────┘
                                     │ reward
                    ┌────────────────▼──────────────────┐
                    │   MelodiaWardrobeSubsystem         │
                    │   ┌──────────────────────────┐     │
                    │   │ Faraway Mother fabrics   │     │
                    │   │ 6 suites +12 V3 +3 tex   │     │
                    │   │ Copernicus PBR → MI      │     │
                    │   └────────────┬─────────────┘     │
                    │                │ equip             │
                    │   ┌────────────▼─────────────┐     │
                    │   │ MelodiaTraversalRegistry  │     │
                    │   │ capability.melodia.glide  │     │
                    │   └────────────┬─────────────┘     │
                    └────────────────┼───────────────────┘
                                     │ IsTraversalUnlocked
                              ┌──────▼──────┐
                              │ BP_Melodia  │
                              │ Portal_Hub  │
                              │ TryInteract │
                              └──────┬──────┘
                                     │ open route
                              ┌──────▼──────┐
                              │ NC    World  │
                              │ PCG pop.    │
                              │ Faraway     │
                              │ meshes      │
                              │ (Nanite)    │
                              └─────────────┘
```

### How one player moment crosses all five

A single verified slice (2026-09-01 real-input) traverses the entire map:

1. **Water/World** — Melusina on `PCGHeroMusicNode_0` pad in water-adjacent PCG volume.
2. **Rhythm** — hits Q/W/O/P with cymatic-shaped windows → `Perfect` (Score 100).
3. **Cymatics** — the successful phrase commits `challenge.first_resonance_echo` (one idempotent typed result) — the cymatic field's role is presentation/grading, not a parallel gate.
4. **Wardrobe** — reward auto-equips `Cos_Accessories_MelusinaV2` (Faraway fabric MI) through `MelodiaWardrobeSubsystem`; save→restart→load restores it (`wardrobe_equip_roundtrip`).
5. **Traversal/Water** — wardrobe grants `capability.melodia.glide`; `BP_MelodiaPortal_Hub` flips `IsTraversalUnlocked` false→true across water-adjacent terrain; airborne `RequestTraversalMode(Glide)` accepted.
6. **PCG/World** — portal `TryInteract` succeeds; Faraway cloth-mountain scatter becomes reachable.

Evidence: `Saved/Audit/p0_real_input_run/01–04_*.png` (4 images per pass).

---

## 7. Material Pipeline — Single-Source PBR, Three Consumers

```
Houdini Copernicus (hython --cook)
  ├─ Cymatic PBR  (BC/N/R/ORM/Height/AO)  ─┐
  ├─ Fabric PBR   (PleatDetail_N, SeamMask) ├─► M_Master_Toon_Universal
  └─ Column PBR   (5 × 9 maps)            ─┘       │
                                              ┌─────┴──────┐
                                              │ PPV / Water │
                                              │ M_Water_Master_Grand_v7
                                              └────────────┘
  GN builders ─► meshes (Nanite) ─► PCG / level
```

- Rule: **bake, never leave playable levels dependent on live HDA cooking** (Master Index §6).
- All textures 1024² (current) → 2048² (next) → 4K hero sets (strongest 2–3 variants only). Tilecheck required; sRGB flags per `verify_tex_contract.py` (the droplet-atlas sRGB→EFFECTS fix in 2026-08-30 is canonical precedent).
- MI strategy: one MI per variant/fiber on the shared master — no variant-owned master. Prismatic dress morph targets (Basis/Nikki_Bloom/Nikki_Swirl/ShimmerWave) remain HB-mapped, not master-derived.
- `Source/MelodiaShader` is `PostConfigInit`; `.usf/.ush` edits need a closed-editor `Build.bat` — not Live Coding.

---

## 8. Field Contracts — Reuse, Don't Invent (Master Index §5)

| Contract | Fields you MUST reuse when bridging | Where they flow |
|----------|--------------------------------------|-----------------|
| **World Field Bus** (§5b) | `FilterFlow / Tension / Moisture / Contact / Residue / Reaction / AnchorStability / Resonance` | Cymatics→rhythm (`Resonance/Tension/Reaction`), cymatics→water (`Moisture/Residue/Contact`), Faraway→PCG (`AnchorStability/Residue`) |
| **SpeedTree semantic bridge** (§5a) | `melodia_moisture / slope / wind_exposure / soil_depth / monolith_proximity / molt_age / filter_flow / tension / ecological_density` | World wetness/pulse → foliage placement on Faraway ridges/valleys |
| **Gameplay labels** | `Melodia.Water.Network.*` / `Melodia.Rhythm.*` as `FGameplayTag` (never raw `FName`) | Puzzle networks, rhythm challenge channels |

Anti-duplication (Master Index §9): if the field name exists in §5, reuse it; if the system is PRESENT (§1) extend it; if SCAFFOLDED (§2) finish it; if WATCH (§3) it needs an owner task; if external (§4) you cannot build it natively.

---

## 9. Gate & Phase Alignment

| Coinsheet gate / Rec | Integration map section | Review pointer |
|----------------------|------------------------|----------------|
| `rhythm_grade_to_result` (pass) | §2 | Cymatics→rhythm monotonicity |
| `wardrobe_equip_roundtrip` + `wardrobe_gameplay_hook` (pass) | §4 | Faraway fabric→MI→wardrobe→Glide |
| `music_world_key` (pass) | §6 (PCG challenge bridge → portal) | Piano phrase→typed result→visible route |
| `battle_integration_map` (pass) | §6 (battle→Quill resume) | 4 outcomes typed, Quill exactly once |
| `static_gates` (pass) | §7 (material pipeline) | Masters + MI + tilecheck baseline |
| Rec 1 cymatics PRESENT | §2 + §7 | 21 variants graduated to §1 |
| Rec 2 Faraway P1 | §4 + §5 | 16 builders + 3 textures → taxonomy/ledger |
| Rec 3 hython↔Monolith | §7 + §8 | Dual path with `cross_path_validation.py` |
| Rec 5 ecosystem | **all sections** | This doc IS the ecosystem map |
| Rec 7 user-facing | §2 + §4 + §7 | Browser/selector/param UI spec (`user_facing_features_spec.json` — not this doc) |

---

## 10. Open Work & Owner Decisions

| Item | Status | Next owner step |
|------|--------|-----------------|
| `melodiaBattleUI` / `MelodiaUI` vestigial vars | Logged — not a binding defect | Owner call to retire (grand_review_document.md §2.1) |
| Starskiff boarding/movement | Genuine gap — Pawn shell only | Isolated adapter proposal (never acquire narrative/battle authority) |
| Shorewake dress equip | Skeleton mismatch (2 vs 465 bones) | Retarget or scope as PCG dressing, not equipable wardrobe |
| Editor modal (MODAL_OPEN) | Recurring — blocks 9316/PIE/gates | Task Manager restart; see onboarding_guide.md §9 |
| 4K cymatic hero sets | Planned (strongest 2–3 of 21) | Human curatorial pick → `hython --res 4096` for selected variants |
| `hythm_monolith_bridge_report.json` typo | Coinsheet misspelling (missing `h`) | Canonical name is `hython_monolith_bridge_report.json` |

---

*Integration companion for Rec 6. Validated that no prior `cross_system_integration_map.md` exists in `Saved/Audit/` or `Docs/`; `grand_review_document.md` §6 confirms non-duplication. Update when Recs 1–5 land — especially variant counts (21), builder counts (16), and texture resolutions — and re-verify gate evidence pointers on refreshed baselines.*
