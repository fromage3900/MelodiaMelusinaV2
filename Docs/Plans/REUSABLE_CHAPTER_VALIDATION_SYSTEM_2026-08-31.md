# Reusable Chapter Validation System — Rider + UE 5.8

**Date:** 2026-08-31  
**Status:** reviewed against Junie's Rider workflow; Shorewake/Starskiff pilot prepared

## Decision

Do not add a chapter manager or another progression authority. Each chapter is a data package over
the existing owners:

- QuillScript: authored narrative and seven notification verbs
- TurnBased JRPG template: combat, inventory, quests, results and saves
- `UMelodiaNarrativeSubsystem`: narrow typed bridge and idempotent narrative record
- wardrobe/traversal owners: outfit capabilities
- Oceanology: water/environment; Starskiff: traversal state
- Echo ledger: evidence authority

The reusable unit is a **chapter validation package**, not a new runtime system.

## Package contract

Every chapter supplies:

1. `specs/progression/<chapter>.v1.json`: IDs, prerequisites, beats, route, checkpoint and source refs.
2. Optional pillar manifests such as `specs/wardrobe/<chapter>.v1.json`.
3. A checked-in `.qsc` and a newer compiled `.uasset`.
4. Offline contract tests for schema, allowlist coverage and exactly-once authored notifications.
5. Native Rider automation under `Melodia.Chapter.<ChapterId>.*` for record/save/capability logic.
6. One PIE evidence manifest containing real input, before/after state, visible payoff, error count and
   screenshot paths.
7. Echo ledger rows only after the chapter acceptance route is proven live.

## Efficient Rider sequence

Use the same sequence for every chapter:

```text
offline spec tests
  -> closed-editor Development Editor build when headers/imports changed
  -> RiderLink focused Melodia.Chapter.<id> tests
  -> one editor / one :9316 listener
  -> compile + read back Quill asset
  -> Find Usages / Code Vision to confirm live hosts
  -> one serialized PIE route with real input
  -> save/restart/load when persistence is claimed
  -> evidence manifest + Echo row
```

Rider is the fast inspection/test surface; UE remains the asset and runtime authority. Code Vision
can confirm references but cannot prove that a level actor is loaded or that a player-facing route
works. PIE evidence remains mandatory.

## Shorewake / Starskiff pilot

### Green preparation

- `BS_GodFileEditor Win64 Development`: PASS on 2026-08-31.
- `Content.Python.Tests.test_shorewake_quest_contract`: 5/5 PASS.
- `Melodia.Quest.Shorewake`: 1/1 PASS in rebuilt WindowsEditor.
- `BP_Starskiff_MK2`, Shorewake skeletal assets, materials and authored specs exist.

### Fix before PIE

- Compile `Content/MelodiaIntegration/Narrative/Shorewake/MelodiaQuillShorewake.qsc` to a paired
  `.uasset`, then read back `SourceCode` and statements before saving.
- Reconcile stale paths in `wardrobe_shorewake_manifest.v1.json` with the live assets; its declared
  `/Game/Melodia/Characters/Melusina/Outfits/Shorewake/SK_DressShorewake` path does not match the
  current on-disk Shorewake assets.
- Remove stale chapter-number/P1 assumptions. `STARSKIFF_STATUS_2026-08-29.md` is authoritative:
  Starskiff is water/current traversal R&D and is not required by Faraway Mother.
- Confirm the Shorewake allowlist values from the live config CDO, not only `echo_allowlist.json`.

### Focused PIE acceptance

1. Start exactly one editor and confirm one listener on 9316.
2. Load the Sea Above route and start the compiled Shorewake Quill asset.
3. Complete dialogue through real UI input; prove exactly one quest/flag/reward commit.
4. Equip `Cos_ShorewakeDress`; prove the canonical save record and observable traversal capability.
5. Restart the process, load the canonical save and prove outfit/capability restoration.
6. Prove `flag.sea_above.starskiff_ready` gates the live Starskiff host.
7. Board through real input and verify Starskiff traversal state while Oceanology remains water authority.
8. Capture before/after JSON, error counts and a visible frame; only then record the corresponding gate.

## Promotion rule

After the Shorewake pilot, promote only the package naming, Rider test filter, evidence schema and
execution sequence. Chapter-specific actors, outfits, Quill beats and visible payoffs stay data/content.
This keeps future chapters repeatable without creating a parallel narrative, combat, wardrobe,
traversal or HUD authority.
