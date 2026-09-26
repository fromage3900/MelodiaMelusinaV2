# TONIGHT — Pi + Muselinn + Unreal MCP + Hermes + Universe Foundry

**Fast entrypoint:** this file.  
**Goal:** get the PC into a safe state where Hermes/Pi can execute the existing Faraway Mother Universe Foundry mission through typed Unreal MCP tools, with one writer and evidence gates.

## 0. Rules before touching the editor

- Work from current `main`. Do **not** merge the old `feat/universe-foundry-v0-1-20260922` branch.
- Universe Foundry describes the mission; it does not replace World Compiler, SaveGame, Hython, Unreal, Hermes, or Jev ownership.
- Start read-only. One UE writer only. No concurrent editor mutations.
- Do not create a second MPC, World Compiler, save owner, OSC bridge, or gameplay authority.
- The committed Faraway delta is a fixture. It cannot certify persistence.
- Human promotion gate remains in force for visual/gameplay changes.

## 1. PC bootstrap — Hermes operator first

Open PowerShell in the Melodia repo root and sync current main:

```powershell
git switch main
git pull --ff-only
git status
```

Launch the existing Hermes TUI from the repo using the project's normal Hermes install:

```powershell
hermes --tui
```

If `hermes` is not on PATH, stop here and repair/use the already-installed project Hermes environment. Do not install an unrelated replacement package.

In Hermes, point the operator at **this file** and `Docs/Production/UNIVERSE_FOUNDRY_CONTRACT.md`.

## 2. Install/launch Pi + Muselinn

Verify Node/npm first:

```powershell
node --version
npm --version
```

Use the canonical Pi installation already chosen for this workstation if present. Verify:

```powershell
pi --version
```

Then install the Muselinn harness package using its current upstream instructions. Do not guess a package name if upstream has changed; verify before installation.

Launch Pi **from the Melodia repo root**.

Initial policy:
- plan/read-only mode first;
- swarm OFF;
- hard budget;
- no UE mutation until MCP discovery succeeds;
- one writer when mutation is promoted.

## 3. Unreal 5.8 MCP

In UE 5.8:

1. Edit -> Plugins -> enable **Unreal MCP**.
2. Enable **All Toolsets** (Toolset Registry dependency follows automatically).
3. Restart Unreal.
4. Edit -> Editor Preferences -> Model Context Protocol.
5. Enable **Auto Start Server**.
6. Keep loopback/default endpoint unless occupied: `http://127.0.0.1:8000/mcp`.

In the UE console:

```text
ModelContextProtocol.GenerateClientConfig All
```

This should generate supported client configuration in the project root. The Unreal server is local-only by default and has no authentication: do not expose port 8000 externally.

Optional protocol sanity check:

```powershell
npx @modelcontextprotocol/inspector
```

Point Inspector at `http://127.0.0.1:8000/mcp` using Streamable HTTP.

### MCP PASS gate

Before any mutation, the connected client must successfully:
1. list/discover Unreal toolsets;
2. inspect the current editor/selection or another harmless read;
3. return structured data without an editor error.

If this fails: HOLD. Fix MCP before involving Foundry.

## 4. Universe Foundry preflight

Run:

```powershell
python Tools/test_universe_foundry.py

python Tools/universe_foundry.py validate `
  --genome specs/universe/faraway_mother.world_genome.v1.json `
  --delta specs/universe/faraway_mother.resolved_demo.world_delta.v1.json

python Tools/universe_foundry.py compile `
  --genome specs/universe/faraway_mother.world_genome.v1.json `
  --delta specs/universe/faraway_mother.resolved_demo.world_delta.v1.json
```

Record the generated `Saved/UniverseFoundry/faraway_mother/<mission_id>/mission.json`.

Compile the same inputs again. The mission id and DAG must be identical.

If tests/validation/determinism fail: HOLD. Do not let an agent compensate by editing runtime content.

## 5. Give Hermes/Pi the mission

Use this operator instruction:

> Read `Docs/Production/UNIVERSE_FOUNDRY_CONTRACT.md`, this launch plan, and the generated Faraway Mother `mission.json`. Treat the mission DAG and its authority fields as constraints. Start read-only. Discover the available Unreal MCP toolsets and map mission tasks to existing Melodia owners. Do not create replacement architecture. Do not mutate Unreal until the MCP read gate and Foundry deterministic compile gate pass. Keep swarm disabled for editor writes. For every action, report mission task id, owner, tool/capability used, evidence produced, and PASS/HOLD. Stop rather than inventing missing asset paths, gameplay ids, or authority.

## 6. First live canary — deliberately tiny

Success tonight does **not** mean completing World Zero.

Target:

```text
Foundry deterministic compile
  -> harness reads mission DAG
  -> Unreal MCP read succeeds
  -> Jev receives ONE authored closed-set decision
  -> existing owner executes at most ONE bounded legal task
  -> viewport/log/tool evidence captured
  -> result mapped back to mission task
  -> PASS or HOLD
```

For the first Jev call, use only a decision already authored in the genome:
- hero resolution visual: SILK_BLOOM / PEARL_RELEASE / LACE_AFTERIMAGE / HOLD
- or post-resolution ecology: PEARL_MOTHS / BROCADE_FLOWERS / SILK_VINES / HOLD

Jev selects. It does not mutate Unreal.

## 7. Mutation permissions

**READ:** tool discovery, asset/actor/level inspection, current state, logs.  
**BUILD:** deterministic Foundry/World Compiler/Hython source outputs.  
**STAGE:** one bounded UE editor mutation after explicit promotion.  
**PLAY:** PIE/automation validation.  
**PROMOTE:** human approval + independent evidence.

Do not let multiple Muselinn workers issue overlapping UE tool calls. Unreal MCP serializes editor tool invocation on the game thread; parallel workers may investigate source/docs, but there is one editor writer.

## 8. Tonight's finish line

Call the experiment successful if all are true:

- Universe Foundry tests pass.
- Same genome+delta produces the same mission id/DAG.
- Pi/Hermes can read the mission.
- Unreal MCP can be discovered and queried from the harness.
- One bounded decision/action traverses the mission ownership chain.
- Evidence is captured.
- No duplicate architecture is introduced.
- No fixture is mislabeled as real persistence proof.

Anything beyond that is bonus.

## Troubleshooting

UE MCP console:
```text
ModelContextProtocol.StartServer 8000
ModelContextProtocol.RefreshTools
ModelContextProtocol.GenerateClientConfig All
```

Raise UE logging:
```text
Log LogModelContextProtocol Verbose
```

If a tool is missing after adding/hot-reloading toolsets, refresh tools and reconnect the client. New C++ UFUNCTION tool declarations require an editor restart.

## Next promotion after canary

Only after the above PASS:
1. connect the real Hython static-field output;
2. replay TD `OUT_SHOW_FIELD`;
3. receive/align field in UE;
4. prove fabric + Niagara + Heart Gate share the field;
5. finally use a **real game-save-export delta** for destroy/regenerate persistence proof.

Do not jump directly to step 5.
