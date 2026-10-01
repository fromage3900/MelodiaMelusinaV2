# Choral Sheep — Capstone Presentation Build Plan

**Goal:** take the crown-and-collar stage (`S5c_decor`) from "geometry ready, zero animation,
ornaments unwrappable-free" to "imports to UE and renders top-notch tonight," reusing the
Nikki / brooch / Higgsas builder libraries rather than authoring new geometry.

**Status of this document:** plan only. Nothing here has been executed except the audit and the
already-staged prep file.

---

## 0. What I measured (2026-10-01, headless re-reads — not memory)

### The file

`Saved/Audit/choral_sheep/capstone_prep_20261001/choral_sheep_CAPSTONE_PREP_20261001.blend`
— staged from `gn_v2_20260919/choral_sheep_GNv3_S5c_decor_20260925.blend` (the declared canon tip
per `CHORAL_SHEEP_AND_SIR_GN_ANIMATION_PLAN_2026-09-27.md` §1.1). Canon never written.
All 12 re-open verification checks passed.

Already applied and verified in that file:
- `Wool_Groom.matrix_parent_inverse = identity` — the 2026-10-01 root-cause fix. 9,000 curves,
  median root→body distance 0.3039 → 0.0074 BU (40.9x closer). Confirmed visually: no pooling.
- `SW_SculptCage` shrinkwrap on `MrSheepFinal` → `sheephighpolydone`, `NEAREST_SURFACEPOINT`,
  offset 0.0, **last in the stack** (after `S5_VariantTint` → `S5_BodySilhouette` → `Armature`).
  Retargeting to a new sculpt is a one-dropdown change.
- Both 1.22M-poly `sheephighpolydone` ghosts + `Skin_Sheep_ZSpheres2` hidden in render **and** viewport.
- Lissajous halo absent (correct — `S5c_decor` deliberately removed it; `S5c_crown` still has it).

### Geometry Nodes — 22 trees, all healthy

| object::modifier | group | nodes | links |
|---|---|---|---|
| `SheepMusicBeads::S5_MusicBeads` | `MEL_S5_music_beads` | 105 | 148 |
| `SheepWreathCollar::S5_FlowerCrown` | `MEL_S5_flower_crown` | 51 | 60 |
| `SheepHorns::S5_Horns` | `MEL_S5_horns` | 45 | 60 |
| `SheepPearlDanglers::S5_Pearls` | `MEL_S5_pearl_string` | 39 | 58 |
| `SheepTailScroll::GN` | `MEL_filigree_spiral_SheepTailScroll` | 31 | 40 |
| `MrSheepFinal_HD::S5_BodySilhouette` | `MEL_S5_body_silhouette` | 31 | 34 |
| `MrSheepFinal_HD::S3_Wool` | `MEL_S3_wool_body` | 28 | 32 |
| `Wool_Cards::S3_Cards` | `MEL_S3_cards` | 21 | 25 |
| `PearlDangl_0..2::GN` | `MEL_sheep_pearl_dangl` | 17 | 21 |
| `ForeheadStar::GN` | `MEL_sheep_star_charm` | 15 | 20 |
| `Wool_Shell::S3_Shell` | `MEL_S3_shell` | 11 | 9 |
| `SheepEarBead_L/R::S5_Bead_Dial` | `MEL_S5_bead_dial` | 9 | 14 |

**Zero muted nodes anywhere. Zero broken trees. Zero dangling links detected.** Frames are present
on the wool/horn/crown/tail groups (3–4 each) — the trees are already organised, not spaghetti.
`MEL_S5_music_beads` already carries the SceneTime node the render lane needs.

**Conclusion: no GN repair is required.** The audit found nothing to fix. That is a real result,
not a skipped step — the tree expansion work is *additive* (new dials), not corrective.

### Mesh health — 3 real defects

| object | ngons | loose verts | severity |
|---|---|---|---|
| `MrSheepFinal` | **38** | 0 | **bake-ray risk** — ngons are where bake rays miss |
| `PearlDangl_0/1/2` | 2 each | 0 | minor, cosmetic |
| all `cs_*` (58 objects) | 0 | all verts | **not a defect** — these are rig controls with 0 polys |

The `cs_*` "loose vertex" reading is a false positive of my own probe: rig controls legitimately
have vertices and no faces. Do not "clean" them — that would destroy the control rig. The 58
controls also carry non-uniform scale (0.098, 0.283, …) which is normal for that rig's setup.

### Animation — ready, completely empty

