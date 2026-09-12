# P1 Arc — Mara Elletra Vell and "The Faraway Mother" — 2026-08-29

**Status: DRAFT FOR OWNER CANONIZATION.** The Faraway Mother beats and asset lists below are
quoted from the Level Design Bible (`Docs/Art/MONOLITH_LEVEL_DESIGN_BIBLE_2026-08-26.md`
§"# 10 — The Faraway Mother" — canon). **Mara Elletra Vell does not exist anywhere in the repo
before tonight** (verified: repo-wide grep) — her identity below is a proposal built from the
Bible's own fashion-semiotics line and is marked at every invented point. Nothing here merges
into `DA_MelodiaIntegrationConfig` until the owner approves.

**Companion spec:** `specs/progression/melodia_mara_faraway_mother_quest.v1.json`
(`status: draft_for_owner_review`, allowlist IDs quarantined behind an owner gate).

---

## 1. Where this sits

The P0 loop closed on: Quill → battle → result → Quill resumes → Shorewake attunement →
Starskiff departure (chapter 2 exit: `objective.shorewake.board_starskiff`). Chapter 3 begins
where the skiff sails: the player has a garment that is also a tide-key, and a horizon that
refuses to get closer. That is the Bible's Faraway Mother read, and it is the natural next
monolith: the Bible ranks it **#1 of the three P0 signature vertical slices**.

## 2. Mara Elletra Vell — character draft (OWNER TO CANONIZE)

- **Role:** veil-seamstress and seam-reader; the first person to recognize what Melusina's
  outfit *is*. She is met on/after the Starskiff route — a small lantern-lit stitch-platform
  moored where the wake goes strange.
- **Grounding (Bible-quoted, not invented):** "textile pattern, silhouette and ornament can be
  read as kinship, ritual language or intrusion" and "Matching ancient embroidery may unlock
  paths that are literally woven for the player." Mara is the living embodiment of that line:
  she reads the Shorewake weave as *kinship-marking* — someone wove Melusina's arrival long ago.
- **Function:** quest-giver for `quest.mara.veil_reading`; grants `reward.mara_seam_map` (the
  Seam Map — an embroidery that is also a map, doubling as the music-as-key object for the
  chapter: seam routes open on rhythm, reusing the existing rhythm authority, no new combat).
- **Do not:** give Mara battle/combat authority, a fifth wardrobe track, or a second narrative
  subsystem. She is Quill + one reward + flags, exactly like the Shorewake chain.

## 3. The Faraway Mother — beat mapping (Bible-canon A–H → gameplay)

| Bible beat | Gameplay shape (proposal) |
|---|---|
| A. The Hemlands | Exploration-only; first "fabric geology" materials; no threat |
| B. The Pleated Range | Fold canyons as traversal; glide/swim states from Shorewake carry over |
| C. The Embroidered Basin | Aerial-vs-ground symbol reading (the Seam Map's first use) |
| D. The Veiled Mountains | Fog + translucency; distance lies (PPV work, presentation-only) |
| E. The Far Horizon | `flag.faraway_mother.first_sighting` — the landmark that won't parallax |
| F. The Approach | Long traversal with zero scale change — the *point* is the wrongness |
| G. Perspective Collapse | Rhythm-stabilized cloth (Bible: "rhythm can stabilize cloth folds"); the climb |
| H. The Blink | Non-combat climax: the reinterpretation beat; aftermath fold stays lifted (world-state) |

## 4. Asset needs — Houdini pipeline tasks (the textile-landscape pipeline)

Following the proven reef-lane pattern (deterministic generator → JSON/OBJ → audit → stage →
import queue → MI):

| Asset | Bible "Model" line | Lane task |
|---|---|---|
| Cloth mountain hero surfaces | "cloth mountain hero surfaces" | `build_cloth_mountains.py`: pleated strata (sine-fold layers), seam-line valleys, motif-scatter forests as normal/detail — same JSON+manifest contract as the reef |
| Seam / embroidery kits | "seam / embroidery kits" | `build_embroidery_kit.py`: stitch masks + motif atlases (PulseBand-style LUT reuse) |
| The eye landmark | "close eye / anatomical landmark" | one hero mesh; everything else implied |
| Fabric deformation zones | "traversal-scale fabric deformation zones" | WPO zone volumes + cloth-fold animation LUTs (KelpSway pattern, U=time loop) |
| **Imply, never model** | "full body; distant maternal silhouette" | fog/parallax/lighting — level-side, no mesh |

Stitch-platform for Mara's meeting: one small kitbash-able platform + lantern set (reuse
Starskiff lantern materials — `MI_Starskiff_LanternGlass` exists as of tonight).

