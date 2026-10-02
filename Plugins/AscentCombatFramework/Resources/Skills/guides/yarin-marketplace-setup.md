# Yarin 2.0 Marketplace Setup

This guide is for users installing the ACF Ultimate plugin with the bundled Yarin 2.0 local companion.

## What Gets Installed

The plugin ships the Yarin local companion under:

```text
AscentCombatFrameworkUltimate/
  Resources/
    YarinLocalAgent/
      Windows/
        node.exe
        yarin-local-agent.mjs
        .next/
        public/
        PACKAGE.json
        NOTICE.txt
```

Users do not need to install Node.js separately for the Windows package.

## Install

1. Download/install the plugin from Unreal Marketplace or the provided plugin package.
2. Put the plugin in one of the normal Unreal locations:
   - Engine plugin folder: `...\UE_5.x\Engine\Plugins\Marketplace\AscentCombatFrameworkUltimate`
   - Project plugin folder: `<Project>\Plugins\AscentCombatFrameworkUltimate`
3. Open the Unreal project.
4. Enable the plugin if Unreal asks, then restart the editor.
5. Open the Yarin panel from the toolbar/menu or use `Ctrl+Shift+A`.

## What Happens On Editor Start

When the editor starts, the `AscentAIAgent` module initializes and:

1. Starts the native MCP server on `127.0.0.1:56571/mcp`.
2. Generates an in-memory per-editor-session MCP bearer token if the project setting is blank.
3. Starts the bundled local companion on `127.0.0.1:3005`.
4. If `3005` is occupied by a non-Yarin process, tries fallback ports `3015-3024`.
5. Passes the selected local URL to the embedded Unreal browser panel.
6. Keeps Unreal/editor tool calls on the local machine.

Yes: for the Marketplace v1 path, starting Unreal Editor is enough to start the local Yarin server as long as **Auto Start Local Agent** is enabled and the Windows package is present.

## Sign In

Yarin uses the existing Yarin account system. Users sign in with:

- Discord, if their Discord account has the required server/role access.
- Existing email/password login, if enabled for that account.

The local companion opens/uses the cloud auth flow at:

```text
https://yarin.darktowerinteractive.com
```

The cloud validates the account, license, device slot, model access, and billing. The local companion stores only a scoped device token; it does not receive provider API keys, database credentials, Stripe secrets, or BYOK plaintext.

## Runtime Split

| Runs locally | Runs in Yarin cloud |
|-------------|---------------------|
| Chat UI in Unreal | Login/account authority |
| Agent loop and approvals | License/device checks |
| Tool catalog and MCP calls | Credits/billing/usage logs |
| Unreal asset/editor automation | Model provider API keys |
| Local chat cache by default | Cloud model gateway |

Hosted browser chat does not control the editor in Marketplace v1. Open Yarin inside Unreal for editor automation.

## Project Settings

Open **Edit > Project Settings > Engine > Yarin 2.0**.

Recommended defaults:

| Setting | Default | Notes |
|---------|---------|-------|
| Auto Start Local Agent | Enabled | Starts the bundled companion on editor launch. |
| Local Agent Port | `3005` | Fallbacks: `3015-3024`. |
| Cloud Base URL | `https://yarin.darktowerinteractive.com` | SaaS auth, gateway, billing. |
| Auto Start TCP Bridge | Disabled | Legacy path, not Marketplace v1. |
| MCP Server Port | `56571` | Loopback-only native MCP. |
| MCP Auth Token | Blank | Blank is okay for local Yarin; plugin generates an in-memory session token. |

## Troubleshooting

If the Yarin panel is blank or says it cannot connect:

1. Check that `Resources/YarinLocalAgent/Windows/node.exe` exists inside the installed plugin.
2. Check whether another process owns `127.0.0.1:3005`.
3. Restart Unreal Editor.
4. If using a custom project setting, reset **Local Agent Port** to `3005`.
5. Look in Unreal Output Log for `Yarin local companion` and `acf-mcp` messages.

If sign-in fails:

1. Confirm the user already has a Yarin account; open public signup is not part of this flow.
2. Confirm Discord server/role access if using Discord.
3. Confirm the Yarin cloud URL is reachable.
4. Check whether the account license is suspended, expired, out of credits, or out of device slots.

If chat loads but editor tools fail:

1. Confirm the MCP log says it is listening on `http://127.0.0.1:56571/mcp`.
2. Confirm no other process owns port `56571`.
3. Restart the editor so a fresh MCP token is generated and passed to the local companion.
4. Use a Yarin tab opened from Unreal, not hosted browser chat.

## Notes For Support

- Local chat history is local by default.
- Cloud sync is opt-in when available.
- Legacy TCP bridge and WebSocket relay are not the default editor automation path.
- Local machine owners can inspect local device/MCP tokens. This is acceptable because the tokens are scoped/revocable and are not provider API keys.
