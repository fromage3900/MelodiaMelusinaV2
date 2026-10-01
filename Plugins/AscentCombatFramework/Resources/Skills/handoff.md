# Handoff

**Last updated:** 2026-06-05 - Bundled the Windows Yarin local companion, hardened login/local routing, and fixed MCP runtime refresh for reused local companion processes.

**Current headline:** Yarin editor automation is now local-first: Unreal starts the bundled local companion, starts native MCP on loopback with a per-editor-session bearer token, and the local chat uses the cloud only for auth/model/billing.

---

## What's Working

- Plugin defaults are set for Marketplace v1: `bAutoStartLocalAgent=true`, local port `3005`, fallback ports `3015-3024`, cloud base URL `https://yarin.darktowerinteractive.com`, and legacy TCP bridge disabled by default.
- The plugin starts MCP before the local companion. If MCP cannot bind, it no longer leaves a valid-looking dead MCP server state and refuses to start the companion.
- The plugin reuses an already-running Yarin companion only after refreshing that process with the current editor MCP URL/token; otherwise it tries a fallback port.
- The embedded browser waits for local companion health before loading and only marks connected after the expected local Yarin URL is loaded and the UE bridge is bound.
- The packaged Windows local companion includes `node.exe`, `.next` standalone output, static assets, `PACKAGE.json`, `NOTICE.txt`, and `yarin-local-agent.mjs`.
- Local unauthenticated chat routes redirect to `/login`; users do not see the chat shell before sign-in.
- Local sidebar user nav and sign-out are restored through a cloud logout URL that returns safely to local `/login`.
- Local package smoke passed on `127.0.0.1:3005`: `/api/local/health`, `/login`, `/settings`, `/skills`, `/`, `/chat/smoke-local`, and loopback MCP runtime refresh.
- A narrowed package secret scan found no provider-key, webhook-secret, or database-URL shaped values.
- ACF Agent `bun run typecheck` passes and `bun run build:local` packages successfully.

## Known Issues

- UE C++ build was attempted through UE 5.7 UBT, but the open Unreal Editor owns the Live Coding mutex. UBT refuses to compile until Live Coding is disabled in-editor or the editor is closed.
- Full editor MCP chat smoke (`ueSysPing`, `ueSysProjectInfo`, `ueAssetList`, `ueAcfAssetListTypes`) should be rerun after the editor is closed/rebuilt with these latest launcher fixes.
- Local route smoke currently uses an unauthenticated local profile, so chat/gateway model streaming was not re-benchmarked in this checkpoint.
- Legacy TCP bridge and WebSocket relay remain in code but are deprecated for Marketplace v1.

## TODO Next Session

- Close Unreal Editor or disable Live Coding, then rerun `ACFSampleEditor Win64 Development` build.
- Relaunch Unreal from the rebuilt plugin and verify auto-start, MCP token refresh, selected port, and CEF panel load.
- Run local Yarin MCP chat smoke: `ueSysPing`, `ueSysProjectInfo`, `ueAssetList`, `ueAcfAssetListTypes`.
- Run one model-gateway chat smoke with a signed-in account and confirm usage is logged cloud-side.
- Push a Marketplace-ready zip/package only after the UE build and editor smoke pass on a clean editor launch.

---

## Checkpoints

**Last Checkpoint:** [2026-06-05_yarin-local-companion-cloud-gateway](checkpoints/2026-06-05_yarin-local-companion-cloud-gateway.md)

---

## Active Specs / Key Documents

- [guides/yarin-marketplace-setup.md](guides/yarin-marketplace-setup.md) - user install and setup guide.
- [checkpoints/2026-06-05_yarin-local-companion-cloud-gateway.md](checkpoints/2026-06-05_yarin-local-companion-cloud-gateway.md) - frozen checkpoint for the bundled local companion work.
- [../Tools/acf-agent/docs/guides/deployment.md](../Tools/acf-agent/docs/guides/deployment.md) - cloud/local deployment notes for the app repo.
