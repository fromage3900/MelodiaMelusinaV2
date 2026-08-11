# Melodia Portfolio — Maintenance Guide

## Quick Reference

| Task | Command |
|------|---------|
| **Full deploy** (sync + commit + push) | `.\deploy\quick-deploy.ps1` |
| **Deploy with custom message** | `.\deploy\quick-deploy.ps1 -Message "Your message"` |
| **Import new UE5 renders** | `.\tools\ingest-renders.ps1` |
| **Import + auto-deploy** | `.\tools\ingest-renders.ps1 -Deploy` |
| **Create new environment page** | `.\tools\add-environment.ps1 -Slug "your-env"` |

---

## How the site works

### Architecture
```
BS_GodFile/
  my-site-clean/          ← Source of truth. Edit everything here.
    wix/                   ← All HTML pages
    content/               ← JSON data files (site-copy.json, site-plates.json, site-manifest.json)
    generated/assets/      ← Renders, webm loops, material images
    public/                ← Shared CSS, JS, fonts, icons
  _github_deploy/          ← Git worktree (auto-synced). DO NOT EDIT DIRECTLY.
```

### Deployment flow
```
Edit in my-site-clean/
       │
       ▼
deploy/quick-deploy.ps1   ← Syncs my-site-clean → _github_deploy worktree
       │
       ▼
Git commit + push          ← Live on GitHub Pages (~30 seconds)
       │
       ▼
https://fromage3900.github.io/my-site/wix/index.html
```

---

## Common Tasks

### 1. Deploy the site (after any edit)

The most important command. Run this after ANY change to make it live:

```powershell
.\deploy\quick-deploy.ps1
```

This will:
1. Sync all files from `my-site-clean/` to the `_github_deploy/` worktree
2. Stage changes, commit, and push to GitHub Pages
3. Site goes live at `https://fromage3900.github.io/my-site/`

### 2. Import new UE5 renders

After capturing screenshots from UE5 (Saved/Portfolio/):

```powershell
.\tools\ingest-renders.ps1
```

This copies new renders into `generated/assets/` organized by type:
- `.webm` → `landscape-loops/`
- Prop/ornament images → `props/` or `ornaments/`
- Everything else → `unreal/`

To import AND deploy in one step:

```powershell
.\tools\ingest-renders.ps1 -Deploy
```

### 3. Add a new environment

Use the scaffolding script to create a new environment page:

```powershell
.\tools\add-environment.ps1 -Slug "crystal-cavern"
```

Or run interactively (no parameters):

```powershell
.\tools\add-environment.ps1
```

**After creating the page, do these 6 things:**

1. **Replace hero images** — put your webm and poster in `generated/assets/landscape-loops/`
2. **Replace macro images** — put ornament/prop detail shots in `generated/assets/ornaments/` or `generated/assets/props/`
3. **Update OG image** — edit the `<meta property="og:image">` path in your new page
4. **Add to hub page** — add a card to the environment grid in `application-hub.html`
5. **Add to index page** — add a card to the environment grid in `index.html` (around line 79–96)
6. **Update site manifest** — add the environment entry to `content/site-manifest.json`

### 4. Update site copy

Edit any HTML page in `wix/`. The main pages are:

| File | Purpose |
|------|---------|
| `index.html` | Home page — hero, environment grid, Nikki-aligned section |
| `application-hub.html` | All environments landing |
| `sakura-case-study.html` | Sakura Dream environment breakdown |
| `space-cathedral.html` | Space Cathedral environment breakdown |
| `cosmic-orrery.html` | Cosmic Orrery environment breakdown |
| `baroque-grotto.html` | Baroque Grotto environment breakdown |
| `shader-breakdowns.html` | Master Toon Universal showcase + 22 material instances |
| `recruiter-one-sheet.html` | Targeted one-sheet for Infinity Nikki recruiters |
| `resume.html` | Professional resume |
| `pipeline.html` | Toolchain + infrastructure breakdown (sends game-dev signal) |

Data files in `content/`:
- `site-copy.json` — centralized page copy
- `site-plates.json` — hero plate mapping (environments → render paths)
- `site-manifest.json` — version info, environment stats, pipeline registry

### 5. Update environment stats

If you update a world's triangle count, draw calls, or materials:

1. Edit the stat row in the environment's page (`wix/your-env.html`)
2. Update the manifest (`content/site-manifest.json`) — this is used by the pipeline page
3. Deploy

### 6. Add a new page to navigation

The main nav (Home, Environments, Shaders, One-sheet, Resume) is hardcoded in every page's `<header>`.
To add a nav link:

1. Find the `<nav class="nav-links">` section in each HTML page
2. Add a new `<a href="your-page.html">Section name</a>`
3. Update the manifest (`content/site-manifest.json`)

---

## Pipeline Details

### Deploy script (`deploy/sync_site_to_github.ps1`)

Copies `my-site-clean/` to `C:\EnvironmentPortfolio\_github_deploy/` (git worktree), then:

```powershell
git add -A
git commit -m "Sync site updates"
git push origin main
```

### Render ingest (`tools/ingest-renders.ps1`)

Scans `BS_GodFile/Saved/Portfolio/` for new files, copies them into the correct subdirectory of `generated/assets/`, and optionally deploys.

### Environment scaffold (`tools/add-environment.ps1`)

Copies `wix/environment-template.html` to `wix/{slug}.html` and replaces all `%%TOKEN%%` placeholders with your values.

---

## Troubleshooting

### "Page shows 404 for images"

The site references assets at `../generated/assets/...` paths. These must exist in the `_github_deploy/` worktree. If missing:

1. Check the file exists in `my-site-clean/generated/assets/`
2. Run `.\deploy\quick-deploy.ps1` to sync
3. Verify in `_github_deploy/generated/assets/`

### "Deploy script says worktree not found"

The script expects the git worktree at `C:\EnvironmentPortfolio\_github_deploy\`. If it's missing:

```powershell
# From the EnvironmentPortfolio repo root:
git worktree add _github_deploy main
```

### "Git push failed"

Check:
- Are you authenticated with GitHub? `git push` should work if origin is set
- Is the worktree on the `main` branch? `cd _github_deploy && git branch`
- Try `git pull origin main` first, then re-run deploy

### "My edits aren't showing up on the live site"

1. Run `.\deploy\quick-deploy.ps1` — did it say "X files changed"?
2. If "No changes to deploy", check that you edited a file in `my-site-clean/`, not directly in `_github_deploy/`
3. Wait ~30 seconds for GitHub Pages to rebuild
4. Hard-refresh your browser (Ctrl+Shift+R / Cmd+Shift+R)

---

## Best Practices

- **Always edit in `my-site-clean/`** — never edit files directly in `_github_deploy/`
- **Deploy after every meaningful change** — keeps the site in sync
- **Test locally** before deploying: open `my-site-clean/wix/index.html` in a browser
- **Commit the source repo too** — `my-site-clean/` changes should also be committed to the main EnvironmentPortfolio repo for backup
- **Keep the manifest honest** — update `site-manifest.json` whenever you change environment stats
- **Use the template** — `tools/add-environment.ps1` handles all the boilerplate so you don't forget anything