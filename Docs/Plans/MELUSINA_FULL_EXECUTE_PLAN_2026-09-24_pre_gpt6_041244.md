# Melusina DollKit — FULL EXECUTE PLAN (2026-09-24)

**Status:** CURRENT MASTER PLAN (overview)  
**Execute checklist SSOT:** `Saved/Audit/MELUSINA_EXECUTE_TO_COMPLETION_GOAL_2026-09-24.md`  
**GN builders companion:** `Saved/Audit/MELUSINA_GN_PLAN_2026-09-24.md`  
**Runtime companion:** `Saved/Audit/DOLLKIT_CONVERGENCE_GOAL_2026-09-24.md`  
**Machine:** fromage · **Blender:** 5.2 LTS · **UE:** Melodia Melusina V2

Doctrine: **EXECUTE TO COMPLETION.** Not research-only.

---

## 1. North star

Ship Melusina as a **segmented BJD runtime doll**:
- 15-bone `MEL_DollRig` map SSOT
- Porcelain ball joints + metal cuff rims + clockwork gears that read at silhouette
- Parametric builders (`MEL_doll_*`) where repeatable; MeshMachine hand-polish where hero
- UE P9 authority geo + preview BP → gameplay pawn path

Study poles (IP study only, never ship): **Orianna** (silhouette/joint language) · **Ashlotte** (literal balljoint + cogwheels).

---

## 2. Tool doctrine (locked)

| Lane | Tools | Use for |
|---|---|---|
| **Hand surface** | MESHmachine **0.16.0**, MACHIN3tools **1.10.1 DeusEx** | Fuse/fillet/stash, cuff rims, porcelain seams, topo hygiene |
| **Parametric GN** | **Higgsas v13** via `higgsas_bridge` (**no silent fallback**) | Spur Gear, SDF cups, circular arrays, even curve-to-mesh, offset/solidify, curvature/AO masks |
| **Curve accents** | CURVEmachine **1.4.1** (+ Higgsas Even Curve to Mesh) | Seam wires, hose, cuff profile sweeps (silhouette-safe) |
| **Support** | Beavel, MeshCleanerPro, SurfaceFill, speedsculpt, ZenUV, quad_remesher, send2ue/ue2rigify | Cleanup / bake / export — careful on 15-bone map |
| **Optional later (ask first)** | ARP zip, UVPackmaster, Deep Paint, Stylized Hair on `D:\Blender` | Retarget / UV ship / hero paint / hair |
| **Not on disk (do not block)** | HardOps, BoxCutter, DECALmachine, Cablerator | Buy later if needed |

**Rule:** Edit-mesh hero detail → MeshMachine. Repeatable / measured → Higgsas. Never silent Higgsas fallback.

---

## 3. Authority paths

| Role | Path |
|---|---|
| Hero WIP (no casual agent save) | `harp_bow_pipeline/Melusina_DollKit_WIP_20260923.blend` (~2.46 GB) |
| Surface workfile | `harp_bow_pipeline/Melusina_DollKit_SurfaceDetail_20260924.blend` |
| P9 GLB | `harp_bow_pipeline/Melusina_DollKit_20260923_P9.glb` |
| Higgsas lib | `RawArt/BlenderLibraries/Higgsas/Blender 5.0 Higgsas Geo Node Groups v13.blend` |
| UE DollKit | `/Game/Melodia/Characters/Melusina/DollKit/` (may be pre-P9 until owner reimport) |
| Staging DollBall_* | **NOT SSOT** |
| Evidence | `Saved/Audit/melusina_doll_surface_20260924/` |

---

## 4. MEL_DollRig (15 bones)

```
spine_01.x
  spine_03.x
    neck.x
    arm.l → forearm.l → hand.l
    arm.r → forearm.r → hand.r
  thigh.l → leg.l → foot.l
  thigh.r → leg.r → foot.r
```

NOT SSOT: ARP `character_rig` (~1124).

---

## 5. P9 station table (mm ball_r / opening_r)

| Station | ball_r | opening_r |
|---|---:|---:|
| neck | 35.0 | 20.0 |
| waist | 45.0 | 30.0 |
| shoulder L/R | 42.0 | 24.0 |
| hip L/R | 45.0 | 26.0 |
| elbow L/R | 33.25 | 19.0 |
| wrist L/R | 26.25 | 15.0 |
| knee L/R | 35.0 | 20.0 |
| ankle L/R | 28.0 | 16.0 |

