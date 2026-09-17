# VERIFICATION / LANDING PASS — 2026-09-17

## Verdict summary

| Claim | Verdict |
|-------|---------|
| 10 my-site heroes on disk | **PARTIAL** — 10 claimed files exist + 1 extra UE viewport; TD set includes 2 alt encodes |
| Audits on disk | **VERIFIED** under Saved/Audit |
| Audits in git / remote | **LOCAL-ONLY** (Saved/ gitignored) until Docs/Audits copy |
| SemesterEvidence bank | **LOCAL-ONLY** (Saved/ gitignored) |
| "Pushed to fromage" as git remote landing | **FALSE / STALE** — disk copy ≠ remote |

## Phase A — remotes

### MelodiaMelusinaV2 (`C:\EnvironmentPortfolio\BS_GodFile`)
- branch: `cleanup/pbr-twin-landing-2026-09-10`
- local HEAD: `c440d12bae22f7ebd0643ae28cc4af5ef38c24ec`
- origin remote branch SHA: `c2aa52563bc906df31e611661bd087a2b5caf977`
- origin/main: `dc3fe383f008a5cdba61b80ea6fef920364e5a05`
- dirty porcelain lines: 1943
- ahead of origin/main: yes (many); behind origin/main: yes
- evidence audits: NOT in commits (Saved/ ignored)

### my-site (`C:\Users\froma\my-site`)
- branch: `main`
- local HEAD at probe: `96f7395ff1a2b080dda3aa336a3970b1b134f9cc`
- origin/main after fetch: `cd73682fa52d519a422c8f11d7b81acd42c1da30`
- local was **behind** origin/main
- heroes path: untracked `public/melodia/melusina-morning-vfx/`

### MelodiaTouchDesigner (`C:\MelodiaTouchDesigner`)
- branch: `main`
- local HEAD: `a1ad7740270e8d9a218f0b5a968e021c104e7726`
- origin/main: `d73983388adf2a6add79738642c41f323883c9fc`
- local **ahead 5**, behind 0; dirty 138
- source plates for TD heroes: VERIFIED present under `scratch\portfolio_hero_renders\`

## Phase B — artifacts

| Path | Disk | git ls-files | Remote |
|------|------|--------------|--------|
| Saved/Audit/NIKKI_STYLE_...md | YES | 0 (ignored) | no |
| Saved/Audit/TD_RENDER_...md | YES | 0 (ignored) | no |
| Saved/SemesterEvidence/.../2026-09-17/ | YES (28 files) | 0 (ignored) | no |
| Docs/Audits/* (landing copy) | YES after this pass | pending commit | pending push |

## Phase C — heroes

ASSERT count==10 exists==10 melusina_lookdev==4 td_portfolio_master==6 for the advertised set.
All **staged-only** (zero page/manifest references in my-site).
Extra orphan: `UE_viewport_capture_142658_candidate.png`.
TD uniqueness caveat: H09/H10 are alt encodes of sheep pasture / siren harp (not new authored plates).

Sheep pasture = H06 (+ H09 alt)
Siren harp = H05 (+ H10 alt)
Water sanctuary = H07
Escher = H08

## Phase D — PCG / TD

Live unique basename containing PCG: **276** (raw 280).
Under `\PCG\` folders unique: **317**.
Offline claim 226: superseded by live recount.
Heatmap tooling: scripts in Content/Python + Tools/PCG + Figma UI heatmap textures; JSON heatmap_assets=10 was tool/spec hits.

## Phase E

Docs/Audits trackable copies created. my-site evidence branch push attempted in same pass.

## Remediation (same day)

- **my-site heroes:** REMOTE on `evidence/melusina-morning-heroes-2026-09-17` @ `99b0cf8089242559083d29370cff2e201f272dd0` (VERIFIED via ls-remote).
- **Melodia fat commit:** `38b5d964` on `cleanup/pbr-twin-landing-2026-09-10` includes Docs/Audits PLUS Content/VFX/ExternalActors/shaders — **do not merge as docs-only**.
- **This branch:** docs-only cherry of `Docs/Audits/*` from that commit onto `origin/main`. Prefer this PR for audit landing.
