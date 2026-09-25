> **Pointer 2026-09-24:** Phase 1+ surface detail executes under `MELUSINA_EXECUTE_TO_COMPLETION_GOAL_2026-09-24.md`; GN builders in this plan still apply.

# Melusina Geometry Nodes Plan - Character DollKit + House (2026-09-24)

**Status:** CURRENT PLAN (authoritative)
**Date:** 2026-09-24 (America/Toronto)
**Owner browse path:** `Docs/Plans/MELUSINA_GN_PLAN_2026-09-24.md`
**Agent/work SSOT:** `Saved/Audit/MELUSINA_GN_PLAN_2026-09-24.md`
(Identical full copies in both places.)

**Supersedes:**
- `Docs/Research/GN_ULTIMATE_FRAMEWORK_RESEARCH_2026-09-23.md` (research retained; this plan is the action SSOT)
- Character/bionic GN sections implied by that research when they conflict with DollKit P9 / MEL_DollRig reality

**Does not replace (still live for House lane detail):**
- `Docs/MelodiaStudio/MELUSINA_HOUSE_GN_FOUNDATION_TO_SHELL_ROADMAP_2026-09-04.md`
- `Docs/MelodiaStudio/MELUSINA_HOUSE_GN_BUILDER_INTEGRATION_2026-09-04.md`
- `MELUSINA_HOUSE_GN_START_HERE.md` (repo root)

**Companion DollKit docs (runtime, not GN-only):**
- `Saved/Audit/DOLLKIT_CONVERGENCE_GOAL_2026-09-24.md`
- `Saved/Audit/DOLLKIT_RUNTIME_GAP_MAP_2026-09-24.md`
- `Saved/Audit/DOLLKIT_SSOT_PARK_2026-09-24.md`
- `Saved/Audit/ORIANNA_TO_MELDOLLRIG_MAP_2026-09-24.md`
- `Saved/Audit/ASHLOTTE_CENSUS_2026-09-24.md`

---

## 1. North star

Melusina ships as a **segmented BJD / runtime doll** (DollKit: `MEL_DollRig` + segment SKMs + ball/gear/cuff SMs) and a **procedural Melusina House** (foundation -> shell -> trim), both built on the **one `melodia_gn` chassis**: `register_builder` -> presets -> headless verify -> GN Stack category -> visual gate -> export. Character lane is PRIMARY now because DollKit convergence is active; House lane continues in parallel and must not wait on character builders. Higgsas groups never silent-fallback. Audio rides bake-lane attributes, never runtime GN simulation.

Higgsas elevated for DollKit: Spur Gear / arrays / SDF / curve companions via `higgsas_bridge` (no silent fallback); edit-mesh detail stays MESHmachine+MACHIN3tools+CURVEmachine.

---

## 2. Two lanes (priority)

| Lane | Name | Priority | Blocks the other? |
|---|---|---|---|
| **A** | Character / DollKit bionic GN | **PRIMARY now** (tied to DollKit P9 convergence) | No |
| **B** | Melusina House GN | Continue foundation -> shell | No - do not park House on character |

Lane A turns hand-made P9 balls/cuffs/gears into `MEL_doll_*` builders and binds them to `MEL_DollRig`.
Lane B keeps the proven house proof ladder (foundation/roof/openings already headless-green) moving toward visual approval and `room_shell` composition.

---

## 3. Current truth table (as of 2026-09-24)

### 3.1 MEL_DollRig (map SSOT)

- **Object / data:** `MEL_DollRig` / `MEL_DollRigData`
- **bone_count:** **15** (confirmed `Saved/Audit/mel_dollrig_hierarchy_2026-09-24.json`)
- **NOT SSOT:** ARP `character_rig` / `Melusina_DollRig` (~1124 bones), SirMelodious, etc.

**Bones (parent chain):**

