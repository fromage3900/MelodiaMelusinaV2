# Unreal MCP ↔ Monolith Governance for Melodia

**Date:** 2026-08-31  
**Project:** Melodia Melusina / UE5.8  
**Status:** R&D governance spec  
**Applies to:** official Unreal MCP, Monolith, T3D injectors, Melodia MCP server, editor-mutating agents.

---

# 1. Why this exists

Melodia already has a mature editor-automation surface:

- `deploy/melodia_mcp_server.py`
- `Tools/mcp_policy.py`
- `specs/mcp_tool_policy.v1.json`
- Monolith/T3D/editor-query tooling

UE5.8 now also ships an official Experimental Unreal MCP implementation.

The danger is not lack of capability. The danger is creating **multiple independent mutation authorities** over one editor.

This document defines one governance model so official Unreal MCP can be evaluated without weakening the existing safety architecture.

---

# 2. Verified properties of official Unreal MCP

Epic's UE5.8 documentation states that Unreal MCP:

- is Experimental;
- embeds an MCP server in the Unreal Editor process;
- exposes editor functionality as MCP tools;
- supports toolsets, including PCG-oriented tooling;
- binds locally by default;
- has no authentication layer;
- is not designed for remote use;
- executes tool calls on the game thread serially;
- has incomplete/changing APIs and data formats.

Primary sources:

- https://dev.epicgames.com/documentation/unreal-engine/unreal-mcp-in-unreal-editor
- https://dev.epicgames.com/documentation/unreal-engine/working-with-pcg-and-llms-using-unreal-mcp-in-unreal-engine
- https://dev.epicgames.com/documentation/unreal-engine/API/PluginIndex/ModelContextProtocol
- https://dev.epicgames.com/documentation/unreal-engine/API/PluginIndex/PCGToolset

---

# 3. Repository baseline

The current Melodia policy layer already provides desirable properties:

## Default deny

`specs/mcp_tool_policy.v1.json` declares a default-deny model.

## Operation classes

Examples include:

- `read`
- `verify`
- `mutate`
- `route`

## Approval levels

The current policy distinguishes:

- `none`
- `editor`
- `owner`

## Forbidden path tokens

The policy can reject mutation against known-dangerous paths.

## Raw editor command denial

The policy currently denies unrestricted raw UE editor command execution and directs mutation through verified surfaces.

This architecture should remain the outer policy boundary even if official Unreal MCP proves useful.

---

# 4. Single mutation authority rule

At any moment, one editor gets exactly one active mutation authority.

Allowed:

```text
Agent
  -> Melodia policy
  -> Monolith/T3D
  -> Unreal Editor
```

or

```text
Agent
  -> Melodia policy
  -> official Unreal MCP
  -> Unreal Editor
```

Forbidden:

```text
Agent A -> Monolith write
Agent B -> Unreal MCP write
Agent C -> T3D write
```

against the same live editor state.

Read-only inspection can be parallel only where the underlying tool is safe and does not implicitly trigger writes/cooks.

---

# 5. Official MCP is a transport/capability provider, not the policy owner

Melodia should not treat "Epic ships the tool" as equivalent to "every tool is safe for this project."

The desired architecture is:

```text
user/agent request
       |
       v
Melodia operation classifier
       |
       v
mcp_tool_policy.v1
       |
       +--> denied -> stop + reason
       |
       v
selected transport
   Monolith OR Unreal MCP
       |
       v
precondition check
       |
       v
single mutation
       |
       v
verification/readback
       |
       v
evidence transcript
```

---

# 6. Phase-1 official Unreal MCP allowlist

The initial benchmark should expose only a tiny surface.

## Read / inspect

- selected actor inspection;
- selected asset inspection;
- PCG graph inspection;
- PCG point/Data View inspection;
- build/status query;
- automation test listing.

## Controlled mutation

- spawn one known R&D actor class;
- create/configure one R&D material instance;
- add one harmless debug branch to an isolated R&D PCG graph;
- run one known automation test;
- modify one explicitly selected sandbox actor parameter.

## Explicitly forbidden in Phase 1

- delete actors/assets;
- rename/move assets in bulk;
- edit production maps;
- enable/disable plugins;
- source-control operations;
- arbitrary Python/shell bridge;
- package/build configuration mutation;
- unattended recursive graph rewriting;
- simultaneous Monolith/T3D mutation.

---

# 7. PCG-specific reason to test official Unreal MCP

Epic's PCG MCP guidance includes skills/tooling intended for:

- PCG graph generation;
- PCG Biome Core;
- Mesh Partition / Mesh Terrain;
- shape grammar;
- mesh-surface instancing;
- Data View inspection.

This gives official MCP one potentially unique value:

> It may understand new UE5.8-native PCG concepts sooner and more directly than project-specific automation surfaces.

That is a testable advantage, not an adoption assumption.

---

# 8. Benchmark: official MCP vs Monolith/T3D

**Map:** `LV_RND_MCP_PCG_Sandbox`

**Graph:** `PCG_RND_MCP_AttributeDebug`

## Task

Given selected PCG sandbox content:

1. inspect the graph;
2. identify a point stream;
3. add a debug-only scalar attribute branch;
4. expose/inspect the resulting values;
5. run a validation step;
6. save only the sandbox asset if approved.

