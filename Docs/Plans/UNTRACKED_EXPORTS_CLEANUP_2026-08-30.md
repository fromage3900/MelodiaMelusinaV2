# Untracked Exports Cleanup Spec

**Generated:** 2026-08-30 (overnight daemon)
**Source:** `Saved/Audit/untracked_exports_audit_2026-08-31.json`
**Mode:** Spec only — proposes .gitignore additions + quarantine moves.

---

## Already Handled (No Action Needed)

| Path | Why Handled |
|---|---|
| `Exports/` | `.gitignore:298` — all exports covered |
| `surreal_sweep/` | `.gitignore:303` |
| `surreal_sweep_wave2/` | `.gitignore:304` |
| `Plugins/HoudiniEngine/Binaries/`, `Intermediate/`, `Content/` | `.gitignore:309-311` |
| `.windows.txt`, `.windows2.txt`, `.windows3.txt` | Already moved to `Saved/Diagnostics/` |

---

## Remaining Untracked Entries (5 items)

These 5 files at repo root are NOT covered by any .gitignore pattern and have 0 runtime references:

| File | Size | Status | Recommendation |
|---|---|---|---|
| `gen_concepts.py` | small | scratch orphan | Quarantine → `Saved/Diagnostics/scratch_orphans/` |
| `gen_posters.py` | small | scratch orphan | Quarantine → `Saved/Diagnostics/scratch_orphans/` |
| `surreal_wardrobe_cops.py` | small | scratch orphan | Quarantine → `Saved/Diagnostics/scratch_orphans/` |
| `harp_flute_lyre_guides.md` | small | scratch doc | Quarantine → `Saved/Diagnostics/scratch_orphans/` |
| `research_harp_bow_refs.md` | small | scratch doc | Quarantine → `Saved/Diagnostics/scratch_orphans/` |

## Proposed Cleanup Actions

### Option A: Quarantine (Recommended)

Move all 5 to `Saved/Diagnostics/scratch_orphans/` (create if needed). They remain on disk for reference but are out of the repo root and won't appear in `git status`.

```bash
mkdir -p Saved/Diagnostics/scratch_orphans
git mv gen_concepts.py Saved/Diagnostics/scratch_orphans/
git mv gen_posters.py Saved/Diagnostics/scratch_orphans/
git mv surreal_wardrobe_cops.py Saved/Diagnostics/scratch_orphans/
git mv harp_flute_lyre_guides.md Saved/Diagnostics/scratch_orphans/
git mv research_harp_bow_refs.md Saved/Diagnostics/scratch_orphans/
```

### Option B: .gitignore (Alternative)

Add 5 entries to `.gitignore`:

```
# Scratch orphans (2026-08-30 cleanup)
gen_concepts.py
gen_posters.py
surreal_wardrobe_cops.py
harp_flute_lyre_guides.md
research_harp_bow_refs.md
```

**Trade-off:** Quarantine removes them from `git status` permanently and signals intentional cleanup. .gitignore is simpler but leaves cruft at repo root.

---

## Live-Referenced Files (NOT to be deleted)

| File | Reference | Action |
|---|---|---|
| `Exports/MelodySlime/SM_MelodySlime.fbx` | `DT_Burdens.json` references MelodySlime | Keep. Already gitignored via `Exports/` |
| `Exports/Starskiff/*.fbx` (10 files, 1.4GB) | harp_flute_lyre_guides.md references Starskiff hero vehicle | Keep. Already gitignored via `Exports/` |

---

## Summary

| Category | Count | Action |
|---|---|---|
| Already handled (gitignore/moved) | 9 | None |
| Scratch orphans to quarantine | 5 | Move to `Saved/Diagnostics/scratch_orphans/` |
| Live-referenced (gitignored) | 2 | Keep as-is |
| **Total from audit** | **16** | |