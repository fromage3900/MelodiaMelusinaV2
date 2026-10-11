# Shorewake — ANMN301 Blender 5.2 Animatic Finish
**Plan date:** 2026-10-09 | **Owner:** Brennan | **Repo:** `fromage3900/MelodiaMelusinaV2` | **Target:** original school animatic, not a new boat framework

## Mission / owner-facing finish line
Finish the existing **Shorewake Calling** silent animatic with readable boat geometry, physically persuasive *stylized* hull-on-wave motion, coherent wakes/ripples/wind and deliberate shot framing. Preserve existing character, outfit, narrative beat and prior exports. Prioritize a **submission-safe version today**; speculative details and full texture rebakes are secondary.

**Recommended frontier agent:** Claude Sonnet 5.5 in a local Blender-aware session (good owner-eye iteration + Python adjustments); alternative GPT-6 Codex for script-only deterministic repairs. **Recon scout:** DeepSeek V4.1 Flash read-only on G: and repository before starting Claude.

## Authorities and pre-existing proof (do not rebuild)
- `Humber_FinalYear_Prep/ANMN301_Animatic/SHOREWAKE_BEAT_BOARD.md` — shot narrative / timing (historical ~72 s / 1080p24 silent; confirm current actual cut before changing).
- `BOAT_MASTER_PLAN_v09.md`, `BOAT_MOTION_PLAN_v08.md` — one rock driver, one wind system, one water surface; do not make competing solvers.
- `SKIFF_FINAL_PUSH_PLAN_v21.md` — its **2026-09-18 snapshot** describes 40x40 ocean, foam collar, widening-V wake and seamless 120-frame boat loop. Re-verify in latest local .blend; the plan is NOT proof of today's state.
- GitHub `SHOREWAKE_VSE_animatic_v01/v02/v03.blend` and `ShepherdBrennan_AnimaticCreation_2026-10-09*.mp4` exist. Presence of exports ≠ approved composition or motion. Keep original exports untouched.
- Confirm Blender executable is **5.2**; do not use known-incompatible MESHmachine/MACHIN3tools or broken FLIP registration as prerequisites.

## Stage F0 — cheap local reconnaissance (read-only; no launch of GUI Blender)
- Identify `G:` repository and file authority, `git status --short`, current branch, LFS assets, `p4 opened` if mounted. **Do not pull or reset a dirty tree.**
- Locate *most recent actual* Shorewake animation `.blend`, VSE cut, current rendered MP4s, linked libraries, dependencies, cache directories. Record full file paths, modification timestamps and file hashes. Do not pick v09 merely because an old plan names it.
- If headless Blender 5.2 is available, open a **temporary duplicate only** and export JSON: scene FPS/range, VSE strips/shot markers, camera assignments and focal lengths, hull anchor animation curves, wave modifier drivers, wind and pennant caches, nonuniform transforms, floating/underwater geometry, missing images, duplicate materials. No saves to originals.
- Produce `Saved/Audit/shorewake_20261009/recon.json` + one-page `handoff.md` with top 5 observable defects and commands to repro. Label unobserved issues UNKNOWN.

## Stage F1 — master the shot *before* making details
1. Compare the current cut to the beat board and actual Oct 9 MP4s. Fix only shots whose story, framing or subject visibility fails. Prioritize **01 establishing, 07/08 water response, 13 wake, 15 crossing**; include 03 close / 16 route-open only when present and visibly deficient.
2. Lock 16:9, output res/frame rate, frame boundaries, camera path, character silhouette/safe areas, horizon placement and visual continuity across cuts. For each promoted shot record start/end frame and one first/middle/last preview.
3. If only a little time remains, freeze shot timing and fix camera cuts + one highest-value water/boat movement issue. Full UV relayout, new decks, material architecture, and particle solvers are **not** submission prerequisites.

## Stage F2 — hull dynamics and animation
- Inspect anchor `Starskiff_MK38` (or verified latest successor) as the **single boat motion authority**. Preserve parent-child coherence: mast, rigging, passengers, waterline FX travel with boat without mesh lag, slips or clipping. Verify driver data and animation loops before changing.
- Make a short local physics-reference pass: wave direction/speed/period vs longitudinal heave, pitch and roll; avoid excessive synchronous bobbing, teleport jumps, water passing through deck, and boat displacement disconnected from swells. Art-directed keyed/cyclic curves are acceptable; no need for full rigid-body ocean simulation.
- Confirm calm → playing → wake → crossing transition has coherent amplitude/velocity/settling and no discontinuous frames. Check lateral wake follows direction of travel, foam wraps hull/waterline, ripple rings expand from source, pennant reads as one directional wind.
- Repair **one** failing curve/system in a new numbered `.blend` generation; sample first/middle/last and a complete loop. No live simulations or enormous cache bake dependency in final file; bake reproducibly if necessary.

