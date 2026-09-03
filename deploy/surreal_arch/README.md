# Melodia Studio

Procedural architecture, ornament, and music-motif generator for **Blender 5.2**.
Generates geometry via Geometry Nodes, exports flat FBX for Unreal/UE5, and includes
stage visibility controls for portfolio and kitbash workflows.

**Product:** Melodia Studio  
**Preferences id:** `melodia_studio`  
**Enable as:** `surreal_architecture_gen` (monolith file name)  
**Operators:** `surreal_arch.*` / `mel_gn.*`  
**SSOT:** `deploy/surreal_arch/` + `deploy/surreal_architecture_gen.py`

---

## Install (school-ready)

```powershell
cd C:\EnvironmentPortfolio\BS_GodFile\deploy
.\install_melodia_studio.ps1          # default Blender 5.2
.\verify_melodia_studio.ps1 -SkipSmoke  # or full smoke queue
```

Manual equivalent: copy **both** `surreal_architecture_gen.py` and the `surreal_arch/`
package (plus `surreal_greybox/`, `surreal_world/`, `surreal_os/` siblings) into:

`%APPDATA%\Blender Foundation\Blender\5.2\scripts\addons\`

Then enable **Melodia Studio** / `surreal_architecture_gen` in Preferences.

Do **not** copy only `surreal_arch/` — the monolith entry module is required.

---

## First generation

1. Open a portfolio stage `.blend` or any mesh scene.
2. Press `N` → **Melodia Studio** tab.
3. Hub panel (Genome Carousel) → **Generate** / **Starlight** / **Sync & Reload** / **Studio Health**.
4. Nested: **GN Stack**, **Stage**, bridges, Living Portrait.

---

## N-panel tour

- **Genome Carousel** — hub; generate, starlight, solo, sync/reload, health. Shows live GN builder / category counts.
- **GN Stack** — 173 Melodia GN builders (27 hidden factory/PCG aliases) + curated presets (42 builders / 127 looks).
- **Stage** — Solo / Starlight / Beauty / Review Queue.
- **Site Publish** — Render & Upload beauty plate → `my-site-clean` + `site-plates.json` (optional git push OFF by default).
- **Live Bridge / Material Bridge** — LiveLink TCP **9876** (Start Server) vs agent **BlenderMCP Connect** (also 9876 — do not run both). Unreal Python **9316**. Legacy 9317 retired.
- **Living Portrait** — Melusina voice/viseme tools.
- **Architecture Picker / Level Design / Style Genome / UV / Export** — overhaul tools. The Modifier properties drawer is **legacy** (off unless Preferences → Show legacy Modifier panel).

---

## Verify without AI chat

```powershell
.\verify_melodia_studio.ps1
.\run_blender_smoke_queue.ps1
```

Failures write JSON under `Saved/Audit/` (`gn_builder_health_last.json`, `blender_smoke_last.json`).

---

## Notes

- Target Blender: **5.2**. Legacy 5.1 AppData installs are stale — re-run `install_melodia_studio.ps1`.
- MCP is optional (classroom default = install + verify). Live BlenderMCP uses port **9876**.
- Do not use `G:\EnvironmentPortfolio` mirrors as SSOT.
