G: Root Sweep — Instructions

Purpose
- Safely canonicalize project root references to the chosen root (`C:\EnvironmentPortfolio`).
- Provide a reviewable, auditable process with backups and diffs.

Files created
- `tools/safe_root_sweep.py` — scan + dry-run + optional apply tool (requires clean git tree).
- `.github/PULL_REQUEST_TEMPLATE/root-sweep.md` — PR template for reviewers.

Recommended workflow
1. Run scan (dry-run):

```powershell
python tools/safe_root_sweep.py --old "C:/EnvironmentPortfolio" --new "C:/EnvironmentPortfolio" --extensions ".py,.ps1,.json,.md" --out tools/g_root_report.json --diffs tools/diffs.patch
```

2. Inspect `tools/g_root_report.json` and `tools/diffs.patch`. Confirm intended changes.
3. Create a branch: `git checkout -b canonical-root-c-sweep` and commit the report files.
4. Create a draft PR using the template `.github/PULL_REQUEST_TEMPLATE/root-sweep.md` and request reviewers from `collaborator/src-safety` and `Rhythm Systems`.
5. If reviewers approve, apply changes locally (must have clean git state):

```powershell
python tools/safe_root_sweep.py --old "C:/EnvironmentPortfolio" --new "C:/EnvironmentPortfolio" --extensions ".py,.ps1,.json,.md" --apply --backup-dir tools/g_root_backups
```

6. Inspect backups, run tests, commit the patched files, push and update PR.
7. Rotate any secrets found in `.mcp.json` files and verify no keys were committed.

Caveats & safety
- The tool is conservative: it only scans text files and requires `--apply` to change files.
- Do not run `--apply` on an unclean working tree; the tool will refuse to proceed.
- Large binary files and generated manifests are excluded from the default extension list. If a reference exists in a binary or blob, handle manually.

Contact
- For questions or to delegate the apply step, assign to `collaborator/src-safety` lane.
