# Universal Garment — Wardrobe Ontology & Ability Mapping Layer

**Date:** 2026-09-02 · **Seed:** 20260902
**Status:** Authoring layer deliverable (offline). Companion JSON:
`Saved/Audit/universal_garment/wardrobe_ontology.json`
**Authority it obeys:** `Docs/Research/INFINITY_NIKKI_UE5_TRANSLATION_FOR_MELODIA_2026-08-30.md`
(§2 outplay abilities, §4 master fabric family, §10 WPO-vs-Chaos), the Nikki ability-outfit
doctrine, `Docs/Art/CYMATIC_GARMENT_NIKKI_PIPELINE_2026-09-02.md` (10 garment layers →
10 Chladni modes), `Docs/Art/FARAWAY_MOTHER_CLOTH_TIERS_2026-09-02.md` (Hemkeeper field hook),
`Docs/Evidence/P0_SEA_ABOVE_CYMATICS_LIVE_2026-09-01.json` (single-writer MPC contract).

---

## What this layer is

The universal garment system borrows the *Nikki ability-outfit doctrine* — "each outfit is a
world-exploration action, not a cosmetic stat skin" — and makes it **Melodia-specific** by
turning each outfit into a contract about *which physical theory the player is allowed to
perceive*:

> Outfits do not only solve puzzles. Each outfit changes which physical theory the world obeys
> for the player, and every garment layer, cymatic mode, and MPC consumer lane responds only to
> the math that outfit publishes.

The response records are **read-only consumer lanes** against a single writer
(`UMelodiaAudioReactivePresentationSubsystem` → `MPC_Melodia_Palette`; `MPC_Cymatics_Driver`
has exactly one writer, `UMelodiaCymaticsWriterSubsystem`). This layer never writes audio — it
declares *which existing lanes each garment is allowed to read*.

---

## 1. Garment → world-ontology → gameplay-verb table

| Garment piece | World ontology | Gameplay verb | Ability family |
|---|---|---|---|
| Shorewake veil / **Hemkeeper** | the world is **fabric** | tension / seam / fold interpretation | `hemkeeper` |
| **Shorelistener** | the world is **water** | Tide Seams / impossible-water attunement | `shorelistener` |
| **Glasswing Courier** | the world is **air / adjacency** | Wayfold alignment and spatial continuity | `glasswing` |
| **Mire Apothecary** | the world is **material state** | Catalyze / residue / membrane state changes | `mire_apothecary` |
| **God That Molts** | the world is a discarded biological material | residue / recent-molt reveal | `god_that_molts` |
| **Horizon Eater** | the world is a filter / mouth | filter-flow direction alignment | `horizon_eater` |

**Nikki doctrine mapping (Melodia-specific):** where Nikki grants float/purify/clean/bug-catch,
Melodia grants a *perception contract*. The verb family is the gameplay action; the ontology is
the world-model the player is handed. Rhythm quality improves the *clarity of the read* (God
That Molts §6: better accuracy → clean pattern / legible molt direction), it never gates whether
basic actions work.

---

## 2. Per-outfit response-record FRAMEWORK (read-only)

Every ability family declares **three response surfaces**, each of which reacts only on the
math that family publishes. No surface here is a writer.

| Family | Wardrobe layers that respond | Cymatic modes | MPC consumer lanes (read-only) |
|---|---|---|---|
| hemkeeper | veil, mantle, hem | (7,9), (6,6), (4,8) | `WorldField.Tension`, `WPO_FabricWind`, `Chaos_HeartGate`, `Emissive_Seam` |
| shorelistener | listening_hem, underskirt, hair | (3,5), (3,4), (2,7) | `WorldField.Moisture`, `TideSeamDirection`, `FoamPCRelativeMotion`, `Niagara_DropletLean` |
| glasswing | wings, trail, ornament | (8,8), (4,8), (2,6) | `WorldField.Resonance`, `WayfoldCorridor`, `TransparencyOrder`, `TrailFlow` |
| mire_apothecary | apothecary_robe, membrane, residue_patch | (5,7), (1,3), (4,8) | `WorldField.Residue`, `WorldField.Reaction`, `MembraneFlex`, `PigmentMigration` |
| god_that_molts | molt_husk, laminate, spore_dust | (3,4), (5,7), (3,5) | `MoltReveal`, `LayerAge`, `PigmentMigration`, `MonolithResonance` |
| horizon_eater | veil, particle_trail, mantle | (2,6), (4,8), (7,9) | `WorldField.FilterFlow`, `ParticleConvergence`, `FocalParallax`, `DebrisTrail` |

