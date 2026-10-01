# ACF Ultimate + Yarin Documentation

This is the documentation entry point for the ACF Ultimate plugin work plus the bundled Yarin 2.0 local companion.

## Reading Order

1. [handoff.md](handoff.md) - current state and next-session priorities.
2. [guides/yarin-marketplace-setup.md](guides/yarin-marketplace-setup.md) - user setup guide for Marketplace/plugin installs.
3. [checkpoints/](checkpoints/) - frozen implementation snapshots.

## Current Status

| System | Status | Summary |
|--------|--------|---------|
| Yarin local companion | WORKING | Windows package is bundled under `Resources/YarinLocalAgent/Windows` and starts on loopback from the UE plugin. |
| Native editor MCP | WORKING | Local Yarin starts MCP on `127.0.0.1:56571/mcp` with a per-editor-session bearer token. |
| Cloud model gateway | WIP | Cloud owns auth, billing, provider keys, usage, and model calls; local companion keeps editor tools local. |
| Legacy TCP/relay editor control | DEPRECATED | Code remains present but is disabled by default and not the Marketplace v1 path. |
| ADS dialogue MCP tools | WORKING | See the 2026-06-04 ADS checkpoint for the last dialogue-specific smoke. |

## Module Index

| System | Primary Doc | What it does |
|--------|-------------|--------------|
| Marketplace Yarin setup | [guides/yarin-marketplace-setup.md](guides/yarin-marketplace-setup.md) | Explains install, auto-start, login, ports, cloud/local split, and troubleshooting. |
| Current handoff | [handoff.md](handoff.md) | Living state for the next agent/session. |
| Local companion checkpoint | [checkpoints/2026-06-05_yarin-local-companion-cloud-gateway.md](checkpoints/2026-06-05_yarin-local-companion-cloud-gateway.md) | Frozen record of the local companion/cloud gateway checkpoint. |
| ACF Agent internals | [../Tools/acf-agent/docs/reference/chatbot.md](../Tools/acf-agent/docs/reference/chatbot.md) | Chatbot runtime, auth, billing, and gateway reference. |

## Documentation Structure

```text
docs/
  README.md
  handoff.md
  checkpoints/
  guides/
  plans/
  reference/
```

README is the map. Handoff is the live state. Checkpoints are historical snapshots.
