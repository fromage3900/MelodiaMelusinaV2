# Lost tool sources — ~91 scripts survive only as bytecode (2026-08-14)

Found while fixing broken links in `Docs/MELUSINA_BLENDER_WARDROBE_SSOT.md`. Two links
pointed at tools that no longer exist. They turned out not to be stale links — the
**source files are gone and only their compiled `.pyc` remains.**

That is not two files. It is roughly ninety.

---

## 1. The count

| Location | Orphaned `.pyc` (no surviving `.py`) | In git history? |
|---|---:|---|
| `Tools/__pycache__/` | **17** | 1 of 17 (`echo_topo.py`) |
| `Content/Python/__pycache__/` | **75** | 0 of 6 sampled |

An orphaned `.pyc` means the script **was written and executed** — Python only emits bytecode
on import — and then deleted without ever being committed.

## 2. Why `Tools/` lost them

`.gitignore:195` is `Tools/*` with ~30 explicit `!Tools/…` carve-outs. Anything not on that
allowlist is invisible to git, so deleting it is unrecoverable and silent.

**This is the same failure that hid the playable route levels and the entire procedural
dungeon system** — both fixed earlier today. The pattern is a blanket ignore plus a
hand-maintained allowlist that nobody updates when they write a new tool.

## 3. Why `Content/Python/` lost them anyway

This is the part that surprised me. `Content/Python/` **is** un-ignored (`.gitignore:100`), so
the rule is not the cause. All six sampled orphans return `history=0` — they were created,
run, and deleted **without ever being committed at all.**

So there are two distinct failure modes, and fixing the ignore rule only addresses one.

## 4. What was lost

`Tools/` (dates are last-execution, from `.pyc` mtime):

```
echo_topo.py                          2026-08-13  22K   <- RECOVERABLE, 1 commit in history
batch_eevee_komikaze_portfolio.py     2026-07-15  50K
upgrade_stage_core_and_waterhair.py   2026-07-10  29K
populate_stage_review_queue.py        2026-07-11  27K
setup_tier_p2_glam.py                 2026-07-10  19K
setup_tier_p3_proc.py                 2026-07-10  15K
melodia_asset_passport.py             2026-07-15  15K   (3 bytecode generations)
setup_tier_b_diorama.py               2026-07-10  14K
setup_tier_p4_wild.py                 2026-07-10  13K
prep_portfolio_render_day.py          2026-07-13  12K
setup_tier_c_audvis_truedepth.py      2026-07-13  12K
komikaze_stage_looks.py               2026-07-11   8K
build_technical_breakdown_manifest.py 2026-07-13   6K
rewrite_content_paths.py              2026-07-09   4K
validate_local_doc_links.py           2026-07-13   2K
```

Most of this is the **portfolio/stage pipeline** — tier setup, stage looks, EEVEE batch
render, review-queue population, asset passports, technical-breakdown manifests. That is the
environment-art track's tooling, and `MELUSINA_BLENDER_WARDROBE_SSOT.md` still documents it as
though it exists.

**`echo_topo.py` (2026-08-13, 22K) is recoverable** — it has one commit and matches the
`feature/echo-topo-chapter2` branch. Restore it before that branch is pruned.

## 5. The detail worth pausing on

`validate_local_doc_links.py` was a **doc-link validator**. It was lost to this rule.

Earlier today I wrote `Tools/doc_link_check.py` — a doc-link validator — because I could not
find one. **I rebuilt a tool that already existed**, and my replacement is currently untracked
under the same rule, waiting to be lost the same way.

`Tools/wardrobe_draft_lint.py`, written this afternoon, is in that state right now.

## 6. Recovery

Bytecode is not source, and the practical options are poor:

- `.pyc` is **Python 3.13** here. `uncompyle6` / `decompyle3` lag well behind 3.13 and will
  likely fail outright. Do not plan around this working.
- Some intent is readable without full decompilation: `python -m dis` on the `.pyc`, and
  strings in the constant pool (paths, asset names, log messages) often recover *what a script
  targeted* even when the logic does not survive.
- For anything still needed, rewriting from the docs that describe it is probably faster than
  fighting a decompiler.

**Do not delete `__pycache__` in these two folders.** Right now it is the only remaining
evidence that these tools existed.

## 7. What would actually stop this

1. **Add the two live lint tools to the allowlist** — `doc_link_check.py`,
   `wardrobe_draft_lint.py`. One line; needs owner sign-off because `.gitignore` is protected.
2. **Invert the `Tools/` rule.** A hand-maintained allowlist of ~30 entries has already failed
   ~16 times. Track `Tools/**.py` and ignore the known-noisy patterns instead — the cost is a
   few scratch scripts in history, against losing pipeline tooling silently.
3. **`__pycache__` as a tripwire.** The check that found this is three lines: for each `.pyc`,
   assert the matching `.py` exists. Worth running in CI — an orphan means someone lost work,
   and it is detectable the same day rather than a month later.
4. The `Content/Python/` losses need no rule change, only committing. Nothing prevented it.

## 8. Scope note

This report **enumerates**; it deletes and restores nothing. `echo_topo.py` is the one clearly
recoverable item and restoring it is a one-line `git checkout` — but which branch tip to take
it from is an owner call, so it is left alone.
