# StepFun handoff — Accordeur procedural Geometry Nodes system

**Owner directive, 2026-10-11:** The *two approved watercolor/ink concept sheets* and seven isolated character crops are **visual references for a PROCEDURAL Geometry Nodes authoring system**. Tripo is optional exploration only; generated Tripo meshes are NOT the asset authority or required production starting point. Build actual reusable geometry procedurally through Melodia Studio.

**Scope:** bounded pilot and registry integration; NO general new Blender framework and NO UE/gameplay edits. Proposed file names are suggestions, not proof of prior existence.

## Preflight and authority
1. Read `Docs/Characters/Accordeurs/README.md`, `CANON_LORE_AND_CHARACTER_BIBLE.md`, `Docs/BLENDER_MELODIA_COCKPIT.md`, `deploy/surreal_arch/melodia_gn/core.py`, `deploy/surreal_arch/melodia_gn/__init__.py`, and `deploy/surreal_arch/melodia_gn/melusina_house_foundation.py`.
2. Locate the actual live working copy and existing Melodia Studio registry. This Git branch is a planning/code lane: do not assume it is deployed to the owner's local AppData addon or `G:` working .blend.
3. Follow existing builder pattern `register_builder(...)` in `deploy/surreal_arch/melodia_gn/core.py` and auto-registered module import **before** the `_rebuild_derived_data()` call in `__init__.py`. Check relevant `presets.py` catalog, GN Stack discovery and `Tools/melodia_studio_source_gate.py`. Use established `safe_node`, `require_node`, parameter helpers. Do not fork GN core, make a side registry, or hardcode a Blender version rewrite.
4. Approved references: `Les Petits Accordeurs Character Lineup.jpeg`, `Les Petits Accordeurs Concept Sheet.jpeg` and the individual `ACC_<ID>_source_front.png` crops from the separate reference pack. **Reject** hyper-detailed `Atelier Magique` furry/goblin style. References must remain on disk rather than embedded in source code.
5. Read `CURRENT_STATE.md`: do not save the live portfolio stage or interrupt running Unreal/Melusina systems; isolated factory-startup Blender proofs only first.

## Target product
A reusable family of coherent, **intentionally different** 15–25cm chibi maintenance spirits, built through editable GN node groups and registry presets. One control group per major body feature, stable default presets keyed by **ACC_* IDs**, accessory instancing by role, deterministic variation from `Seed`.

**Not:** one procedurally random creature with 7 palette swaps; seven unrelated AI meshes; Tripo-only retopology; photoreal fur; fully baked armatures/UE import in first pass.

## Build ladder — keep changes minimal
| Group proposed name | Responsibility |
|--|--|
| `MEL_acc_body` | create coherent body/head volume, feet, arms, belly/face planes as continuous or deliberately separate deformable regions |
| `MEL_acc_ears` | leaf ears, droopy ears, curl/heart tips; orientation, length, tip bend |
| `MEL_acc_face` | oversized eyes, eyelids, tiny mouth, expression; glasses and beard as named detachable accessories |
| `MEL_acc_outfit` | role-specific hat/cap/ribbon/neck scarf; separation from body |
| `MEL_acc_props` | ID-driven detachable hats, stamp/ledger, thread/needle/spool, satchel, mallet, keys, map, mail bag |
| `MEL_acc_character` | assemble named groups from presets; publish controllable `Character ID` / `Seed` and normalized scale |

These names are **proposed**. Before registering, verify against the existing registry and follow its naming conventions. Prefer few authoritative groups; add new ones only where necessary. In Blender GN, representing a body using several primitives for prototyping is fine, but this does **not** make it skinnable topology. Plan explicit bake/retopo after silhouette acceptance.

## Parameter contract (proposed defaults, tune against art)
- `Character ID`: named deterministic preset, 7 possible values.
- `Seed`: int, fixed for reproducible variation; it must not randomize species identity, face, or major silhouette.
- `Height cm`: default per character within [15, 25], export metric consistent.
- `Head/Body ratio`, `Body width`, `Foot offset`, `Arm length`.
- `Ear mode`, `Ear angle`, `Ear length`, `Tip bend`, `Antenna curl`.
- `Eye separation`, `Eye size`, `Lid shape`, `Mouth curve`.
- `Cap/Helmet/Scarf type`, `Accessory toggles`, `Expression`.
- `Palette ID` and **separate** named material slots; do not use texture noise as a substitute for shape.
- `Proxy/Export mode` distinguishes instanced lookdev previews from frozen editable mesh output.