```
frame range [0, 0]   fps 24   actions: []  (zero)
rig: 474 bones / 198 c_* controls / 285 drivers / 326 pose constraints
shape keys: MrSheepFinal_HD 16 · Wool_Shell 16 · Wool_Cards 16  (Basis + 15, all 0.0)
```

The 16 shape keys are the asset: `Breath_In/Out`, `Blink_L/R`, `Cheek_Puff`, `Jaw_Open`,
`Lip_Curl`, `Ears_Perk`, `Muzzle_Sniff`, `Body_Squash/Stretch`, `Tail_Curl`, `Wool_Puff`,
`Wool_Ripple`, `Fleece_Settle`.

`S5c_decor` has **0 actions**. `A1_idle_20260927.blend` has the idle take but is the wrong
lineage (no crown). So the idle work needs re-porting onto the crown stage — that is Stage 3 below.

### UV — the substance blocker

```
MrSheepFinal_HD   raw [UVMap, BakeUV]   eval [UVMap, BakeUV]   ✓
Wool_Shell        raw [UVMap, BakeUV]   eval [UVMap, BakeUV]   ✓
Wool_Cards        raw [UVMap, BakeUV]   eval []                 ✗ LOST ON EVALUATE
SheepHorns        raw []                eval []                 ✗
SheepMusicBeads   raw []                eval []                 ✗
SheepPearlDanglers raw []               eval []                 ✗
SheepWreathCollar raw []                eval []                 ✗
SheepTailScroll   raw []                eval []                 ✗
```

Five ornaments are **pure Geometry Nodes** — 0 raw verts, everything generated, no UV attribute on
the output. `S3_Cards` declares a single `Geometry` output and no UV passthrough.

### Addons confirmed enabled in this Blender

`ZenUV` · `MESHmachine` · `MeshCleanerPro` · `SimpleBake` · `Sanctus-Bake` · `UvSquares` ·
`auto_bake` · `Jiggle_Maker` · `SwingyBonePhysicsAddon` · `Handy Curve Profile` ·
`animaide-master` · `Animation_Layers` · `AnimationRetimer` · `LightPainter` · `CURVEmachine`

**`fluffy_maker` is NOT in the enabled list.** Per prior sessions the S3 wool stack is native
`MEL_S3`, not addon-generated, so this is consistent — but do not plan any Fluffy-Maker work.

### Builder libraries available to draw from

- `RawArt/BlenderLibraries/Higgsas/Blender 5.0 Higgsas Geo Node Groups v13.blend` (20 MB, v13)
- `Saved/Accessories/Melodia_Accessory_Studio_v2_MFX_20260922.blend`
- `Saved/Accessories/brooch_lab/backups/` — FlowerBrooch pre/post runs
- `Tools/`: `brooch_silhouettes.py`, `gen_flower_brooch_v10.py`, `gen_brooch_sparkles_v7.py`,
  `spawn_editable_ornament_gn.py`, `organize_ornament_hierarchy.py`, `regenerate_*_surreal_arch*.py`,
  `higgsas_gate.py`, `higgsas_bridge.py` (`deploy/surreal_arch/`), `gn_health_check.py`,
  `cleanup_stage_keep_editable_gn.py`
- `Saved/Audit/nikki_decor/`, `Saved/Audit/NikkiDecorFBX/`, `Saved/Audit/nikki_master/`

---

## Stage 1 — Bake-blocker clearance (do first; everything else depends on it)

**Why first:** Substance and UVB cannot start on an object that has no UVs, and `MrSheepFinal`'s
38 ngons are where bake rays silently miss. Both are cheap and both gate the rest.

1. **Triangulate-before-bake decision on `MrSheepFinal`.** 38 ngons on a 988-poly cage is a large
   fraction. Options: (a) Triangulate modifier above the GN stack, kept live, so it stays
   reversible; (b) triangulate only in an export copy. **Recommendation: (a)** — the body is a
   closed low-poly cage, a live Triangulate above `S5_BodySilhouette` is safe and reversible, and
   it keeps the sculpt-swap workflow intact.
   *Verify:* re-probe ngons → 0; eval poly count roughly 988 → ~1,400–1,600 tris; GN trees unchanged.

