# MEL_DollHumanoid: GN Convergence Spec (draft, read-only survey 2026-10-17)

Repo surveyed: `C:\EnvironmentPortfolio\BS_GodFile` (this is the **MelodiaMelusinaV2** checkout: origin = github.com/fromage3900/MelodiaMelusinaV2). No separate checkout was found under C:\ at depth 2. Nothing was modified, no Blender or UE was launched, and drive D: was not touched.
Owner of the build and final plan: Animation Expert. This doc is the spec input.

---
## (a) Inventory (brief)

| # | Path | What it is | Verdict |
|---|------|------------|---------|
| 1 | `deploy/surreal_arch/melodia_gn/doll_socket.py` | GN builder `MEL_doll_socket` (registered, category `bionic`). It cuts two EXACT boolean cup cavities into the **skin mesh** and seats a UV-sphere ball (32x16) between them. Inputs: `Center` (vec), `Axis` (vec), `Ball Radius` 0.032 [0.01-0.08], `Cup Shift` 0.45 [0-0.7], `Cavity Scale` 1.05 [1-1.25]. It sets `M_GNJ_Porcelain` and the point attr `mj_porcelain=1`, and adds the audio attributes. | **Adapt**. Keep the cup-cavity idea and the porcelain attr, but the ball must become its own object (right now it is joined into the skin) and the boolean must run on per-segment shells, not on a continuous skin. UV sphere poles break the "quad sphere" rule. |
| 2 | `deploy/surreal_arch/melodia_gn/bionic_joint.py` | GN builder `MEL_bionic_joint` (category `bionic`). It makes a ball/hinge, 0-4 seam rings (tori), two cylindrical socket cups, a string eyelet and a cuff torus. Inputs: `Ball Radius` 0.025, `Seam Rings` 2 [0-4], `Seam Width` 0.25, `Hinge` 0-1 (z-squash), `Cup Depth` 0.35, `Eyelet` bool, `Cuff` bool, `Cuff Radius` 0.07, `Cuff Height` 0.008. Presets: MARIONETTE_BALANCED, KNEE_HINGE, WRIST_BALL, ANKLE_CUFFED, NECK_EYELET (owner direction 2026-09-23: "marionette, NOT cyborg"). | **Reuse** as the per-joint hardware module (the joint-type vocabulary and preset pattern). Swap the UV sphere for a quad sphere and add the contract attrs. |
| 3 | `deploy/surreal_arch/dollkit_pipeline/p0_runner.py` | Runs `Saved/Audit/p0_restpose.py` (rest pose) and saves `C:\EnvironmentPortfolio\harp_bow_pipeline\Melusina_DollKit_WIP_20260923.blend`. | Reference only (the blend lives outside the repo and was not opened). |
| 4 | `.../p1_partition.py` | Splits the `Melusina_DollKit` skin into **15 segments** (`MEL_seg_<head/chest/pelvis/upperarm/forearm/hand/thigh/shin/foot>_l/r`) using vertex groups, a KD flood fill and a PCA arm split (0.55/0.85). Gates: 15 segments and an area ratio of 1.0-1.15. | **Reuse** the segment naming and the gates. The partition logic itself is retired for the new builder, which generates shells directly. |
| 5 | `.../p2_seam_v5.py` | Holds `SEG_STATIONS` (joint label + **ball radius in m** per segment). It places stations at the closest-approach "throat" and deletes twin faces on the b-side. Gate: zero z-fight pairs. | **Reuse** `SEG_STATIONS` radii as the default joint radii table. Twin-face repair becomes unnecessary once shells are generated. |
| 6 | `.../p2_detail.py` | 14 balls + 14 rivet rings + 4 gears (shoulders and hips), plus mats `mj_porcelain`, `mj_brass`, `mj_steel`. | Adapt (the hardware placement source). |
| 7 | `.../p3_rigid_v3.py` | Builds the **15-bone MEL_DollRig** (`neck.x, spine_03.x, spine_01.x, arm/forearm/hand.l/r, thigh/leg/foot.l/r`), applies a rigid bind (one vertex group, weight 1.0), sweeps the ROM and gates collisions (G3, G_bind, G_axes, G4). Notes clearance closes to ~0.2 mm at elbow +60 deg, with ~45 deg the "comfortable" range, and calls rim chamfering a future upgrade. | **Reuse**: the bone names, rigid-bind method, ROM table and gates are the backbone of this spec. |
| 8 | `.../p4_export.py` | Smart UV per segment (66 deg) and a GLB export of segments, hardware and rig (Y-up, skins) to `harp_bow_pipeline\Melusina_DollKit_20260923.glb`. | Adapt. Replace Smart UV with authored identical UVs per joint type, and keep cm/Z-up for UE FBX. |
| 9 | `.../p6_refine.py` | Larger waist/neck balls (0.038/0.026, "proud like Ashlotte's corset joints"), a stacked double ring (Ashlotte layering), 12 rivets, cog gears at shoulders and hips, flared cuffs over rim scars, and a wind-up key. | Adapt (style module, opt-in per preset). |
| 10 | `.../p7_clockwork.py`, `.../p9_seating.py` | Control mesh `MEL_dollkit_stations` (points = joints, attrs = editable params) plus a master GN tree `MEL_clockwork_GN` (ball, ring, rivets, spinning gear, cuff). P9 fixes: opening radius = authored `br`, rim ≥4 mm outside the ball, L/R averaged ball_r. | **Reuse** the station-point control mesh as the driver pattern for the new builder. |
| 11 | `.../repair_p9_mechanics.py` | Scoped repair of the P9 graph. Its own `remaining` list says cuff seating, rig-following articulation, Higgsas gear refinement and visual acceptance are **still open**. | Retire after convergence. Carry its open items forward. |
| 12 | `Tools/wardrobe_pipeline/proof_mk39_balljoints.py` | Proof for `MEL_skiff_balljoints` (skiff hull, 18 stations; params `Ball Diameter`, `Collar Ratio`). It is a boat/biomech builder, not humanoid. | Pattern only (proof-gate style). Not a doll source. |
| 13 | UE: `Content/Melodia/Characters/Melusina/DollKit/` | `IK_MEL_DollRig`, `BP_MelusinaDollKit_Preview`, `MI_DollKit_Nikki_Porcelain`, `MI_DollKit_Nikki_Brass`, one retargeted idle anim; `Melusina_DollKit_20260923/SkeletalMeshes/MEL_seg_*` (15 segments, each with its own Skeleton and PhysicsAsset); `StaticMeshes/MEL_dollkit_ball_*` (**14** on disk: neck, waist, shoulder/elbow/wrist/hip/knee/ankle _l/_r; the brief said 13); `MEL_dollkit_gear_{hip,shoulder}_{l,r}` (4); mats `mj_porcelain`, `mj_steel`. | **Keep** as the target and the regression baseline. The new builder must export into these names and that rig. |
| 14 | `.blend` files | No `*.blend` whose name matches doll/bjd/ball/orianna/ashlot/mannequin/puppet was found under `C:\EnvironmentPortfolio` (the DollKit blends sit in `harp_bow_pipeline\` with generic names). So node groups were **not** listed via headless Blender. The inputs above come from the builder source. | n/a |

Note: on-disk UE ball meshes = 14, matching p2_detail's 14-ball gate and the 14 `SEG_STATIONS` labels. The "13 ball joints" in the brief does not match disk. `melodia_gn/__init__` was reported broken on another branch (`barrel_vault_kit` import, per the mk39 docstring).

---
## (b) Lessons from Orianna and Ashlotte

**Research docs NOT found.** `Saved/Audit/ORIANNA_TO_MELDOLLRIG_MAP_2026-09-24.md` and `Saved/Audit/ASHLOTTE_CENSUS_2026-09-24.md` are cited by several plans, but neither exists in `Saved/` or `Docs/`. (Technical Art Lead is hunting for them.) What the repo does contain:

- References (study-only IP, never import into Content): `Reference/Orianna_StarGuardian/StarGuardian Orianna WildRift/` (Orianna.fbx, .pmx, Mat_A-G, DDS) and `Reference/Ashlotte_Maedel/` (SC4_Ashlotte_Maedel.zip plus extracted XPS 1P/2P: `43_Balljoint-D/S`, `44_Balljoint-N`, `34_Cogwheels-*`, `02/23_Metal-*`, lace, bonnet, `prev.png`).
- `Docs/Plans/MELUSINA_GN_PLAN_2026-09-24.md` L111-122, 207-231:
  - **Orianna** gives silhouette, joint language and the companion-slot lesson, which feed the MEL_DollRig station map.
  - **Ashlotte** is the literal balljoint and cogwheel vocabulary (XPS bone_count=200; texture families Balljoint/Cogwheels/Ceramic/Metal).
  - GN supplies only mesh islands and named attrs (`mj_porcelain`, gear metal masks), never IP textures.
- `Docs/Plans/MELUSINA_FULL_EXECUTE_PLAN_2026-09-24.md` L32-33, 54: the Ashlotte comparison criteria are **exposed ceramic spheres, seated metal cuffs, visible gaps, and restrained cog clusters**. Orianna gives joint rhythm and companion/weapon placement. Bind keepers to the 15 bones, accounting for both segment sides of a cuff, with no separation or double transforms when posed.
- `Docs/Plans/MELUSINA_EXECUTE_TO_COMPLETION_GOAL_2026-09-24_pre_gpt6_041244.md` L141: readability means **ceramic ball vs metal rim**.
- `p6_refine.py` L22, 119: proud torso balls (waist and neck) and a stacked double ring (outer proud equator plus inner seat ring) "like Ashlotte".
- Not found in the repo: prescribed proportions, seam-line maps, or reference links from either character. Proportions below come from the P2 conventions doc instead.

---
## (c) Proposed converged builder: `MEL_DollHumanoid`

### Registry fit
- Module: `deploy/surreal_arch/melodia_gn/doll_humanoid.py`. Call `register_builder("MEL_DollHumanoid", build_fn, "Doll Humanoid", desc, category="bionic", role="factory", params=...)` (signature from `core.py` L1295). Presets go in a `DOLL_PRESETS` dict in the same shape as `BIONIC_PRESETS` ("presets, never tree copies").
- Sub-builders: reuse `MEL_bionic_joint` (hardware) and an adapted `MEL_doll_socket` (cup cutter on shells only), plus new `MEL_doll_shell` and `MEL_doll_quadball`.
- Driver: the p7/p9 pattern, a `MEL_dollkit_stations` point cloud (one point per joint carrying `joint_id`, `ball_r`, `axis`). Dragging a point moves a joint.
- Proof script: `Tools/.../proof_doll_humanoid.py` in mk39 style (constructs, evaluates, params move geometry, gates). Receipt goes to `Saved/Audit/`.

### Parameters (suggested inputs)
| Input | Default | Notes |
|---|---|---|
| `Height` | 165 cm | Melusina/Nikki doll figure (`P2_CONCEPT_SHEET_CONVENTIONS_2026-10-17.md` L39: "165 cm, 6.5-head doll"). |
| `Head Ratio` | 6.5 heads | head height = Height / ratio |
| `Shoulder Width`, `Hip Width` | from preset | elegant, slim, non-sexualised; no exaggerated bust or hip forms (team rule) |
| `Upper Arm / Forearm / Hand`, `Thigh / Shin / Foot` | proportional to Height | split fractions are exposed |
| `Joint Radius Scale` + per-joint override | p2 `SEG_STATIONS` (m→cm at 165 cm): neck 2.6 (p6), waist 3.8 (p6), shoulder 2.4, elbow 1.9, wrist 1.5, hip 2.6, knee 2.0, ankle 1.6 | L/R averaged (P9) |
| `Shell Thickness` | 0.3 cm (TBD) | solidify on shells |
| `Socket Depth` / `Cup Shift` / `Cavity Scale` | 0.45 / 1.05 | from `MEL_doll_socket` |
| `Rim Bevel Width` / `Rim Bevel Segments` | 0.25 x ball radius / 3 | user decision 2026-10-17: bevel rims for ROM |
| `Rim Clearance` | ≥0.4 cm | the P9 ≥4 mm rule |
| `Seam Rings`, `Hinge`, `Eyelet`, `Cuff`, `Gears` | per joint type | `MEL_bionic_joint` presets; gears at shoulders and hips only |
| `Fingers` | off | optional finger joints |
| `Style Preset` | — | see below |

**Style presets** (Melusina-style elegant dolls gone wrong; palette per contract v2, MAT_Brass = index 20: dark Velvet/MourningCrepe dresses, Umber hair, Bisque faces, one Rouge accent per doll). Silhouettes are proposals; I found no design docs for these five in the repo.
- `BIRDCAGE_BELLE`: crinoline cage skirt as a `cloth` or rigid cage part; tall neck ball with a 3-ring eyelet.
- `TWIN_TAIL_WALKER`: twin-tail hair parts (deform/cloth); long legs; ankle cuffs.
- `PUPPET_STRUNG`: eyelets on every major joint plus SKT_Emit string anchors; the most visible ball/gap read.
- `VEILED_LANTERN`: veil as a cloth part; lantern socket at the hand; SKT_Emit glow.
- `RUFFLE_SPINE`: segmented spine (extra waist/spine balls) with ruffle collars at the rims.

### Modules
1. **Torso/pelvis shells** (`chest`, `pelvis`): closed solidified shells with cup sockets at neck, waist, shoulders and hips.
2. **Limb segments**: `upperarm/forearm/hand`, `thigh/shin/foot`, `_l/_r`, following the 15-segment names from p1/UE.
3. **Hands**: a mitten block by default; finger segments optional.
4. **Head**: a separate segment with a neck cup; face is Bisque.
5. **Ball joints**: each one is a **separate quad-sphere object** seated in cup sockets cut into **both** adjacent segments, with the origin at the ball centre. A bone rotates the segment and ball rigidly (one vertex group, weight 1.0, as in p3). There is no mesh deformation.
6. **Hardware** (opt-in): rings, rivets, cuffs, gears and the key from `MEL_bionic_joint` / p6.
7. **Elastic cord** in the gaps: a thin tube between the two cup centres per joint, material `MAT_PinkThread`.

### Joint list, bone names, and ROM
Pivots are named after the **IK_MEL_DollRig / MEL_DollRig** bones (p3 `SEG_MASTER`). The pivot sits at the ball centre and is parented to the child bone. ROM defaults come from p3 `BONE_RANGE` (± deg, single main flex axis chosen by p3). "Comfort" is the p3 note (~45° before rim contact).

| Joint | Ball object | Pivot empty | Bone (child) | ROM ± (p3) | Suggested comfort |
|---|---|---|---|---|---|
| neck | `MEL_dollkit_ball_neck` | `SKT_Joint_neck_x` | neck_x | 25 | 25 |
| waist | `..._ball_waist` | `SKT_Joint_spine_03_x` | spine_03_x | 30 | 30 |
| (pelvis) | — | no ball; `spine_01_x` sits under the new `SKT_Root` bone | spine_01_x | — | — |
| shoulder L/R | `..._ball_shoulder_l/r` | `SKT_Joint_arm_l/_r` | arm_l/r | 60 | 45 |
| elbow L/R | `..._ball_elbow_l/r` | `SKT_Joint_forearm_l/_r` | forearm_l/r | 60 | 45 (hinge, one axis) |
| wrist L/R | `..._ball_wrist_l/r` | `SKT_Joint_hand_l/_r` | hand_l/r | 45 | 45 |
| hip L/R | `..._ball_hip_l/r` | `SKT_Joint_thigh_l/_r` | thigh_l/r | 60 | 45 |
| knee L/R | `..._ball_knee_l/r` | `SKT_Joint_leg_l/_r` | leg_l/r | 60 | 45 (hinge) |
| ankle L/R | `..._ball_ankle_l/r` | `SKT_Joint_foot_l/_r` | foot_l/r | 30 | 30 |
| fingers (opt) | `..._ball_finger_<n>_l/r` | `SKT_Joint_finger_<n>_l/_r` | new bones (rig extension, open question) | 0-90 flex only | — |

CONFIRMED (Animation Expert, 2026-10-17): 14 balls. The waist ball belongs to `spine_03_x` (pivot `SKT_Joint_spine_03_x`), riding the child bone and seated in a cup on `spine_01_x`. Bone names in `IK_MEL_DollRig` use underscores (`spine_01_x`, `arm_l`), so no sanitising is needed. A new `SKT_Root` bone sits above `spine_01_x` in the Blender rig only; the UE `IK_MEL_DollRig` asset is not edited, and the new root is mapped at import.

### Topology rules
- Balls are **quad spheres** (subdivided cube, spherified), not UV spheres (doll_socket/bionic_joint use UV spheres today). This gives even quads and no poles above valence 6 (the quad-sphere corners are valence 3).
- Shells: even quads, **support loops at every socket rim** (2 loops, one on the rim and one inset), solidify for real thickness, and closed so there are zero open edges.
- Cup cuts: per the locked topology standard (no booleans in delivered meshes), model the cup into each shell's profile as quads where possible; if a boolean is used during generation, the shell must be cleaned or remeshed to quads before export.
- **Rim bevel (DECIDED by the user 2026-10-17): bevel/chamfer every socket rim** to buy ROM past the p3 ~45° comfort limit. New inputs `Rim Bevel Width` (default 0.25 x ball radius) and `Rim Bevel Segments` (default 3, quads, with a support loop either side). Keep the p9 rule (rim ≥ 4 mm outside the ball) measured at the bevel's inner edge. Target comfort ROM after bevel: shoulder/hip/elbow/knee 60°, wrist 45-50°, verified by re-running the p3 ROM sweep and collision gates; the table above shows pre-bevel comfort values until that sweep is re-run.
- The bevel also gives the `gap` mask a clean ring to run on (0 at the rim top, 1 at the bevel bottom), so the Membrane/PinkThread reveal reads cleanly as the joint opens.
- **One contract-tagged part per object**, merged only at export.

### Materials (combines both steering messages; one conflict flagged)
- Shells: outside `MAT_Bisque` (Porcelain allowed), mapped to UE `MI_DollKit_Nikki_Porcelain` until a Bisque MI exists.
- Ball joints (AGREED with Material Artist, 2026-10-17): balls = glazed `MAT_Porcelain`; rings, cuffs, rivets and gears = `MAT_Brass` (index 20) -> `MI_DollKit_Nikki_Brass`. Glazed balls against matte `MAT_Bisque` shells give the hard-against-soft read. The cup lip inside each shell is `MAT_Bisque` with an AO-darkened edge so the seam reads at distance.
- Membrane: shows inside the socket rim only when the `gap` mask is >0 (driven in UE from bone rotation).
- Cord: `MAT_PinkThread`.
- Dresses: Velvet/MourningCrepe; hair Umber; face Bisque; one Rouge per doll.
- UVs: **identical UV layout per joint type** (all knees share one, and so on), so one cracked-bisque texture set works across all five dolls.

### Contract tags (per object)
| Attr | Type | Notes |
|---|---|---|
| `p2_mat` | int index into `palette_order` (Blender) / string (Houdini) | `materials/p2_palette.json` is referenced by `Tools/concept_sheets/make_concept_sheet.py` L49/901 but was **not found in this repo** |
| `part_id` | snake_case string (Blender: index into the mesh's `p2_part_names` list) | e.g. `seg_thigh_l`, `ball_knee_l`, `cord_knee_l` |
| `p2_part_index` | int | stable ordering |
| `p2_class` (face attr) | enum `rigid` / `deform` / `cloth` | segments and balls = rigid; hair = deform; dress and veil = cloth (requested for the validator) |
| `reveal` | float/int | reveal ordering per the P2 contract (semantics per `Docs/HoudiniForge/ENEMY_WIRING_LIVE_2026-10-15.md`, not re-read here) |
| `joint_id` | int | on ball, cup rim and cord parts. **Defined by the joint contract, see below** |
| `gap` | float 0-1 | socket-rim mask. **Defined by the joint contract** |
| Empties | `SKT_Root` (new root bone above `spine_01_x`), `SKT_Joint_<bone>` (ball centre), `SKT_Emit_*` (lantern/strings), `SKT_Weak_*` (weak points, e.g. cord gaps) | |

### Joint contract (owned by Technical Art Lead, referenced not redefined)
> `SKT_Joint_*` naming, `joint_id`, `gap` mask semantics, cord parts and the identical-joint-UV rule are defined in the Technical Art Lead's joint contract for the validator (path TBD). This builder **emits** those fields and follows that doc. Where this spec and that contract disagree, the contract wins.

### Outputs
- Rigid segments (15) + balls (14) + hardware + cords, each its own object, collected under `MEL_DollHumanoid_<preset>`.
- An auto-generated armature with the IK_MEL_DollRig bone names, heads at ball centres, rigid-bound (weight 1.0, one group per object, the p3 method).
- Export: merge at export only, FBX in cm, Z-up, targeting `Content/Melodia/Characters/<Doll>/DollKit/` and mirroring the Melusina DollKit layout. Prefer one skeletal mesh with a shared skeleton over 15 skeletal meshes, each with its own Skeleton and PhysicsAsset (today's layout). See Open Questions.

### QC checklist (validator-aligned)
- [ ] Zero open (non-manifold boundary) edges per object
- [ ] No poles with valence > 6
- [ ] UVs present on every mesh; joints of the same type have identical UVs
- [ ] Units cm, Z-up, transforms applied, ball origin = ball centre = `SKT_Joint_*` location (≤0.1 mm)
- [ ] Every object has `p2_mat`, `part_id`, `p2_part_index`, `p2_class` (+ `joint_id` where applicable)
- [ ] `SKT_Root` present; one `SKT_Joint_*` per bone in the joint list
- [ ] p3 gates reused: G3 (one group, weight 1.0), G_bind (rest = identity), G_axes (>5 mm displacement at 30°), G4 (min clearance >0.1 mm through the ROM table)
- [ ] P9 rules: rim ≥4 mm outside the ball; L/R ball_r symmetric
- [ ] No Orianna/Ashlotte meshes or textures in Content
- [ ] Silhouette is elegant and non-sexualised (team rule; art review)

---
## (d) Open questions for the user
1. RESOLVED: Porcelain balls, Brass rings/cuffs/gears.
2. The Orianna map and Ashlotte census docs (`Saved/Audit/*_2026-09-24.md`) are missing. Where are they?
3. RESOLVED: 14 balls including the waist.
4. RESOLVED: waist ball on `spine_03_x`. OPEN (user): add finger bones?
5. Export layout: one skeletal mesh with shared skeleton, or keep the per-segment skeletal meshes?
6. RESOLVED: palette and contract live with Material Artist (`contract\p2_contract.json` v2, `materials\p2_palette.json`); MAT_Brass is index 20 and maps to `MI_DollKit_Nikki_Brass`.
7. Are there design briefs for the five P2 dolls? None were found in the repo.
8. RESOLVED (user, 2026-10-17): bevel the socket rims for more ROM; see the Rim bevel rule.


## Contract v2 alignment (Material Artist, 2026-10-17)
- Units: cm. Metre scenes FAIL; FBX/GLB height is checked in cm.
- `p2_mat` on FACES only (Houdini string in `palette_order`, Blender index in range).
- `SKT_Root` may be an empty, a socket, or the armature root bone; a bone literally named `root` FAILS.
- Skipped: Stage/Ground/Lights/Cameras/Ref collections, `GND_`/`STG_`/`REF_`/`CAM_` names, `p2_skip=1`.
- `p2_class` per face: rigid / deform / cloth; on cloth only hems tagged `hem=1` may be open.
- `doll_joint`: `SKT_Joint_<bone>` matched to `IK_MEL_DollRig`, `joint_id`, `gap`, Brass or Porcelain balls, PinkThread cord, identical UVs per joint type.

## Joint contract and validator section (Technical Art Lead, 2026-10-17; packing per contract v2.4)
Follows Material Artist's `p2_contract.json` (`doll_joint`, `ue_export_packing`, `joint_id_order` v2.3, non-joint fix v2.4). Palette v2.6, 21 materials, `MAT_Brass` = 20.

**Rig:** bones match `IK_MEL_DollRig` exactly, underscores only: `spine_01_x, spine_03_x, neck_x, arm_l, forearm_l, hand_l, arm_r, forearm_r, hand_r, thigh_l, leg_l, foot_l, thigh_r, leg_r, foot_r`. `SKT_Root` is a new root bone above `spine_01_x` (Blender only; a bone named `root` fails). 14 pivot empties at ball centres, parented to the child bone head; `spine_01_x` has no ball or pivot.

| joint_id | pivot | station | type |
|---|---|---|---|
| 0 | SKT_Joint_neck_x | neck | neck |
| 1 | SKT_Joint_spine_03_x | waist (cup on spine_01_x) | waist |
| 2 / 3 | SKT_Joint_arm_l / arm_r | shoulder | ball |
| 4 / 5 | SKT_Joint_forearm_l / r | elbow | hinge |
| 6 / 7 | SKT_Joint_hand_l / r | wrist | cuff |
| 8 / 9 | SKT_Joint_thigh_l / r | hip | ball |
| 10 / 11 | SKT_Joint_leg_l / r | knee | hinge |
| 12 / 13 | SKT_Joint_foot_l / r | ankle | cuff |

**Parts:** balls `ball_<station>_<side>`, glazed MAT_Porcelain, rigid, pivot at centre. Rings, cuffs, gears MAT_Brass. Shells MAT_Bisque, joint_id -1, `gap` 0, except cup lips (Bisque, joint_id of their joint, cavity AO). `gap` only on bevel-ring faces, 0 at rim top to 1 at bottom. Cords `cord_<station>` MAT_PinkThread with joint_id. Same-type joints share UV0 within 1%. Rigid pieces and balls skinned 100% to one bone.

**UE packing:** one slot per `MAT_*` key. Vertex colour R `gap`, G `reveal`, B cup-lip AO, A crack seed. UV0 texture; UV1.U 0-1 bevel strip; UV1.V = (joint_id + 0.5)/16 for joints and **15.5/16 for non-joint faces (decodes to 15 = no joint; 14 reserved)**, decoded as `floor(V*16)`; UV2 lightmap. GLB export with vertex colours (`COLOR_0`) and all UV maps (`TEXCOORD_1`). Blueprint writes 14 bend values (0-1) to Custom Primitive Data 0-13.

**Validator (GLB):** `SKT_Root` parents `spine_01_x`; no `root`, dotted or `.001` names; exactly 14 `SKT_Joint_*` mapping to rig bones; slots are palette keys; UV0, UV1 and vertex colour present; UV1.V decodes to 0-13 on joints and 15 elsewhere, constant per face; UV1.U in 0-1; joint faces only Brass/Porcelain/PinkThread/Bisque; cords PinkThread; `gap` > 0 only on rims; rigid parts one bone; same-type joint UVs within 1%; pivots within 0.2 cm of ball centres; contract v2 basics (exclusions, snake_case `part_id`, valid `p2_class`, open edges only on cloth hems, height in cm).

**Build reference (user, 2026-10-17):** match proportions, joint placement and silhouette of the UE DollKit (15 `MEL_seg_*`, 14 balls, 4 gears) and the Melusina character meshes, read-only; build fresh clean quads, don't copy old geometry.

## Roster
Locked: Birdcage Belle, Twin-Tail Walker, Puppet Strung, Veiled Lantern, Ruffle Spine. Optional pending the user: Moth Bride, Motherfold Matron.

- `part_id` encoding (AGREED 2026-10-17): contract v2 snake_case names via `p2_part_names`; the palette's RGB table is now `part_id_debug_colors`, a viewport tint only.
- Build approach (Animation Expert): rig first (`SKT_Root` + 15 bones, 165 cm, cm); shells as lofted quad tubes with cup lips; each ball a quad sphere on its child bone; contract fields, `gap` rim mask and PinkThread cord on every joint; identical joint UVs per type (within 1%); proof script, then a UE import test.
- Housekeeping for the user's next commit: the contract folder is under `Saved\Audit` and not in git (proposed move to `Tools/p2_contract/`); dollkit scripts still point at the old `harp_bow_pipeline` folder.

## UE export packing (contract v2.1, Material Artist, 2026-10-17)
UE drops custom mesh attributes on FBX/GLB import, so pack before export:
- Material slots: one per `MAT_*`, slot named after its key.
- Vertex colour: R = `gap`, G = `reveal`, B = cavity AO on cup lips, A = crack-mask seed.
- UV0 = texture UVs; UV1.x = 0-1 strip along each bevel ring (Membrane/thread gradient), UV1.y = joint id packed per v2.4 (see joint section); UV2 = lightmap.
- Cloth: VAT carries the animated `reveal`.
- The doll Blueprint pushes the 14 live joint angles into the material so the `gap` ramp opens with the bend.
- Validator (Technical Art Lead) opens the exported file and checks: slots named by `MAT_*`, R = `gap` and 0 off the rim, UV1.x ramp, UV1.y one whole `joint_id` per joint, exactly 14 IDs including the waist.
- Gate (user, 2026-10-17): nothing is imported into Unreal and no Copernicus bakes are staged until the first doll passes the validator; ask the user before that import.

## User decisions (2026-10-17, final)
- Export: **15 separate rigid pieces** (matching the 15 `MEL_seg_*`), each skinned 100% to its one bone, so every joint rotates individually. Balls ride their child bone.
- Rig: **Auto-Rig Pro (ARP)**. Bones exported/renamed to the `IK_MEL_DollRig` names with `SKT_Root` on top. If ARP isn't installed, ask the user first.
- Order of work: (1) ARP rig, (2) shells + balls with a 60° pose test, (3) validator, (4) materials and v2.2 packing, (5) UE import only after a pass and the user's go-ahead.
- Export packing follows contract v2.2: `gap` in vertex colour R; UV1.u is the bevel strip; UV1.v = (joint_id + 0.5)/16, with 15.5/16 for non-joint faces (v2.4); the Blueprint writes 14 normalised bend values into Custom Primitive Data slots 0-13.