## 5. Assets already in place (tonight)

### 5.1 Mara base — built from the Melusina base (owner directive)

- `SK_Mara_Vell_Body` = duplicate of `SK_Melusina_V2_Body` (15.5 MB), **sharing
  `SK_Melusina_Skeleton`** — no skeleton fork, `ABP_Melusina_Current` remains the shared anim
  authority.
- `MI_Mara_Skin_006` / `MI_Mara_Skin_007` = duplicates of Melusina's SBW skin family on
  `M_Master_Toon_Universal`, retinted to Mara's **moonlit-veil palette**
  (`DreamTint` 0.82/0.92/1.0, `ShadowDreamTint` 0.30/0.28/0.52) and assigned to body slots 0–2.
  Slots 3–4 (outline, iris) still shared with Melusina — Mara's outline + eye identity is a
  follow-up pass. Read-back verified, saved.
- **Next for Mara:** her veil-seamstress gown (Outfit Hub stages A–E, the Shorewake pipeline),
  own outline/eye pass, then world placement + `MelodiaQuillMaraVeilReading.qsc` after owner
  canon.

### 5.2 Jellyfish v3 SERAPH (second expansion, same session)

- **190 m main dome**, three **floating veil tiers** with golden-ratio radii
  (95 / 58.7 / 36.3 m) and Fibonacci lobe cascade (21/13/8), detached halo ring (40.6 m),
  **55-filament cilia crown** (deep-sea burglar alarm), **13 arms × 640 m** (7 football fields
  each) on golden-angle phyllotaxis, double bifurcation + 1.5π twist + stronger rise.
- 59 static parts + 13 arms; topology contract verified (zero mismatches); every static part
  carries the 4-pose shape-key set; LUTs unchanged.
- `JELLY_Seraph_Body.fbx` (root armature + 59 parts) + `JELLY_Seraph_Arms.fbx` + clay QA
  renders (`Saved/Audit/sea_above/renders/jelly_v3/`) — visually verified.
- v1/v2 kept untouched: the three variants form a size family (90 → 136 → 190 m) for depth
  staging — a reef juvenile, a cathedral adult, and the SERAPH.

### 5.3 Starskiff MI family (from earlier tonight)

- Starskiff MI family live on `M_Master_Toon_Universal`: Hull_Regal, Brass, Cushion,
  LanternGlass, PlankNail, Wake_Emission (emissive wired).
- Jellyfish v2 GRAND authoring complete (136 m bell, 12 × 480 m double-bifurcating arms,
  1.5π twist) — the surreal-scale language rehearsal for the Mother's garment scale, and a
  direct Sea Above occupant: a creature whose body is already "too large for perspective."

## 6. Queue

1. **OWNER:** canonize/adjust Mara (name, voice, role) → unlock allowlist merge + `.qsc` authoring.
2. `MelodiaQuillMaraVeilReading.qsc` draft (7-verb grammar; `melodia:item:` stays a logging stub).
3. Houdini: `build_cloth_mountains.py` v0 (one hero surface + one seam valley) → audit renders.
4. Contract test: `test_mara_faraway_mother_contract.py` mirroring the Shorewake tests (runs red
   until owner canon — wire it to the draft spec, not the allowlist).
