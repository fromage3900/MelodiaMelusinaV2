# Melusina ↔ AIRI P0 acceptance

**Overall: PARTIAL.** Design, protocol, generated character-card scaffold, and a bounded vertical slice are present on `feat/melusina-airi-bridge-p0`. The full UE 5.8 editor target now builds successfully. No live AIRI SDK round trip or PIE session was run, so source and build evidence is not runtime proof.

Status values are `PASS`, `PARTIAL`, `BLOCKED`, and `NOT STARTED`. `PARTIAL` means the implementation or source/build evidence exists but its acceptance proof is incomplete.

| # | Acceptance criterion | Status | Evidence / limit |
|---:|---|---|---|
| 1 | AIRI architecture reviewed against current implementation | PASS | Official plugin architecture, Server SDK, Character Card V3 importer, VRM display-model, and module/provider docs reviewed; sources linked in `MELUSINA_AIRI_ARCHITECTURE.md`. SDK pinned to the reviewed beta version. |
| 2 | Existing Melodia architecture inspected | PASS | Read Jev workflow, Listening Field contract, narrative subsystem, character voice/persona docs, and current HTTP/module setup. Reuse map recorded in architecture doc. |
| 3 | Bridge design document exists | PASS | `Docs/AIRI/MELUSINA_AIRI_ARCHITECTURE.md`. |
| 4 | Versioned event schema exists | PASS | JSON Schema, executable Node validator, transport contract, and tests define protocol v1. |
| 5 | Unreal can emit at least one semantic Melodia event | PARTIAL | `UMelodiaAiriBridgeSubsystem` serializes and asynchronously posts `melodia.world.location`; it is opt-in and shipping-disabled, and the UE 5.8 editor target compiles and links. PIE emission is unverified. |
| 6 | Lightweight external bridge/plugin can receive it | PARTIAL | Node loopback relay validates/posts a v1 event through the AIRI SDK shape; automated relay tests pass. Dependency install and live AIRI SDK receipt are unverified. |
| 7 | Constrained AIRI-side intent can return to Unreal | PARTIAL | The relay extracts one allowlisted emotion from AIRI's standard ACT marker in `output:gen-ai:chat:message`, then queues and polls the typed intent. Parser/relay tests pass; no live SDK-to-UE round trip, and raw ACT delivery on the pinned runtime is unverified. |
| 8 | Unreal validates before doing anything | PARTIAL | Compiled source validates envelope, version, UUID, timestamp, exact type/payload, enum, and rate limit before setting debug fields. Runtime receipt/rejection behavior is unverified. |
| 9 | AIRI offline has zero effect on ordinary gameplay | PARTIAL | Subsystem is opt-in, shipping-disabled and async with one-second timeouts; no gameplay/save call exists. Runtime startup/offline behavior still needs PIE proof. |
| 10 | No major production system rewritten | PASS | Changes are isolated to a new subsystem, external relay, docs, and generated card. Existing narrative, Jev, phrase bus, rhythm/combat, and hero asset sources were not edited by this work. A separately dirty 130-byte `BP_Melusina.uasset` LFS-pointer path was detected in the worktree; its provenance is unknown and it is excluded from all bridge staging. |
| 11 | No arbitrary LLM-to-Unreal execution path | PASS | One typed emote enum reaches debug state only; no console/reflection/Blueprint/filesystem/shell/save/gameplay executor exists. |
| 12 | Next VRM/voice/character-card steps documented | PASS | Blender-derived lightweight VRM path, provider-swappable voice boundary, card generator, and P1 steps are documented. |

## Verification performed

- `npm test` (`node --test --test-isolation=none`): **12/12 passing** (protocol validation, malformed/unknown-version handling, AIRI ACT marker allowlist, rate limits, relay forwarding, offline relay behavior, queue behavior).
- Node syntax checks: **PASS** for `bridge.mjs` and `relay.mjs`.
- Character-card generator: generated manifest/card/ZIP and read-back checked their JSON and exact root-file package structure.
- The repository pre-commit policy rejects ZIP files, so the verified `Melusina.airi-card.zip` is kept as a local generated artifact; the generator, JSON card, and manifest are the committed sources.
- UE 5.8 editor target build: **PASS** (`BS_GodFileEditor Win64 Development`, isolated worktree, `-MaxParallelActions=3`; UBT result `Succeeded`, 729.33 seconds). The bridge translation unit compiled and the `UnrealEditor-BS_GodFile.dll` linked. Two UE 5.8 API mismatches were fixed: `FTSTicker::FDelegateHandle` and the return-value `FJsonObject::TryGetField` API.
- Build-only local dependencies were supplied inside the worktree: Oceanology descriptor/source/matching editor binaries and Claireon descriptor/source. Their large content directories were not copied; the active checkout and editor were not modified. Existing plugin deprecation/conversion warnings remain outside this bridge change.
- PIE connection, AIRI live receipt/response, and the offline runtime scenario are **not proven**.

## Safe P1 gate

Run the relay and AIRI locally, prove the Sea Above/Morning context in AIRI, pass a generated ACT emotion marker back to the debug property, and repeat with AIRI offline in PIE. Only after those steps should event owners be wired for rhythm/instrument/proximity or any visible UE response.
