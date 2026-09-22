# Melusina UE Close-Out Plan v5 — Stage the Regalia in UE 5.8

> **For Hermes:** Prereqs already true: FBX+GLBs staged at
> `Exports/MelusinaFX_20260922/` (contents verified), Blender-side staging done
> (portfolio stage v24_MFX, Accessory Studio v2_MFX, viewer wiring — no push).
> Editor booting as of 2026-09-22 00:50 (PID 49788, `-nosplash`, single instance).
> Evidence standard: JSON state assertions + PNG captures; `success:true` is not evidence.

## U0 — Recon before any writes

- Read `Docs/Handoffs/PORTFOLIO_RENDERS_HANDOFF_2026-09-21.md` for the capture map name
  (portfolio stage level used by the 09-21 renders).
- Locate the Melusina skeletal mesh + actor in that level (`SK_Source_Melusina` is the
  canonical rig per `generated/melusina_animation_library.json`).
- Identify whether a UE "Accessories" runtime system exists (`/Game/Accessories/**`,
  any Accessory DataAsset/component). If none: the UE runtime unit is created fresh in U6.
- Monolith health chain BEFORE editor work: `netstat :9316` → reconcile PID via tasklist →
  `curl http://localhost:9316/health` (200) → probe call. Check `Saved/Logs/BS_GodFile.log`
  for `MODAL_OPEN` before ever concluding the editor is dead — a modal blocks the game
  thread and Monolith goes silent; NEVER kill the editor on that.

## U1 — Import the staged FBX (Interchange)

- Import `MelusinaFX_regalia_wings_rings_eval.fbx` → `/Game/Melusina/FX/Regalia20260922/`.
- 4 static meshes: `SM_FX_AngelWings`, `SM_FX_ClockworkRing_Outer/Mid/Inner`.
- Build settings: Nanite OFF for the three rings (small, thin — tri overhead not worth it);
  Nanite ON for the wings (dense feather geometry); collision NONE; no lightmap UVs
  (dynamic lighting lane); normals from FBX preserved.
- Verify: asset registry counts, bounds sanity (wings span ≈ 2.3 m in UE units 230).
- NO ghost `.uasset` siblings issue for FBX imports (that trap is PNG auto-import) — still
  verify no stray files beside the package.

## U2 — Materials (placeholder now, flipbooks later)

- Assign existing house masters as placeholders (iridescent/brass/water MI families —
  gate every param via `MEL.get_scalar/vector_parameter_names(parent)` before setting).
- Full lookdev arrives with Wave H flipbooks wired as image-sequence samplers
  (H3-UE): wings shimmer, brass ring sweep, glob nacre — never a second material writer;
  extend the existing Melodia material families.

## U3 — Sockets on the Melusina skeletal mesh

- Add sockets to the Melusina SkeletalMesh asset (not per-actor):
  - `FX_WingRoot` — on `spine_03` equivalent bone, orientation matching the Blender
    carrier (behind upper back, tilt baked)
  - `FX_RingStack` — behind back, the ring cluster anchor (Blender offsets: rings drift
    back −0.06/−0.13/−0.20 m in y from the wings plane)
- Verify socket transforms by attaching in-PIE and measuring component world offsets.

## U4 — Portfolio level placement

- DUPLICATE the portfolio/capture map first (`L_…_MFX_20260922`) — AGENTS rule: never
  save over existing portfolio maps. Stage in the duplicate.
- Attach `SM_FX_AngelWings` + the ring stack to the live Melusina actor's sockets.
- Verify world positions in-PIE against the Blender-stage numbers (JSON deltas).

## U5 — Ring motion (UE-side, deterministic)

- The Blender Scene-Time spin does NOT survive FBX. Recreate in UE: rotating components
  on the three ring attachments — outer +0.6 rad/s, mid −0.42, inner +0.78
  (Scene-Time equivalents of tonight's dial speeds), classical Blueprint/tick math only.
- Quantum is a pre-play ranking service ONLY — never frame-loop rotation (house rule).

## U6 — Accessories runtime unit

- If U0 finds an existing accessories system: register the four FX as entries per its
  contract. If not: create `DA_MelusinaFX_Accessories` (DataAsset: id, mesh, socket,
  scale, motion spec) under `/Game/Melusina/FX/Regalia20260922/` as the runtime unit,
  documented as the first entry of that system.

## U7 — Evidence + capture

- In-editor captures: PNG + JSON state assertions (socket transforms, spans, rotation
  deltas between two frames) saved together — frames without a report are not evidence.
- One PIE capture pass on the duplicated map; the melody runtime gates (real-input) are
  NOT claimed by staging work — this is placement evidence only.

## U8 — Close-out checklist

- [ ] Interchange import verified (counts + bounds)
- [ ] Placeholders assigned; flipbook lookdev queued (Wave H3-UE)
- [ ] Sockets exist on the SkeletalMesh with verified transforms
- [ ] Duplicated portfolio map staged + saved; original untouched
- [ ] Ring motion live and deterministic
- [ ] Accessories runtime unit recorded (existing system or fresh DataAsset)
- [ ] Capture evidence pair on disk
- [ ] Owner eyeball gate
