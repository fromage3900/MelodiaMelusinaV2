# UE Tools Improvements and Bugs to Fix

## Purpose
Track practical improvements and bugs for the UE tools used by the agent harness.

## Current Issues
- Unreal bridge asset inspection calls can time out on the game thread.
- Some tool calls fail when the wrong parameter name is used.
- Asset verification can be interrupted by editor responsiveness issues.

## Improvement Ideas
- Add clearer tool parameter validation before dispatch.
- Surface timeout errors with enough context to identify the failing UE operation.
- Add a retry or backoff path for safe read-only inspection calls.
- Add a simple end-to-end verification flow for asset creation and attachment checks.

## Notes
- Keep this list focused on UE tool reliability and workflow friction.
- Move resolved items into a dated changelog or checkpoint doc when fixed.