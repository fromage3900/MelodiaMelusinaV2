# Work Order — Choral Sheep VFX + StarryNight Sky Remediation

**Date:** 2026-09-14
**Type:** repair work order (not a status doc; status lives in `CURRENT_STATE.md`)
**Evidence basis:** disk audit 2026-09-14 (no live-editor reads; game-thread channel was down).
Verify live bindings before executing — disk says what's committed, not what's loaded.
**Authority:** Board 06 + Nikki Cymatics material lock for look; C++ owns gameplay truth;
single-writer UI; one editor at a time.

---

## 1. Problem statement

**VFX:** `NS_ChoralSheep_BeatBurst`'s material references a texture that does not exist
in this branch; both sheep Niagara systems are unaudited clones; two committed scripts
make opposite color-space claims with no recorded winner.

**StarryNight:** the only on-disk assets are two surface-domain masters; the post-process
hero profile they were supposed to feed does not exist here; the one documented wiring
(a surface material in PPV blendables) is a silent engine no-op (defect #3, 2026-08-29).

## 2. File inventory (verified on disk 2026-09-14)

| Asset | State |
|---|---|
| `Content/Melodia/Companions/ChoralSheep/VFX/NS_ChoralSheep_WoolMotes` | clone of `NS_Melusina_Glint`, unaudited since fork, **modified in working tree** |
| `Content/Melodia/Companions/ChoralSheep/VFX/NS_ChoralSheep_BeatBurst` | clone of `NS_Melodia_ClickSparkle`, unaudited, **modified in working tree** |
| `.../VFX/Materials/MI_NS_ChoralSheep_WoolMote` | diamond-glint pearl/lilac intent, **modified in working tree** |
| `.../VFX/Materials/MI_NS_ChoralSheep_BeatStar` | documents `T_Spark_Twinkle8` — **0 copies on disk**, **modified in working tree** |
| `Content/EnvSandbox/Materials/Masters/M_Melodia_StarryNight_VanGogh` | surface-domain master, exists |
| `Content/EnvSandbox/Materials/Masters/M_Melodia_StarryNight_Impressionist` | surface-domain master, exists |
| `MI_StarryNight_Hero` / `M_PP_StarryNightOverlay_Candidate` / Profiles folder | **absent — not on disk** |
| `Saved/Audit/choral_sheep/fix_vfx_tex_samplers.py` | forces grayscale/linear on (phantom) textures |
| `Saved/Audit/choral_sheep/revert_spark_tex_color.py` | reverts to sRGB, calls the above a "hack" |
| `Saved/Audit/choral_sheep/SHEEP_NIAGARA_VFX_SCAFFOLD_2026-09-09.md` | clone lineage + user params (`WoolGlow` 0.35, `ChladniDrive` 0, `PitchHue` 0.75); "Next: BP wiring" never done |
| `Content/Python/fix_ppv_stack.py` | defect-#3 repair, **in-memory only**, persistence owner-gated |
| `Content/Python/finalize_ppv_hero_stack.py` | hero-stack authoring; targets assets that don't exist here |

## 3. Coordination constraints (read before touching anything)

1. All four sheep VFX assets are **modified in the working tree right now** — another
   hand is in them. Claim the lane (or wait for it) before editing; do not double-edit.
2. `.hermes/plans/` dated today + `index.lock` activity 2026-09-14 — a second operator
   is committing on this branch. Coordinate writes.
3. One editor only. No second MCP surface on the same graph.
4. No wholesale promotion from `collab/laptop/longterm`; no `git clean -fd`;
   no `git checkout -- .`; never Python-load skill Blueprints.
5. Showcase soft freeze (2026-09-07) is active — this is repair of approved-look
   systems, not a redesign. Board 06 + Nikki path stay locked.

## 4. Workstream A — VFX texture canonization + emitter audit

**A1. Canonize ONE spark texture.** Import or nominate the surviving spark/glint alpha.
Record: chosen path, why, sRGB **off** + grayscale iff it is a pure alpha mask,
sRGB on iff it carries color. One texture, one decision, written here on completion.
**A2. Repoint `MI_NS_ChoralSheep_BeatStar`.** Bind the A1 texture; set sampler type to
match (mask → linear grayscale; color → sRGB). Compile, save.
**A3. Retire the sRGB war.** Annotate both scripts' headers with the A1 decision and
date; do not delete (audit trail). No third script.
**A4. Emitter audit, module by module.** For each system: list every emitter, renderer
facing mode (must be an explicit camera-facing mode, never Custom-without-axes),
material binding (must have Niagara-Sprites usage flag), user-param bindings
(`WoolGlow`, `ChladniDrive`, `PitchHue`, Melodia bus), and stale modules inherited
from the donor systems. Remove or justify each leftover.
**A5. BP wiring (scaffold's open item).** Attach WoolMotes to fleece; drive
`ChladniDrive` from coat `BeatAccent`/`ChladniEmissive`; fire BeatBurst on pitch hits.
**A6. Proof.** One lit PIE capture with a visible burst + motes on the sheep, frames
committed under `Saved/Audit/choral_sheep/vfx_proof_<date>/` plus a JSON receipt
(samples, log gating, frame list). Prose is not proof.

## 5. Workstream B — StarryNight decision + missing-material authoring

**B1. Answer surface-vs-overlay — DECIDED 2026-09-14 (owner): surface-domain
overlay that blends with UDS.** StarryNight lives on sky-dome geometry
(surface domain, as the VanGogh/Impressionist masters already are) and
composites with Ultra Dynamic Sky rather than replacing it. Option (b)
post-process overlay is rejected — do not author `MI_StarryNight_Hero`.
**B2. Author the missing material.** Whichever B1 picks, the artifact must exist on
disk with the correct `MaterialDomain` (this is the entire defect #3 class).
**B3. Wire + persist with evidence.** Apply to the agreed maps (lookdev-only unless
the owner says otherwise — StarryNight was scoped cinematic/lookdev-only); save levels;
write `Saved/Audit/starrynight_wire_<date>.json` with before/after blendable lists
including each entry's resolved domain. Memory-only fixes are not fixes.
**B4. UDS coexistence.** Ultra Dynamic Sky owns the Morning sky and its time-of-day
is not readable from Python — pin it before any A/B, and verify StarryNight
composites instead of fighting it.
**B5. Proof.** Lit capture showing the night sky effect in-frame, committed with receipt
as in A6. Re-run `fix_ppv_stack` logic as a *check* (droppers must read zero).

## 6. Acceptance

- [ ] BeatBurst renders a visible sprite in a lit PIE capture (no missing-texture fallback).
- [ ] Both systems' emitter audits committed (module list, facing modes, bindings).
- [ ] sRGB decision recorded once; scripts annotated.
- [ ] B1 choice recorded; B2 material on disk with correct domain.
- [ ] PPV/domain audit JSON shows zero droppers; receipt frames committed.
- [ ] No unrelated files touched; `CURRENT_STATE.md` updated in the same change set.

## 7. Non-goals

No new VFX framework, no second TD bridge, no material-master redesign, no website
changes, no laptop-branch promotion, no lookdev re-art-direction. Repair to the
approved look, then stop.
