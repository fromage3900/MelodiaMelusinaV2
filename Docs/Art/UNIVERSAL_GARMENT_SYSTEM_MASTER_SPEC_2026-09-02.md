# Universal Garment Creation System — Master Spec

**Date:** 2026-09-02 · **Seed:** `20260902` · **Registry:** `Saved/Audit/universal_garment/universal_garment_system.json` (schema 1.0.0)
**Status:** Authority document. **Supersedes any single garment lane doc.** No lane forks a parallel garment system; every new garment, veil, water zone, or drapery piece must register here first.

## Purpose
Unify every garment-related offshoot (Shorewake dress, Faraway Mother fabric mountains, Cymatic Garment Nikki, singing-water-veil, Klein Veil, MD/Vellum drape) into **one extensible creation system** with one material authority (a 3-master small family), one harmonic/mode vocabulary (Chladni `(m,n)`), one MPC audio-writer contract (single writer, read-only consumers), and one per-level placement contract (height-aware on CanonicalLandscape). A change to any stage that would introduce a *parallel* master, a *second* harmonic vocabulary, a *new* audio writer, or a *new* landscape is a defect.

**Authorities it obeys:** `Docs/Research/INFINITY_NIKKI_UE5_TRANSLATION_FOR_MELODIA_2026-08-30.md` (10 principles), `AGENTS.md` evidence culture + echo contract (maps + ledger row, never prose-only), `Docs/Handoffs/PCGEX_NIKKI_WISE_2026-09-02.md` (height-aware CanonicalLandscape contract).

---

## 1. System architecture

```
Pattern Library (48 panels, one slotted dress mesh)
   └─> Silhouette Classifier 48→10 garment layers
         └─> Cloth-Tier Dispatch A/B/C/D (cost ladder, gameplay piece = expensive)
               └─> Fabric/Cymatic Material Generation (Chladni PBR 9-map + animated flipbook; singing-water zones)
                     └─> Per-Garment MI on the VERIFIED small family (M_Master_Nikki / M_Universal_Enhanced_Fabric / M_Master_Toon_Universal_Alpha)
                           └─> Per-Level PCG Placement (height-aware, CanonicalLandscape, PCGEx measured-curve pleats)
                                 └─> MD Drape Integration Seam (Houdini Vellum / FLIP / Chaos, VAT for terrain)
```

### Stage-by-stage
| # | Stage | Contract / definition-of-done | Echo gate |
|---|-------|-------------------------------|-----------|
| S0 | **Pattern Library** | 48 Shorewake panels packed into `SM_ShorewakeDress_48MAT_v2_slotted.obj`; every panel addressable `SW_Dress_P01..P48` with geometry spans. Deterministic seed `20260902`, hashed. | `universal_garment_s0_pattern_library` |
| S1 | **Silhouette Classifier (48→10)** | `silhouette_garment_label.py` maps all 48 panels into exactly 10 garment-layer material groups; no default/ambig panel; layers pairwise distinct. Manifest v2 seed-locked. | `universal_garment_s1_silhouette_classifier` |
| S2 | **Cloth-Tier Dispatch A/B/C/D** | Every garment/veil/water placement carries a `ClothTier` tag: **A** rigid-authored, **B** Chaos/Cloth (gameplay-meaning hero — expensive), **C** WPO cheap (km + distant), **D** VAT/cache authored bake. Piece with gameplay meaning gets the expensive tier; rest support cheaply. | `universal_garment_s2_cloth_tier_dispatch` |
| S3 | **Fabric/Cymatic Generation** | Per layer a 9-map copernicus PBR set (BaseColor/Normal/Height/Roughness/Metallic/Iridescence/Emissive/ORM/Opacity) + seamless 8-frame flipbook; singing-water zones get zone PBR sets. All texture-only, seed `20260902`, committed. | `universal_garment_s3_fabric_cymatic_generation` |
| S4 | **Per-Garment MI on Small Family** | One MI per garment layer (10) + per water zone (4), each parented to a verified small-family master *only* (masked→Toon_Alpha, satin→Nikki, hero sheet→Enhanced_Fabric). Phantom `M_Master_FarawayMother_Fabric` remapped away first. Import via Interchange/`unreal` python. | `universal_garment_s4_per_garment_mi` |
| S5 | **Per-Level PCG Placement** | Per level, placements grounded on **CanonicalLandscape** (never a new landscape) via Visibility raycast `50000→-50000` + 15cm re-trace + `floating_check`. PCGEx `ExCreateSpline→TensorSpin` for fabric-ridge pleats (not scatter dumps). ISM/Nanite/HLOD/DataLayer conform. | `universal_garment_s5_per_level_pcg_placement` |
| S6 | **MD Drape Integration Seam** | Drape seam for hero sheets (Skirt_Full tier-B, RoseWindow, Klein Veil) + singing-water FLIP veil. Houdini Vellum node presence probed; FLIP OBJ written (Houdini 22 `particlefluidtank→flipsolver→isooffset→OBJ`). Runtime import idempotent; km-terrain contraction is **VAT bake, never runtime sim**. | `universal_garment_s6_md_drape_integration_seam` |

