# AWS Agent Toolkit — Setup Record (2026-07-26)

Set up per official instructions at `https://raw.githubusercontent.com/aws/agent-toolkit-for-aws/refs/heads/main/setup-instructions/setup.md`, on this machine (`froma`), for Claude Code use.

## What was installed
- **AWS CLI v2.36.8** — official signed MSI installer (`awscli.amazonaws.com`), installed to `C:\Users\froma\AppData\Local\Programs\Amazon\AWSCLIV2`.
- **Region**: `ca-central-1` (chosen for lowest latency from Ontario; note the Agent Toolkit itself always operates in `us-east-1` regardless of this setting).
- **Auth**: `aws login` — a real, current AWS CLI browser-based OAuth flow (distinct from the older `aws sso login`). Completed successfully.
- **Agent Toolkit**: `aws configure agent-toolkit --yes --region us-east-1` installed 16 default AWS skills (Bedrock, billing/cost management, CDK, CloudFormation, compute, containers, deployment, messaging/streaming, observability, SDK usage for JS/Python/Swift, serverless, launch-with-aws, signing-in-to-aws) to `~/.claude/skills`, and registered an `aws-mcp` MCP server entry in `~/.claude.json` (`uvx mcp-proxy-for-aws@latest https://aws-mcp.us-east-1.api.aws/mcp`).

## One real thing to fix
Authentication landed on the **AWS root account** (`arn:aws:iam::322037002075:root`), not an IAM user/role. This works but is against AWS's own best practice — root should be reserved for account-level tasks (billing, closing the account, etc.), not day-to-day CLI/agent use. **Recommended next step**: create an IAM user (or role) with scoped permissions for whatever this toolkit ends up doing (S3 backup, Deadline Cloud rendering), and re-run `aws login`/reconfigure against that identity instead of root.

## Verification performed
- `aws sts get-caller-identity` confirmed the authenticated identity.
- `aws agent-toolkit list-available-skills --region us-east-1` returned a real, long list of legitimate AWS service skills (Aurora MySQL/PostgreSQL, Bedrock, DocumentDB, etc.) — confirmed the toolkit installed and works. (One cosmetic Windows-console Unicode encoding crash on a later skill's description — not a functional failure, the data had already printed successfully.)
- The `~/.claude/skills/` directory and `~/.claude.json`'s `mcpServers.aws-mcp` entry were read back directly to confirm exactly what got written before treating the setup as trusted — no unexpected content, matches the official install log 1:1.

## Why this matters for this project
Two concrete, already-identified uses (see conversation this session):
1. **AWS Deadline Cloud** — has first-class Unreal Engine + Movie Render Queue support (Service-Managed Fleets, confirmed UE 5.4-5.7, likely 5.8) — directly relevant to this project's active MRQ portfolio-render standup. Submit MRQ jobs from the editor, AWS handles distributed rendering.
2. **S3 / Glacier Deep Archive** — solves the real gap found earlier this session: `Backups/` doesn't exist yet on the post-relocation C: copy, and the project's own `.gitignore` explicitly defers asset backup to manual snapshots rather than git. Glacier Deep Archive is ~$1/TB/month — real off-site backup for the 154GB project at negligible cost.

Neither of these has been actually used yet — this doc records the toolkit installation only. Next step when ready: pick one (Deadline Cloud for the MRQ standup, or S3/Glacier for the backup gap) and set it up as a follow-on task.
