# Sea Above asset grounding pass — 2026-09-04

The attached placement manifest was parsed by label and full `StaticMeshActor_UAID` identity. It contained 184 geometry entries: 40 `SA_HM_SA_AbyssFloor`, 84 `SA_HM_SA_ReefGarden`, 29 Atlantis palace pieces, 20 plants, 6 trees, and 5 ivy meshes. Non-geometry entries in the same manifest were ignored.

Each target was traced from above the Landscape bounds to below them with all static mesh actors ignored. Only a Landscape hit was accepted. The actor was then moved vertically by `terrainZ - boundsBottomZ`, preserving XY, rotation, and scale. The three ivy meshes beyond the north landscape edge were clamped by their bounds to the nearest valid landscape footprint before the same trace.

Applied result (disk-verified):

- 184/184 target identities matched.
- 184/184 received a Landscape hit.
- 183 actors moved on the clean reload; one was already within 0.5 cm.
- 0 unresolved no-hit or outside-footprint targets.
- The 184 World Partition external actor packages were explicitly saved with
  Monolith `editor.save_packages` (`saved: 184/184`), along with the map
  package.
- After unloading and reloading the level, the same read-only audit reports a
  maximum remaining bottom-to-terrain delta of 0.15 cm.

Evidence: `Saved/Audit/sea_above_attached_mesh_grounding_disk_save_2026-09-04.json`
and `Saved/Audit/sea_above_attached_mesh_grounding_disk_verified_2026-09-04.json`.

The earlier `*_post_2026-09-04.json` report was an in-memory checkpoint and is
retained for history; it must not be treated as disk proof.

The raycast is a vertical contact pass. It intentionally preserves authored XY and orientation; slope alignment and artistic grouping remain a separate dressing decision for the PCG/hero pass.
