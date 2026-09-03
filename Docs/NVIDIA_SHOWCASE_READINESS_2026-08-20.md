# NVIDIA Showcase — Site + Render Readiness (2026-08-20)

Verified against the LIVE site and the live editor. Read-only audit; nothing
synced, deployed, or captured. Two decisions need you (§4).

## 1. LIVE 404s — 3 are linked from index.html

Checked `https://fromage3900.github.io/my-site/wix/` directly (not inferred from
disk):

| Page | Live | Linked from index.html? | Matters for NVIDIA |
|---|---|---|---|
| `melusina-agent-harness.html` | **404** | **YES** | **Critical** — the MATH whitepaper |
| `dashboards.html` | **404** | **YES** | Medium |
| `project_health.html` | **404** | **YES** | Medium |
| `nous-research-packet.html` | **404** | no | Low for NVIDIA |
| everything else on index.html | 200 | — | fine |

**3 clickable dead links on your landing page.** The harness page is the one the
NVIDIA packet leads with as agent-orchestration evidence.

Note: `NVIDIA_DEVREL_PACKET_2026-08-20.md:75` already recorded the harness 404 and
told you to use `agent-dashboard-t3d.html` + the GitHub repo instead. That
workaround still holds — `agent-dashboard-t3d.html` is live and 200.

Also corrected: a disk-only comparison suggested `pipeline.html`,
`melodia-gameplay-loop.html` and `melodia-stage-character.html` were broken too.
They are **live and fine**. Trust the HTTP check, not the file diff.

## 2. Root cause: two divergent wix/ trees

| Tree | Pages | Role |
|---|---|---|
| `C:\EnvironmentPortfolio\wix\` | 48 | your working copy — where edits happen |
| `C:\EnvironmentPortfolio\BS_GodFile\wix\` | 34 | what `sync_site_to_github.ps1` actually deploys |

`sync_site_to_github.ps1:22` sets `$source = Split-Path -Parent $PSScriptRoot`,
i.e. `BS_GodFile/`. So anything authored in root `wix/` never ships.

Divergence is **bidirectional** — this is why it must not be blind-synced:

- **19 pages** exist only in root `wix/` (never deployed)
- **5 pages** exist only in `BS_GodFile/wix/` (deployed, absent from your copy):
  `baroque-grotto`, `melodia-hero-embed`, `melodia-passport-embed`,
  `melodia-project-card`, `melodia-smooth-scroll`
- **27 shared pages differ in content**, and the newer side is split — 11 newer in
  root, 16 newer in BS_GodFile

A one-directional copy either way silently reverts real work. That is why I
stopped here.

## 3. Renders — editor is live, but nothing is new

Live surface confirmed:
```
Monolith 0.20.3 · UE 5.8 CL-55116800 · 1402 actions · 24 namespaces · port 9316
UnrealEditor.exe running (pid 18468, ~8.7 GB)
```

Existing render inventory: `generated/assets/unreal/` holds **32 PNGs, all dated
Jul 31 or earlier** (source timestamps Jun 27 / Jul 09). Content includes hero
level plates, `materials-grid-showcase` sheets (2048²), `pcg-heatmap.png`,
`scene-sakuradream-full.png`.

**Nothing has been captured today.** If the showcase needs fresh plates, that
capture hasn't started.

### Known capture limitations (from `UNREAL_CAPTURE_GAPS.md`) — plan around these
- No **Detail Lighting** mode and no **unlit/albedo-only** pass → sculptural
  showcase and PBR breakdown sheets can't be auto-captured
- No **G-buffer export** (roughness/metallic/AO/specular) → no automated PBR
  channel breakdowns
- `capture_scene_preview` renders in **isolated preview worlds**, so it ignores
  level lighting AND level-global post-process — **Toon outlines will be missing**
  from asset previews. For anything showing the Substrate Toon spine, capture in
  the placed level, not via asset preview.
- Water master ignores wave displacement in preview worlds (no distance fields)
- Niagara needs `seek_time` warmup; particle layout is not reproducible run-to-run

The Toon-outline gap is the one most likely to quietly ruin an NVIDIA material
plate — the whole pitch is the 138-material Toon spine.

## 4. Decisions needed from you

**A. Which wix/ tree is source of truth?** Options, least to most invasive:
   1. Cherry-pick only `melusina-agent-harness.html` (+ `dashboards.html`,
      `project_health.html`) into `BS_GodFile/wix/` → kills the 3 index 404s,
      touches nothing else. **Lowest risk before a showcase.**
   2. Root wins: sync 19 missing + 11 root-newer, preserve the 5 BS-only pages.
   3. Repoint `sync_site_to_github.ps1` at the repo root instead of copying.

**B. What am I capturing for NVIDIA?** Environments / Melusina character /
   material spine / PCG — and at what res and aspect.

## 5. Recommendation if you just want it working

Option A1 + deploy. Three file copies, kills every linked 404 on the landing page,
zero risk of reverting divergent work. Then handle the tree unification *after* the
showcase, not during it.

## 6. Facts, with how each was verified

| Claim | Verified by |
|---|---|
| 3 linked 404s + 1 unlinked | `urllib` HTTP status against live gh-pages |
| Deploy source is `BS_GodFile/` | `sync_site_to_github.ps1:22` |
| 48 vs 34 pages | `os.listdir` on both trees |
| 27 shared pages differ | SHA-256 per file, both trees |
| Editor live, 1402 actions | `monolith_status` JSON-RPC on :9316 |
| 32 renders, none newer than Jul 31 | `ls -lat generated/assets/unreal/` |
| Capture gaps | `UNREAL_CAPTURE_GAPS.md` §1-3 |
