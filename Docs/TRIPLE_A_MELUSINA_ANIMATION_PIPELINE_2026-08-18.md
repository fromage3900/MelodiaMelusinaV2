# Triple-A Melusina Animation Pipeline — 2026-08-18

**Goal**: A repeatable pipeline that takes Cascadeur/Quaternius/Source animations
and lands them correctly on Melusina's 465-bone skeleton, plus a facial animation
subsystem. The idle gets fixed (mocap idle, properly trimmed), ground locomotion
is wired, and glide gets a real state.

---

## 1. The Four-Axis Problem (closed)

Every non-mocap source animation misses Melusina's live contract on four axes:

| Axis | Source (ARP / Blender / Cascadeur / Quaternius) | Live Melusina | Result |
|------|-------------------------------------------------|---------------|--------|
| Bone names | dots `DEF_eye.L`, `c_kilt_master.x` | underscores `DEF_eye_L`, `c_kilt_master_x` | 0 bones align by name |
| Units | meters | centimetres | 100× collapse (Y −0.128 vs −12.84) |
| Bone count | 432 / 463 | 465 | rigs structurally differ |
| Frame rate | 24 FPS | 30 FPS | clip desync |

Mocap avoids all four by going through the IK retargeter chain:
`SK_MocapSource → IK_MocapSource → RTG_Mocap_to_Melusina → IK_Melusina_Body → clip`

---

## 2. Pipeline Stages

```
[ Authoring ]          [ Offline Gate ]          [ UE Import ]           [ Promotion ]
Cascadeur /    →   Blender scan + remap    →   Monolith MCP   →   ABP state machine
Quaternius /       (fix names + units)          (import + retarget)     (bind clips to
Source FBX                                                           blendspace/states)
```

### Stage 1 — Authoring
- Cascadeur exports animation-only FBX, 30 FPS, baked
- OR Quaternius pack (already downloaded, 42 clips, ~883 KB each)
- OR Source retargeted (already have: FemaleBard, SourceRetargeted)

### Stage 2 — Offline Gate (`scan_cascadeur_fbx.py`)
- Blender factory-startup import of FBX
- Check: armature present, 30 FPS, required bones exist
- Report: `lane_a_ready` OR `needs_remap`
- If needs remap → `remap_arp_fbx_to_ue.py` (dots→underscores, ×100 unit, bake)
- Output: remapped FBX + `.remap.json` sidecar

### Stage 3 — Import (`import_chain.py` or `headless_retarget_mocap.py`)
Two paths:
- **Lane A (canonical source rig)**: import directly onto `SK_MocapSource`, retarget via `RTG_Mocap_to_Melusina`
- **Lane B (foreign rig)**: import onto source skeleton, then IK retarget

All imports go through Monolith MCP (`animation_query` namespace).

### Stage 4 — Promotion
- Validate post-import contract (bone count, scale, fps)
- Bind clip into ABP state machine / blendspace
- `Saved/Audit/promotion_report.json`

---

## 3. ABP State Machine — Target

Current (broken):
```
Idle → JumpStart → Airborne → Land → Idle
```
No locomotion, no glide, idle bound to wrong clip.

Target:
```
                    ┌──────────────┐
                    │   Locomotion  │ ← blendspace (Idle/Walk/Run/Sprint)
                    │  (Speed>10)  │
                    └──────┬───────┘
                           │ bJumpWindup
                    ┌──────▼───────┐
  SpaceBar hold →   │  JumpWindup   │ ← always_reset_on_entry
                    └──────┬───────┘
                           │ WasInAir (after JumpLaunch notify)
                    ┌──────▼───────┐
                    │   Airborne    │ ← A_Melusina_JumpLoop_Mocap_RootX
                    └──────┬───────┘
                           │ auto (end of loop)
                    ┌──────▼───────┐
                    │     Land      │ ← always_reset_on_entry
                    └──────┬───────┘
                           │ Speed>10 → Locomotion; Speed<10 → Idle
                    ┌──────▼───────┐
     Glide entry →  │     Glide     │ ← bIsGliding (BP_MelusinaJRPGCharacter)
   (BP sets flag)   │  (float up,   │
                    │   shawl lift) │
                    └───────────────┘
```

Transitions:
- Idle ↔ Locomotion: Speed > 10 / < 10
- Any → JumpWindup: bJumpWindup
- JumpWindup → Airborne: WasInAir (after JumpLaunch notify fires)
- Airborne → Land: auto (end of clip)
- Land → Locomotion: Speed > 10 (running landing)
- Land → Idle: Speed < 10 (standing landing)
- Any → Glide: bIsGliding

---

## 4. Idle Fix

Current: `A_Melusina_Idle` (unsuffixed, Aug 8, 695 KB) — trimmed wrong, snaps to T-pose.

Fix: bind Idle state to `A_Melusina_Idle_Mocap_RootX` (Aug 14, 821 KB).

