# Twinmotion + RealityScan side lane — 2026-08-13

**Side lane only.** Authored Melodia art stays **Blender 5.2 Melodia Studio → UE 5.8** ([`Docs/BLENDER_MELODIA_COCKPIT.md`](../BLENDER_MELODIA_COCKPIT.md)). Twinmotion and RealityScan do **not** own gameplay, Quill, JRPG, Melusina character, or the First Dream battle loop.

Owner ask: how to use these with the project without inventing a second art pipeline.

## What each tool is for here

| Tool | Use in Melodia | Do not use for |
|------|----------------|----------------|
| **RealityScan** | Photogrammetry props / set dressing / reference plates into EnvSandbox | Characters, battle UI, Blueprints, overwriting live meshes |
| **Twinmotion** | Portfolio lighting, vegetation, client stills, camera paths; optional CAD/site import via Datasmith | Shipping game materials, rhythm/combat look, replacing Melodia Studio |

## RealityScan → UE (scan props)

1. Capture and process in RealityScan (phone and/or desktop).
2. Export mesh + textures (FBX/OBJ + maps). Dense Nanite-friendly meshes are fine for env props.
3. In UE, import to a **new** path only, e.g.  
   `/Game/EnvSandbox/Scans/<AssetName>/`  
   Never import into a path that already holds an asset (redirector hazard — see AGENTS.md).
4. Import options: enable **Nanite** for static env meshes; accept temporary PBR materials on first import.
5. Retarget look to Melodia: create a toon/Substrate **MI** from the EnvSandbox spine and drive albedo/normal from the scan maps. Do not ship orphan Datasmith/glTF materials (same class of defect as the Melody Token orphan material).
6. Place first in `L_Template` or a personal sandbox level. Promote into Morning / KaleidoNave / portfolio heroes only after a deliberate review.

**Preferred when the prop must match Melodia Studio / PCG:** scan → light Blender cleanup → Melodia Studio send → UE. Direct RealityScan→UE is for speed and reference.

## Twinmotion ↔ UE

### A. Present Melodia in Twinmotion (portfolio / client)

1. Match Twinmotion to your Epic/UE install family.
2. Bring EnvSandbox content via **Datasmith** or Twinmotion’s UE project link / Direct Link path for your version.
3. Dress lighting, foliage, cameras in Twinmotion.
4. Export stills/video outward. Do **not** round-trip Twinmotion materials back as the game look.

### B. Bring a Twinmotion / CAD set into UE

1. Datasmith import into `/Game/EnvSandbox/Imports/Twinmotion/<SetName>/` (new folder only).
2. Replace Twinmotion materials with Melodia toon MIs before any First Dream map references the set.
3. Keep imports out of `MelodiaIntegration/`, JRPG template trees, and `Content/Characters/Melusina/`.

## Hard project rules (side lane)

- One UnrealEditor. Do not Datasmith-import while another lane owns the same `.umap`.
- `L_SakuraPath` art direction stays human-owned — ask before dropping scans there.
- Bulk scan / Twinmotion caches are often huge: prefer `Exports/` or ignored trees unless you intentionally track a small kit (same LFS budget discipline as EnvSandbox art).
- Gameplay proof stays in PIE: `L_MelusinaMorning` → `L_KaleidoNave` ([`PIE_RUNTIME_NOTES_2026-08-12.md`](PIE_RUNTIME_NOTES_2026-08-12.md)). Twinmotion never closes a rhythm or Quill gate.

## Related

- Blender authority: [`Docs/BLENDER_MELODIA_COCKPIT.md`](../BLENDER_MELODIA_COCKPIT.md)
- Workflow doors (do not add a sixth gameplay door): [`WORKFLOW_UNIFY_2026-08-12.md`](WORKFLOW_UNIFY_2026-08-12.md)
- Level designer path: [`Docs/LEVEL_DESIGNER_ONBOARDING.md`](../LEVEL_DESIGNER_ONBOARDING.md)
- Material spine context: EnvSandbox Substrate Toon (recent salvage/fold work on `main`)