```
spine_01.x                    (root)
  spine_03.x
    neck.x
    arm.l -> forearm.l -> hand.l
    arm.r -> forearm.r -> hand.r
  thigh.l -> leg.l -> foot.l
  thigh.r -> leg.r -> foot.r
```

**Bone name list:**
`spine_01.x`, `spine_03.x`, `neck.x`, `arm.l`, `forearm.l`, `hand.l`, `arm.r`, `forearm.r`, `hand.r`, `thigh.l`, `leg.l`, `foot.l`, `thigh.r`, `leg.r`, `foot.r`

### 3.2 Blender / UE DollKit

| Item | Truth |
|---|---|
| Blender SSOT | `C:\EnvironmentPortfolio\harp_bow_pipeline\Melusina_DollKit_WIP_20260923.blend` |
| P9 GLB | `...\Melusina_DollKit_20260923_P9.glb` |
| P9 seating | DONE in Blender (balls + cuffs + gears hand-placed; seating numbers = canon defaults) |
| UE DollKit | `/Game/Melodia/Characters/Melusina/DollKit/` - packages may still be **pre-P9** until owner reimport |
| Owner reimport gate | Output Log: `py "C:/EnvironmentPortfolio/BS_GodFile/Saved/Audit/_dollkit_p9_reimport_inner.py"` then **owner Ctrl+S only** |
| Staging | `Portfolio/Staging_20260923/DollBall_*` = **NOT SSOT** |
| Parenting debt | Many DollBall / MEL_dk2_cuff / gear meshes still **parent=null** (seating only). Bone-parent to `MEL_DollRig` is Phase A/2 Blender work (may be parenting, not GN). |

### 3.3 Hand-made vs builders

P6-P9 scripts proved stations with **hand mesh instances**. They are **NOT yet** the proposed `MEL_doll_ball_joint` / cuff / gear_cluster family (see section 6 verify).

### 3.4 Melusina House

| Builder family | Registry | Headless smoke | Visual artist approval | Notes |
|---|---|---|---|---|
| `MEL_mh_foundation_*` (pod/cluster/porch/master) | registered | ok | pending | smoke Foundation Master in clay |
| `MEL_mh_roof_ribbon` | registered | ok | pending | |
| `MEL_mh_opening_family` | registered | ok | pending | Packet C DONE 2026-09-16 |
| `MEL_mh6_room_shell` / round interior | exists | re-smoke pending | pending | compose with new foundation |
| `MEL_mh_porch_stair` | next build | - | - | House Packet D |
| Trim / dress / Blue Room | deferred | - | - | after silhouette |

Evidence root: `Saved/Audit/melusina_house/`.

### 3.5 WARN debt (hygiene, do not block new builders)

`Saved/Audit/gn_warn_audit_2026-09-18.md`: **19 distinct (tree, class) pairs** across 18 named trees (Class A None-socket, Class B node-vs-socket, Class C Mesh Line End Location absence on 5.2.1, Class D component link). Park under hygiene / StairStep Oversight; loud fail in `core.link_sockets` is the P0 fix when owner schedules it.

---

## 4. Study poles (NOT ship)

| Ref | Role | Constraint |
|---|---|---|
| **Orianna** (StarGuardian) | Silhouette + joint language + companion-slot lesson -> MEL_DollRig station map | Study only. Never import Orianna IP into Melodia Content. |
| **Ashlotte Maedel** | Literal balljoint + cogwheel vocabulary (XPS bone_count=200; textures Balljoint / Cogwheels / Ceramic / Metal) | Study only. Landed under `Reference/Ashlotte_Maedel/`. Never ship Ashlotte meshes/textures into Melodia content. |

Map: `ORIANNA_TO_MELDOLLRIG_MAP_2026-09-24.md`. Census: `ASHLOTTE_CENSUS_2026-09-24.md`.

---

## 5. Constraints (hard)

