# Tripo Launch Card — Les Petits Accordeurs (2026-10-11)

**Generation status:** NOT STARTED in chat. A connected model catalog lists Tripo 3D, but currently available generation actions only submit images/video/audio; Tripo 3D submission is unavailable in this session. No credits spent.

Official Studio guide: https://www.tripo3d.ai/help/features/how-to-use-the-image-to-3d-feature
Official image-to-3D v3 endpoint: https://developers.tripo3d.ai/en/docs/generation-image-to-model
Official H3.1 details and credit cost matrix: https://developers.tripo3d.ai/en/models/v3-1

## Do this in the Tripo Studio UI
1. Open **Tripo Studio** and choose Image to 3D, *Best Quality / HD Model / H Series* for the first fidelity test.
2. Upload exactly one PNG: ACC_BUILD_source_front.png from the separately delivered **Accordeurs_Tripo_Reference_Pack.zip**. Inspect the crop first: it is taken from a crowded character lineup and may include neighbor edges/overlapping props; clean them in a proper art editor if the model picks them up.
3. Preserve proportions. Avoid 'smart low-poly' or quad claims at first; choose default standard geometry, enable texture only if painted likeness is important. For a cheap blockout test, no texture/PBR is preferable. Do not pay for ultra geometry before silhouette approval.
4. Generate once. Compare orbiting mesh to 2D sheet. Mark ACCEPT/REWORK/REJECT; record job id, credits, model version, options and GLB filename in accordeurs_manifest.json.
5. Only after Le Build passes, repeat for Mlle. Merge, then Petit Cache, using their own images. Keep multiple image views for ONE character only if they are truly matching views (not separate creative redesigns).
6. Export GLB (or provider's supported output), import to Blender staging, separate props, topology clean-up, validate 0.15–0.25m character height and neutral deformation, then sandbox UE5.8 import.

## Provider facts as of audit
- Tripo H3.1 Studio offers Best Quality (H series) vs Clean Topology (P series).
- H3.1 API endpoint takes one image (PNG/JPEG/WebP) or upload token, and returns asynchronous generation tasks; generated models are not guaranteed game-ready.
- H3.1 image-to-3D published API table: 20 credits no texture, 30 standard texture, 40 detailed texture, plus optional charges for additional geometry/topology. **This is API pricing, not verified user account balance or Studio checkout pricing**.
- **For parts generation**, the official v3 API notes `texture=false, pbr=false` and no `quad`/`smart_low_poly`, if the mode supports parts. The Studio UI may not expose that toggle.
- Never assume the Tripo-generated object is textured correctly, cleanly deformable or equivalent to UE-authoritative art.

## Three first-pass character directions
**ACC_BUILD:** short mint chibi body, two leaflike appendages, expressive joyful face and separate yellow helmet. Detach mallet as its own prop after generation. Test bright front-facing silhouette.

**ACC_MERGE:** cream-pink doll-like body, long soft ears and gentle face; treat gold thread, needle, ribbon, spool as separate accessories, avoid realistic fur and humanoid arms.

**ACC_CACHE:** sleeping blue short chibi; oversized navy cap and treasure pouch, mostly closed eyes. Test readable front outline, not fused cap to face or purse to feet.

## Gate before uploading to Git
Do not add raw GLBs to metered LFS by default; save generation receipt and source in the user's local art staging. A project owner must explicitly approve an LFS batch according to Docs/GIT_BATCH_DISCIPLINE.md.
