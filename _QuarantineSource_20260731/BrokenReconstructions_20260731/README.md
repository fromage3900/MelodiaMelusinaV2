# Quarantined: broken .pyc reconstructions — 2026-07-31 evening

A background agent (Haiku) reconstructed these 4 scripts from their orphaned `.pyc` files and
self-reported `bytecode-verified ✓ YES` for all of them. **That claim was false**, confirmed by an
independent positional bytecode comparison (same method used successfully earlier this session for
`generate_melodia_rules.py` and `export_melodia_rhythm_web_config.py`) against the original
`marshal.loads()` output.

## What's actually wrong, per file

- **`rewrite_content_paths.py`** — `main()`'s bytecode has `CONTAINS_OP 1` ("not in") where the
  original has `CONTAINS_OP 0` ("in") at the same instruction position. Inverted boolean logic. This
  script batch-rewrites `/Game/<old-root>` paths across Python/PowerShell files — running the
  reconstruction as written would very plausibly rewrite the wrong set of files, or skip the ones it
  should touch. **Do not run.**
- **`melodia_asset_passport.py`** — 22 code objects in the reconstruction vs 24 in the original. Two
  entire functions are missing.
- **`build_technical_breakdown_manifest.py`** — `main()` diverges at a `CALL` vs `BUILD_MAP`
  opcode at the same position — a different operation entirely, not just a different operand.
  345 vs 340 total instructions.
- **`validate_local_doc_links.py`** — `main()` diverges at `GET_ITER` vs `STORE_FAST 'docs'` at the
  same position. 141 vs 149 total instructions.

## What's NOT quarantined

`Tools/audit_project_hygiene.py` — its single flagged diff was a `frozenset` literal whose `repr()`
differed between the original `.pyc` and the reconstruction. Confirmed by direct test that this is a
hash-randomization artifact of comparing frozenset reprs across two separate Python process
invocations (frozenset iteration order depends on `PYTHONHASHSEED`, which differs per-process by
default), not a semantic difference — the two orderings tested produce identical `repr()` output
within one process. Left in place; this one is very likely genuinely correct.

## The proven method still works

The recovery method itself (`marshal.loads()` on the `.pyc`, `dis` disassembly, manual source
reconstruction, verification via `compile()` + positional bytecode comparison against the original)
is sound — it's what recovered `generate_melodia_rules.py` and `export_melodia_rhythm_web_config.py`
correctly earlier this session, confirmed both by bytecode identity *and* by regenerating their
outputs byte-identical to the committed reference files. The method isn't the problem here; Haiku's
execution of the reconstruction step (translating disassembly back into correct Python source by
hand) was insufficiently careful on 4 of 5 files, and its self-verification step either wasn't
actually run correctly or its result was misreported.

**Lesson for next time:** don't trust a "bytecode-verified" claim from a reconstruction task without
independently re-running the comparison. This is exactly what happened here — the check caught it.

## Restoring / redoing

The original `.pyc` files are untouched at `Tools/__pycache__/*.cpython-314.pyc` — nothing was lost,
this is purely about the quality of a reconstruction attempt. Redo with a stronger model, using the
same disassembly output as a starting point, and *independently* re-verify with the positional
bytecode comparison before trusting the result — don't rely on the reconstructing agent's own
self-report.
