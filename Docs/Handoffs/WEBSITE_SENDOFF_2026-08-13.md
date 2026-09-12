# Website sendoff — 2026-08-13

Portfolio + recruiter sendoff for `C:\EnvironmentPortfolio\my-site-clean`. Game SSOT remains `BS_GodFile`. No second Unreal/Blender. No Flip rebake. Rhythm + Quill left locked.

Generated JSON (`geometry_nodes_pipelines.json`, `surreal_architecture_catalog.json`, passports) was **hand-edited**. No regen script was run: the live catalogs are not produced by a headless site script, and factory-startup Blender was skipped (PID 27644 is the live v22 GUI).

## Recruiter 30s (existing pages, no new micro-site)

| Page | Role |
|------|------|
| `wix/recruiter-one-sheet.html` | Primary 30s skim: who / shipped / stack / links |
| `wix/hiring-dossier.html` | Compact passport landing (was an “In Progress” stub) |
| `README.md` | Recruiter blurb at top |
| `application/infold-recruiter-message.md` | Paste-ready recruiter note |
| `generated/recruiter_review_path.json` | Review order |

## Pages touched

- `wix/index.html` — Recruiter nav + CTA
- `wix/recruiter-one-sheet.html`
- `wix/hiring-dossier.html`
- `wix/resume.html`
- `wix/application-hub.html`
- `wix/melodia-gameplay-loop.html`
- `wix/design-specs.html`
- `wix/melodia-stage-character.html`
- `wix/melodia-melusina.html`
- `wix/geometry-nodes.html`
- `wix/surreal-architecture.html`
- `content/site-copy.json`
- `content/site-manifest.json`
- `generated/passports/melusina_passport.json`
- `generated/geometry_nodes_pipelines.json`
- `generated/surreal_architecture_catalog.json`
- `generated/recruiter_review_path.json`
- `EDITING.md` — extra forbidden claims
- `README.md`

## Claims corrected

| Was | Now |
|-----|-----|
| Idle “not live until PIE” / implied Blender idle | Speed 0 = mocap `A_Melusina_Idle_Mocap_RootX`. Blender idle on disk, **not wired** |
| Flip Fluids / Cam_Beauty as live hair | Cine = Geometry Cache (Alembic 1–240) + Niagara drip. Gameplay = `SK_MelusinaHair`. **Not** Niagara 3D FLIP |
| Unreal B2 Cam_Beauty plates | Not claimed published. Local EEVEE Flip stills only; git push of plates historically off |
| Live `L_Melodia_Dreamstate` | Merged into `L_KaleidoNave`. Route = Morning → KaleidoNave |
| Nikki / Genshin SDF character ship | Hybrid **Komikaze + UE Toon**. Melodia Studio is the GN product |
| Recruiter 60+ PCG graphs / 19 showcase MIs | Dropped unverified counts |
| Broken `WBP_MainMenu` fonts | Fonts live: Syne / Instrument Serif via `F_Melodia_UI` |
| GN 24/165 or 73 looks | Already 165 / 12; presets **33/165 (20%)**, **100 looks** — leftover 24/73 not found on live pages |

Rhythm OWNER LOCK WORKED and QuillScript OWNER LOCK WORKED left as-is. A1 stock battle and Q/W/O/P harness still OPEN.

## Still needs a still / screenshot

- **Unreal B2 Cam_Beauty** plates — blocked / not published. Do not fake them.
- **Gameplay idle** viewport or PIE still of `A_Melusina_Idle_Mocap_RootX` (not collapsed Blender idle).
- **Gameplay hair** still of `SK_MelusinaHair` next to cine GC (so recruiters can see the fallback vs cine).
- **Niagara drip** socketed on `head_x` — cine GC import exists; socket still an editor owner step.
- **GitHub Pages push** of local Flip EEVEE stills (`melusina_flip_hair_eevee_glam_20260813_01/02.png`) — files are on disk; remote publication historically off.
- **P0 gate PIE proof** — 12 foundation gates remain unverified until PIE is recorded.

## Do not reopen

Rhythm, QuillScript, Flip rebake, second Blender.exe, second Unreal.
