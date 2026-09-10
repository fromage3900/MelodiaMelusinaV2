# Melusina Cascadeur Live Link Studio — 2026-09-08

> Canonical spec for the Melusina performance-capture lane: OBSBOT Meet 2 4K → Cascadeur 2026.2 Video Mocap (Alpha) → Live Link → UE 5.8 preview map.

## Pipeline Summary

```
OBSBOT Meet 2 4K (1080p60, locked tripod, auto-framing OFF)
  → H.264 MP4
    → Cascadeur 2026.2 Video Mocap Alpha (AutoPosing → key pose repair → feet/contacts → AutoPhysics → polish)
      → Cascadeur Live Link → UE 5.8 (L_Melusina_MocapStudio)
        → Sequencer / Animation Sequence → final game animation
```

Body capture is skeletal only. Cloth/hair/secondary motion are solved downstream in UE (Control Rig / Chaos Cloth / Groom).

## 1. Cascadeur 2026.2 Setup

### Canonical Scene

- **One canonical scene:** `Melusina_BodyCapture_2026.casc` (tracked in `Content/Melodia/Companions/Melusina/` or `Docs/`; single source of truth for rig + import settings).
- **AutoPosing rig:** Import `SK_Melusina` (or `SK_Melusina_FIXED`) via FBX, run Cascadeur **AutoPosing** to bind. Re-use this rig for every take — do not re-rig per clip.
- **Video Mocap Alpha:** Import H.264 MP4 (1080p60). Cascadeur estimates pose onto the AutoPosed rig. Expect noisy depth — treat output as a timing/gesture sketch, not a final solve.
- **Cleanup order:** key-pose repair → foot contacts / ground locks → trajectory / center-of-mass arcs → AutoPhysics pass → additive polish. Hands and depth are manual priorities.

### Live Link Plugin (2026.1+)

- **Version:** Requires Cascadeur **2026.1+**; current generation is **2026.2**.
- **What it does:** Streams the Cascadeur timeline animation directly into UE in real time.
- **Three choices on connect (new in 2026.1+):**
  1. **Cascadeur root** — which Cascadeur character/root to stream.
  2. **Target UE Skeleton** — e.g. `SK_Melusina_Skeleton`.
  3. **Target / new Animation Sequence** — choose existing or create new `UAnimSequence` to write the stream into.
- **Compat:** UE **5.5 – 5.8** (verified for 5.8 project).
- **Platform / license:** **Windows only**, paid tiers — **Indie / Pro / Teams** (not available on Free). Install the Cascadeur Live Link plugin on both sides (Cascadeur plugin + UE plugin enabled).
- **Source:** Cascadeur docs — Live Link announcement and Video Mocap Alpha guidance.

### OBSBOT Meet 2 4K Preset (Mocap)

| Setting | Value |
|---|---|
| Mount | Fixed tripod, floor-marked position |
| Resolution | **1080p60** for mocap (temporal > spatial); 4K30 reserved for slow acting reference |
| Auto-framing / tracking | **OFF** (digital crop fixed at 1x) |
| Focus | PDAF off or manual lock; stable exposure + white balance |
| Framing | Full body always in frame, plain contrasting background, chest/waist camera height |
| Capture | OBS clean H.264 MP4 |

Reference/rehearsal preset may re-enable auto-framing for gesture studies — never use it as mocap source.

### Capture Space

~3×3 m, two broad lights at ~45° to performer, plain background, floor contact markers, camera fixed. Wear silhouette-readable clothing; avoid large occluding skirts or black-on-black for the body pass.

## 2. UE Preview Map — `L_Melusina_MocapStudio`

**Location:** `Content/Melodia/Levels/Mocap/L_Melusina_MocapStudio.umap` (create under `Melodia/Levels` or `Melodia/Companions/Melusina` if Levels is restricted).

**Purpose:** Dedicated, empty sandbox for real-time preview while editing in Cascadeur. No gameplay, no streaming.

| Element | Notes |
|---|---|
| `BP_Melusina_AnimationPreview` | Actor with `SkeletalMeshComponent` (`SK_Melusina`), `LiveLinkComponent` / `Live Link Skeletal Animation` component. Assign `ABP_Melusina_Current` or Live Link pose node. |
| `CineCameraActor` | Locked hero framing (full-body + mid-shot presets), 35–50 mm, fixed exposure. |
| Neutral floor | Flat plane / `SM_Floor` at 0,0,0, matte mid-grey material, grid markers for foot contacts. |
| Lighting | Silhouette-readable: key + fill + rim, neutral HDRI or plain backdrop. No auto-exposure hunting. |
| Live Link subject | Cascadeur subject appears under **Window → Live Link**; map to Melusina skeleton via Live Link. |
| IK Retargeter | `IK_Melusina` / `RTG_Cascadeur_Melusina` if source rig proportions differ. Keep one canonical retargeter. |
| Sequencer recorder | Level Sequence `LS_Melusina_Capture` with Take Recorder / Live Link track → bake to `AnimSequence` in `Content/Melodia/Companions/Melusina/Animations/Capture/`. |

**Live Link wiring:** Epic recommends **Live Link Skeletal Animation Component** for animation subjects; **Live Link Pose** node in AnimBP is alternative where needed.

**Workflow in map:**

1. Open `L_Melusina_MocapStudio`, enable Live Link source (Cascadeur).
2. Scrub/edit in Cascadeur — Melusina performs live in UE viewport under game lighting.
3. When satisfied, record via Sequencer / Take Recorder → creates or overwrites the chosen Animation Sequence.
4. Export/naming: `AS_Melusina_<Action>_<Take>_<Date>` (e.g. `AS_Melusina_InstrumentPhrase_A01_20260908`).

## 3. Boundaries

- **Capture:** body intent → skeletal animation.
- **Downstream:** UE Control Rig cleanup → hair (Groom) → dress / cloth (Chaos Cloth / sim) → secondary physics → final animation. Do not bake dress into mocap.
- Cascadeur Video Mocap depth is alpha-quality (single-camera). Rebuild feet, depth, hands, arcs, weight — keep timing and gesture.

## 4. The Five Things That Make It a Studio

1. One OBSBOT mocap preset (1080p60, locked).
2. One capture corner (marked tripod + lights + backdrop).
3. One canonical Cascadeur Melusina scene + AutoPosing rig.
4. One UE map (`L_Melusina_MocapStudio`) with Live Link + recorder.
5. One naming/export convention.

Once these five exist, stop setting up mocap and just perform.

## 5. First Benchmark

Neutral stance → reach/grasp → 4–8 bar instrument performance phrase → weight shift / turn → expressive flourish → return to neutral. Validates feet, hands, depth, shoulder arcs, rhythm timing, dress-aware posing, and retargeting end-to-end.

## 6. Notes

- Quadruped AutoPosing improved in 2026.1 — same Live Link lane reusable for Choral Sheep.
- Keep this doc as the handoff; update paths once the `.casc` scene and `.umap` are committed.

---
*Teams lane — source paste: `paste_2_201725.txt` (OBSBOT + Cascadeur + UE 5.8 live evaluation stage).*
