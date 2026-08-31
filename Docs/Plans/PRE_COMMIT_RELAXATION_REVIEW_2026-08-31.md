# Pre-Commit Hook Relaxation — Owner Review

**Generated:** 2026-08-31 (overnight daemon)
**Status:** PENDING OWNER REVIEW
**Scope:** `.githooks/pre-commit` line-68 exception pattern

---

## Summary

The pre-commit hook's "UE build artifacts" check (line 68) currently exempts **3 specific** Saved/Audit JSON files. The proposed change widens this to **all** Saved/Audit files (`*.json` AND `*.md`). This is a meaningful policy relaxation — the hook will no longer reject any Saved/Audit artifact from being staged.

---

## Current Behavior

```bash
grep -Ev '^Saved/Audit/(first_dream_experience_contract_20260824|gameplay_authority_atlas_20260824|non_ue_gate_truth_20260824)\.json$'
```

- **Only** these 3 files can be staged from Saved/Audit/
- All other Saved/Audit/*.json and Saved/Audit/*.md are **blocked**

## Proposed Behavior

```bash
grep -Ev '^Saved/Audit/.*\.(json|md)$'
```

- **Any** file under Saved/Audit/ with `.json` or `.md` extension can be staged
- The blanket ban on Saved/Audit is removed

---

## Risk Assessment

| Dimension | Current (3 files) | Proposed (all Audit) |
|---|---|---|
| Build artifact protection | Strong — only 3 known-safe files | Weak — any file passes |
| Accidental junk staging | Nearly impossible | Possible (e.g., scratch notes, temp JSON) |
| False positives for work | High — every new Audit file triggers block | None |
| Review friction | High — owner must edit hook each time | Low — smooth workflow |

**Net assessment:** Moderate risk. Saved/Audit/ is supposed to contain audit reports and session artifacts, not build output. But it's a policy change from "deny by default" to "allow by default."

---

## Recommendation

**Conditionally approve.** The relaxation aligns with the directory's purpose (audit data, not build artifacts). However:

1. **Rename `Saved/Audit/` to `Saved/Reports/` or `Saved/Evidence/`** to make the directory's non-build-artifact purpose explicit. Then the hook change is clearly correct.
2. **Alternatively:** Add a comment at line 68 documenting why the exception exists:

```bash
# Saved/Audit/ contains audit reports (json/md), not UE build artifacts.
# These are owner-reviewed, git-tracked evidence files.
grep -Ev '^Saved/Audit/.*\.(json|md)$' || true
```

3. **Keep the *.md addition** — markdown reports are increasingly common (COPERNICUS_AAA_LIVE_REPORT, graph_reachability).

---

## Rollback Command

If the relaxation causes issues:

```bash
git checkout HEAD -- .githooks/pre-commit
```

Or to commit the rollback:

```bash
git add .githooks/pre-commit
git commit -m "revert: restore strict Saved/Audit pre-commit exception"
```

---

## Owner Decision

- [ ] **APPROVE** — apply the relaxation as-is
- [ ] **APPROVE WITH COMMENT** — apply + add documenting comment
- [ **DEFER** — keep current strict behavior until directory rename
- [ ] **REJECT** — keep strict, list each new file explicitly

---

## Files Affected

| File | Status |
|---|---|
| `.githooks/pre-commit` | Modified (line 68) — M status |

## Guardrails

- Daemon will **NOT** commit this change without owner sign-off
- This is a policy/contract change, not a content change
- No .uasset writes involved
- No gate ledger impact