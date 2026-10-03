# Melodia ↔ AIRI protocol v1

**Schema:** `Tools/AIRI/MelodiaBridge/melodia-bridge-v1.schema.json`
**Executable validator:** `Tools/AIRI/MelodiaBridge/protocol.mjs`
**Transport owner:** `Tools/AIRI/MelodiaBridge/relay.mjs`

## Envelope

Every event and intent has exactly these fields:

```json
{
  "id": "a-unique-per-message-id",
  "type": "melodia.world.location",
  "version": 1,
  "timestamp": "2026-09-29T12:00:00.000Z",
  "payload": { "location": "Sea Above" }
}
```

`id` is 1–80 ASCII letters, digits, dot, underscore, colon, or hyphen. `version` must be integer `1`. `timestamp` must parse as ISO 8601 and be at most 40 characters. `payload` must be an object. Unknown envelope fields fail validation. A complete HTTP request body may be at most 8,192 bytes.

## Recognized Unreal → AIRI events

| Type | Payload | Source status |
|---|---|---|
| `melodia.world.location` | `{ "location": "Sea Above" }` | Emitted for known worlds by P0. |
| `melodia.world.phase` | `{ "phase": "exploration" }` (`exploration`, `rhythm`, `combat`, `narrative`) | Schema and validator only. |
| `melodia.melusina.state` | `{ "state": "Exploring" }` (`Exploring`, `Interacting`, `Performing`, `InRhythm`, `InCombat`, `Unavailable`) | Schema and validator only. |
| `melodia.rhythm.combo` | `{ "combo": 34, "accuracy": 0.96, "instrument": "Sonic Scepter" }` (`instrument` optional) | Schema and validator only. |
| `melodia.sir_melodious.distance` | `{ "distance_cm": 420, "state": "nearby" }` (`state` optional: `nearby`, `following`, `distant`, `unavailable`) | Schema and validator only. |

String labels are 1–80 Unicode letters/numbers, spaces, periods, apostrophes, or hyphens. Numeric values must be finite. Combo must be a nonnegative safe integer; accuracy is in `[0,1]`; companion distance is in `[0,100000]` cm. Recognized payloads reject extra fields.

An unknown event type with an otherwise valid v1 envelope is acknowledged as ignored. A malformed envelope/payload is rejected; an unsupported version is rejected with HTTP 409. This allows a newer producer to coexist without an older relay executing anything it does not understand.

## AIRI → Unreal intent

P0 allows exactly one intent:

```json
{
  "id": "694b0b76-2d2e-4f35-9247-3b6741e5a76d",
  "type": "melusina.emote",
  "version": 1,
  "timestamp": "2026-09-29T12:00:01.000Z",
  "payload": { "emotion": "happy" }
}
```

Allowed emotions are `neutral`, `happy`, `curious`, `sad`, `surprised`, and `determined`. The relay listens to AIRI SDK `output:gen-ai:chat:message` and extracts at most one standard `ACT` marker of the form `<|ACT emotion="happy" intensity="0.7"|>`. The intensity is checked in `[0,1]` but is not sent to Unreal. Ordinary assistant text is ignored; malformed, duplicate, or unlisted `ACT` markers are rejected. No text becomes an executable command.

World state is sent to AIRI as a transient `context:update` event with stable `contextId: "melodia.world"` and `strategy: "replace-self"`. It updates the current AIRI context and does not itself trigger a model response. AIRI can use it in the next ordinary conversation turn.

The relay limits events to 30/minute, intents to 5/minute, and the intent queue to 8 entries. Unreal independently caps accepted emotes at 5/minute. Malformed, unknown-version, unlisted, and rate-limited intents are rejected and counted. A valid emote changes only the bridge's debug state.

## HTTP endpoints (loopback only)

The Node relay binds to `127.0.0.1:8765` by default.

- `GET /v1/health` returns protocol version, AIRI connection state, counters, last event types, and queue depth.
- `POST /v1/events` accepts a versioned Unreal event; returns `202` for accepted or ignored messages, `400` malformed input, `409` unsupported version, or `429` rate limit.
- `GET /v1/intents` returns one queued intent or `null` inside a `melodia.bridge.intent_poll` version-1 response defined by `$defs.intentPollResponse` in the schema.

Unreal uses asynchronous `FHttpModule` calls with one-second timeouts and polls every two seconds only when started with `-MelodiaAiriBridge`. It never waits on the relay from the game thread. A missing relay means no event delivery and no intent; ordinary game logic and saves continue independently.

## AIRI authoring proposals (separate workbench surface)

Developer proposals do **not** use the `melodia.*` game protocol or the game relay. The source
scaffold is `Tools/AIRI/ClaireonWorkbench/authoring-gate.mjs`, a pure validation and receipt module;
it is not connected to AIRI, Claireon, Unreal, Git, or Perforce. It accepts only
`asset.inspect` and `asset.propose_change` proposal kinds, for scoped `/Game/Melodia/...` or
`/Game/MelodiaIntegration/...` targets, and rejects maps, levels, ABPs, protected Melusina assets,
path traversal, console/Python execution, and source-control operations.

Eligibility requires an explicit released editor owner and asset owner, with source control marked
read-only. An accepted receipt is `OWNER_REVIEW_REQUIRED`, includes a canonical SHA-256 proposal
digest, and records `executed: false`; duplicate submission is idempotent and ID reuse with changed
content is rejected. No AIRI output can create an approval. A human must inspect the exact proposal
and use Claireon's existing catalog/workflow separately. This gate does not issue Claireon calls,
write assets, save packages, or authorize Git/P4 changes. The wider workbench remains observer →
proposal → owner executes; only the proposal gate has source scaffolding in this slice.

Claireon's `python_execute` runs editor Python with filesystem and network access, so it is not an
allowlisted operation and is not exposed by this proposal gate. Do not treat a proposal receipt as
live UE proof or as authority to invoke an editor tool.

## ElevenLabs speech audition adapter

`Tools/AIRI/MelusinaVoicebank/voicebank.mjs` is a separate spoken-line audition adapter, not a
singing voicebank trainer or a runtime voice integration. It accepts authored text and a configured
ElevenLabs voice ID; it accepts no source-audio upload, voice-cloning, or training input. The
supported current v4 model IDs are `eleven_v4` and `eleven_v4_turbo`; use the official model list and
TTS API contract linked in the architecture doc. Requests are dry-run by default and keep the API
key in `ELEVENLABS_API_KEY` outside the repository. The artifact writer emits an MP3 and a hashed
`AUDITION_ONLY_NOT_APPROVED` receipt and refuses to overwrite an existing output. No candidate is
promoted to the production voicebank or AIRI/UE runtime without provenance review and owner
listening.

## Authority and rejection behavior

The schema does not grant authority. Unreal validates the poll envelope, exact intent type, UUID, version, timestamp, exact payload keys, allowlisted emotion, and local rate limit before updating a debug property. It has no console, Blueprint reflection, filesystem, shell, save, spawn/destroy, actor-property, combat, or narrative executor path. Any future visible/gameplay intent needs its owning deterministic/authored gate (including Jev where that system owns the decision) and separate tests before it can execute.
