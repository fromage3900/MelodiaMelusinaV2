# Melusina ↔ AIRI bridge architecture

**Status:** P0 remains PARTIAL; the game bridge has no live AIRI/PIE proof. Claireon workbench and
ElevenLabs v4 voice audition adapters are separate source-only scaffolds; neither has live runtime
integration or owner approval.
**Reviewed:** 2026-09-29 · **Target:** UE 5.8 and current AIRI Server SDK 0.12.0-beta.5.

## Authority map

| Surface | Owns | Bridge relationship |
|---|---|---|
| Melodia canon and authored content | Melusina identity, voice, world facts, established relationships | Source for the generated AIRI card; edits belong in canonical project data first. |
| `UMelodiaNarrativeSubsystem` and its record | Validated narrative flags, quest transactions, save synchronization | Remains the game’s canonical narrative/save authority. This P0 bridge never writes to it. |
| Existing Jev and authored gameplay systems | Bounded choices, deterministic reactions, combat/rhythm rules, safety gates | Remain the decision and execution owners. P0 only records a validated emote in debug state; any meaningful action needs its owning authored gate. |
| Unreal production Melusina | Gameplay, animation, combat, world simulation | Remains authoritative in game. P0 emits one semantic location event and reads an emote into a debug field. |
| AIRI | External conversation, configurable voice and perception modules, lightweight avatar presentation | A companion embodiment. AIRI chat/session context is transient and does not become Melodia canon or UE save data. |
| `MelodiaAiriBridge` relay | Versioned semantic transport and allowlisted intent queue | Local adapter only; no memory service or second game-state store. |

## Existing Melodia systems reused

- **Narrative and persistence:** `Source/BS_GodFile/MelodiaIntegration/MelodiaNarrativeSubsystem.*` already validates authored transactions and synchronizes the canonical record. The bridge does not call its mutation API.
- **Jev:** `Docs/Production/JEV_CANONICAL_WORKFLOW.md` keeps Jev in the director role: select among bounded authored candidates, then let the existing owner execute and verify. AIRI output cannot replace that boundary.
- **Phrase and TouchDesigner transport:** `UMelodiaPhraseBusSubsystem` and the Listening Field contract already own OSC/UDP `127.0.0.1:9002`. That musical stream is left intact; this bridge does not create a second phrase bus.
- **Unreal HTTP:** the game module already depends on Unreal HTTP/JSON/networking modules. The new `UWorldSubsystem` uses asynchronous HTTP requests and adds no module, project setting, or config change.
- **Rhythm, Phoenix/Monolith combat, instruments, Quill, and world state:** their current owners remain unchanged. The v1 schema has a few future semantic payloads, but only `melodia.world.location` is emitted by this source slice.

## AIRI implementation fit

AIRI’s current plugin architecture is multi-node and uses Eventa for cross-node events; its Server SDK exposes a client over AIRI’s WebSocket endpoint. Unreal sends JSON over loopback HTTP to a small Node relay, which sends AIRI a passive `context:update` and listens for `output:gen-ai:chat:message`. That extra local hop keeps Unreal’s side simple and non-blocking while avoiding a custom AIRI fork or a second direct WebSocket implementation.