Cuff span min 4 mm · ball_r max 45 mm · P9 seating PASS in Blender.

---

## 6. GN builder state

**Exist:** `MEL_doll_socket`, `MEL_bionic_joint`, generic `MEL_gear`  
**Build next:** `MEL_doll_ball_joint`, `MEL_doll_cuff_ring`, `MEL_doll_gear_cluster`, (+ later segment shell / fastener row)  
**Stack category:** add **Melusina Doll** when first new builder lands  
**Presets:** seed from P9 + E1 measured bevels

---

## 7. Execute phases (E0→E8)

### E0 Gate — plugs + workfile
- [x] MeshMachine / MACHIN3tools / CURVEmachine on 5.2
- [x] Higgsas v13 library + bridge (no silent fallback)
- [x] SurfaceDetail workfile copied from WIP
- [x] E0 plug audit written
- [ ] Optional: open Blender once to confirm plugs enabled

### E1 Joints (MeshMachine primary)
- [x] Prep/inventory on SurfaceDetail (2026-09-24 ET): `E1_station_inventory.json`, collections, bevel hints, `OWNER_E1_MESHMACHINE_CLICKLIST.md`
- [ ] Interactive MeshMachine Y-menu: neck + shoulder_L ceramic/metal stills (Brennan)
- [ ] Remaining P9 balls/cuffs + mirror; stills bank
Neck + one shoulder first then all P9 balls/cuffs. Ceramic ball vs metal rim read. Stills to `melusina_doll_surface_20260924/`.

### E2 Gears (Higgsas Spur Gear primary)
Shoulder/hip clusters; tooth silhouette; micro wrist/ankle only if clean.

### E3 Segment shells
Light hard-surface language on SKM edges — not full armor. Conformal plating later.

### E4 Bind
Bone-parent keepers to MEL_DollRig; clear parent=null debt.

### E5 GN parametrize
`MEL_doll_*` builders + presets from P9+E1; headless receipts; Higgsas groups claimed must be real (F2-style gate).

### E6 Export + UE (owner gate)
Detail GLB → Output Log: `py .../_dollkit_p9_reimport_inner.py` → **owner Ctrl+S** → CuteIdle visual gate.

### E7 Runtime unit
Sockets, capsules, camera, pawn scaffold from preview BP (gap map).

### E8 Docs / COMPLETE
CURRENT_STATE bump · docs PR · stamp this plan + execute goal COMPLETE with date.

**House lane:** parallel, non-blocking for DollKit DONE (foundation/roof/openings headless-green; porch_stair / room_shell next).

---

## 8. Constraints

- No Monolith/`save_packages` from agents — owner Ctrl+S only
- No casual save of hero WIP / live harp blends
- Orianna / Ashlotte = study only
- Do not explode 15-bone map via ue2rigify misuse
- Audio = bake-lane attrs, not runtime GN sim
- HardOps/DECAL stack does not block

---

## 9. Immediate next actions

1. **E1 now** on SurfaceDetail workfile — MeshMachine neck + shoulder_l (ceramic/metal read)
2. Bank stills under `Saved/Audit/melusina_doll_surface_20260924/`
3. Parallel: scaffold `MEL_doll_ball_joint` preset matrix from P9 numbers
4. Owner when ready: P9 Output Log reimport + Ctrl+S (E6)

---

## 10. Evidence index

| Artifact | Role |
|---|---|
| `MELUSINA_EXECUTE_TO_COMPLETION_GOAL_2026-09-24.md` | Checklist SSOT |
| `MELUSINA_GN_PLAN_2026-09-24.md` | Builder / House lanes |
| `DOLLKIT_CONVERGENCE_GOAL_2026-09-24.md` | Runtime companion |
| `DOLLKIT_RUNTIME_GAP_MAP_2026-09-24.md` | Preview → pawn |
| `ORIANNA_TO_MELDOLLRIG_MAP_2026-09-24.md` | Study map |
| `ASHLOTTE_CENSUS_2026-09-24.md` | Balljoint/cog study |
| `melusina_doll_surface_20260924/E0_plug_audit.md` | E0 receipt |
| `mel_dollrig_hierarchy_2026-09-24.json` | 15-bone dump |
| `p9_seating_done.json` | Station radii |

When E0–E8 checked: stamp `STATUS: COMPLETE` + date on execute goal and this plan.