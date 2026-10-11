# Les Petits Accordeurs — character design authority (concept, 2026-10-11)

**Status:** design authority only; not proof of rig, mesh, GN builder, UE actor, collection, interaction, save/restart or runtime. Runtime/project status is exclusively `CURRENT_STATE.md`.

## Source and ownership
Original artworks recovered from the owner's ChatGPT Library (2026-09-18): `Les Petits Accordeurs Character Lineup.png`, `Les Petits Accordeurs Concept Sheet.png`, `Les Petits Accordeurs Atelier Magique.png`. Artwork files are **not committed here**; bulk binary intake is subject to the existing Perforce/LFS storage contract. This file and `specs/companions/les_petits_accordeurs.v1.json` are the **design registry**, not a replacement for the Blender/GN builder registry, UE Asset Registry or game-save authority. The new generated exploration sheet is optional, not canonical for silhouettes.

Identity: **Maintenance Spirits of Melody, Memory, and Small Repairs.**
Mottos: **Small hands. Better worlds. / Keep things in tune. / Different tasks. Same song.**
Original concept scale: **15–25 cm** beside Melusina (~160 cm in the concept sheet). Paper, ink, cloth, wood, aged brass, leather, and minute star-glow; pastel watercolor shapes with small functional props.

## Canonical lineup
| ID | Character | Silhouette lock | Signature action | Production gameplay idea |
|---|---|---|---|---|
| `monsieur_committe` | Monsieur Committe | round spectacles; twin upright lavender leaf ears; ledger block silhouette; ink-tail flourish | page-flip | `archive_hint` (proposed) |
| `mademoiselle_merge` | Mlle. Merge | floppy ribbon ears; golden treble-loop ornament; broad spool plus fine needle | thread-pull | `lullaby_mend` (proposed) |
| `petit_cache` | Petit Cache | oversized soft sleeping cap; rounded drooping posture; treasure bag larger than torso | doze | `lost_fragment` (proposed) |
| `le_build` | Le Build | helmet with musical note; tall tool-and-mallet diagonal; green sprout-ears | hammer-hit | `repair_fixture` (proposed) |
| `madame_lfs` | Madame L.F.S. | stern arched brow; huge parcel-pack with dangling keys; angular scarf | key-jingle | `supply_request` (proposed) |
| `monsieur_rebase` | Monsieur Rebase | long curling sprout; whisker/beard triangle; map-scroll silhouette | map-unfold | `route_reveal` (proposed) |
| `le_bot` | Le Bot | heart-tipped upward ears; raised running legs; floating envelope trail | dash | `message_delivery` (proposed) |

## Visual and animation rules
- Preserve **chibi nonhuman proportions**, soft bean/pear body, oversized eyes, expressive ears/antennae, small mitt-like hands and feet; do not make them humanoid toddlers.
- Props and ears carry identity even in unlit silhouettes. Ensure all seven remain recognizable at 15–25 cm in a Melodia scene.
- Use one approved *compatible* deformation skeleton/rig as an authoring goal; **do not share the Melusina skeleton** or retarget blindly. Different ear, tail, satchel, prop bones should be attachable optional modules.
- Each character needs, at minimum, turnarounds (front, profile, back), face/emote row (neutral, delighted, worried, focused), prop separation, idle/action loop, contact/shadow, in-world scale verification. Concept images are not final orthographic technical turnarounds.
- Separate static hard props from deformation mesh. Preserve low-area eye/ear readability and consistent scale in Unreal; verify contact and silhouette under the actual project PPV.
- Seeded palette, costume, prop variants are authored **data** feeding registered Geometry Nodes; stable IDs and deterministic seeds; no new scene/asset manager.

## Pilot vertical slice — Mlle. Merge / Lullaby Mend (proposal)
**Why this first:** a visible, bounded piece of world repair can reuse the existing `specs/blueprints/fixtures/lullaby_mend_resonance_skill.v1.json` motif and already-owned world/gameplay interaction seams.

1. Author an approved Mlle. Merge model and props from the concept sheet in Blender; find existing suitable registered GN builder first, register one only if needed. The existing source is `Tools/BlenderAddons/melodia_studio/` + `deploy/surreal_arch/melodia_gn/`.
2. Export via **Melodia Studio Export UE5** and hand off to the **existing** UE integration/companion authority. Do not create another companion manager. Stage assets under the appropriate, approved P4-owned content destination; do not edit Melusina rig, materials, maps or game saves as part of the design pass.
3. Author one supervised scene interaction: a broken *resonance-thread footbridge* with three visible stitch anchors; the player triggers a familiar Lullaby Mend/resonance interaction, Mlle. Merge stitches the seam, and traversal changes. These are gameplay design acceptance targets, **not an assertion the feature exists**.
4. Acceptance: both owner-approved model silhouette and Mlle. Merge facial expression visible in a real UE viewport; deterministic reimport; one deliberate physical-input interaction; traverse the repaired span; reload/restart preserves the world repair through the **existing** save authority; actual audio/FX layer, no new PhraseBus/MPC writers.
5. Failure boundary: if the existing skill/fixture cannot express the stitch action, record the exact contract gap; do not invent a second effect bus, save system, or compiler.

## Production rail / gates
`original source` -> `approved 3-view / proportion lock` -> `Blender Melodia Studio source and existing GN registry discovery` -> `headless registry/geometry/silhouette pass` -> `rig + four emotes` -> `UE import/readback` -> `existing gameplay hook` -> `PIE physical-input + persistence` -> `owner approval`.

**Read before implementation:** `Docs/MelodiaStudio/MELODIA_STUDIO_HOW_TO_USE_2026-09-18.md`, `Docs/MelodiaStudio/PIPELINE_OVERVIEW.md`, `Docs/Production/AGENT_PRODUCTION_PLAYBOOK.md`, `Docs/Production/MULTI_AGENT_LANES.md`.

No live Blender, Houdini, Unreal, P4 or LFS asset bytes were modified in this design-only pass. All expected build/rig/runtime gates remain **UNVERIFIED**.
