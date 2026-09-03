# Melodia Portfolio — Maintenance Guide

Rewritten 2026-08-20. The previous version described a pipeline that had stopped existing: it named
`my-site-clean/` as source of truth (it had decayed to 11 stray PNGs and was gitignored), pointed the
deploy at a git worktree that no longer had a `.git` (so every deploy since silently copied into a
dead directory), and targeted a `gh-pages` branch the site repo does not have. Every command in its
Quick Reference table either failed or wrote somewhere nothing read.

---

## Quick Reference

| Task | Command |
|------|---------|
| **Deploy the site** | `.\deploy\quick-deploy.ps1` |
| **Deploy with a message** | `.\deploy\quick-deploy.ps1 -Message "Your message"` |
| **Preview without deploying** | `.\deploy\sync_site_to_github.ps1 -Deploy $false` |
| **Import new UE5 renders** | `.\Tools\ingest-renders.ps1` |
| **Import + deploy** | `.\Tools\ingest-renders.ps1 -Deploy` |
| **Scaffold an environment page** | `.\Tools\add-environment.ps1 -Slug "your-env"` — see Known gaps |

---

## How the site actually works

The live site is **a separate GitHub repo**, `fromage3900/my-site`, published by GitHub Pages:

```
https://fromage3900.github.io/my-site/wix/index.html
```

Pages is configured with `build_type: workflow` — an **Action on that repo's `main` branch** builds
and publishes. There is **no `gh-pages` branch**; the Pages API still reports one in its `source`
field, but the branch does not exist and writing to it does nothing.

```
BS_GodFile/                     <- you edit here
  wix/                          <- 34 pages + 44 css/js assets   (tracked)
  components/  projects/        <- embeddable fragments          (tracked)
  generated/                    <- render assets                 (mostly untracked)
       |
       |  .\deploy\quick-deploy.ps1
       v
C:\EnvironmentPortfolio\_github_deploy\    <- a CLONE of fromage3900/my-site
       |
       |  git commit + git push origin main
       v
GitHub Action on my-site main  ->  Pages  ->  live (~1 min)
```

### One-time setup

The deploy target must be a real clone. Create it once:

```bash
git clone https://github.com/fromage3900/my-site.git C:\EnvironmentPortfolio\_github_deploy
```

`sync_site_to_github.ps1` refuses to run and prints this command if the target is missing or its
`origin` is not the my-site repo. It also hard-resets the clone to `origin/main` before syncing, so a
half-finished earlier deploy cannot leak into the next one.

