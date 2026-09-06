# Melodia Melusina — Semester Scope Ledger & Production Contract (Fall 2026)

> **Authority Document**: Companion to `PROJECT.md`, `Docs/Production/WORLDBUILDING_LOOKDEV_PLAN_2026-09-06.md`, and `content/site-copy.json`.  
> **Status**: ACTIVE PRODUCTION CONTRACT (2026-09-06)  
> **Target Audience**: Brennan Shepherd, academic faculty, technical review panel, studio recruiters (Papergames/Infold, HoYoverse, stylized AA/AAA).

---

## 1. Executive Authority & Single Source of Truth

This ledger defines the exact production scope and quality boundaries for the upcoming academic semester. Every deliverable maps to concrete file paths, gate assertions, and verification contracts.

### Non-Negotiable Architectural Invariants
1. **QuillScript** owns all narrative sequencing, dialogue, and 7-verb game notifications.
2. **TurnBased JRPG Template** owns party state, turn sequencing, damage math, inventory, and canonical saves (`BP_JRPGSaveGame`).
3. **No Parallel Authorities**: Rhythm timing, wardrobe attributes, and music puzzles plug directly into the above two authorities. No secondary combat loops or duplicate managers.
4. **Editor Lock Discipline**: Port 9316 must have exactly one listener. Active P0 golden run validation outranks offline content authoring.

---

## 2. Semester Production Matrix & Deliverable Ledger

| Milestone | Creative Deliverable | Authoritative Source / Map | Material & Asset Binding | Gate Ledger Verification |
|---|---|---|---|---|
| **M1: Route & Narrative** | *Chapter 02: Shorewake Calling* Vertical Slice | `Chapters/02_shorewake_calling/`<br>`/Game/EnvSandbox/Environments/L_KaleidoNave`<br>`/Game/EnvSandbox/Monoliths/SeaAbove/Prototype/LV_SeaAbove_Prototype` | Starskiff Kit (`M_Starskiff_Hull`, `M_Starskiff_Brass`), SeaAbove Reef PCG | `chapter_02_route_pass`<br>`repeat_consume` idempotent |
| **M2: Music-as-Key** | Starskiff Lyre Puzzle Unlock | `Source/BS_GodFile/Piano/`<br>`APCGHeroMusicGraphHost` | Piano keys (`SM_PianoKey_*`), Chime stones | `music_world_key` (PASS) |
| **M3: Haute Couture** | Melusina Shorewake Dress & Animated Cloth | `SK_ShorewakeDress_*`<br>`MI_Melusina_Dress_Shorewake` | `MF_FlipbookScrub`<br>`M_Melusina_FlipbookCloth`<br>PearlWoven 16-frame PBR set | `wardrobe_presentation_swap`<br>`wardrobe_gameplay_hook` (Swim) |
| **M4: Character Acting** | Mocap Polish & FACS Performance | `Content/Melodia/Characters/Melusina/Animations/Mocap/`<br>`Tools/build_melusina_face_rig.py` | 464-bone contract (`SK_Melusina`), 68 morph targets → 15 visemes | `anim_contract_pass`<br>`facs_lipsync_test` |
| **M5: VFX Treatment** | Nikki Treatment Tiers T1–T2 | `EnvSandbox/VFX/Materials/`<br>`M_Niagara_SakuraSprite` | `MF_NikkiPastelGrade`<br>`MF_NikkiDreamGrade`<br>`MF_NikkiRimGlow` | `vfx_nikki_tier_recompile`<br>`verify_baseline` (re-freeze) |
| **M6: Shader Convergence** | `NikkiChain` Single Owner Refactor | `M_Master_Toon_Universal_NikkiChain_RepairV2` | 19 showcase MIs reparented; retire V1 and Repair variants | `static_gates` (PASS)<br>Zero dead parameter overrides |
| **M7: Master Showcase** | 60–90s Master Cinematic Reel | `my-site/`<br>`content/site-copy.json` | 4K beauty frames: Sakura arrival, Shorewake departure, wardrobe transform | Public editorial review (Zero-slop compliant) |

---

## 3. Four-Phase Semester Timeline

```
┌────────────────────────────────────────────────────────────────────────┐
│ Phase 1: Weeks 1–4 — Shorewake Vertical Slice & Route Stabilization   │
├────────────────────────────────────────────────────────────────────────┤
│ • Connect KaleidoNave terrace trigger to Starskiff departure route.    │
│ • Wire Quill dialogue beats (MelodiaQuillSkiffDeparture.qsc).          │
│ • Hook Starskiff lyre host to APCGHeroMusicGraphHost puzzle contract.  │
│ • Validate packaged launch outside the editor.                         │
└────────────────────────────────────────────────────────────────────────┘
                                   │
                                   ▼
┌────────────────────────────────────────────────────────────────────────┐
│ Phase 2: Weeks 5–8 — Haute Couture & Shader Treatment Pipeline         │
├────────────────────────────────────────────────────────────────────────┤
│ • Build and test MF_FlipbookScrub for 16-frame PBR texture scrubbing.  │
│ • Wire MI_Melusina_Shorewake_Flip with PearlWoven shimmering cloth.    │
│ • Converge NikkiChain variants onto RepairV2 and re-freeze baseline.   │
│ • Apply T1 (pastel grade) and T2 (rim twinkle) to 30 Niagara sprites. │
└────────────────────────────────────────────────────────────────────────┘
                                   │
                                   ▼
┌────────────────────────────────────────────────────────────────────────┐
│ Phase 3: Weeks 9–12 — Character Performance & Audio-Visual Unity       │
├────────────────────────────────────────────────────────────────────────┤
│ • Retarget and polish 2 hero mocap acting performances for Melusina.   │
│ • Execute FACS lip-sync test with frost-rave vocal stem audio.         │
│ • Tune M_Water_Master_Grand_v10 audio-reactive Gerstner wave pulses.   │
│ • Complete end-to-end playable 5-minute route playthrough.             │
└────────────────────────────────────────────────────────────────────────┘
                                   │
                                   ▼
┌────────────────────────────────────────────────────────────────────────┐
│ Phase 4: Weeks 13–16 — Lookbook Editorial, Master Reel & Showcase     │
├────────────────────────────────────────────────────────────────────────┤
│ • Direct 60–90s master showcase video reel (4K 60fps editorial cuts).  │
│ • Audit content/site-copy.json against high-fashion lookbook standard. │
│ • Deploy updated web portfolio via Vite pipeline to my-site-deploy/.   │
│ • Package recruiter one-sheet dossier for studio submissions.          │
└────────────────────────────────────────────────────────────────────────┘
```

---

## 4. Scope Guardrails & Anti-Drift Contract

### Strictly IN-SCOPE
- Refining existing maps (`L_KaleidoNave`, `LV_SeaAbove_Prototype`, `ZenForestTest`).
- Rigging and shading existing couture models (`T_HauteCouture_*`, `SK_ShorewakeDress_*`).
- Utilizing existing audio tracks (`studio/tracks/frost-rave/`).
- Documenting artistic intent in `content/site-copy.json`.

### Strictly OUT-OF-SCOPE
- Writing new gameplay framework C++ classes outside proven adapters.
- Generating new open-world terrain heightmaps or resetting Gaea setups.
- Spawning uncontrolled subagent swarms that pollute working trees with log files.
- Modifying `Content/TurnBasedJRPGTemplate/Blueprints/Skills/` via raw Python scripts.
