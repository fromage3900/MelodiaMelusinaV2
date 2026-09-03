# Interchangeable Wardrobe Pipeline — Melodia (Infinity Nikki dev lens)

**Date:** 2026-09-02 · **Author:** Melusina (Hermes agent) · **Authority:** this doc
**Grounded in:** the real, on-disk system — not a hypothesis. Every layer below exists.

---

## 0. The honest reality (read first)

Three things are true on this machine, verified today:

1. **The interchangeable wardrobe authority already exists and is compiled.**
   `Plugins/MelodiaWardrobe/` is a real UE 5.8 plugin: `UMelodiaWardrobeSubsystem` +
   `UMelodiaWardrobeComponent` (slot-swap engine), `UMelodiaCosmeticDefinition` +
   `UMelodiaCosmeticCatalog` (global registry), `UMelodiaWardrobeGachaSubsystem`, and **38
   cosmetic draft definitions across 7 slots** (`Accessory/Dress/Footwear/Outerwear/Skirt/
   Special/Top`), `DA_MelodiaCosmeticCatalog.uasset`, a `MelodiaWardrobe.dll` (compiled), and
   automation tests. This is the engine that makes pieces *interchangeable*.

2. **The garment creation system is also already spec'd.**
   `Docs/Art/UNIVERSAL_GARMENT_SYSTEM_MASTER_SPEC_2026-09-02.md` (S0–S6): 48 panels → 10 garment
   layers → cloth-tier A/B/C/D → one cymatic Chladni vocabulary → verified small master family →
   height-aware PCG staging → MD drape seam. Wardrobe ontology →
   `Docs/Art/UNIVERSAL_GARMENT_WARDROBE_ONTOLOGY_2026-09-02.md` (outfit = a perception contract).

3. **CLO/MD drape is INTERACTIVE-ONLY on this install — no automation.**
   Verified: `Marvelous Designer Enterprise` (the sister app to CLO) ships with **zero script
   API** — empty `PythonLib\`, 0 `.pyd/.py`, stdlib-only CPython 3.7, no headless/console exe,
   no socket surface. It DOES ship real **USD / FBX / Alembic / OBJ** native import/export
   (Omniverse resolver + OmniUsd exporter). So:
   - **You author/drape pieces in MD or CLO (interactive GUI).**
   - **The pipeline ingests the exported USD/FBX/OBJ automatically** (that part IS scriptable).
   - There is **no "CLO store download" API** and no headless CLO — downloading premade pieces
     comes from **Fab / Sketchfab / asset markets** as FBX/OBJ/MHPKG (2nd-citizen intake), or**MD's
     own asset/preset library** browsed interactively.

**Consequently this doc designs the interoperable intake + runtime swap, and names the honest
interactive step (MD drape) rather than pretending to automate it.**

---

## 1. Goal

One pipeline: **any outfit piece → interchangeable runtime slot**, at Nikki bar.
A piece = geometry (skinweight or static) + fabric (cymatic/albedo PBR) + an ontology (which
ability/perception it publishes). Change a slot at runtime without rebuilding Melusina.

```
[Source market: Fab/MD-library/autonomous-interactive]
      │  FBX / OBJ / USD / MHPKG  (2nd-citizen intake; MD drape = interactive)
      ▼
[Source prep — Blender 5.2.1]  scale/rename/slot, cluster panels, per-slot rig attach
      │  OBJ/FBX  |  +  USD where sim cache matters
      ▼
[Canonical stage — Substance Painter]  28 open sets + Chladni variant + AO/geometry resources
      │  (artist textures; base maps pre-baked)
      ▼
[Runtime swap — UMelodiaWardrobe plugin]  slot-swap engine, cosmetic registry, gacha
      ▼