1. **No Monolith** `save_packages` / `recompile_material` from agents. Owner **Ctrl+S** only for UE.
2. **Do not casually save** live WIP harp / DollKit blends from agents.
3. **Orianna + Ashlotte = study only** - never ship their IP into Melodia content.
4. **DollKit = future runtime unit**; **`MEL_DollRig` is map SSOT** (not ARP `character_rig` ~1124).
5. **`melodia_gn` chassis:** `register_builder` -> presets -> headless verify. **Higgsas never silent-fallback** (`Tools/higgsas_gate.py` pattern).
6. **Audio = bake-lane attrs** (`audio_amp` / `audio_band` etc.), not runtime GN sound simulation on the doll.

---

## 6. Lane A - builder family (`MEL_doll_*`)

### 6.1 Naming

Prefer **`MEL_doll_`** to match DollKit product language (parallel to House `MEL_mh_`).
GN Stack target category label: **"Melusina Doll"** (add `TREE_CATEGORIES` entry; today `MEL_bionic_joint` / `MEL_doll_socket` register `category="bionic"` but **no `bionic` category key exists** in `core.py` - fix when landing the family).

### 6.2 Verify result (2026-09-24 Select-String on `deploy/surreal_arch/melodia_gn`)

| ID | Exists? | File / notes |
|---|---|---|
| `MEL_doll_socket` | **YES** | `doll_socket.py` - ball + boolean cups into base mesh; category bionic |
| `MEL_bionic_joint` | **YES** | `bionic_joint.py` - research-era marionette joint; keep as predecessor / wrap or deprecate into `MEL_doll_ball_joint` |
| `MEL_gear` | **YES** | `geometry_extras.py` - generic star gear (primitives), not doll cluster |
| `MEL_doll_ball_joint` | **NO** | propose new |
| `MEL_doll_cuff_ring` | **NO** | propose new |
| `MEL_doll_gear_cluster` | **NO** | propose new (Higgsas Spur Gear; no silent fallback) |
| `MEL_doll_segment_shell` | **NO** | optional later |
| `MEL_doll_fastener_row` | **NO** | rivets / circular array |

Also: music-influence denylist already includes `MEL_dollkit_`, `MEL_doll_socket`, `MEL_bionic_joint` (joints must not get the default 20 mm musical pulse).

### 6.3 Proposed builders (concrete)

| Builder ID | Owns | Key dials | Default preset seed |
|---|---|---|---|
| `MEL_doll_ball_joint` | Ball + socket cup + seam ring | radius, cup depth, seam thickness, seat offset | `ROUND_BJD_DEFAULT` from P9 seating |
| `MEL_doll_cuff_ring` | Rim / collar at station | inner/outer radius, height, bevel | P9 cuff A/B pairs |
| `MEL_doll_gear_cluster` | Spur / planet cluster at shoulder/hip | tooth count, module, rim width, planet count | P9 shoulder/hip gears |
| `MEL_doll_segment_shell` | Optional conformal panel (later) | offset, thickness, panel gap | Phase 4 only |
| `MEL_doll_fastener_row` | Rivets along circular array | count, radius, bolt scale | after ball+cuff stable |
| `MEL_doll_socket` (existing) | Boolean cups cut into skin / segment | keep; compose with ball_joint rather than duplicate | - |

### 6.4 Socket / station map (target MEL_DollRig)

| Station | MEL bone | Typical SM / segment |
|---|---|---|
| waist | spine_01.x <-> spine_03.x | ball_waist + seg pelvis/chest |
| neck | neck.x | ball_neck |
| shoulder_l/r | arm.l / arm.r | ball + gear |
| elbow_l/r | forearm.l / forearm.r | ball + cuff |
| wrist_l/r | hand.l / hand.r | ball + cuff |
| hip_l/r | thigh.l / thigh.r | ball + gear |
| knee_l/r | leg.l / leg.r | ball + cuff |
| ankle_l/r | foot.l / foot.r | ball + cuff |

P9 ball stations (14): neck, waist, shoulder_l/r, hip_l/r, elbow_l/r, wrist_l/r, knee_l/r, ankle_l/r.

