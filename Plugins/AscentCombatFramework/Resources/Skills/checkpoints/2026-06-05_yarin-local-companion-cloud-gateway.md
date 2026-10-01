# Checkpoint: Yarin Local Companion Cloud Gateway

**Date:** 2026-06-05  
**Branch:** `codex/acf-local-companion-cloud-gateway`  
**Summary:** Bundled the Windows Yarin local companion into the plugin, hardened local login/routing, and fixed the UE launcher path so native MCP and the local companion stay in sync through a per-editor-session bearer token.

## Files Changed

### Plugin Launcher / Browser

- `Source/AscentAIAgent/Private/AscentAIAgentSubsystem.cpp`
- `Source/AscentAIAgent/Private/AscentAIAgentSubsystem.h`
- `Source/AscentAIAgent/Private/AscentAIAgentWebBrowser.cpp`
- `Source/AscentAIAgent/Private/AscentAIAgentWebBrowser.h`

### Bundled Local Runtime

- `Resources/YarinLocalAgent/Windows/**`

### ACF Agent Source

- `Tools/acf-agent/apps/chatbot/**`
- `Tools/acf-agent/docs/**`

### Docs

- `docs/README.md`
- `docs/handoff.md`
- `docs/guides/yarin-marketplace-setup.md`
- `docs/checkpoints/2026-06-05_yarin-local-companion-cloud-gateway.md`

## What's Working

- Local companion Windows package builds and is copied into plugin resources.
- The local launcher sets `APP_RUNTIME=local`, loopback host/port, `AUTH_TRUST_HOST`, generated local `AUTH_SECRET`, cloud URL, MCP URL, and MCP token.
- Local unauthenticated chat paths redirect to `/login`.
- Login no longer depends on stale Next server actions; client-side NextAuth sign-in handles Discord and email/password.
- Local settings redaction no longer exposes device fingerprint, local user IDs, or MCP bearer token.
- `POST /api/local/settings` can refresh the running local companion with the current MCP URL/token from the UE launcher and returns only redacted settings.
- Plugin MCP startup now resets failed state if the HTTP router cannot bind.
- Plugin refuses to start the local companion if MCP did not start.
- Existing local companion reuse now requires a successful MCP token refresh; otherwise the plugin tries fallback ports.
- Browser waits for local health and binds the UE bridge before reporting connected.
- Resource lookup now uses the real plugin descriptor name `AscentCombatFramework`.

## What's Not Working / Known Issues

- UE C++ build is blocked while the currently open editor owns the Live Coding mutex.
- Full signed-in model gateway chat smoke was not rerun in this checkpoint.
- Full editor MCP tool smoke through the Unreal panel should be rerun after a clean editor restart and C++ rebuild.

## Review Findings

### Code Review

Three reviewer agents were run with the available Codex multi-agent roles. They found real issues and the blocking ones were fixed:

- Stale local companion reuse could keep an old MCP token. Fixed by runtime refresh before reuse.
- Localhost dev-server overrides could be blocked by local health gating. Fixed by only gating when auto-start local agent is enabled.
- Browser could report connected before UE bridge binding. Fixed by only connecting on the expected local URL and `OnLoadCompleted`.
- MCP bind failure could leave a valid-looking dead server object. Fixed by resetting failed MCP state and refusing companion launch.
- Plugin resource lookup used the wrong plugin name. Fixed to `AscentCombatFramework`.

Remaining review note:

- Synchronous socket health probes are short, but still run on the editor timer during reconnect. Keep an eye on startup/reconnect hitches if users have many local services occupying the fallback range.

### Documentation

Created/updated:

- `docs/README.md`
- `docs/handoff.md`
- `docs/guides/yarin-marketplace-setup.md`
- this checkpoint

### Performance / GAS / Network Review

- No GAS-specific changes.
- Network exposure remains loopback-only for local companion and MCP.
- MCP token is held in memory/env for the local process and is not returned by health/settings responses.
- Legacy TCP bridge remains disabled by default.

## Verification

- Passed: `bun run typecheck` from `Tools/acf-agent/apps/chatbot`.
- Passed: `bun run build:local` from `Tools/acf-agent/apps/chatbot`.
- Passed: local package boot on `127.0.0.1:3005`.
- Passed: local route smoke for `/api/local/health`, `/login`, `/settings`, `/skills`, `/`, `/chat/smoke-local`.
- Passed: `POST /api/local/settings` MCP runtime refresh returned `{"ok":true}` and health showed `hasMcpAuthToken:true` without exposing the token.
- Passed: narrowed package secret scan found no provider-key, webhook-secret, or database-URL shaped values.
- Blocked: UE build via `C:\Program Files\Epic Games\UE_5.7\Engine\Build\BatchFiles\Build.bat ACFSampleEditor Win64 Development -Project=D:\Gamedev\ACFSample\ACFSample.uproject -WaitMutex -NoHotReload` because Live Coding is active in the open editor.

## Next Steps

- Close Unreal Editor or disable Live Coding, then rerun the UE build.
- Relaunch Unreal and verify automatic local companion startup in the CEF panel.
- Run MCP chat smoke through local Yarin with `ueSysPing`, `ueSysProjectInfo`, `ueAssetList`, and `ueAcfAssetListTypes`.
- Run one signed-in model gateway chat smoke and confirm cloud usage logging.