## Non-interchangeable silhouette features
- **COMMITTE:** lavender, two twig/leaf antennae; circular glasses, large book and stamp.
- **MERGE:** cream-pink, wide droopy lateral ears, gold loop/ribbon; spool/needle are detachable.
- **CACHE:** blue, half-asleep, voluminous floppy nightcap and deep satchel.
- **BUILD:** mint, prominent yellow helmet and mallet, elevated leaf ears.
- **LFS:** compact pale body, stern lids, large square loaded backpack, curled purple antenna, key ring.
- **REBASE:** pale sage, long white beard, curled question-mark antenna, map and scroll.
- **BOT:** coral, upward heartlike antennae, high-energy large expression, mailbag.
Ensure each is recognizable **in clay silhouette and from the camera distance** before materials. The original two sheets are source of truth where descriptions are imperfect.

## Delivery split
**Phase 0 — discovery only:** Report exact repository paths, registration mechanism, launch command, any conflicts/stale branches; include an explicit SHA and don't modify unrelated code.
**Phase 1 — one tiny working pilot, Le Build:** Implement reusable body/ear/face grouping plus role accessory params; integrate via existing registry and GN Stack; build Le Build preset. Use primitive-based blockout first, pass nonzero evaluated geometry tests. Capture front/side/three-quarter orthographic and silhouette comparisons to reference. Do not present screenshot renders as proof unless actually captured from Blender.
**Phase 2 — derivability proof:** Demonstrate **Mlle. Merge and Petit Cache** using the SAME registered groups with different parameters and detachable props; confirm meaningful geometry differences, not just palette. If one family cannot share a deforming topology, document that instead of forcing it.
**Phase 3 — other four characters:** only after owner visual review of first three.
**Phase 4 — export/rig/UE:** deferred until clean bake topology, proportions, materials and UV seams are inspected. Optionally investigate appropriate existing rig route; Auto-Rig Pro humanoid solving is not assumed appropriate.

## Verification and evidence
- Open on a Blender **5.2** factory-startup session, never overwrite live stage.
- Existing registry collision check; unique stable node group IDs; `GROUP_BUILDERS` registration is discoverable in GN Stack.
- Re-run with same seed; geometry counts, vertex bounds, deterministic part choices and presets identical. Different seeds can vary minor cosmetic details without identity drift.
- Evaluated object is nonempty, bounded, upright, no huge/NaN coordinates; dimensions in meters correspond to 15–25cm.
- Verify seven stable preset identities can be selected; **only first three need visually complete prototypes in this task**.
- Accessibility of *individual mesh parts*: distinguish arms/body/eyes/helmet/hammer etc; retain explicit named parts/attributes for post-bake cleanup.
- Take front/side/three-quarter screenshots **at the same scale** as the reference for all pilot characters; no unsupported claims about geometry quality.
- Record source files, exact commands and output manifest; `git check-ignore -v` on new scripts, avoid accidental ignored files.
- Existing `Tools/melodia_studio_source_gate.py` plus relevant Melodia Studio verifier must still pass; only quote actual runs and results.
- No binary art committed to LFS without approval; no Unreal edits and no packaged proof claims.

## StepFun done definition
Small code diff registered in the **existing** addon + documented presets + automated verifier + three distinct generated spirit prototypes (Le Build, Mlle. Merge, Petit Cache) **only if their visual approval can be demonstrated**. Otherwise report a bounded working subset and blocker, do not invent screenshots/results. Leave the branch as draft for owner review.

## Handoff answer format
Report:
1. base/head SHA and commit SHA(s)
2. files changed and why
3. exact builder group names and parameters
4. which pilot figures actually generated
5. screenshots/evidence paths
6. gates passed/failed/unverified
7. cheapest next action without opening a second pipeline