The mocap idle is 0.5s — too short for baked blink curves. Instead drive
eyesCloseL / eyesCloseR from a randomised AnimBP timer (~2 blinks per 7s).

Breathing (innerBrowRaiserL/R) can still be baked — one cycle per 0.5s
loop reads as fine since it's just micro-motion.

---

## 5. Glide Implementation

Source candidates (existing on disk):

| Clip | Path | Reuse for |
|------|------|-----------|
| `A_Q_Melusina_Sprint_Loop` | QuaterniusRetargeted/ | Main glide loop — forward lean reads as floating |
| `A_Mocap_LiftOff` | Mocap/ | Glide start (rising) |
| `A_Mocap_GracefulLanding` | Mocap/ | Glide end (soft descent) |
| `A_Mocap_LittleDance_*` | Mocap/ (x3) | Glide idle variations |

If Quaternius packages stay unloadable: use Mocap clips as placeholders,
author proper glide in Cascadeur later.

Glide state entry: `bIsGliding` (already exists in ABP, set by BP_MelusinaJRPGCharacter).

Glide state exit: `!bIsGliding` → Land (if airborne) or Idle (if grounded).

---

## 6. Facial Animation Pipeline

### 6.1 — Morph Target Contract

Of 103 morph targets on `SK_Melusina_V2_Body`:
- 68 carry real deltas
- 52-key ARKit block is bit-identical to Basis (inert — Unreal discards)
- 35 FACS keys populated from ARKit source

Name traps (compile clean, do nothing):
- `eyeBlinkLeft` / `eyeBlinkRight` → use `eyesCloseL` / `eyesCloseR`
- `browInnerUp` → use `innerBrowRaiserL` / `innerBrowRaiserR`

### 6.2 — FACS-Driven Facial Animation

Use Control Rig to drive FACS curves from:
- AnimNotifies (timed to dialogue/lip-sync)
- Blueprint events (emotion state changes)
- Curves baked into animation assets

### 6.3 — Lip Sync

Options:
1. **Audio-driven**: Audio2Face (NVIDIA) → curve export → UE
2. **Phoneme-driven**: detect phoneme from dialogue text → map to FACS viseme curves
3. **Hand-authored**: bake curves per dialogue line in Cascadeur/Blender

For indie: phoneme-driven is cheapest. Map 15 visemes to FACS curves,
drive from dialogue system (QuillScript already has the text).

### 6.4 — Emotion Layer

Additive FACS layer on top of base facial animation:
- Joy: `cheekRaiserL/R` + `lipCornerPullerL/R`
- Anger: `browLowerer` + `lipTightener`
- Surprise: `browRaiserL/R` + `jawDrop`
- Sadness: `browInnerUp` + `lipCornerDepressorL/R`

Blend via AnimBP emotion weights (0-1), additive on top of base.

---

## 7. Tooling

### Existing (use as-is)
- `Tools/scan_cascadeur_fbx.py` — offline FBX validation
- `Tools/remap_arp_fbx_to_ue.py` — name + unit fix
- `Tools/animation_import_pipeline/import_chain.py` — import + retarget
- `Tools/build_melusina_locomotion_stack.py` — ABP state machine repair
- `Tools/build_melusina_idle_life.py` — blink/breath curves
- `Tools/melusina_anim_unit_guard.py` — pre-flight checks

### To Build
- `Tools/wire_melusina_glide.py` — add Glide state to ABP
- `Tools/build_melusina_face_rig.py` — Control Rig FACS wiring
- `Tools/import_quaternius_batch.py` — batch import the 42 Quaternius clips
- `Tools/validate_melusina_animation_contract.py` — post-import verification

---

## 8. Execution Order

1. **Fix idle** — repoint Idle state to mocap idle (no new authoring)
2. **Wire ground locomotion** — add Locomotion state + blendspace (build_melusina_locomotion_stack.py)
3. **Add glide state** — wire bIsGliding → Glide state (wire_melusina_glide.py)
4. **Fix retarget pipeline** — get Cascadeur/Quaternius importing correctly
5. **Author new clips** — Cascadeur: proper glide, idle variants, victory twirl
6. **Facial pipeline** — Control Rig + FACS curves + lip sync

---

## 9. Evidence Ledger

| Claim | Evidence |
|-------|----------|
| 4-axis mismatch | `Saved/Audit/melusina_idle_retarget_rca_2026-08-13.md` |
| Mocap idle approved | `Saved/Audit/melusina_idle_restore_mocap_2026-08-13.md` |
| ARP→contract bone map verified | `specs/anim_presets/melusina_arp_to_contract_bones.json` |
| ABP has bIsGliding + Glide state | `specs/anim_presets/melusina_locomotion_state_machine.json` § _LIVE_PREFLIGHT |
| 42 Quaternius clips exist on disk | `Content/Melodia/Characters/Melusina/Animations/QuaterniusRetargeted/` |
| FACS keys populated | `Tools/populate_melusina_arkit_shapekeys.py` |
