# Checkpoint: ADS Dialogue Graph + VO MCP Tools

**Date:** 2026-06-04
**Branch:** codex/acf-local-companion-cloud-gateway
**Summary:** Added the v1 native MCP tool family for ADS dialogue graph authoring and approval-gated ElevenLabs VO. Wired the Yarin chatbot planner and bundled runtime skill so dialogue prompts can reach the new editor tools, then rebuilt Unreal and verified a branching smoke graph through live editor MCP.

## Files Changed

Root plugin:
- `Config/mcp-tools.json`
- `Source/AscentAIAgent/AscentAIAgent.Build.cs`
- `Source/AscentAIAgent/Private/AscentAIAgentSubsystem.cpp`
- `Source/AscentAIAgent/Private/Commands/ADSDialogueAgentTools.h`
- `Source/AscentAIAgent/Private/Commands/ADSDialogueAgentTools.cpp`
- `Source/AscentAIAgent/Private/Commands/UEDialogueCommands.cpp`
- `Source/AscentAIAgent/Public/Commands/UEDialogueCommands.h`
- `docs/handoff.md`
- `docs/checkpoints/2026-06-04_ads-dialogue-graph-vo-mcp-tools.md`

Nested Yarin repo:
- `Tools/acf-agent/apps/chatbot/app/(chat)/api/chat/route.ts`
- `Tools/acf-agent/apps/chatbot/lib/ai/agent-loop/pi-experiment.ts`
- `Tools/acf-agent/apps/chatbot/lib/ai/permissions/tiers.ts`
- `Tools/acf-agent/apps/chatbot/skills/acf-dialogue-designer/SKILL.md`
- `Tools/acf-agent/apps/chatbot/skills/acf-dialogue-designer/references/gotchas.md`

Ignored/unrelated dirt not included:
- `Resources/YarinLocalAgent/Windows` generated local companion output
- pre-existing auth/login/docs edits in `Tools/acf-agent`
- parent project test asset file, because `D:/Gamedev/ACFSample` is not a Git repo

## What's Working

- Five native MCP tools are registered: `ue_dialogue_validate_spec`, `ue_dialogue_create_graph`, `ue_dialogue_inspect`, `ue_dialogue_voice_suggest`, and `ue_dialogue_generate_audio`.
- `FUEDialogueCommands` routes all five commands through the AscentAIAgent module; no ADS editor module command shim is needed.
- Graph creation now uses AGS schema conversion so ADS runtime edge objects are produced, not only direct editor pin links.
- `ue_dialogue_inspect` reports `has_runtime_edge` per edge and warns on broken child links.
- `ue_dialogue_generate_audio` remains approval-gated, clamps timeout and per-call node count, and reports save failures.
- Runtime chat has the bundled `acf-dialogue-designer` skill, PI planner exposure, permission classifications, and a dev-only editor MCP override guarded against production.

## Verification

- Closed Unreal, rebuilt `ACFSampleEditor Win64 Development`, reopened Unreal, and confirmed native MCP exposed all five dialogue tools.
- Direct editor MCP validate/create/inspect recreated `/Game/YarinGenerated/Dialogues/DA_CodexDialogueGraphSmoke.DA_CodexDialogueGraphSmoke`.
- Final direct inspect result: `ADSDialogue`, 7 nodes, 7 edges, 1 root, no warnings, all seven `has_runtime_edge` flags true, and all `SoundToPlay` fields empty.
- Chat bench previously created and inspected the same smoke graph using `useAgentSkill`, `ueGameplayTagsSearchMany`, `ueDialogueValidateSpec`, `ueDialogueCreateGraph`, and `ueDialogueInspect`.
- Chatbot TypeScript validation passed with `bun --filter chatbot typecheck`.

## What's Not Working / Known Issues

- Latest full chat bench artifact still scores `59/100`, `gate=fail`, `rawScore=74`, because the scorer flags the smoke prompt as a prompt-shaped shortcut and cost is high.
- The full chat bench was not rerun after the runtime-edge fix to avoid another high-cost eval; direct editor MCP was rerun against the rebuilt DLL instead.
- VO generation is not live-tested yet. It must remain blocked until the user explicitly approves voice choices and node scope.
- Existing dialogue replacement still mutates the in-memory asset before package save completes. Build and direct save passed in the smoke path, but a more robust temp/swap rebuild flow is a future hardening task.
- PIE traversal of the generated graph is still pending; inspect now verifies runtime edge objects, but gameplay traversal should be exercised next.

## Review Findings

### Code Review

- Fixed: direct editor pin links did not create runtime ADS edge objects.
- Fixed: inspect could have falsely passed direct child links with no `UAGSGraphEdge`.
- Fixed: audio generation ignored sound/dialogue package save failures.
- Fixed: replacing a non-dialogue asset path could collide with existing assets.

### Documentation

- Created this checkpoint and replaced the scaffolded handoff with current state.
- Updated bundled dialogue skill guidance and gotchas for runtime chat routing, editor MCP env, and PI planner exposure.

### Performance / GAS / Network Review

- Fixed: sync HTTP callback no longer captures stack state that can outlive timeout cancellation.
- Fixed: TTS timeout is clamped and a single approved request is limited to 8 selected nodes.
- Fixed: `YARIN_ENABLE_EDITOR_MCP_IN_DEV` is ignored in `NODE_ENV=production`.
- Fixed: open-ended reflected node properties are constrained to the v1 ADS allowlist.
- No GAS, replication, authority, or runtime gameplay mutation issue found; these are editor asset-authoring tools.

## Next Steps

- Run a lower-cost reusable workflow dialogue bench so the scorer no longer treats the smoke prompt as a shortcut.
- Test `ue_dialogue_voice_suggest` with real participant descriptions.
- Test `ue_dialogue_generate_audio` only after explicit paid-TTS approval, using one short node first.
- Run PIE traversal on the generated graph to verify start, responses, rejoin, and end behavior in gameplay.
- Consider a temp/swap rebuild flow for replacing existing dialogue assets.