**Parent chain rule:** segments / balls / gears **bone-parent to `MEL_DollRig`**. Many are currently `parent=null` - call this out as Phase 0/2 Blender work (parenting pass may precede or accompany GN replace).

---

## 7. Phases (ordered)

### Phase 0 - Hygiene / SSOT (1 session)

- This plan + supersession pointers (this document).
- Confirm Staging `DollBall_*` is not authority (`DOLLKIT_SSOT_PARK`).
- List owner P9 UE reimport gate (does **not** block Blender GN work).
- Add GN Stack category **"Melusina Doll"** when first new `MEL_doll_*` lands.
- Do not save WIP blends; do not touch UE packages.

### Phase 1 - Parametrize what P9 already proved (PRIMARY)

- Implement `MEL_doll_ball_joint`, `MEL_doll_cuff_ring`, `MEL_doll_gear_cluster`.
- Replace hand mesh instances in a **scratch / construct** scene (not casual WIP save).
- Headless construct receipts under `Saved/Audit/melusina_doll_gn/`.
- Encode P9 seating numbers as default presets (`ROUND_BJD_DEFAULT`, station variants).
- Reuse / compose `MEL_doll_socket` + migrate useful bits from `MEL_bionic_joint`; do not leave two competing ball APIs without a deprecation note.
- Higgsas Spur Gear via bridge + gate; native fallback only if gate explicitly allows and logs loud.

### Phase 2 - Rig binding

- Instance / output stations aligned to `MEL_DollRig` bones listed above.
- Bone-parent remaining free floaters to the correct bones.
- Export discipline to DollKit GLB: **do not break P9 seating gates**.
- Keep UE reimport as owner-gated (Ctrl+S).

### Phase 3 - Joint readability / Ashlotte lessons

- Cog visibility, balljoint ceramic/metal **split cues**.
- Material assignment stays **UE Nikki porcelain/brass** (lookdev keepers).
- GN only supplies **mesh islands / named attrs** (e.g. `mj_porcelain`, gear metal masks) - no IP textures from Ashlotte/Orianna.

### Phase 4 - Conformal plating (optional, later)

- Raycast / shrinkwrap panels; Higgsas Surface Bind.
- Only after runtime pawn path is stable (see DollKit runtime gap map).

### House Phase (parallel)

- Next: visual smoke Foundation Master (+ roof + openings artist pass).
- Compose `MEL_mh6_room_shell` with new foundation (re-smoke).
- Build `MEL_mh_porch_stair` (Packet D) when silhouette work needs arrival.
- Trim / dress / Blue Room / Nanite deferred until silhouette gate passes.

---

## 8. Explicit non-goals

- Monolith package saves / material recompiles from agents.
- Saving live harp / DollKit WIP blends from agent automation.
- Importing Orianna or Ashlotte into `Content/`.
- Treating Staging `DollBall_*` or takeover FBX as DollKit SSOT.
- Exploding bone count (fingers/toes) without mocap need.
- Runtime Sample Sound on the doll pawn (bake-lane only).
- Silent Higgsas fallback.
- Rewriting House AAA trim / furniture / foliage before silhouette.
- Claiming `MEL_doll_ball_joint` / cuff / gear_cluster already exist (they do not as of 2026-09-24).
- Overwriting IK / RTG / preview BP / Nikki MIs on UE reimport.

---

## 9. Proof ladder (House pattern, Doll category twin)

```
source exists
  -> register_builder(... category=melusina_doll)
  -> GROUP_BUILDERS / GROUP_METADATA / __init__ import
  -> GN Stack category "Melusina Doll"
  -> constructs in Blender 5.2
  -> presets respond (P9 defaults)
  -> visual gate (three lights: key/fill/rim)
  -> export discipline (GLB seating gates intact)
  -> approved asset / receipt under Saved/Audit/melusina_doll_gn/
```