2. **Give the five GN ornaments a UV attribute.** Two routes, genuinely different trade-offs:
   - **(a) Bake-to-mesh + unwrap** — duplicate each ornament, `Object > Apply`, `MESHmachine`
     or `ZenUV` smart-unwrap. Fast, guaranteed UVs, but **loses the parametric dials.** The
     flower crown's 9 dials and the horns' curl controls would freeze at their current values.
   - **(b) UV-output nodes inside each group** — append a `Store Named Attribute` (UV) to each
     tree. Keeps every dial live and animatable, costs a small per-tree authoring job.

   **Recommendation: (b) for the three hero pieces** (`SheepWreathCollar`, `SheepHorns`,
   `SheepTailScroll`) because they carry the silhouette and may still be animated for the film;
   **(a) for `SheepMusicBeads` and `SheepPearlDanglers`** — small, dense, unlikely to need
   re-dialing, and the fastest route to a clean bake.
   *Verify:* re-probe raw+eval UV per object; each must show a populated layer with non-zero range.

3. **Add UV passthrough to `S3_Cards`.** One `Store Named Attribute` node so `Wool_Cards` keeps
   `BakeUV` through evaluation instead of losing it.
   *Verify:* `Wool_Cards` eval UV == `['UVMap','BakeUV']`, `lost_on_evaluate: false`.

4. **Clean the 2 ngons on each `PearlDangl_0/1/2`.** Triangulate modifier, live.

**Gate:** every ornament and both wool layers report a populated, non-zero UV set on the
**evaluated** mesh. Run this against a re-opened copy, not the writing session.

---

## Stage 2 — Clean the render surface

1. **The floating ornaments.** The `04_back_wool` preview shows `ForeheadStar`, a pearl and two
   dark spheres detached beside the body. Audit `placement` in the receipt for each: world
   position vs the body's bounds, and parent. Either parent to the correct bone, or delete from the
   presentation copy if they are studio leftovers. **Do not guess** — measure each one's distance
   to the nearest body surface with a BVH, same method as the groom fix.
2. **Decide the two `sheephighpolydone` ghosts.** Hidden now. For a presentation file they are
   2.4M polys of dead weight. Keep one hidden (the shrinkwrap target) and delete the duplicate
   **on a copy only**.
3. **Confirm `SheepWreathCollar` scale.** The skill records a historical 2.0065 unapplied scale;
   this file reads `1,1,1`, so it was resolved. Re-verify rather than assume.

**Gate:** a from-scratch render shows no object floating free of the body.

---

## Stage 3 — Build the animation stack

**The existing plan already names these takes** (A2, from
`CHORAL_SHEEP_AND_SIR_GN_ANIMATION_PLAN_2026-09-27.md` §3). I am not inventing new ones — I am
sequencing them against tonight's UE deadline and adding the two that the film actually needs.

### 3a. Re-port A1 Idle onto the crown stage

`A1_idle_20260927.blend` authored idle on the pre-crown lineage. Channels:
`Breath_In 0.55 / Breath_Out 0.45 / Fleece_Settle 0.10 / Ears_Perk 0.06 / Tail_Curl 0.08`,
plus head micro on `c_neck.x` X ±1° and `c_head.x` Z ±0.8°.

Port those exact values onto `choral_sheep_CAPSTONE_PREP_20261001.blend`. Keep the crown —
that is the whole reason for the re-port.

**Loop gates (same four the prior run passed):** frame-0 key == end key · head-tip delta 0.0 mm at
the loop · "alive" displacement > 0 (prior: 4.53 mm) · bbox deviation ≤ 0.5% (prior: 0.47%).

**Note:** `c_neck.x` measured **0.0** on the Sir rig — dead channel. The sheep's prior run keyed it
and passed gates, but confirm on the sheep rig that head acting reads before relying on it.

### 3b. The A2 event takes

| take | channels | loop? | film use |
|---|---|---|---|
| Graze | `Muzzle_Sniff` + head-down on `c_head.x` | 96f | yes — ground interaction |
| Bleat | `Jaw_Open` + `Cheek_Puff` | 48f | yes — the character's voice |
| EarFlick | `Ears_Perk` | 24f | yes — secondary life |
| TailWag | `Tail_Curl` | 60f | yes — reads from behind |
| Harmonize | head raised + `Wool_Puff` | 120f | yes — pairs with the fleece response |

Each take: shape keys + the matching `c_*` control, own action, own frame range, loop keys closed.

**Gate per take:** FBX anim-only export → reimport → span/loop/alive re-measured. Plus one
key-pose still per take for the owner's eye.

### 3c. Locomotion — the gap I am adding

A1 + A2 give idle and events. **The film needs the sheep moving.** The plan's A-series has no
walk cycle, and the UE side already has 6 retargeted clips (Idle 6.25s / Walk 2.667s / WalkSlow
2.0s / Run 0.833s / Jump 1.125s / Death 1.083s) that were authored elsewhere.

