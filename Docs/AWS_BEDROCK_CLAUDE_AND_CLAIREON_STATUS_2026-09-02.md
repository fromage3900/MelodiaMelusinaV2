# AWS Bedrock + Claireon — verified status & the one console gate (2026-09-02)

Outcome of the "verify AWS state and wire Claude on Bedrock end-to-end" pass.
Run date: 2026-09-02, ~[late night]. Everything below was measured live, not assumed.

## 1. AWS project-wide — healthy

| Check | Result |
|---|---|
| AWS CLI | v2.36.8 installed |
| Profiles | `default` (root login, ca-central-1), `bedrock` (IAM user, us-east-1) |
| `bedrock` identity | `arn:aws:iam::322037002075:user/melodia-bedrock` — resolves (verified 2026-09-02) |
| IAM policy `BedrockInvoke` | Allows `bedrock:InvokeModel/InvokeModelWithResponseStream/Converse/ConverseStream` on `foundation-model/*` + `inference-profile/*`; catalogue reads; `bedrock-mantle:CreateInference` etc. |
| Mantle models (qwen.qwen3-coder-next, kimi-k2-*) | WORKING (project docs 08-13/08-14 verified; cost tracked in `Saved/router_ledger.jsonl`) |
| Claude Code CLI | 2.1.252 installed |

**Conclusion:** the AWS/cloud platform itself and the Mantle model lanes are set up and
healthy. No CLI work needed there.

## 2. THE ONE GATE — Bedrock-runtime model access is disabled (Claude cannot run yet)

Reproduced two ways on 2026-09-02:
- `bedrock-runtime.invoke_model` on `anthropic.claude-sonnet-4-5-20250929-v1:0` → `ValidationException: Operation not allowed`
- The committed harness `Tools/bedrock_model_test.py` (Converse, cross-region `us.`/`global.` profiles) → **every** model `Operation not allowed`, including `qwen.qwen3-coder-next`, `us.anthropic.claude-haiku-4-5-20251001-v1:0`, `global.openai.gpt-5.6-luna`.

Root (which bypasses IAM) fails identically, so this is NOT an IAM problem — the policy is
correct and complete. It is **account-level Bedrock model access**: the account only ever
invokes Bedrock through the **Mantle** service; no **bedrock-runtime** foundation model is
enabled. Enabling it requires a human in the AWS console.

**Only the owner can unblock this.** Steps (region **us-east-1 / N. Virginia**):
1. AWS Console → **Amazon Bedrock** → ensure region = **N. Virginia (us-east-1)** (account default ca-central-1 hosts none of these).
2. Left nav **Access management → Model access** (or **Providers → Anthropic → Manage model access**).
3. Select the Claude model(s) wanted (e.g. `Claude Sonnet 4.5`, `Claude Haiku 4.5`; optionally `Claude Sonnet 4` legacy).
4. Submit the **use-case details / request form** and accept the Claude end-user licence agreement (the form was never submitted — the 08-14 doc's "not authorized solely because the form was never filled" remains true).
5. Once enabled, verify with: `AWS_PROFILE=bedrock python Tools/bedrock_model_test.py`
   — Claude rows should flip FAIL→OK.

After that, "Claude on Bedrock end-to-end" is complete: IAM already grants it, Claude Code
auth is default (no `ANTHROPIC_*` override), and the router/Mantle seam is unchanged.

## 3. Claireon (UE MCP plugin) — installed, wired, server currently down

- Plugin present: `Plugins/Claireon` (git clone incl. `Binaries/`).
- MCP config present in project `.mcp.json`: `claireon → http://127.0.0.1:60162/mcp`.
- `Saved/Claireon/MCPServer.json`: port 60162, mode direct, pid 99956 (STALE — that editor is gone).
- Live probe 2026-09-02: port 60162 → connection refused (`claude mcp list` shows `claireon ✘ ConnectionRefused`; curl 000). Monolith 9316 is UP (200); aws-mcp/rider/blender/envoy/gaea/agent_bridge/melodia all Connected.

**To use Claireon**, start its in-editor MCP server:
- Editor running → toolbar **Claireon** button (or Window → General → Miscellaneous → Claireon), which starts the server on the stable worktree port 60162; or
- Relaunch the editor with `-StartMCPServer`; or
- Editor-less proxy: `Scripts/Utilities/Start-MCPProxy.ps1` (binds 60162, client can still run `tool_search`/`workflow`).

Claude Code then talks to it with zero config (committed). Governance note (AGENTS #7 /
Decision 025): one MCP surface per lock — currently Monolith, UnrealMCP, UEBlueprintMCP and
Claireon all exist; keep them serialised through the single editor holder.

## 4. Next fronts (not yet started)
- Hermes integration for recursive-learning pipelines
- Git health (tree was 328 commits ahead of origin/main at session start)