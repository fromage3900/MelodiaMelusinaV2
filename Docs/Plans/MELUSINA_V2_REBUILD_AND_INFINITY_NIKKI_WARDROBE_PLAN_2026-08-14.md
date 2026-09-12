# Melusina V2 Rebuild and Long-Term Wardrobe Plan

Date: 2026-08-14

## Current status

The editor is closed for rebuild. The deformation and import work is substantially complete, but gameplay promotion and PIE validation are still open.

| Gate | Current result | Evidence / remaining work |
| --- | --- | --- |
| V2 bind and split | PASS | `Saved/Audit/melusina_v2_piece_bind_report.json`; five pieces, 465 contract bones, zero zero-weight vertices. Shirt had three deterministic repairs. |
| Actual FBX contract | PASS | `Saved/Audit/melusina_v2_actual_fbx_contract_report.json`; actual mesh tables and parent chains validate, root shim accounted for, body morphs preserved with 120 shape keys. |
| UE import | PASS | `Saved/Audit/melusina_wardrobe_contract_import.json`; five skeletal meshes use `/Game/Melodia/Characters/Melusina/SK_Melusina_Skeleton`, 465 referenced bones, approved materials, no WorldGrid references. |
| C++ build | PASS | `BS_GodFile` Development build succeeded; only existing warnings were reported. |
| Pawn mesh promotion | OPEN | `CharacterMesh0` was still the original `SK_Melusina` at the last live query. It must be changed to `SK_Melusina_V2_Body` after rollback evidence is captured. |
| Garment defaults | OPEN | The single existing `MelodiaWardrobeComponent` was present, but its default garment map was empty at the last live query. Add the four V2 defaults through the existing API. |
| Animation/hair preservation | READY TO VERIFY | `ABP_Melusina_Current`, hybrid locomotion BlendSpace, hair component/skeleton, sockets, collision, and gameplay settings were preserved in the implementation. Verify after rebuild. |
| PIE and visual QA | OPEN | Run the speed matrix, traversal/combat states, equip/unequip, materials, hair, and rollback checks. |

### ARP/export nuance

The final bind report records the required ARP exporter gate and the native contract finalizer. The temporary ARP module was incomplete during the last regeneration, so the recorded ARP gate evidence was reused and the final canonical hierarchy/export was completed with Blender's native FBX exporter. On the rebuild, rerun the true ARP preflight if the complete exporter module is available; do not overwrite the v22 source blend.

## Tonight's rebuild runbook

1. Confirm the UE editor is closed, the build is current, and no unrelated bulk-save process is running.
2. Re-run the V2 Blender preflight/export from a copy of `Melodia_Portfolio_Stage_v22_ZenRebuild_WIP.blend`. Require 465 canonical bones, underscore names, centimetre scale, seven helper drops, valid deform groups, normalized weights, no zero-weight vertices, and preserved morphs.
3. Run the actual-FBX validator against all five exports. Stop on any mismatch in the mesh bone table or hierarchy.
4. Run the importer in verify-only mode first. Confirm each piece is skeletal, uses the existing canonical skeleton, has approved material instances, and has no WorldGrid or placeholder references.
5. Capture rollback evidence from the pawn: original `SK_Melusina`, `ABP_Melusina_Current`, hybrid BlendSpace, hair mesh/component, socket setup, collision, wardrobe component count, and battle gate state.
6. Promote `CharacterMesh0` to `/Game/Melodia/Characters/Melusina/Outfits/V2/SK_Melusina_V2_Body`.
7. Configure the same single wardrobe component with default `Shirt`, `Skirt`, `Boots`, and `Accessories` references. Keep saved selections authoritative when present; defaults apply only when no saved selection exists.
8. Compile the Blueprint and require zero new Melusina errors. Save only the scoped pawn/wardrobe assets.
9. Verify animation and attachment invariants: `ABP_Melusina_Current`, `BS_Melusina_Locomotion_Hybrid`, hair runtime, sockets, collision, and gameplay settings.
10. Run PIE at speeds `0 / 150 / 180 / 300 / 420 / 540 / 630`; inspect idle, walk, run, sprint, jump, sword, hit, spell, death, hair attachment, material visibility, equip/unequip, and rollback.
11. Leave battle wardrobe disabled. Record the result under `Saved/Audit/` and update the tracked evidence note without staging unrelated worktree changes.