### Cloth-tier mapping (S2 → S3/S4)
| Garment layer | Tier | Solution |
|---|---|---|
| Bodice_Torso / Front / Side / Upper | C | WPO micro-swell via cymatic Height (cheap) |
| Collar / Shoulder_Trim | A | rigid authored motion (structured lace) |
| Shoulder_Ornament | A | rigid studs |
| Sleeve / Underskirt | C | WPO drape |
| **Skirt_Full** | **B** | **Chaos candidate** — hero sheet, collision fidelity where the sing matters; VAT bake for terrain scale |

---

## 2. Naming / reference contracts — one shared vocabulary

All garment layers, cymatic modes, water zones, and drapery tiers speak **one harmonic/mode vocabulary**. The atomic unit is a **sing** = `{domain, piece, chladni:[m,n], read_as}`.

### Harmonic key
- **`(m,n)`** Chladni standing-wave integers, `1≤m,n≤8`. `≤8` keeps nodal lines crisp at 2K; `≥1` keeps them a readable woven motif.
- Bass→treble map (from audio-hero recipe): `m=round(sqrt(f/220)*3), n=round(sqrt(f/220)*5)`.

### Domains (each item carries exactly one `(m,n)` unless tier says otherwise)
| Domain | Set |
|---|---|
| **garment_layer** | 10 layers: `M_Bodice_Torso(5,7) M_Bodice_Front(3,4) M_Bodice_Side(2,6) M_Bodice_Upper(1,3) M_Collar(6,6) M_Shoulder_Trim(4,8) M_Shoulder_Ornament(8,8) M_Sleeve(2,7) M_Underskirt(3,5) M_Skirt_Full(7,9)` |
| **water_zone** (singing-water-veil) | 4 zones: `SheetVeil(2,4) SingingFall(5,7) HearthPool(1,3) TideSeam(6,6)` |
| **drapery_tier** | orth prescription A/B/C/D (independent of mode — a piece's tier and its sing mode are separate contracts) |
| **veil** | hero sheets: Klein Veil, RoseWindow, SheetVeil — tier-B or C drape candidates |

### Filenames, MIs, gameplay tags — contracts
- **Texture:** `T_<Domain>_<Piece>_<Channel>.png` — Domain ∈ {`Cymatic_Garment`, `SingingWater`, `Shorewake_Garment`, `KleinVeil`}; Channel ∈ {BaseColor,Normal,Height,Roughness,Metallic,Iridescence,Emissive,ORM,Opacity}.
- **MI (S4):** `MI_Melusina_<Family>_Cymatic_<Layer>` parented to a verified small-family master chosen by tier.
- **Gameplay tag root:** `Melodia.Sing.Garment.<Layer>` · `Melodia.Sing.Water.<Zone>` · `Melodia.Sing.Veil.<Piece>` — the single `Melodia.Sing.*` namespace that cymatics, water zones, and drapery tiers all key against.

### Audio/MPC contract (non-negotiable)
> **Single writer** `UMelodiaAudioReactivePresentationSubsystem → MPC_Melodia_Palette` (BP: `BeatPulse, BassIntensity, BeatIntensity, BeatPhase, BeatTracker`). Every garment/water/veil consumer is **READ-ONLY** via `UMelodiaCymaticsSubsystem`. Never add a second audio writer.

### Uniqueness rule (breaks today — see gaps)
> **No two co-singing pieces within a level may share the same `(m,n)`.** Adjacent garment layers must differ. This is enforced by the vocabulary gate `universal_garment_vocab_uniqueness` against this registry.

---

## 3. Definition-of-done + echo-contract gate per stage

Each stage closes only through **maps + a ledger row**, never prose. Gate closure = `python Tools/echo_run.py record <gate_id> pass|fail`.

| Stage | DoD evidence (what "pass" means on disk) | Gate id |
|---|---|---|
| S0 | slotted 48-panel OBJ present; panel spans recorded | `universal_garment_s0_pattern_library` |
| S1 | `garment_layers_manifest.json` maps 48→10, no default/ambig | `universal_garment_s1_silhouette_classifier` |
| S2 | every placement tags A/B/C/D; gameplay piece = expensive; budget ≤2 translucent layers (OIT) | `universal_garment_s2_cloth_tier_dispatch` |
| S3 | cymatic 91 + animated 400 + water-zone 38 maps exist with seed manifests; texture-only | `universal_garment_s3_fabric_cymatic_generation` |
| S4 | 10+4 MIs exist on small family; did-not-add-a-master; phantom remapped | `universal_garment_s4_per_garment_mi` |
| S5 | placements ground-snap to CanonicalLandscape (live hit, not `offline_synthetic`); no 774-instance dumps | `universal_garment_s5_per_level_pcg_placement` |
| S6 | Vellum node presence recorded; drape seam import idempotent; Chaos/VAT binding per tier | `universal_garment_s6_md_drape_integration_seam` |
| — | vocabulary uniqueness (no `(m,n)` collision across co-singing set) | `universal_garment_vocab_uniqueness` |

---

## 4. Roadmap — DONE vs editor-gated next

| Stage | State | Note |
|---|---|---|
| S0 Pattern Library | **DONE** | slotted OBJ + spans recorded |
| S1 Silhouette Classifier 48→10 | **DONE** | manifest v2 seed `20260902` |
| S2 Cloth-Tier Dispatch | **PARTIAL** | tier model + table done; Chaos binding + actor-tag wiring pending |
| S3 Fabric/Cymatic Generation | **DONE** | 91 + 400 + 38 maps, manifests, seed-locked |
| S4 Per-Garment MI Small Family | **EDITOR-GATED** | MIs not yet created; import + cook needs editor (Monolith proxy was down 2026-09-02) |
| S5 Per-Level PCG Placement | **EDITOR-GATED** | 0/7 live ground-snap; offline synthetic only; run_in_editor() required |
| S6 MD Drape Integration Seam | **PARTIAL → EDITOR-GATED** | Vellum probe staged, FLIP OBJ written; import + Chaos binding gated |

**Editor-gated backlog (owner):** materialize the 14 MIs on the small family (S4) · fix the `TraceChannel` int-vs-enum raycast bug and ground-snap FarawayMother/SeaAbove placements (S5) · bind tier-B Chaos and run the Vellum presence probe (S6) · enforce the vocabulary uniqueness gate against the registry.

---

## 5. Contracts folded in from prior lanes (do not re-derive)
- `Docs/Art/CYMATIC_GARMENT_NIKKI_PIPELINE_2026-09-02.md` — 10 layer→Chladni table, cymatic fabric recipe, audio contract. **Folded as S1+S3.**
- `Docs/Art/SURREAL_FABRIC_NIKKI_AUDIT_2026-09-02.md` — 10-principle audit; phantom master + ~290-master defect. **Folded as S2/S4 constraints.**
- `Docs/Art/FARAWAY_MOTHER_CLOTH_TIERS_2026-09-02.md` — A/B/C/D per placement + cost ladder. **Folded as S2.**
- `Docs/KLEIN_VEIL_SING_2026-09-02.md` — VDM/Cymatic/LOD/MPC/height-aware placement + idempotent import. **Folded as S3/S5/S6 exemplar.**
- `Docs/Handoffs/PCGEX_NIKKI_WISE_2026-09-02.md` — height-aware CanonicalLandscape contract + wise PCGEx pleats. **Folded as S5.**
- `Saved/Audit/melusina_lookdev/singing_water/*` — zone PBR + FLIP veil manifests. **Folded as S3/S6.**

---

## 6. Gaps blocking true universality (top 3)
1. **Editor materialization (S4/S5).** Everything is offline-manifest-only. MIs are not cooked, PCG placement is 0/7 live ground-snap (`offline_synthetic`, `TraceChannel` bug, empty landscape). The system is manifests until the editor cooks it onto CanonicalLandscape.
2. **Harmonic vocabulary uniqueness is unenforced.** 3 of 4 singing-water zones already collide with garment modes (SingingFall(5,7)=Bodice_Torso; HearthPool(1,3)=Bodice_Upper; TideSeam(6,6)=Collar). No validate gate scores `universal_garment_vocab_uniqueness`, so a future lane can still fork a parallel harmonic.
3. **Master-family consolidation is not enforced.** ~290 masters vs the Nikki-4 small family; 1114 MIs; phantom `M_Master_FarawayMother_Fabric` (referenced, 0 bytes). Until remapped and a do-not-add-a-master gate runs, a lane can fork a parallel authority or fail the cook.

**Gate ceremony (when closing any stage):** run the stage DoD → `echo_run.py record <gate_id> pass|fail` (ledger row) → commit manifests/proof → reference this spec as authority. **Registry edit ceremony:** any new sing surface or mode change updates `universal_garment_system.json` **first**, then the vocab gate is re-scored.