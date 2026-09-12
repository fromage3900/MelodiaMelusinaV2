# Read-Only Sweep — 2026-09-12 (execution record)

**Cause:** 3,868 `.uasset`/`.umap` files under `Content/` carried the ReadOnly
flag (bulk-stamped, mostly 09-02 vintage — likely an extraction/copy artifact,
not source-control discipline; this repo is git, which does not track the bit).
The editor cannot save over read-only files: `save_asset` returns False
silently, and aContent-Browser save escalates to fatal `appError`.

**Crashes attributed:** 2026-09-11 12:40 (`WBP_MelodiaQuillDialog`) and 20:39
(`WBP_MelodiaQuillChoiceEntry`, via Claireon MCP) — both read-only save
failures. Plus silent save failures on 8 Melusina assets (09-10, recovered by
per-file flag clear).

**Action:** cleared ReadOnly → Archive on all 3,868 files (attribute-only,
reversible, content-untouched). Remaining: 0.

**Worst affected:** EnvSandbox 1775, Melodia 1272, __ExternalActors__ 355,
_PROJECT 155, Surfaces_CC0 82, MelodiaIntegration 76, Characters 71.

**Freeze gate (proposed):** no ReadOnly `.uasset`/`.umap` under `Content/` —
re-run the one-liner below before any material/PIE session:
`Get-ChildItem Content -Recurse -File -Include *.uasset,*.umap | ? Attributes -match ReadOnly`

**Evidence level:** source-built (filesystem census + crash-log attribution).