The relay deliberately does not use `input:text` for world events. AIRI defines that event as a `chat-ingestion` consumer-group delivery, and open AIRI issue [#2305](https://github.com/moeru-ai/airi/issues/2305) reports that fresh stage sessions can drop external input events until reconnect. `context:update` is a separate event that AIRI’s stage context bridge ingests into its transient context store. The update informs the next ordinary chat turn; it does not autonomously invoke the model. This limitation is explicit until the current AIRI build is exercised end to end.

The external relay binds only to `127.0.0.1:8765`; its default AIRI SDK target is `ws://localhost:6121/ws` and can be changed with `AIRI_WS_URL`. The AIRI SDK dependency is pinned to `@proj-airi/server-sdk` `0.12.0-beta.5`. The SDK is beta and may change; the adapter isolates that churn from Unreal.

AIRI’s current character-card importer takes a ZIP whose root contains `manifest.json` and Character Card V3 `card.json`; it can optionally contain a display model. AIRI documents VRM as a display-model option. Chat, Speech, Hearing/transcription, and desktop Vision are separate configurable modules/providers, so voice or perception choices do not have to become part of the Melodia bridge contract.

References: [AIRI plugin architecture](https://github.com/moeru-ai/airi/blob/main/packages/plugin-sdk/docs/design/architecture.md), [Server SDK](https://github.com/moeru-ai/airi/blob/main/packages/server-sdk/README.md), [protocol event definitions](https://github.com/moeru-ai/airi/blob/main/packages/plugin-protocol/src/types/events.ts), [stage context bridge](https://github.com/moeru-ai/airi/blob/main/packages/stage-ui/src/stores/mods/api/context-bridge.ts), [reported fresh-session input issue #2305](https://github.com/moeru-ai/airi/issues/2305), [AIRI Character Card template](https://airi.moeru.ai/docs/en/docs/manual/tamagotchi/character-card-template), [AIRI setup and modules](https://airi.moeru.ai/docs/en/docs/manual/tamagotchi/setup-and-use/), and [AIRI audio setup](https://airi.moeru.ai/docs/en/docs/manual/config/audio).

## P0 data path

```text
UE world location
  -> opt-in UMelodiaAiriBridgeSubsystem
  -> POST 127.0.0.1:8765/v1/events (async, bounded JSON)
  -> Node validator and AIRI Server SDK context:update (replace-self)

AIRI output:gen-ai:chat:message containing one standard ACT emotion marker
  -> Node allowlist + 5/minute limiter + queue (maximum 8)
  -> GET /v1/intents by Unreal (async poll)
  -> Unreal envelope/payload/rate validation
  -> LastAcceptedDebugIntent only
```

Start the Unreal side only in a non-shipping build with `-MelodiaAiriBridge`. Without the flag the subsystem is not created. HTTP requests have a one-second timeout, run asynchronously, and a missing relay is treated as offline; there is no gameplay wait or save interaction. The Node service itself is optional and binds only to loopback.

The first emitted event is `melodia.world.location` with a semantic label for the known map. The protocol also recognizes phase, Melusina state, rhythm combo/accuracy, and Sir Melodious distance for a future owner-wired expansion. This bridge deliberately does not scrape actors or stream raw engine internals.

The only current AIRI-to-UE intent is `melusina.emote` with one of six enum values. The relay reads only an AIRI `ACT` marker from assistant output and rejects multiple markers, malformed values, and emotions outside the bridge enum. The card asks for subtle emotion markers where appropriate; a marker is still untrusted model output. Unreal stores an accepted value in a diagnostic property and writes a log line. No production expression, animation, combat, dialogue, Quill, save, filesystem, console, shell, reflection, or arbitrary Blueprint path is reachable.

Before any intent gains visible or gameplay effects, route it through the appropriate authored/Jev gate and game owner. A model response is not an execution authorization.

## State and persistence boundary

- **Canonical:** Melodia’s authored canon and existing UE narrative/save records.
- **Transient bridge state:** current event envelope, queue entries, diagnostics, and AIRI session context. Restart clears them; they do not commit to a save.
- **AIRI-local:** conversation history, selected speech/transcription provider, and current companion presentation under AIRI’s own controls.
- **Not in P0:** a shared `MelusinaStateService`, Railway relay, cross-session memory merge, or copying AIRI conversations into UE saves.

The bridge sends only session context; AIRI memory is not a source of truth. If a future shared service is introduced, it needs an explicit field-level ownership and consent contract before either runtime can write it.

## AIRI Oracle and Claireon workbench boundary

The future Oracle is an observer of explicitly supplied UE/session facts. It may summarize those
facts, surface unknowns, propose a named owner-system route, and coordinate a review; it cannot
invent current narrative truth, write canonical memory, or become a second rhythm, combat, save, or
narrative authority. Game facts still arrive through their existing owner seams and remain transient
when passed into AIRI.

The separate workbench follows the existing owner handoff: read-only `project.status`,
`project.diff`, `project.context`, and `ue.status`, plus `ue.propose`. The new
`Tools/AIRI/ClaireonWorkbench/authoring-gate.mjs` implements only deterministic validation and
proposal receipts. Its allowlist is `asset.inspect` and `asset.propose_change`, targeting scoped
Melodia package paths; it explicitly denies raw Python, console, arbitrary asset/path, and
source-control operations. A proposal can be eligible only when both editor and asset ownership
are released and the source-control mode is read-only. Receipts bind the exact proposal digest,
remain `OWNER_REVIEW_REQUIRED`, and always say `executed: false`. The module has no network or
Claireon client, no approval endpoint, and no asset-write route. The human reviews the exact target
and operation, then separately operates the approved Claireon catalog tool. Git/P4 mutation still
requires a distinct exact owner request. This is a source scaffold, not a live workbench or PIE
proof.

Claireon's documented MCP surface is `tool_search` plus `python_execute`; the latter grants full
editor Python, filesystem, and network access. The AIRI path does not call or expose it. Keep the
Claireon port local and firewall-protected according to the plugin's security guidance.

## Character and avatar path

`Tools/AIRI/MelusinaCard/generate_card.py` reads the existing persona soul, voice bible, and dream-state prologue, records their hashes, and emits the AIRI card package. The package is a projection: update canonical docs first, then regenerate. It does not contain game saves or runtime state.

For a later VRM, derive a lightweight companion from an approved character source in Blender. Retain identity-defining silhouette and facial expression; remove UE-specific controllers, gameplay sockets, FluidNinja/runtime effects, and nonportable material dependencies; reduce geometry/material count; bake needed textures; map a humanoid VRM skeleton and expression set; validate scale, axes, eye/mouth motion, and AIRI desktop display. Keep the production UE rig untouched and make source selection an explicit future asset gate.

Keep voice provider swappable. AIRI's configured Speech module and Hearing transcription remain
separate from game state and the game bridge. The standalone `Tools/AIRI/MelusinaVoicebank/voicebank.mjs`
provides a dry-run-by-default ElevenLabs spoken-line audition request adapter and local hashed
artifact receipt. It supports the current ElevenLabs `eleven_v4` and `eleven_v4_turbo` TTS model IDs;
it does not clone/train a voice, upload source audio, or call the provider unless a future caller
explicitly enables network access. Credentials are read from `ELEVENLABS_API_KEY` and are never
written into source or receipts. Outputs remain `AUDITION_ONLY_NOT_APPROVED`; owner audition and
provenance review are required before any promotion. This is not a singing-bank pipeline.

Official provider references: [ElevenLabs models](https://elevenlabs.io/docs/overview/models),
[ElevenLabs create speech API](https://elevenlabs.io/docs/api-reference/text-to-speech/convert),
and [ElevenLabs v4 Text to Speech guide](https://elevenlabs.io/docs/eleven-creative/playground/text-to-speech).

## P1 sequence

1. In an owner-approved closed-editor window on the existing `main` checkout, build the UE editor target and fix any engine-version compile errors.
2. Install the pinned Node dependency; run the relay beside AIRI; launch PIE in `L_MelusinaMorning` with `-MelodiaAiriBridge` and verify that AIRI receives `Melodia's Morning` as transient context.
3. In an ordinary AIRI conversation, request a subtle expression and verify the generated ACT marker reaches the relay, then verify UE validation, rate limit, and debug-only receipt.
4. Repeat with AIRI/relay absent and confirm normal PIE startup and gameplay continue with no blocking request.
5. Add semantic emissions only by subscribing to existing state-owner events (for example, rhythm judgment or companion distance), then pass authored/Jev gates before any response reaches production animation or gameplay.
6. Review the SDK against its then-current stable API before upgrading the beta pin; keep the VRM export and speech provider as separate approval/evidence lanes.

## Limits and risks

- No AIRI process or live SDK session was available in this P0 implementation; SDK forwarding and Unreal receipt are not claimed as runtime proof.
- The UE subsystem has not yet been compiled against UE 5.8. Its activation, async transport, and offline behavior still need a PIE check.
- The ACT-output contract is based on AIRI’s documented marker system and the current Server SDK event types; whether the pinned runtime exposes raw ACT markers on `output:gen-ai:chat:message` still needs a live compatibility check.
- The AIRI HTTP listener is loopback-only, but any local process can address it. It has no authentication token on the UE-to-relay HTTP leg; keep it local and do not bind it to LAN interfaces.
- P0 emits location only; semantic instrument, rhythm, encounter, narrative, and proximity emitters remain unimplemented.