## Stage F3 — geometry / FX / appearance (shot-driven, optional after F1-F2)
- Inspect hull silhouette, rail/hardware contacts, mast sail placement, ropes, visible hull intersections and face/normal/UV defects only in approved cameras. Prioritize legibility and clean geometry over adding new objects.
- Reuse existing ocean, foam collar, widening-V wake and cloth bake where valid. Add only the minimum shimmer, droplets, response rings or light glint that makes shots 07/08/13/15 read. Static waves should not fight animated hull motion; no competing wind or ocean object.
- Correct lighting or metallic legibility in a copy; preserve currently approved materials/texture links. If a bake map is missing, fall back to previously verified materials instead of inventing a new Copernicus pipeline today.

## Stage F4 — evidence and packaging
- Render low-cost preview/contact sheet with labeled promoted shot frames + side-by-side old/new stills and 3-5 s water/boat motion loop.
- Then only after owner-eye gate: render new versioned 1080p24 silent MP4 with cut and title/end cards as required; leave October 9 earlier MP4s intact. Save the final `.blend`, source/linked path manifest, render settings, file hash and proof frames.
- **Acceptance:** shot order and durations match current story; no missing textures, broken dependencies, unexpected pop/foot-slide/boat slip, visible hull-wave discontinuity or camera subject crop; wake/foam animate in correct direction; full export plays; return an explicit PASS/FAIL and exact remaining defect list.
- **Stop rule:** one submission-safe final cut beats a prettier unfinished boat. Scope creep goes to backlog.

## Cost / concurrency contract (all lanes)

1. **Flash read-only reconnaissance, then frontier intervention.** Use DeepSeek V4.1 Flash (`deepseek-flash`) or an already-paid low-cost model. Bound reconnaissance to 1 repo search + 1 local filesystem inventory + 1 targeted report; max ~15 tool invocations; no binary mutation, UE editor launch, shader rebuilding, file deletion, P4 submit, or commits. Cap output to 1-2 pages and machine-readable candidate files. Do not dump whole logs or old plans into the frontier model's context.
2. Hand the expensive agent: (a) current head SHA + branch/worktree, (b) `git status --short` and P4 opens when relevant, (c) exact absolute paths *as locally observed*, (d) authoritative references / conflicts, (e) prioritized defects with evidence and confidence, (f) exact next runnable commands and rollback path. Mark **UNKNOWN** rather than inventing data.
3. Only one writer per `.blend` or UE `.uasset` / level at a time. Work on a new generation or isolated worktree / `refs/agents/<lane>`; never overwrite an open scene, force-push, merge another agent's branch, bulk-delete assets, or submit unrelated P4 changelists.
4. Run bounded **inventory → one fix → test → evidence → next fix**. Two unsuccessful attempts on the same issue trigger a documented blocker and owner review, not a token-expensive loop. Restrict frontier context to the current lane's evidence packet and relevant files.
5. CI/headless checks establish structure only; *visual* success requires inspected images / video and *UE* gameplay success requires actual editor/PIE playback where specified. Never report success from a manifest alone.
6. `G:` is local storage, not accessible through this GitHub-only plan authoring session. The local reconnaissance agent must resolve G: against its own running machine and report `unavailable` if not mounted. Never confuse a GitHub snapshot with current disk or P4 state.

## Frontier handoff prompt
> Work ONLY on this Shorewake animatic lane. Read the recon packet and the three named authorities. Identify the current local Blender 5.2 scene and cut; preserve all original scene/export generations. In an isolated new generation, fix the worst camera/boat-wave/VFX defects shot-by-shot; test with headless Blender where possible, show labeled previews, and export a submission-safe 1080p24 silent animatic only after evidence. Never regenerate unrelated wardrobes, solve a new ocean system or overwrite an open Blender session. Report exact files, before/after frames, blockers and rollback.

## Relationship to other lanes
Separate from film toon-spine and UE Melusina runtime. Do not import game runtime skeleton fixes into the ANMN301 animatic without explicit owner approval.
