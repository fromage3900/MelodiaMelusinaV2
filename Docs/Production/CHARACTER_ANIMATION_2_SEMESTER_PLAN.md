# Character Animation — 2-Semester Prep Plan
> **Goal:** Go from "a few short clips, nothing polished" to a portfolio of 3-4 polished character performances.
> **Focus:** Acting, lip-sync, body mechanics.
> **Timeline:** Semester 1 (foundation + 1 polished piece) → Semester 2 (range + portfolio).

---

## Table of Contents

1. [Pipeline Audit — What You Have](#1-pipeline-audit--what-you-have)
2. [Immediate Actions (This Week)](#2-immediate-actions-this-week)
3. [Semester 1 Plan — Foundation + Piece #1](#3-semester-1-plan--foundation--piece-1)
4. [Semester 2 Plan — Range + Portfolio](#4-semester-2-plan--range--portfolio)
5. [Reference & Resource List](#5-reference--resource-list)
6. [Risk Register](#6-risk-register)

---

## 1. Pipeline Audit — What You Have

### ✅ WORKING (Verified)

| System | Location | Notes |
|--------|----------|-------|
| **Mocap import** | `Content/Python/import_rokoko_mocap.py` | Rokoko FBX → `A_Src_Rokoko_*` on `SK_MocapSource` |
| **Mocap retarget** | `Content/Python/headless_retarget_mocap.py` | `A_Src_*` → `A_Mocap_*` on `SK_Melusina` via `RTG_Mocap_to_Melusina_Current` |
| **Headless runner** | `Tools/run_headless_mocap_retarget.ps1` | Editor-closed batch retarget, writes `Saved/Melodia/retarget_report.json` |
| **Animation probe** | `Tools/probe_ue_animation_tracks.py` | Read-only bone pose sampling for root-motion verification |
| **Contract tests** | `Tools/test_melusina_animation_library.py` | 343-line offline test suite for manifest validation |
| **FACS face rig** | `Tools/build_melusina_face_rig.py` | 68 morph targets → 15 visemes, blink timer, emotion layer |
| **Rig remap** | `Tools/remap_melusina_rig_to_contract.py` | ARP dotted names → UE contract (464-bone) |
| **Source export** | `Tools/export_melusina_animation_source.py` | Blender 5.2 headless FBX export at 30 FPS with v2 manifest |
| **Mocap library** | `Content/Melodia/Characters/Melusina/Animations/Mocap/` | 30+ existing mocap clips (dance, combat, locomotion) |
| **Locomotion set** | `Content/Melodia/Characters/Melusina/Animations/Locomotion/` | Idle, walk, run, sprint, jump (start/loop/land) — all mocap |
| **Retargeter** | `Content/Melodia/Mocap/Retarget/RTG_Mocap_to_Melusina_Current.uasset` | Canonical IK retargeter, 19 chains |
| **OpenUtau voice** | `studio/tracks/frost-rave/` | Melusina JA VCV renders for lip-sync source |

### ⚠️ NEEDS VERIFICATION

| System | Risk | Action |
|--------|------|--------|
| **FACS lip-sync** | Script exists but untested end-to-end | Render a test clip with audio → verify mouth tracks |
| **ARP rig → contract** | 464-bone contract is large; remap may have gaps | Run `--check-only` on stage, verify all deform bones resolve |
| **Blender scene template** | Doesn't exist | Build one (see Immediate Actions) |
| **Mocap cleanup** | Existing clips may have foot slide, hand penetration | Audit 3-5 clips, identify worst offenders |

### ❌ MISSING (Build These)

| System | Priority | Notes |
|--------|----------|-------|
| **Lip-sync automation** | HIGH | Audio → phoneme → FACS curve pipeline (no manual keyframing) |
| **Face capture integration** | MEDIUM | iPhone ARKit → Melusina FACS (if you have iPhone) |
| **Second character rig** | MEDIUM | ZunZun family or Sir Melodious for Semester 2 |
| **Reference library** | HIGH | Real-world video reference for animation study |
| **Scene template .blend** | HIGH | Pre-lit, pre-rigged starting file |

---

## 2. Immediate Actions (This Week)

Do these BEFORE the semester starts. Each is 1-2 hours.

### Day 1: Verify Mocap Pipeline (2h)

```bash
# 1. Drop a test FBX in Imports/Mocap/Rokoko/Inbox/
# 2. Run headless retarget (editor CLOSED):
Tools/run_headless_mocap_retarget.ps1

# 3. Check report:
cat Saved/Melodia/retarget_report.json
```

**Success criteria:** `A_Mocap_*` clip exists, skeleton = `SK_Melusina_Skeleton`, no errors.

**If it fails:** Check `Saved/Melodia/retarget_report.json` for the specific error. Common issues:
- FBX bone names don't match `SK_MocapSource_Skeleton` → re-export from Rokoko with correct profile
- Target skeleton rebind failed → run `unreal.MelodiaAssetRepairLibrary.set_skeletal_mesh_skeleton()` manually in editor

### Day 2: Test FACS Lip-Sync (2h)

```bash
# 1. Open editor, load Melusina
# 2. Run face rig builder:
python Tools/build_melusina_face_rig.py --plan

# 3. If plan looks good:
python Tools/build_melusina_face_rig.py --apply

# 4. Feed it a test audio (WAV), verify mouth moves
```

**Success criteria:** Mouth opens/closes on audio, blinks happen, no crashes.

### Day 3: Build Scene Template (1h)

Create `Templates/Melusina_Animation_Stage.blend`:

- [ ] Import FinalUERig43 (or load from stage)
- [ ] Add 3-point lighting (use `melodia_stage` addon pattern: key 800W, fill 300W, rim 500W spot)
- [ ] Add beauty camera (85mm, f/2.8, aimed at chest)
- [ ] Add macro camera (90mm, f/2.8, aimed at head)
- [ ] Set render: 1600×2000, EEVEE Next, 30 FPS
- [ ] Save as template

### Day 4: Audit Existing Mocap (1h)

Open 5 existing `A_Mocap_*` clips in editor. Check for:
- Foot sliding (does the foot stay planted when it should?)
- Hand penetration (does the hand go through the body?)
- Root motion (does the character drift?)
- Shoulder twist (does the arm rotate unnaturally?)

**Document findings** in `Saved/Audit/mocap_audit_2026-09-03.json`.

### Day 5: Gather Reference (1h)

Start a reference folder: `Saved/AnimationReference/`

Subfolders:
- `body_mechanics/` — jumps, turns, lifts, falls
- `acting/` — facial expressions, emotional performances
- `lipsync/` — close-up mouth/tongue/jaw reference
- `walk_cycles/` — different moods (sad walk, happy walk, sneaky walk)

**Sources:**
- Pinterest board (create one, pin 50+ images)
- YouTube: "animation reference," "mocap cleanup," "facial acting study"
- Your own phone video (record yourself acting out the shot)

---

## 3. Semester 1 Plan — Foundation + Piece #1

### Week 1-2: Animation Principles (Body)

**Study:** The 12 principles (squash/stretch, anticipation, staging, etc.)

**Exercise:** 10-15 second clip — Melusina does a jump, turn, and land.

- Block the key poses first (stepped mode)
- Add breakdown poses (overshoot, settle)
- Polish arcs (no linear motion)

**Deliverable:** `A_Melusina_JumpTurnLand_v01` — blocked + splined, no face yet.

### Week 3-4: Mocap Cleanup

**Exercise:** Take an existing mocap clip (e.g., `A_Mocap_LittleDance`). Clean it up:

- Fix foot sliding (plant IK, remove drift)
- Fix hand penetration (rotate shoulder/elbow)
- Smooth jitter (filter high-frequency noise)

**Deliverable:** `A_Melusina_Dance_Cleaned_v01` — same performance, no artifacts.

### Week 5-6: Face + Lip-Sync

**Exercise:** 15-second talking clip.

- Render Melusina singing a line from OpenUtau (or speak into a mic)
- Drive FACS from audio (automated or hand-keyed)
- Add blinks (randomized, ~2 per 7s)
- Add one emotion (joy, sadness, anger — pick one)

**Deliverable:** `A_Melusina_Speaking_v01` — synced mouth + blinks + emotion.

### Week 7-8: Acting (Body + Face Combined)

**Exercise:** 30-second performance. One character, one emotion, one clear intention.

Example: "Melusina is trying to convince someone to come with her. She's hopeful but scared."

- Block body language first (weight shifts, gestures, eye contact)
- Add face (subtle — don't over-animate)
- Polish timing (holds, accents, breathing)

**Deliverable:** `A_Melusina_Acting_v01` — full performance, rough render.

### Week 9-10: Polish + Render

**Exercise:** Camera, lighting, rendering, editing.

- Set up 2-3 camera angles (beauty + macro + dramatic)
- Light for mood (warm/cool, key/fill ratio)
- Render at 1600×2000, 30 FPS
- Edit to music (use your UNDERTOW track or something similar)
- Color grade in post

**Deliverable:** **PIECE #1 — "Melusina's Plea" (30-60s polished)**

---

## 4. Semester 2 Plan — Range + Portfolio

### Week 1-2: Second Character

**Goal:** Rig and retarget a second character (ZunZun family or Sir Melodious).

- Import VRM (Zundamon) or FBX (Melusina for bird)
- Remap to UE skeleton (or create new IK rig)
- Test mocap retarget on new body

**Deliverable:** Second character moves with mocap.

### Week 3-4: Contrast Piece

**Goal:** Show range. If Piece #1 was sad/quiet, go loud/physical.

Example: "Melusina is furious — she's been betrayed."

- Big, fast movements
- Sharp accents, no smooth easing
- Angry face (brow down, lips tight, jaw clenched)

**Deliverable:** **PIECE #2 — "Melusina's Rage" (30s, opposite energy)**

### Week 5-6: Dialogue Scene

**Goal:** Two characters, real conversation timing.

- Two characters on screen (or one character + voiceover)
- Overlapping dialogue (interrupt, pause, react)
- Subtext (what they're NOT saying matters more)

**Deliverable:** **PIECE #3 — "The Conversation" (45-60s)**

### Week 7-8: Style Experiment

**Goal:** Break the rules. Use your unique tools.

Options:
- Audio-reactive: Melusina's face/body driven by music amplitude
- Cymatic: Chladni patterns on her dress synced to her voice
- Abstract: Non-photoreal, stylized, motion-graphics feel

**Deliverable:** **PIECE #4 — "UNDERTOW" (20s experimental)**

### Week 9-10: Portfolio Assembly

**Goal:** Reel + breakdowns.

- Edit 4 pieces into a 90-second reel
- Write breakdowns for each (what you did, what was hard, what you learned)
- Export stills (3-5 per piece)
- Upload to ArtStation/YouTube/Vimeo

**Deliverable:** **PORTFOLIO — Reel + 4 breakdowns + stills**

---

## 5. Reference & Resource List

### Books (Read These)

| Book | Author | Why |
|------|--------|-----|
| **The Animator's Survival Kit** | Richard Williams | THE bible. Every principle, every exercise. |
| **Timing for Animation** | Harold Whitaker | How many frames for each action. |
| **Facial Animation: A Practical Guide** | 3DTotal | FACS, blendshapes, lip-sync. |
| **Acting for Animators** | Ed Hooks | Performance = acting, not moving. |
| **Drawn to Life** | Walt Stanchfield | Disney's gesture and force. |

### Online Courses

| Course | Platform | Focus |
|--------|----------|-------|
| **Animation Bootcamp** | Animation Mentor | Body mechanics, acting |
| **iAnimate** | iAnimate | Game animation, mocap cleanup |
| **AnimSchool** | AnimSchool | Full program, rigging + animation |
| **CGMA — Character Animation** | CGMA | Portfolio-focused |
| **Blender Animation (GDQuest)** | YouTube/GDQuest | Blender-specific workflows |

### YouTube Channels

| Channel | Content |
|---------|---------|
| **Sir Wade Neistadter** | Animation principles, Blender |
| **Howard Wimshurst** | 2D/3D animation theory |
| **The Animator's Survival Kit (app)** | Richard Williams' demos |
| **AnimState** | Game animation breakdowns |
| **Taylor Hokanson** | Facial animation, FACS |

### Reference Footage

| Source | What |
|--------|------|
| **Pinterest** | Pose reference, facial expressions |
| **YouTube "acting reference"** | Film scenes, emotional performances |
| **Your own phone** | Record yourself acting out the shot |
| **Mixamo** | Pre-made animations for timing study |
| **Rokoko Motion Library** | Free mocap clips for cleanup practice |

### Tools You Already Have

| Tool | Use |
|------|-----|
| `build_melusina_face_rig.py` | FACS face setup |
| `run_headless_mocap_retarget.ps1` | Batch mocap processing |
| `probe_ue_animation_tracks.py` | Root-motion verification |
| `melodia_stage` addon | 3-point lighting setup |
| `melodia_showroom` | Multi-render AAA |
| OpenUtau + Melusina JA VCV | Voice renders for lip-sync |
| FL Studio + TouchDesigner | Audio-reactive visuals |

---

## 6. Risk Register

| Risk | Likelihood | Impact | Mitigation |
|------|------------|--------|------------|
| **Mocap pipeline breaks mid-semester** | Medium | HIGH | Verify NOW. Document the exact steps. Save a working retarget report as baseline. |
| **FACS lip-sync doesn't track audio** | Medium | HIGH | Test in Week 1. If it fails, fall back to hand-keyed visemes (slower but works). |
| **Scope creep — too many ideas** | HIGH | MEDIUM | Stick to the plan. One piece per semester is the minimum. Two is the goal. |
| **Perfectionism — never "done"** | HIGH | HIGH | Set hard deadlines. "Done" = rendered + edited, not "perfect." |
| **Rig/skeleton issues with second character** | Medium | MEDIUM | Start second character in Week 1 of Sem 2, not Week 3. |
| **No time for polish** | Medium | HIGH | Build in 2-week polish buffer at end of each semester. |
| **Reference gathering takes forever** | Medium | LOW | Start with 10 images. Add more as you need them. Don't spend a week on Pinterest. |

---

## Summary Checklist

### This Week (Before Semester)
- [ ] Test mocap pipeline end-to-end (drop FBX → retarget → verify)
- [ ] Test FACS lip-sync (audio → mouth movement)
- [ ] Build `Templates/Melusina_Animation_Stage.blend`
- [ ] Audit 5 existing mocap clips for quality
- [ ] Create `Saved/AnimationReference/` folder structure
- [ ] Pin 50+ reference images to Pinterest
- [ ] Read first 3 chapters of *The Animator's Survival Kit*

### Semester 1 Milestones
- [ ] Week 2: Blocked jump/turn/land clip
- [ ] Week 4: Cleaned mocap clip (no foot slide)
- [ ] Week 6: Talking clip with lip-sync + blinks
- [ ] Week 8: 30s acting performance (body + face)
- [ ] Week 10: **PIECE #1 — Polished + rendered**

### Semester 2 Milestones
- [ ] Week 2: Second character rigged + retargeted
- [ ] Week 4: **PIECE #2 — Contrast piece (opposite energy)**
- [ ] Week 6: **PIECE #3 — Dialogue scene**
- [ ] Week 8: **PIECE #4 — Experimental/audio-reactive**
- [ ] Week 10: **PORTFOLIO — Reel + breakdowns + stills**

---

*Plan written 2026-09-03. Review and adjust after Week 1 based on actual pipeline state.*