## Run A

Use existing Melodia/Monolith/T3D path.

## Run B

Use official Unreal MCP PCG toolset/skill.

## Record

- setup minutes;
- command count;
- failed tool calls;
- accidental changes;
- graph correctness;
- verification quality;
- token/context burden where observable;
- total time;
- recovery from one intentionally invalid request;
- transcript readability.

## Decision

Official MCP is promoted only if it is meaningfully safer/faster/clearer for at least one UE5.8-native workflow.

---

# 9. Transaction envelope

Every editor mutation request should be represented conceptually as:

```json
{
  "request_id": "uuid-or-stable-id",
  "transport": "unreal_mcp",
  "tool": "...",
  "operation": "mutate",
  "approval": "editor",
  "target": "/Game/...",
  "precondition": {
    "expected_asset": "...",
    "expected_fingerprint": "..."
  },
  "mutation": {},
  "verification": {},
  "rollback": {}
}
```

The exact runtime representation can differ, but these concepts must exist before broad adoption.

---

# 10. Idempotency rules

Agent/editor automation must distinguish:

## Naturally idempotent

- set scalar property to known value;
- inspect asset;
- run validation;
- set material parameter to exact value.

## Conditionally idempotent

- create actor if actor with stable R&D ID does not already exist;
- add PCG node if node tagged with stable test ID is absent.

## Non-idempotent / dangerous

- duplicate actor;
- append node blindly;
- randomize layout;
- create unique assets without deterministic naming;
- destructive reparenting.

Phase 1 should strongly prefer naturally idempotent operations.

---

# 11. Precondition checks

Before any mutation, verify:

- editor is in expected project;
- expected map is open;
- target is in R&D path;
- asset exists and is the expected class;
- no PIE/session mode conflict;
- one mutation lock is held;
- current fingerprint/revision is known if graph-sensitive;
- operation is allowed by policy.

Failure of a precondition means **no write**.

---

# 12. Postcondition checks

After mutation, verify:

- target still exists;
- asset class unchanged unless intended;
- graph compiles where applicable;
- expected node/property exists;
- no unexpected siblings were changed;
- error count did not increase;
- fingerprint differs only in expected region where practical;
- save state is known.

A tool call returning `success` is not enough.

---

# 13. Transcript standard

Every official Unreal MCP spike should commit a compact transcript summary:

```markdown
## MCP Mutation Transcript

- request_id:
- date:
- UE build:
- MCP plugin build:
- transport:
- map:
- target:
- policy decision:
- preconditions:
- tool calls:
- postconditions:
- unexpected changes:
- rollback performed:
- result:
```

Do not commit huge raw logs unless needed for a bug report. Preserve enough information to reproduce the workflow.

---

# 14. Local-only / no-auth consequence

Because official Unreal MCP is local and unauthenticated by default:

- do not expose it directly to LAN/WAN;
- do not treat it as a remote-agent daemon endpoint;
- do not bind it externally as part of a convenience setup;
- keep remote orchestration terminating at a controlled Melodia service/policy layer if remote workflows are later needed.

A local-only R&D surface is acceptable. A remotely exposed unauthenticated editor mutation endpoint is not.

---

# 15. Game-thread serialization consequence

Epic documents serial tool execution on the game thread.

This is useful because it reduces internal concurrent mutation, but it does **not** solve cross-transport concurrency.

A Monolith write and an Unreal MCP write can still conceptually race from separate clients unless Melodia enforces a higher-level lock.

## Required project lock

Define one logical resource:

```text
MEL_EDITOR_MUTATION_LOCK
```

The exact implementation can be file lock, coordinator state, or editor-side lock, but every mutating transport must respect it before production use.

---

# 16. Promotion ladder

## WATCH
Official Unreal MCP exists and is relevant.

## SANDBOX
Tiny allowlist; no production writes.

## OPTIONAL TRANSPORT
Proves a unique advantage for specific UE5.8-native tasks and passes policy/readback tests.

## STANDARD TRANSPORT
Only after:
- stable build pinning;
- robust allowlist;
- lock integration;
- transcript/evidence standard;
- rollback behavior;
- second-machine verification.

It should never become "all editor tools exposed by default."

---

# 17. Immediate implementation checklist

- [ ] Add official Unreal MCP to the toolchain version/license ledger.
- [ ] Record exact plugin names enabled: ModelContextProtocol, Toolset Registry, selected toolsets.
- [ ] Do not enable All Toolsets for the first constrained security test unless needed to discover required capabilities.
- [ ] Create `LV_RND_MCP_PCG_Sandbox`.
- [ ] Create one disposable PCG graph.
- [ ] Define the Phase-1 allowlist in project docs before executing mutations.
- [ ] Compare against current Monolith/T3D path.
- [ ] Commit transcript/result.
- [ ] Decide ADOPT-OPTIONAL / PARK / REJECT.

---

# 18. Bottom line

Official Unreal MCP is valuable because Epic can expose new UE5.8-native workflows such as PCG/Biome/Mesh Partition concepts directly to agents.

Melodia's existing policy, evidence, and single-writer discipline are valuable because official MCP intentionally exposes powerful editor capability and is still Experimental.

The correct integration is to combine those strengths, not replace one with the other.
