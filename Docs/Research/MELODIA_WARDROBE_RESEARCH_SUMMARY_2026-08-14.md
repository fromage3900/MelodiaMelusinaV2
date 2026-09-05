# Melodia Wardrobe Research Summary

## Decision summary

The wardrobe platform is a presentation and collection system first. The V2
Melusina deformation contract is the blocking art/runtime gate; the battle
wardrobe lane remains a named, disabled soft gate.

## Five research areas

1. **Outfit catalog and gacha** — target 39 records: one demo outfit and 38
   gacha outfits. Reuse `UMelodiaTokenWalletSubsystem`, the existing wardrobe
   save fields, weighted rarity, Golden-token pulls, grant-id deduplication,
   and refund-on-failure. Register one passing outfit before bulk registration.
2. **T3D text injection** — normalize external control into the existing
   fail-closed Monolith workflow. LiveLink uses port 9876; OSC uses 8000 inbound
   and 9000 outbound; Monolith editor mutation remains on its configured MCP
   endpoint. No external bridge may bypass fingerprint, compile, graph-assert,
   save, and evidence checks.
3. **NPR shaders** — existing Substrate toon materials are the production
   baseline. MooaToon is deferred pending a measured quality/performance gap;
   NextCAS-UE remains an isolated future cloth/blendshape experiment.
4. **Wardrobe to battle** — runtime capability exists, but Decision 043 keeps
   the gameplay axis deferred. `bEnableBattleWardrobe` defaults false and must
   be deliberately enabled later.
5. **UI/lookbook** — start with the existing `.nikki-outfit-board` assets:
   browser grid, paper-doll preview, rarity/ownership, equip, lore, resonance
   quiz hooks, and shareable-card extension points.

## Delegated analysis retained

The Qwen technical comparison and three-phase roadmap are represented here as
the current decision record: Phase 1 is catalog/gacha/browser, Phase 2 is
Substrate presentation with deferred alternatives, and Phase 3 is T3D/
TouchDesigner/lookbook control. The original 39-outfit catalog and owner gates
remain the source of truth; ignored runtime ledgers are evidence, not the only
documentation authority.

## Delegation/runtime provenance

The research delegation ledger is preserved in `Saved/router_ledger.jsonl`.
The Qwen hard-task outputs are captured in the tracked comparison/roadmap
brief, and AWS Bedrock access was verified under the `bedrock` profile for
future long-term gameplay scaffolding experiments. Bedrock is not a dependency
of the V2 mesh, Unreal import, or T3D mutation gates.

## Owner gates

- First passing outfit review before the remaining 38 are registered.
- Explicit approval before enabling wardrobe in battle.
- Explicit benchmark before replacing the Substrate baseline with MooaToon or
  making NextCAS-UE a runtime dependency.