**Two routes:**
- **(a) Author Walk + WalkSlow + Run in Blender** on the `c_user_c_leg_fk` chain. Full control of
  the footfall so the UE follow has something tuned to match. Hours of work.
- **(b) Export-only:** author nothing; take the existing UE clips as the locomotion truth and
  spend tonight on idle/events/presents.

**Recommendation: (b) for tonight, (a) as the next session's job.** The UE clips exist and are
bound to `ABP_ChoralSheep`; the foot-slide tune is already logged as the open item. Writing new
locomotion tonight competes with the presentation for hours you do not have.

### 3d. Scene setup

`frame_end` is **0** — every take needs its range set, and the file needs a default playback range
once takes exist. fps 24 matches UE.

---

## Stage 4 — GN tree expansion (additive, using your libraries)

The audit found the trees healthy, so this stage **adds dials**, it does not repair. Every item
here pulls from a library that already exists.

1. **Flower crown — pull Nikki/brooch blossom builders into `MEL_S5_flower_crown`.**
   `Tools/gen_flower_brooch_v10.py` and `Saved/Accessories/brooch_lab/` already produce blossom
   geometry at higher fidelity than the current 51-node tree. Target: a **blossom-variety dial**
   (currently all 13 blossoms read the same) and a **colour-variation dial** using
   `MEL_S5_variant_tint`'s existing pattern, which is already proven on the body.
2. **Horns — Higgsas curl/spiral builders.** `MEL_S5_horns` is 45 nodes and already produces a
   good curl; a Higgsas variant dial for curl density would give the film a second horn silhouette
   without a second mesh.
3. **Sparkle/rim accents for UE.** `Tools/gen_brooch_sparkles_v7.py` already exists and is tuned
   for presentation lighting. Port as a **render-copy-only** tree — never in the export copy.
4. **Wool density dial.** The 2026-10-01 fix put the groom on the body; the coat still reads
   sparse. `MEL_S3_cards`/`MEL_S3_shell` get one **strand-count / card-density** input so the
   fuller coat is a dial, not a rebuild. This was the open item in
   `groom_fix_20261001/RESULT.md`.

**Guardrail for all of Stage 4:** add inputs to the **modifier interface**, never to the group
defaults. Group defaults get pinned into the modifier when a group is swapped — a known 5.2 trap
recorded in the sheep skill. Force re-eval with `frame_set`, never `view_layer.update()` alone.

---

## Stage 5 — Export + UE handoff

1. **Export hygiene.** `use_armature_deform_only=True` on every mesh export (an as-is FBX carries
   234 LimbNodes from `c_*` controls and shreds retarget). Anim-only FBX per take.
2. **Fix the `SK_MrSheep` ~100× unit artifact** by re-exporting `SK_MrSheep` at true scale. This is
   already A4 in the plan and is a known open item.
3. **Add Graze/Harmonize to `ABP_ChoralSheep`.** The RTG spec already calls for a separate Graze
   slot. This is the one part of tonight that needs the editor — and **the editor is currently
   wedged in a modal loop** (`LogMonolith: MODAL_OPEN` ×17, MCP bridge dead). Dismiss that dialog
   before any UE step, or the whole stage blocks.

---

## Sequencing for tonight

```
1. Bake-blockers (ngons + 5 ornament UVs + S3_Cards passthrough)   ~90 min, headless
2. Render-surface clean (floaters, ghosts, scale verify)          ~30 min, headless
3. Re-port A1 idle onto crown stage                               ~45 min, headless
4. A2 event takes ×5                                              ~3 hr, headless
5. Verdict pass: re-render 4 angles at correct exposure          ~20 min
   └─ owner eye gate on crown + coat density
6. Export FBX set + sidecars                                      ~45 min, headless
7. UE import + ABP states                    ← BLOCKED on editor modal
```

Stages 1–6 are all headless and independent of the editor. **You can dismiss the UE modal
whenever; nothing above waits on it.** Stage 7 does.

## Two things that will block or weaken this, stated plainly

- **The UE editor is wedged.** Until that modal is dismissed, stage 7 cannot start and no
  in-editor proof is possible. Everything before it is fine.
- **The wool coat still reads sparse.** The parent-inverse fix put the groom on the body; it did
  not make the coat plush. Stage 4.4 is the dial that addresses it, and it is a taste call, not a
  bug — `WOOL_LOOK_CHOICE` stays yours.