## Promotion guardrails

- Do not overwrite `/Game/Melodia/Characters/Melusina/SK_Melusina`.
- Do not create a new skeleton or use the V2Test static meshes or legacy `G:\MelusinaRigFinalSeparate` FBXs.
- Do not create a second mesh or wardrobe authority. The existing pawn mesh plus one `UMelodiaWardrobeComponent` remain authoritative; the legacy `MelodiaOutfitComponent` stays compatibility-only.
- Do not retarget the 42 Quaternius clips again. They remain on `SK_Melusina_Skeleton`.
- Do not introduce Chaos Cloth, MooaToon, NextCAS-UE, or battle ability behavior into the V2 promotion gate.

## Long-term roadmap

### Phase 1 — One outfit and lookbook gate

- Define one data-driven outfit record and register one fully passing demo outfit.
- Reuse `UMelodiaTokenWalletSubsystem`, save v2→v3 wardrobe fields, Golden-token costs, rarity weights, grant-ID deduplication, and refund-on-failure behavior.
- Build the minimal browser using the existing `.nikki-outfit-board` assets: grid, rarity/ownership state, equip action, lore, and paper-doll preview.
- Stop for owner review before registering the remaining 38 gacha outfits.

### Phase 2 — Catalog and presentation foundation

- Expand the outfit definition for slots, approved material instances, palettes, dye state, glow/evolution stages, ownership, acquisition, animation/presentation, clipping, hidden body zones, and audio profiles.
- Keep Substrate toon shading authoritative and benchmark material variants before any renderer change.
- Keep dynamic skirt cloth disabled until deformation, leader pose, and clipping QA are stable.

### Phase 3 — Presentation experiments

- Prototype photo poses, Control Rig/Aim Offset presentation, outfit-specific idle/pose layers, and lookbook/share-card output.
- Keep MooaToon deferred and NextCAS-UE isolated behind benchmark/evidence gates.
- Add terrain/outfit audio and effect profiles only after the catalog contract is stable.

### Phase 4 — T3D and controlled runtime wiring

- Continue the fail-closed commands in `Docs/T3D_Patterns/t3d.py`: `validate_wardrobe_nodes`, `inject_wardrobe_node`, `validate_wardrobe_catalog`, and `wire_wardrobe_battle_gate`.
- Preserve dry-run default, `--go` plus expected fingerprint, rollback graph export, compile-zero validation, graph assertion, save, re-export, and evidence under `Saved/T3D/`.
- Keep the data flow `TouchDesigner/LiveLink → 9876 → normalized T3D request → Monolith 9316 → Blueprint validation/mutation`, with OSC input 8000 and output 9000. Unavailable bridges fail closed.
- Do not enable the battle lane until the owner explicitly approves it and the first outfit has passed catalog, save/load, equip, preview, and PIE review.

## Exit criteria for the V2 promotion

Promotion is complete only when the five actual meshes pass the contract, the pawn resolves the V2 body, all four garments resolve through the one wardrobe component, the current AnimBP/hybrid BlendSpace and hair remain live, materials and morphs are visible, PIE passes the speed/state matrix, and rollback is proven by changing only pawn mesh/wardrobe references.

## Scoped git handoff

When staging is requested, stage only the Melusina/wardrobe scope: the V2 bind/validation/import tools, the relevant wardrobe/token/narrative C++ files, `Docs/Research`, `Docs/Plans`, `Docs/Architecture`, `Docs/UI`, `specs/wardrobe`, the T3D validator/health-check tooling, and explicitly approved V2 audit/export artifacts. The worktree contains unrelated dirty changes; never use broad `git add .`.
