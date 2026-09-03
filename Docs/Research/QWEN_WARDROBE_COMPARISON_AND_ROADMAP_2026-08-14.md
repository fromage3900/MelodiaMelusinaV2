# Wardrobe Rendering Comparison and Three-Phase Roadmap

This is the tracked record of the delegated wardrobe findings. It is an
implementation guide, not a claim that every optional system is already live.

## MooaToon versus NextCAS-UE

MooaToon is the lower-risk presentation experiment: it can provide a coherent
toon ramp, outlines, and stylized lighting with relatively little runtime
surface area. It is attractive when the measured problem is line quality,
shadow readability, or per-material artistic control. Its tradeoff is that it
would introduce another shading convention beside the existing Substrate toon
materials, so migration cost and visual drift must be measured before adoption.

NextCAS-UE is the higher-capability but higher-risk experiment. Blendshape and
cloth-oriented deformation can improve skirt and garment motion, but it adds
simulation state, authoring dependencies, and more failure modes around
leader-pose skeletal meshes, morphs, and PIE determinism. It should not be a
dependency of the V2 deformation gate.

**Decision:** keep the existing Substrate toon instances as production
baseline; benchmark MooaToon only against a concrete quality/performance gap;
keep NextCAS-UE isolated behind a future cloth/blendshape spike.

## Three implementation phases

### Phase 1 — collection and lookbook (S/M)

1. Validate one demo outfit end to end: import, approved materials, equip,
   save/load, TokenWallet grant, rarity display, and browser review.
2. Stop for owner review at the first-outfit gate.
3. Register the remaining 38 gacha drafts only after the first outfit passes.
4. Use `UMelodiaTokenWalletSubsystem`, Golden-token pulls, weighted rarity,
   grant-id deduplication, and refund-on-failure.
5. Build the minimal browser grid and paper-doll preview using the existing
   `.nikki-outfit-board` styling contract. Lore, resonance, and share-card
   hooks remain presentation extensions, not new wardrobe authorities.

### Phase 2 — presentation (M/L)

1. Route approved Melusina material instances through the current Substrate
   toon path.
2. Verify body, shirt, skirt, boots, accessories, hair, morphs, and leader
   pose at the seven locomotion speeds.
3. Keep dynamic skirt cloth disabled until canonical skeletal deformation is
   stable.
4. Run a bounded MooaToon benchmark only if a visible or measured gap exists.
5. Keep NextCAS-UE as a separate experiment with no gameplay dependency.

### Phase 3 — T3D and external control (L)

1. Normalize TouchDesigner/LiveLink and OSC events into the versioned wardrobe
   T3D request schema.
2. Validate requests before they reach Monolith.
3. Use the safe-wire transaction: rollback graph, fingerprint, dry-run
   validation, mutation, compile-zero, graph assertion, save, re-export, and
   evidence.
4. Add bridge health checks and fail closed when LiveLink, OSC, or Monolith is
   unavailable.

## Owner decisions

- Enable wardrobe in battle only through the named soft gate.
- Approve bulk registration after the first outfit passes.
- Adopt MooaToon only after benchmark evidence.
- Start the lookbook with the existing outfit-board assets.
- Keep T3D writes explicit, fingerprint-protected, and dry-run by default.