> There is a stale `BS_GodFile/_github_deploy/` directory (938 files, no `.git`, gitignored). It is
> the corpse of the old worktree. Nothing reads it. Do not edit it, and do not use it as the deploy
> target — the target lives one level up, in `C:\EnvironmentPortfolio\`.

### What syncs, and what deliberately does not

`$dirsToSync = @("wix", "components", "projects", "generated")`

**`content` is deliberately excluded.** Windows paths are case-insensitive, so a `content` entry
resolves to this project's UE **`Content\` tree — 26,591 asset files**. The old sync list contained
it, which would have copied the entire game project into the public site. The script now hard-fails
if `content` reappears in that list.

The site's own `content/` (`site-copy.json`, `site-plates.json`), plus `public/`, `application/` and
`tools/`, exist **only in the my-site repo** — they are not mirrored into BS_GodFile. Edit those in
the clone and commit them there. Only `wix/`, `components/` and `projects/` round-trip through here.

---

## Common tasks

### 1. Deploy

```bash
.\deploy\quick-deploy.ps1
```

Syncs, commits, pushes to my-site `main`. The Pages Action publishes from there — allow about a
minute, then hard-refresh (Ctrl+Shift+R).

To see what *would* deploy without committing:

```bash
.\deploy\sync_site_to_github.ps1 -Deploy $false
```

### 2. Import new UE5 renders

After capturing to `Saved/Portfolio/`:

```bash
.\Tools\ingest-renders.ps1
```

Sorts into `generated/assets/` by type — `.webm`/`.mp4` to `landscape-loops/`, prop and ornament
stills to `props/` or `ornaments/` by filename heuristic, everything else to `unreal/`.

### 3. Edit page copy

Edit the HTML in `wix/` directly. The main pages:

| File | Purpose |
|------|---------|
| `index.html` | Home — hero, environment grid |
| `application-hub.html` | Integrated level routes & Echo DCC bridge |
| `pcg-system-impact.html` | L_FallenMoon PCG scatter survey |
| `sakura-case-study.html` | Sakura Dream breakdown |
| `space-cathedral.html` | Space Cathedral breakdown |
| `cosmic-orrery.html` | Cosmic Orrery breakdown |
| `baroque-grotto.html` | Baroque Grotto breakdown |
| `surreal-architecture.html` | Surreal architecture systems |
| `shader-breakdowns.html` | Master Toon Universal + material instances |
| `zbrush-breakdown.html` | ZBrush sculpt breakdown |
| `geometry-nodes.html` | Geometry Nodes pipelines |
| `world-bible.html` | World bible |
| `recruiter-one-sheet.html` | Recruiter one-sheet |
| `resume.html` | Resume |

`wix/` holds **34 pages**; the live `index.html` nav links **8** of them. The rest are reachable only
by direct URL. Surfacing more is a nav edit in `wix/index.html` and `wix/melodia-site-nav.js` — the
pages already exist and are already styled.

### 4. Add a page to the nav

The nav is hardcoded in each page's `<header>`. Add `<a href="your-page.html">Section</a>` to the
`<nav class="nav-links">` block.

---

## Encoding — read before editing any `.ps1`

Every script here must be saved as **UTF-8 *with* BOM** and CRLF.

Windows PowerShell 5.1 (which is what runs on this machine) assumes the system ANSI codepage when a
file has no BOM. Any em-dash, arrow or box-drawing character then decodes as mojibake, and the stray
bytes terminate string literals early. On 2026-08-20 both `Tools/ingest-renders.ps1` and
`Tools/add-environment.ps1` were found to be **syntactically invalid for exactly this reason** — they
could not run at all, independent of their broken paths. Adding a BOM fixed both with no content
change.

Parse-check a script before committing it. Run this in PowerShell, swapping in the file you touched
— it prints `OK` or the parse errors:

```
$e=$null; [void][System.Management.Automation.Language.Parser]::ParseFile((Resolve-Path 'deploy\sync_site_to_github.ps1').Path,[ref]$null,[ref]$e); if($e){$e|ForEach-Object{$_.Message}}else{'OK'}
```

---

## Known gaps

- **`add-environment.ps1` cannot run.** It reads `wix/environment-template.html`, which does not
  exist anywhere in the repo. The script parses and its paths are now correct, but it will fail at
  its template check until someone authors that template. Scaffold new pages by copying an existing
  environment page for now.
- **Website ship is Blocked**, not in progress — `_ROADBLOCKS_2026-07-31.md` C8, reconciled against
  `_PORTFOLIO_SHIP_CHECKLIST.md`. It waits on owner-supplied hero renders. Nav and copy work can
  proceed; final sign-off cannot.
- **`generated/` is nearly empty here** (1 tracked file). Render assets live in the my-site clone.
  `ingest-renders.ps1` writes into `generated/assets/` locally, and the sync carries it up.

---

## Troubleshooting

**"is not a git clone of the site repo"** — run the one-time `git clone` above. The target is
`C:\EnvironmentPortfolio\_github_deploy`, *not* the dead `BS_GodFile/_github_deploy/`.

**Edits not showing live** — did the deploy print "N file(s) changed"? If it said "No changes",
confirm you edited under `wix/` and not in the clone. Then allow ~1 min for the Action and
hard-refresh.

**Push failed** — GitHub connectivity from this workstation is intermittent (the README says the
same). Retry before diagnosing. `git -C C:\EnvironmentPortfolio\_github_deploy pull origin main`
then re-deploy.

**Images 404** — the asset must exist under `generated/assets/` here and survive the sync. Check the
clone after deploying.

---

## Best practices

- **Edit in `wix/`.** Never edit the deploy clone directly — the next sync hard-resets it.
- **Pull before you push.** The live site has been ahead of the tracked copy before; on 2026-08-20,
  57 of 78 files were behind live and deploying would have regressed the public site.
- **Preview first** with `-Deploy $false` on anything structural.
- **Save `.ps1` as UTF-8 with BOM** and parse-check it (see Encoding).
- **Never add `content` to `$dirsToSync`.**
