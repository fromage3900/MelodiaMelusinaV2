# Melusina V2 Wardrobe Platform Roadmap

## Gate 0 — canonical deformation

Use a copy of the bound v22 Blender stage. Repair null armature modifiers,
split the bound meshes into body, shirt, skirt, boots, and accessories, and
preserve or transfer weights from the v22 donors. Remap actual deform groups to
the 465-bone `SK_Melusina_Skeleton` contract, preserve morphs, export in
centimetres, and reject zero-weight vertices or helper-only groups.

Import only validated skeletal FBXs under `Outfits/V2/` against the existing
skeleton. Do not use the unskinned separate FBXs or the failed ARP candidate.
Promote the pawn only after reference-pose, locomotion, hair, material, and PIE
checks pass. The original body, ABP, BlendSpace, animation library, and hair
remain rollback assets.

## Phase 1 — collection and lookbook (S/M)

- Keep the catalog at 39 records: one demo plus 38 gacha records.
- Reuse TokenWallet, save v2→v3 fields, weighted rarity, Golden cost, and
  idempotent grants.
- Register one passing outfit, review it, then bulk-register the remaining 38.
- Build the browser grid and paper-doll preview from the existing CSS assets.
- Surface rarity, ownership, lore, equip state, and future resonance/share-card
  hooks without making UI a second wardrobe authority.

## Phase 2 — presentation (M/L)

- Use existing Substrate toon shading and approved Melusina material instances.
- Add visual QA for deformation, morphs, leader pose, hair, and materials.
- Keep dynamic skirt cloth off until skeletal deformation is stable.
- Benchmark MooaToon separately; defer integration by default.
- Keep NextCAS-UE isolated until a dedicated cloth/blendshape spike passes.

## Phase 3 — external control and automation (L)

- Add named T3D wardrobe commands for validation, node injection, catalog
  validation, and battle-gate wiring.
- Use dry-run by default and require an expected fingerprint plus `--go` for
  mutation.
- Normalize LiveLink/TouchDesigner and OSC messages into the versioned T3D
  request schema before sending them to Monolith.
- Record rollback exports, compile status, graph assertions, fingerprints, and
  bridge health in `Saved/T3D/`.

## Rollout rule

No phase may make the battle lane live implicitly. The only promotion switches
are the V2 pawn mesh/garment defaults and the explicitly named battle gate.
