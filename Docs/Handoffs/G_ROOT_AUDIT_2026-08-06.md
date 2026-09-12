# G: Root Audit — 2026-08-06

Summary
- Purpose: inventory workspace files that reference `C:\EnvironmentPortfolio` (the alternate project root) and recommend remediations.
- Findings: many hardcoded references exist across deployment scripts, tools, and generated logs; grep found 1,000+ matches in ~13 files (notably large manifest files and tool scripts).

Top affected files / folders (representative)
- `.clean_repo/import.fi` — many `py "C:/EnvironmentPortfolio/..."` entries (huge file; contains pipeline invocations)
- `robocopy_BS_GodFile.log` — copy log showing G: tree
- `deploy/mcp_git.py` — hardcoded `PROJECT_ROOT = "C:/EnvironmentPortfolio/BS_GodFile"`
- `BS_GodFile/.rider/mcp.json`, `.cursor/mcp.json`, `.idea/mcp.json` — editor MCP configs referencing G:\ paths
- `deploy/agent_bridge_mcp.py`, `deploy/blender_mcp_adapter.py`, `deploy/hermes_mcp.py` — deployment adapters referencing G:\ or expecting G: layout
- `tools/*.ps1` — many PowerShell publishing/build scripts with `ProjectRoot = "C:\EnvironmentPortfolio\BS_GodFile"`
- `tools/_consistency_pass.py`, `tools/_verify_site_facts.py` — constants pointing at G:\ path

Immediate risks
- Agents and editor MCP servers operate on different roots (C: vs G:) causing divergence and coordination failures.
- `mcp_git.py` and other agent scripts may run `git` against the wrong repo root and perform unsafe wide commits.
- Plaintext API keys exist in .mcp.json files on the G: tree — credential exposure risk.

Recommended next steps (short)
1. Decide canonical root (C: or G:). I recommend `C:\EnvironmentPortfolio` (contains today's HEAD and active edits). Confirm choice.
2. Produce a single PR that updates the following files to the chosen root: `deploy/mcp_git.py`, all `.mcp.json` under `BS_GodFile/.*`, `tools/*.ps1`, `tools/*.py`, and any top-level scripts that hardcode G:. Use a scoped search/replace with a verified whitelist.
3. Add safety guards to `deploy/mcp_git.py` (require explicit paths, refuse `git add .`) and to agent scripts (dry-run flag).
4. Move secrets out of `.mcp.json` into environment variables or a `.env` file loaded at runtime; rotate any exposed keys.
5. Retire or reconcile the G: repository: either archive it and remove editor configs that point to it, or mirror C: changes into G: and consolidate.

Commands to reproduce / explore
PowerShell (run from `C:\EnvironmentPortfolio`):

```powershell
# Find files with G:\ references
Get-ChildItem -Recurse -File | Select-String -Pattern "G:\\EnvironmentPortfolio|C:/EnvironmentPortfolio" | Select-Object Path, LineNumber, Line | Out-File G_root_matches.txt -Encoding utf8
# Count matches
Get-Content G_root_matches.txt | Measure-Object -Line
```

Optional: automated replace (DO NOT RUN until canonical root chosen)
```powershell
$old = 'G:\\EnvironmentPortfolio'
$new = 'C:\\EnvironmentPortfolio' # or chosen root
Get-ChildItem -Recurse -File -Include *.py,*.ps1,*.json,*.md | ForEach-Object {
  (Get-Content $_.FullName) -replace [regex]::Escape($old), $new | Set-Content $_.FullName
}
```

Where I can help next
- Produce the exact file list (one-per-line) of files referencing G: and open PR(s) to change them to the canonical root.
- Perform the safe sweep and open a PR (I will not push changes without your confirmation).
- Implement `mcp_git.py` safety changes and rotate keys found in .mcp.json.

I created this audit at: [BS_GodFile/Docs/Handoffs/G_ROOT_AUDIT_2026-08-06.md](BS_GodFile/Docs/Handoffs/G_ROOT_AUDIT_2026-08-06.md)

Next: confirm which root to canonicalize (C: recommended).