[Commit clothing sim — Chaos/VAT/WPO per cloth tier]  (hero gameplay piece = expensive)
```

## 2. The 7-slot runtime model (already live)

| Slot | Count (drafts) | Gameplay meaning |
|---|---|---|
| Accessory | 4 | wings / hat / headband / ribbon |
| Dress | 4 | Elemental / Ethereal / Noble / Royal |
| Footwear | 4 | boot / sandals / shoes / slippers |
| Outerwear | 4 | cloak / coat / jackets / vestment |
| Skirt | 4 | Classical / Fantasy / ... |
| Top | 4 | ... |
| Special | 14 | resonant forms / gacha |

Catalog contract (from source): `Cos_<Slot>_Melusina<Descriptor>` PascalCase (this is the
09-01 naming-audit standard), `FMelodiaCosmeticRecord` (id/slot/rarity/mesh) + `FMelodiaResonantForm`
(ability), `SlotStyleWeights` (silhouette slots outweigh accessories = composition over count),
`FindCosmeticsWithDanglingForm()` surfaced as data (no silent-no-op).

**Constrain:** every new piece registers in `DA_MelodiaCosmeticCatalog` + a `Cos_` draft; do NOT
invent a second registry. One engine, many pieces.

## 3. Geometry intake & rigging (Blender 5.2.1, scriptable)
- Normalize units (dress-meter space; cm→×100 to UE), rename `SM_/SK_` per slot, **keep the
  Melusina skeleton** (`SK_Melusina_Skeleton`, 465 bones) or the UE5 Manny/Quinn skeleton.
- Cluster 2nd-citizen pieces into the **10 garment layers** (silhouette classifier, seed
  `20260902`) so MD-draped + downloaded pieces land on the SAME cadence.
- Export OBJ (Substance) + FBX (UE). USD only where you need a draped-sim cache.
- **Check Z-up/handedness on import** — the recurring *"biggest win nobody budgets for."*

## 4. Fabric stage (Chladni + AO), scriptable
- One 9-map cymatic PBR family per garment layer on a **verified small master family only**
  (`M_Master_Nikki` / `M_Universal_Enhanced_Fabric` / `M_Master_Toon_Universal_Alpha`).
- **Proper AO bakes** from the canonical (Blender bake of-record → Substance import), not a
  baked-in guess — this is what the canonical stage (done) now provides.
- Chladni variant maps (ShorewakeTidepool, eigenmode lane) give fast hand-painted variants.
- Commit refs: `garment_refresh/` (80), `.../cymatic/` (490), `.../seasons/`.

## 5. Substance stage (done — CanonicalOutfit.spp)
28 open texture sets from the canonical (`Saved/.../CanonicalOutfit/`), 196 MB, `saved: true`,
Chladni 81 + sbs 7 + dress 5 base maps imported, `all_pass: true`, contact sheet + manifest
mirroring night-pkg schema.

## 6. Runtime swap — the interchange
`UMelodiaWardrobeComponent` swaps per-slot mesh/materials live; `UMelodiaWardrobeSubsystem`
owns equipped state + save. New piece = new `FMelodiaCosmeticRecord` + form, NOT new logic.
Cloth tier decides cost on the hero piece (Skirt_Full = Chaos B candidate; WPO C elsewhere).

## 7. Honest workflow boundaries
| Step | Automatable? | How |
|---|---|---|
| Mesh prep / slot / rig attach | **YES** | Blender 5.2 headless scripts |
| Texture + AO bake | **YES** | Substance startup module (proven) |
| Runtime swap / catalog | **YES** | UE plugin (already live) |
| **MD/CLO drape sim** | **NO (interactive)** | GUI; MD/CLO has no script API here |
| **Download via CLO store** | **NO API** | Use Fab/asset markets, or MD library interactively |

---

## 8. Suggested next concrete batch (all offline/scriptable except MD drape)

1. **Ship the canonical stage as a reusable re-runner** — wrap the canonical export (Blender
   5.2) + Substance staging (startup module) into one command so any future outfit revisits it.
2. **Add a `Sources/` intake folder + manifest** under `Saved/Audit/wardrobe_pipeline/` mirroring
   the night-pkg schema (sha256, seed, slot, source prov) — detect source drift on download.
3. **Wire 2–3 downloadable 2nd-citizen pieces** (e.g. Fab "Dresses for MetaHumans") through the
   FAB→OBJ→Substance→catalog path as the interchange proof (Blender-exported, same 10-layer
   cadence). Flag MD-draped hero pieces separately (interactive step).
4. **Close the S4/S5 editor gates** (materialize 14 MIs on the small family; live ground-snap on
   CanonicalLandscape; fix the `TraceChannel` int-vs-enum raycast) — everything is manifest-only
   until the editor cooks it.

## 9. Delivery map
| Deliverable | Path | State |
|---|---|---|
| Wardrobe plugin runtime engine | `Plugins/MelodiaWardrobe/` | **compiled/live** |
| Universal garment master spec | `Docs/Art/UNIVERSAL_GARMENT_SYSTEM_MASTER_SPEC_2026-09-02.md` | done |
| Wardrobe ontology / ability mapping | `Docs/Art/UNIVERSAL_GARMENT_WARDROBE_ONTOLOGY_2026-09-02.md` | done |
| MD integration seam (interactive truth) | `Docs/Art/UNIVERSAL_GARMENT_MD_INTEGRATION_2026-09-02.md` | done |
| Canonical Substance stage | `substance_staging/CanonicalOutfit/` | **done** (28 open sets) |
| This pipeline plan | `Docs/Art/UNIVERSAL_GARMENT_INTERCHANGEABLE_WARDROBE_2026-09-02.md` | live |

*No `.uasset` writes, no `Content/**` by this agent in this pass — offline spec + archaeology.
MD/CLO drape is the interactive-owned step; everything downstream is scriptable and already exists.*