### Usage rule
The **garment piece carrying gameplay meaning** receives the expensive solution (Chaos / hero
sheet); the rest support it cheaply (WPO / rigid). Per-family `garment_layer_primary` marks the
hero piece. E.g. hemkeeper → `Skirt_Full` (big skirt plate = "full sing", Tier B Chaos
candidate); shorelistener → `Underskirt` (the "listening hem").

### Single-writer enforcement (echo, verified)
- Sole audio writer: `UMelodiaAudioReactivePresentationSubsystem` (writes `MPC_Melodia_Palette`).
- `MPC_Cymatics_Driver` has exactly one writer: `UMelodiaCymaticsWriterSubsystem` (verified by
  grep — no second `SetScalarParameterValue` on that collection).
- This garment layer adds **zero** writers. Every `mpc_consumer_lane` above is a read lane.

---

## 3. Ability families → 10 garment materials + cymatic water zones

### 10 garment materials (chladni mode per layer — no two alike)

| Material | Chladni (m,n) | Reads-as | Primary ability |
|---|---|---|---|
| M_Bodice_Torso | (5,7) | chest note — lowest full-body bass | mire_apothecary |
| M_Bodice_Front | (3,4) | front chest/yoke panels | god_that_molts |
| M_Bodice_Side | (2,6) | side torso | horizon_eater |
| M_Bodice_Upper | (1,3) | upper bodice band | mire_apothecary |
| M_Collar | (6,6) | symmetric collar frame | hemkeeper |
| M_Shoulder_Trim | (4,8) | shoulder/armhole cap trim | glasswing |
| M_Shoulder_Ornament | (8,8) | bead-dot grid nodal | glasswing |
| M_Sleeve | (2,7) | sleeve/arm | shorelistener |
| M_Underskirt | (3,5) | mid skirt/slip | shorelistener |
| M_Skirt_Full | (7,9) | the big skirt plate — full sing | hemkeeper |

### Cymatic water zones (Sea Above)

| Zone | Primary MI | Water theory | Primary ability |
|---|---|---|---|
| lagoon_shallow | GildedCoral | shoreline birth of the tide seam | shorelistener |
| reef_wall | CrystalCathedral | vertical fold where water becomes wall | hemkeeper |
| abyssal_keel | StarlitAbyss | deep fog, leviathan keel filter-flow sink | horizon_eater |
| sky_motes | CymaticReactive | airborne jelly arms — water lifted into air (Wayfold) | glasswing |

**Every zone carries at least one ability**; each ontology family owns a water-theory reading so
an outfit re-perceives the same pool differently.

---

## Strongest ability/garment pairing

> **hemkeeper → Skirt_Full ("the world is fabric" → tension/seam/fold) on the Shorewake veil.**

It is the **only pairing already proven end-to-end** in the codebase: the Heart Gate veil
(Tier B Chaos) is the documented Hemkeeper ontology test, coupling `WorldField.Tension` to both
WPO amplitude on terrain **and** Chaos release on the Veil — the same field driving two costs,
which is exactly the "expensive solution on the gameplay-meaning piece" doctrine and the
single-field/multi-responses pattern this whole layer generalizes. It is live-authored and
wired, so it is the reference to extend rather than a hypothesis.

---

## Deliverables
| Path | What |
|---|---|
| `Docs/Art/UNIVERSAL_GARMENT_WARDROBE_ONTOLOGY_2026-09-02.md` | this document |
| `Saved/Audit/universal_garment/wardrobe_ontology.json` | seed 20260902, ability families, garment→ontology→verb table, MPC read-only lane map, garment materials, water zones |