State the exact level you have. Source-on-disk alone is not done.

---

## 10. File / path index

| Path | Role |
|---|---|
| `Saved/Audit/MELUSINA_GN_PLAN_2026-09-24.md` | Agent/work SSOT (this plan) |
| `Docs/Plans/MELUSINA_GN_PLAN_2026-09-24.md` | Human browse (identical full copy) |
| `Docs/Research/GN_ULTIMATE_FRAMEWORK_RESEARCH_2026-09-23.md` | Superseded research |
| `Docs/MelodiaStudio/MELUSINA_HOUSE_GN_FOUNDATION_TO_SHELL_ROADMAP_2026-09-04.md` | House next-work detail |
| `Docs/MelodiaStudio/MELUSINA_HOUSE_GN_BUILDER_INTEGRATION_2026-09-04.md` | House registration chain |
| `MELUSINA_HOUSE_GN_START_HERE.md` | House agent entry (repo root) |
| `deploy/surreal_arch/melodia_gn/` | Chassis + builders |
| `deploy/surreal_arch/melodia_gn/bionic_joint.py` | Existing `MEL_bionic_joint` |
| `deploy/surreal_arch/melodia_gn/doll_socket.py` | Existing `MEL_doll_socket` |
| `harp_bow_pipeline/Melusina_DollKit_WIP_20260923.blend` | Blender DollKit SSOT (do not casual-save) |
| `harp_bow_pipeline/Melusina_DollKit_20260923_P9.glb` | P9 export |
| `/Game/Melodia/Characters/Melusina/DollKit/` | UE DollKit |
| `Saved/Audit/mel_dollrig_hierarchy_2026-09-24.json` | Rig dump |
| `Saved/Audit/melusina_house/` | House smoke evidence |
| `Saved/Audit/melusina_doll_gn/` | (create) Doll GN receipts |
| `Saved/Audit/gn_warn_audit_2026-09-18.md` | WARN debt (19 pairs) |
| `Saved/Audit/_dollkit_p9_reimport_inner.py` | Owner UE reimport script |

---

## 11. Immediate next 3 actions (agent tomorrow morning)

1. **Phase 0 closeout check:** confirm both plan copies exist; Staging DollBall still parked; create `Saved/Audit/melusina_doll_gn/` folder; skim `MEL_bionic_joint` + `MEL_doll_socket` interfaces and write a one-page dial/preset matrix for `MEL_doll_ball_joint` / cuff / gear_cluster using P9 numbers (no blend save).
2. **Phase 1 start:** scaffold `MEL_doll_ball_joint` (and category `melusina_doll` / label Melusina Doll) in `melodia_gn`, register + preset stub + headless construct smoke receipt; do not replace WIP instances until smoke is green.
3. **House parallel (non-blocking):** run `Tools/verify_melusina_house_gn_catalog.py` and/or schedule artist visual smoke of Foundation Master + roof + openings; note `MEL_mh_porch_stair` as next House builder when Packet D is pulled - do not block on Doll builders.

**Owner-only (listed, not agent-blocking for Blender GN):** paste Output Log P9 reimport one-liner; Ctrl+S; stamp `DOLLKIT_P9_UE_REIMPORT_RECEIPT.md`.

---

## 12. Blockers

| Blocker | Blocks | Workaround |
|---|---|---|
| UE remote Python UDP 6766 not advertising | Agent-driven UE reimport | Owner Output Log `py` one-liner |
| Live WIP blend save discipline | Casual instance replace in SSOT blend | Scratch construct + receipts; owner saves SSOT |
| Missing Melusina Doll GN Stack category | Discoverability of `category="bionic"` builders | Add category with first `MEL_doll_*` land |
| WARN 19 pairs | Quality hygiene | Parked; do not block new builders |
| P9 geo not yet in UE packages | Runtime visual gate in UE | Does not block Blender GN Phase 1 |

---

*End of CURRENT PLAN 2026-09-24.*