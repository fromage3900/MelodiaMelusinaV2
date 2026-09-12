# Melusina Meet2 OBSBOT Studio — 2026-09-08

> Contract: `Docs/CANONICAL_REPO_CONTRACT.md` — game repo is `fromage3900/MelodiaMelusinaV2` at `C:/EnvironmentPortfolio/BS_GodFile`, TD repo is `C:/MelodiaTouchDesigner` (private). This doc lives in the game repo.

hey — this is your tiny fixed-cam mocap corner. no gimbal nonsense, just one locked camera and a boring background that Cascadeur actually likes.

## the camera — OBSBOT Meet2 4K

fixed cam, not a PTZ. tracking is digital crop, not physical movement — which is exactly what we want.

- **4K30 + 1080p60** — both native, pick per-job
- **79.4° diagonal FOV**
- **PDAF + manual focus**
- **4x digital zoom** (we leave it at 1x for mocap)

tiny, light, tripod-friendly. leave it on a real tripod, not the monitor clip.

## two presets — don't mix them

### MOCAP (the real one)
this is your Cascadeur source. lock everything down.

- **1080p60** — temporal > spatial for body. twice the frames beats extra pixels for hands/feet/turns
- **auto-framing OFF**
- **digital zoom 1x fixed**
- **exposure locked, WB locked, focus fixed/manual** (or at least stable — no hunting mid-take)
- **PTZ locked** — camera doesn't move, you do
- full body always in frame, feet visible

→ `OBS clean H.264` → `Cascadeur 2026.2 Video Mocap` → `Live Link` → `UE 5.8 Melusina`

> why 1080p60: faster arcs, foot plants, rhythm hits get double-sampled vs 4K30. use 4K30 only for slow acting/reference where you want face/hand detail.

### REFERENCE / REHEARSAL
for when you want the camera to help you act.

- **tracking ON, auto-framing ON**
- auto-zoom allowed
- use for close-ups, gesture studies, previs, acting ref
- **never** as Cascadeur mocap source — the crop drift messes with the monocular solve

## the room — keep it boring

- **~3×3m clear** if you can swing it
- **camera at chest/waist height** — not floor, not ceiling
- **two broad lights at ~45°** off performer (both sides, soft)
- **plain contrasting background** — silhouette is everything
- **floor markers** for your feet + tripod feet
- **clothing: strong silhouette**, solid color contrast vs background. no big billowy skirt for the base capture, no black-on-black, nothing that hides elbows/knees. dress motion comes later in UE/Cascadeur, not baked into the solve.

```
        [OBSBOT on tripod — chest height, locked]

              ┌─── CAPTURE AREA ~3x3m ───┐
              │                         │
    light 45° │          YOU            │  light 45°
     ○        │       (floor x)         │       ○
              │                         │
              └─────────────────────────┘
               plain wall — no clutter
```

## tripod marks + calibration

mark the tripod feet on the floor (tape or little dots). camera goes back to the exact same spot every time.

keep 4 presets saved in OBSBOT Center so you can just click and go:

1. **neutral** — full-body standing, feet + head with margin, your default mocap
2. **wide** — bigger capture box, for traveling moves / weapon swings / big turns
3. **seated** — chair/kneeling height, camera stays put, just reframe for lower action
4. **upper** — waist-up, for hand acting / instrument / face+gesture takes (still 1080p60, still locked)

auto-framing stays OFF for all four mocap presets. if you want a tracking version of any of them, dupe it as `*_REF` with tracking ON.

---

that's it — one cam, one locked preset, one boring corner, four framings. once this is dialed you stop fiddling with mocap and just perform.

pipeline recap: **Meet2 4K @ 1080p60 locked → OBS H.264 → Cascadeur 2026.2 (AutoPosing / cleanup / AutoPhysics) → Live Link → UE 5.8 Melusina in `L_Melusina_MocapStudio`**
