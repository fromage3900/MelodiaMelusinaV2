> **SUPERSEDED AS PRIMARY BUILD ROUTE (2026-10-11):** User confirmed the approved sheets/crops are references for an original **procedural Geometry Nodes generator**. The authoritative workflow is [STEPFUN_GN_HANDOFF.md](STEPFUN_GN_HANDOFF.md) using the existing Melodia Studio GN registry and presets. Tripo may provide optional supplementary shape studies, but no Tripo mesh is required or considered canonical. This document is retained strictly as a fallback/reference experiment.

# Accordeur Base Meshes — Tripo to Blender/Houdini to UE5.8

**Status:** production recipe; no Tripo job / GLB or UE import verified in this branch.  
**Visual references:** ONLY owner-approved watercolor Character Lineup and Concept Sheet, not rejected Atelier Magique render.

## Tripo availability
The connected Higgsfield catalog lists **Tripo H3.1 Image to 3D** and **Tripo H3.1 Multiview to 3D**. The currently exposed Higgsfield generation interface may not expose a dedicated 3D submission action; verify the active tool before asserting direct generation is available. If blocked, run jobs manually in Tripo or through an authorized dedicated endpoint. Do not spend credits without an estimate/choice.

## Stage A — source assets
Create seven isolated transparent-or-light-neutral character image crops at good resolution, clearly named and with no overlapping neighbors, labels, extra vignettes, frame ornaments, or foreign characters. Favor intact full-body three-quarter-front from the accepted lineup. Save complete concept sheet as review-only, not direct multi-subject Tripo input.
- ACC_BUILD: first pilot; crop Le Build with hat, hammer. Accept that props may be fused; separate/remove in Blender after generation.
- ACC_MERGE: second; crop Mlle. Merge with needle and thread. Plan manual thread/needle meshes.
- ACC_CACHE: third; crop Petit Cache with cap and satchel. Satchel may require separate accessory model.
- ACC_COMMITTE, ACC_LFS, ACC_REBASE, ACC_BOT: queue after first pilot accepts.

## Stage B — generation brief
**Global Tripo image-to-3D prompt (if supported):**
'One single small original chibi fantasy maintenance spirit, identical silhouette, head/ear proportions and palette to the supplied watercolor reference. Simple rounded anatomy, clean separate limbs, expressive large eyes, soft painted-fabric/toy/storybook surface, neutral upright pose. Focus on faithful shapes rather than micro-details. Keep the base body distinct from attached props. No platform, scene, extra characters, typography, realistic fur or metallic clutter.'

**Negative brief:** 'photorealistic fur, goblin, gremlin, realistic child anatomy, noisy micro-detail, ornaments, baroque armor, extra limbs, text, multiple creatures, merged hands/tools, floating components, theatrical lighting'.

**Suggested first request:** geometry quality=standard, texture=true, PBR=false where exposed, face_limit approximately 20k (budget a source asset, not target production triangles). If using multiview use 2–4 *verified consistent images of the SAME character*, ordered front/side/back; don't supply different characters or generated inconsistent views.

**Important:** exported GLB from AI generation is a **blockout/reference base**, never production-retopo by default. Do not assume quad topology or clean UVs from a 'quad' toggle. Treat texture quality as lookdev only.

## Stage C — base mesh inspection / cleanup
1. Import GLB to an isolated Blender 5.2 collection 'ACCORDERS_STAGING', named ACC_<ID>_tripo_source. Preserve original as immutable reference.
2. Compare directly against the owner sheet from front, side and three-quarter; record mismatch checklist: silhouette, eyes, ear tips, mouth, costume props, exact colors, seam or internal surface artifacts.
3. Resolve/fix disconnected components and holes; apply transforms on copies, not sources; record source axis/orientation, top and underside.
4. Remove generated accessory fusions. Reconstruct hat, cap, spool, backpack, papers and needle as detachable meshes or GN parametric pieces.
5. Retopologize clean deformation regions and remove self-intersections. Keep distinct material IDs, stable UVs, and readable face in projected game-camera pixel size.
6. Native working scale: per concept sheet 0.15–0.25 m tall. Record exported size and axis in a manifest; do not rely solely on 'auto_size'.
7. Unify a base biped-spirit deform skeleton ONLY if species proportions allow; otherwise use family-specific skeletal variants. A nonhumanoid sprite is **not** automatically appropriate for Auto-Rig Pro's humanoid solution.
8. Export production version (FBX for skinned UE or GLB for reference) separately from immutable Tripo GLB. Confirm weights/rig with basic idle, blink or bounce.

## Stage D — UE sandbox
Suggested staging path: /Game/Melodia/Characters/Accordeurs/Prototypes/ (proposal, not confirmed existing).
Import only after validating mesh and artifact sizes. Prefer existing stylized/painterly material infrastructure after audit; no duplicate material system. Unreal units are centimeters: 15–25 cm target. In a test map verify face readability, shadows, LOD/nanite suitability and performance. No changes to active Melusina skeleton, AnimBP, world levels or save owner.

## Naming / provenance
Source crop: ACC_<ID>_source_front.png
Tripo export: ACC_<ID>_TripoRaw_<jobid>.glb
Blender cleaned source: ACC_<ID>_Base_v001.blend
Production export: SK_ACC_<ID>_v001.fbx or SM_ACC_<ID>_v001.fbx
Captures: ACC_<ID>_front_side_back.png
Track generation model/version, account, credits, generation settings, image source path, reviewed_by and ACCEPT / REWORK / REJECT.

## Review rubric
**Must pass:** resemblance to actual approved watercolor character; simple intentionally designed read; two recognizable features at game camera distance; no Atelier Magique art drift; plausible anatomy; neutral pose viable for rigging; separate accessories.
**Must fail:** realistic fur/goblin face, excess gold/steampunk noise, fused multi-character geometry, no usable limb separation, silhouette divergence, broken license/provenance.

## Seed priorities
1. ACC_BUILD: easiest body/face with distinct helmet; medium prop-separation work.
2. ACC_MERGE: tests expressive ear treatment and detachable string/spool.
3. ACC_CACHE: tests unusual hat/satchel shapes and idle motion.
4. Remaining cast only after shared-body and rig feasibility is proven.

## Execution boundaries
Tripo cost, licensing and exports are provider-dependent. Check currently applicable provider terms before distributing or selling any generated mesh. Do not commit heavyweight source GLBs or textures by default: inspect existing metered Git LFS policy (README and Docs/GIT_BATCH_DISCIPLINE.md) and use owner-approved source/artifact storage.
