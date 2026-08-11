# Handoff — Transform Surreal Architecture → Melodia System

**Date:** 2026-07-12  
**Audience:** Next agent / DeepSeek / human co-pilot  
**Workspace:** `G:\EnvironmentPortfolio` · primary code in `BS_GodFile/`  
**Blender:** **5.1 only** (do not use 4.2 headless on Melodia stage)  
**Related chat:** [GN editable Melodia Studio](ffa3f1b9-a9b6-4d6f-9afe-3f047531b297)

---

## 0. One-sentence mission

Finish turning the **Surreal Architecture** Blender monolith into a coherent **Melodia Studio** product (editable Melodia GN + Studio UI + stage kitbash + website/Figma/UE continuity), without breaking Kitbash SSOT, Live Link, or dual-lineage HUD rules.

---

## 1. Identity map (do not confuse)

| Layer | Name | Truth |
|-------|------|--------|
| Product (UI) | **Melodia Studio** | Preferences name, N-panel category |
| Addon module id | `surreal_architecture_gen` | Unchanged forever unless migration epic |
| Operators | `surreal_arch.*` | Unchanged |
| Monolith file | `deploy/surreal_architecture_gen.py` | RNA host + generate; **freeze new kits here** |
| Overhaul package | `deploy/surreal_arch/` | All new behavior via `integration.patch_monolith` |
| Melodia GN library | `deploy/surreal_arch/melodia_gn/` | Stackable MEL_* node groups + bake |
| Route switch | `melodia_gn_route.try_apply_melodia_gn` | Prefer Melodia GN when `prefer_melodia_gn` |
| Stage SSOT | `KitbashExport/Melodia_Portfolio_Stage_v4.blend` | Live authoring |
| Gothic FBX SSOT | `KitbashExport/OrnamentalMeshes/SM_Orn_*.fbx` | Flat; `store_live: false` |
| Musical FBX SSOT | `KitbashExport/MusicalOrnamentalMeshes/SM_Orn_*.fbx` | Flat; do not invent folder hierarchy as SSOT |
| Game | Melodia Melusina (UE MelodiaCore) | Rhythm JRPG — separate from ornament SKU |
| Website | `my-site-clean/wix/` | Lookbook + Melusina HUD proof |
| Figma | Grandmaster `Yx8ud7n39NdWZvnNvo4Xlf` | Tokens + Game UI + MG Chrome |

**Contract doc:** [`deploy/surreal_arch/MONOLITH_CONTRACT.md`](../deploy/surreal_arch/MONOLITH_CONTRACT.md)  
**Cockpit doc:** [`Docs/BLENDER_MELODIA_COCKPIT.md`](BLENDER_MELODIA_COCKPIT.md)  
**Gate 3 UI:** [`Docs/MELODIA_STUDIO_GATE3_UI_UNLOCK.md`](MELODIA_STUDIO_GATE3_UI_UNLOCK.md)

---

## 2. Edit / sync / ports (hard rules)

### Paths

| Role | Path |
|------|------|
| **Edit SSOT** | `G:\EnvironmentPortfolio\BS_GodFile\deploy\` |
| Live Blender 5.1 addons | `%APPDATA%\Blender Foundation\Blender\5.1\scripts\addons\` |
| Sync | `deploy\sync_surreal_to_live.ps1` |

After any `surreal_arch/` or monolith edit:

```powershell
powershell -ExecutionPolicy Bypass -File "G:\EnvironmentPortfolio\BS_GodFile\deploy\sync_surreal_to_live.ps1"
```

Then in Blender: disable/enable **Melodia Studio** addon, or restart Blender 5.1.  
Do **not** leave `BS_GodFile\deploy` on `sys.path` as a second copy — it breaks `register` and causes dual-load bugs.

### Ports

| Port | System | Use |
|------|--------|-----|
| **9877** | BlenderMCP (`user-blender` / Cursor) | Agent ↔ open Blender session |
| **9876** | Live Link Unreal | Scratch → `/Game/LiveLink/` only — never ornament/wardrobe SSOT |

Ensure MCP:

```text
# In open Blender 5.1 (Text Editor / MCP execute):
exec(open(r"G:\EnvironmentPortfolio\BS_GodFile\Tools\ensure_blender_mcp.py").read())
```

Cursor MCP server: `user-blender` → tool `execute_blender_code`. User must have Blender open with stage + MCP started.

### Constraints still in force

- KitbashExport SSOT stays **flat**; product mirror may copy but `store_live: false`.
- Collection visibility toggles preferred over mass object hide.
- Do **not** recreate deleted review/WIP folders as SSOT.
- Do **not** flip store_live / monetize rhythm game casually.
- No dual-lineage HUD (MelodiaCore Rhythm WBPs only for Melusina).
- TrebleClef / MusicalCorner historically hand-remake sensitive — prefer live GN edit over blind FBX overwrite unless asked.

---

## 3. Current state (honest, 2026-07-12 evening)

### What already works

- Preferences + N-panel branded **Melodia Studio**; Gate 2/3 unlocked.
- Overhaul kits (gothic, zen, escher, scifi, …) patch via `integration.py`.
- `melodia_gn/` builders + `ARCH_TO_GN` route for music/ornament/castle aliases.
- Editable spawn: `Tools/spawn_editable_ornament_gn.py`  
  - Collections: `OrnamentGN_Editable` (gothic fix-list) + `MusicalGN_Editable` (musical).  
  - `apply_modifiers=False`, `auto_update=True`.
- Cleanup: `Tools/cleanup_stage_keep_editable_gn.py` purges review meshes, respawns editable GN.
- Stage visibility prefers those two collections (`stage_visibility.py`).
- Tutorial icons fixed for Blender 5.1: `TRIA_LEFT` / `TRIA_RIGHT` / `FILE_REFRESH` (was crashing on `ARROW_RIGHT`).

### Why “new GNs not editable in Melodia Studio” (resolved understanding)

1. **Studio crash** — invalid tutorial icons broke N-panel `draw` (fixed; re-register/restart if stale).
2. **UX mismatch** — SurrealArch node groups often expose only **Geometry**; real knobs are on `obj.surreal_arch_props` + Generate / Auto Update, **not** Modifier sockets.
3. **Melodia GN Stack** (`melodia_gn/stack.py`) is a **separate** MEL_* stack UI — not the SurrealArch RNA path.
4. Some Melodia GN bakes still fail on Blender 5.1 socket APIs (`NodeSocketVectorXYZ`, Translation `.inputs`) for note_head / staff — spawn may fall back to SurrealArch natives.
5. Live stage may be missing some musical `_edit_*` (MusicalCorner + MelodyToken_01–03 were missing at last probe; 13/17 present).

### Known hazards

- Setting `auto_update=True` on many objects can cascade regenerates (SheetMusicRail MelodiaGN attach spam).
- Addon disable/enable can fail if `surreal_arch` imported from deploy without `register`.
- Base mesh staying at 8 verts is **normal** when modifiers are live; trust **evaluated** vert count.

---

## 4. Target architecture — “full Melodia system”

```text
                    ┌─────────────────────────────┐
                    │  Figma Grandmaster (tokens, │
                    │  Game UI 12–13, MG Chrome)  │
                    └──────────┬──────────────────┘
           Code Connect / sync │  ART_SOURCE lock
                               ▼
┌──────────────┐      ┌────────────────┐      ┌─────────────────┐
│ my-site-clean│◄────►│ portfolio      │◄────►│ UE MelodiaCore  │
│ wix Melodia  │      │ package JSON   │      │ WBP + EnvSandbox│
└──────┬───────┘      └───────▲────────┘      └────────▲────────┘
       │ plates/passports     │                        │ FBX import
       ▼                      │                        │
┌──────────────────────────────────────────────────────┴──────────┐
│ Blender 5.1 Melodia Studio (surreal_architecture_gen + surreal_arch)│
│  • RNA props + Melodia Studio N-panel                             │
│  • SurrealArch GN (legacy/catalog) OR MelodiaGN MEL_* (preferred) │
│  • Stage v4 · OrnamentGN_Editable · MusicalGN_Editable            │
│  • MCP 9877 · Live Link 9876 (scratch only)                       │
└───────────────────────────────────────────────────────────────────┘
```

### Transformation pillars (priority order)

| # | Pillar | Done means |
|---|--------|------------|
| A | **Melodia GN as default** | Musical + ornament arches build MEL_* with **exposed sockets** + Studio RNA sync |
| B | **Studio UI IA** | One coherent Melodia Studio: Stage / Wardrobe / Accessories / Photo / Generate / GN Stack; no tutorial crashes; Figma icons via `icon_loader.py` |
| C | **Editable authoring loop** | Select `_edit_*` → change props or GN sockets → live update → optional bake to Kitbash flat FBX |
| D | **Website continuity** | Stage plates + passport embeds + geometry-nodes / surreal-architecture sheets stay honest |
| E | **Figma bridge** | Tokens + Game filigree stay SSOT; Studio icons/chrome pull from same language |
| F | **UE catch-up** | Ornament/musical import + Melusina HUD BindWidgets (designer) — no dual HUD |

---

## 5. Website context

| Area | Path / notes |
|------|----------------|
| Site root | `my-site-clean/wix/` |
| Tokens CSS | `melodia-tokens.css` (luxury stack: Syne / Instrument Serif / Bricolage / Azeret) |
| Melusina HUD proof | `melodia-melusina.html` + `melodia-game-ui.js/css` |
| Nav / chrome | `melodia-site-nav.js`, `melodia-site-chrome.css` |
| Orrery web mirror | `melodia-orrery-system.js` |
| Generated embeds | `my-site-clean/generated/design-system/` (hero, passport) |
| GN pipeline honesty | `my-site-clean/generated/geometry_nodes_pipelines.json` |
| Figma↔site notes | `my-site-clean/wix/FIGMA_SITE_SYNC.md` |
| Plates → site | `Tools/melodia_stage_shot.py`, `run_melodia_plate_batch.py` → passports under `generated/passports/` |

**Do not** claim full Figma↔Wix auto-sync; Code Connect is selector map honesty.

AAA site/HUD plan: [`Docs/MELODIA_FIGMA_AAA_SYSTEMS_PLAN_2026-07-12.md`](MELODIA_FIGMA_AAA_SYSTEMS_PLAN_2026-07-12.md)  
Luxury + Nikki motion: [`Docs/MELODIA_LUXURY_UI_FILIGREE_NIKKI_MOTION_PLAN_2026-07-12.md`](MELODIA_LUXURY_UI_FILIGREE_NIKKI_MOTION_PLAN_2026-07-12.md)

---

## 6. Figma integrations

| Item | Value |
|------|--------|
| File | https://www.figma.com/design/Yx8ud7n39NdWZvnNvo4Xlf/Untitled |
| File key | `Yx8ud7n39NdWZvnNvo4Xlf` |
| Doc | [`FIGMA_GRANDMASTER.md`](../FIGMA_GRANDMASTER.md) |
| Tokens | `melodia-design-system/tokens.json` → `pipeline/figma/` |
| Sync | `Tools/sync_figma_design_doc.ps1` (+ optional `-PostToFigma` with `FIGMA_API_TOKEN`) |
| Code Connect | `pipeline/figma/code_connect_map.json` |
| Game UI export | `pipeline/figma/export_melodia_game_ui_assets.py` |
| Cursor MCP | `plugin-figma-figma` — skills: `/figma-use`, `/figma-generate-design`, `/figma-code-connect`, etc. |
| Studio icons | `deploy/surreal_arch/icon_loader.py` (Gate 3 polish — Figma PNGs) |

Pages that matter for Melodia system:

- **01–02** tokens/type  
- **05** Wix embeds  
- **08** asset slots  
- **12–13** Game UI + Magical Girl chrome (Batch N ornate filigree; Batch O reactivity)

Respect `ART_SOURCE.json` locks — do not overwrite ornate atlases without `--force-procedural` / `--ornate-only`.

---

## 7. Blender MCP connection (agent ops)

1. Open Blender **5.1** with `Melodia_Portfolio_Stage_v4.blend`.
2. Enable BlenderMCP addon; Start Server on **9877** (or run `ensure_blender_mcp.py`).
3. In Cursor, use MCP server **`user-blender`** → `execute_blender_code`.
4. Prefer short Python snippets; write audits to `Saved/Audit/*.json`.
5. After deploy edits: sync script → reload addon in Blender → re-probe with MCP.
6. Never confuse MCP (agent control) with Live Link 9876 (UE scratch sync).

Useful MCP probes:

```python
import bpy
print(bpy.data.filepath)
print([o.name for o in bpy.data.objects if o.name.startswith("_edit_SM_Orn_")])
```

```python
# Evaluated verts (not base mesh)
o = bpy.data.objects.get("_edit_SM_Orn_TrebleClef")
dg = bpy.context.evaluated_depsgraph_get()
eo = o.evaluated_get(dg); me = eo.to_mesh(); print(len(me.vertices)); eo.to_mesh_clear()
```

---

## 8. Key file index

| Path | Role |
|------|------|
| `deploy/surreal_architecture_gen.py` | Monolith RNA + generate |
| `deploy/surreal_arch/integration.py` | `patch_monolith` / `register_overhaul` |
| `deploy/surreal_arch/branding.py` | PRODUCT_NAME, N_PANEL_CATEGORY |
| `deploy/surreal_arch/melodia_gn_route.py` | ARCH_TO_GN routing |
| `deploy/surreal_arch/melodia_gn/*.py` | MEL_* builders + stack + bake |
| `deploy/surreal_arch/genome_carousel.py` | Melodia Studio panels |
| `deploy/surreal_arch/stage_visibility.py` | Stage presets + GN editable cols |
| `deploy/surreal_arch/tutorial.py` | Tutorial overlay (icons fixed) |
| `deploy/surreal_arch/icon_loader.py` | Figma icons for Studio |
| `Tools/spawn_editable_ornament_gn.py` | Spawn live editable ornaments |
| `Tools/cleanup_stage_keep_editable_gn.py` | Purge review + respawn |
| `Tools/ensure_blender_mcp.py` | MCP 9877 |
| `Tools/prep_ornament_music_mesh_session.py` | Authoring session prep |
| `Tools/regenerate_*_ornaments_surreal_arch.py` | FBX bake pipelines |

---

## 9. Open work queue (concrete)

1. **Confirm Studio draws** without tutorial traceback after restart.
2. **Respawn missing** `_edit_SM_Orn_MusicalCorner` + MelodyTokens via spawn script.
3. **Expose Melodia GN sockets** for SurrealArch-routed musical types OR wire RNA → modifier inputs in Studio draw.
4. **Fix Blender 5.1 Melodia GN bake** for `NOTE_HEAD` / `SHEET_MUSIC_RAIL` (Vector/Translation API).
5. **Unify edit UX:** select editable ornament → Melodia Studio shows arch-specific props + “Open GN Stack” if MEL_* attached.
6. **Gate 3 polish:** Figma icons, demote leftover PROPERTIES drawers.
7. **Website:** refresh geometry-nodes / surreal-architecture sheets if editable GN story changes.
8. **Optional:** headless smoke `deploy/surreal_arch/smoke_harness.py` after route changes.

---

## 10. Copy-paste prompts (agents)

Use these as full first messages. Replace nothing unless noted.

---

### Prompt A — Master orchestrator (full transformation)

```text
You are continuing Melodia System work in G:\EnvironmentPortfolio\BS_GodFile.

Read and obey:
- Docs/HANDOFF_SURREAL_TO_MELODIA_SYSTEM_2026-07-12.md
- deploy/surreal_arch/MONOLITH_CONTRACT.md
- Docs/BLENDER_MELODIA_COCKPIT.md

Mission: Transform Surreal Architecture into a coherent Melodia Studio system.
Rules:
- Blender 5.1 only. Edit SSOT = deploy/. Sync with deploy/sync_surreal_to_live.ps1.
- Do NOT add new kits to surreal_architecture_gen.py — extend surreal_arch/ and melodia_gn/.
- Operators stay surreal_arch.*; product name Melodia Studio.
- KitbashExport FBX SSOT stays flat; store_live false.
- MCP = 9877 (user-blender). Live Link 9876 = scratch only.
- Prefer Melodia GN (prefer_melodia_gn) with exposed sockets; SurrealArch RNA remains host.
- Do not recreate deleted review/WIP folders as SSOT.
- Do not start GN review loops unless asked.

Phases:
1) Verify MCP + stage + Melodia Studio draws (tutorial icons TRIA_*).
2) Complete MusicalGN_Editable + OrnamentGN_Editable (all intended _edit_* live).
3) Fix Melodia GN Blender 5.1 bake for note_head/staff; route TREBLE_CLEF/NOTE_*/SHEET_* through MEL_* with sockets.
4) Studio UX: selecting _edit_* shows arch props + GN Stack when MelodiaGN present; auto_update without cascade spam.
5) Sync docs/site honesty in geometry_nodes_pipelines.json if behavior changes.
6) Report audits under Saved/Audit/.

Start by probing Blender MCP for filepath, _edit_ count, and whether tutorial draw still errors.
```

---

### Prompt B — Melodia GN technical (Blender-only)

```text
Focus: Melodia GN library + routing only.

Context: deploy/surreal_arch/melodia_gn/, melodia_gn_route.py, quality_props.prefer_melodia_gn.
Blender 5.1 — NodeSocketVectorXYZ / Translation .inputs break some music builders; NOTE_HEAD and SHEET_MUSIC_RAIL often fall back to SurrealArch natives. SurrealArch modifiers typically expose only Geometry; users think GNs are "not editable."

Tasks:
1. Fix music.py (and bake) so MEL_music_note_head, MEL_music_treble_clef, MEL_music_staff build cleanly on 5.1 with named INPUT sockets.
2. Ensure try_apply_melodia_gn attaches MelodiaGN modifier and does not fight SurrealArch (clear order: MelodiaGN preferred OR SurrealArch — pick one primary per arch).
3. Wire melodia_gn/stack.py so Melodia Studio GN Stack edits work on _edit_SM_Orn_* objects.
4. Sync to live via sync_surreal_to_live.ps1; verify via MCP execute_blender_code.
5. Do not overwrite KitbashExport FBX unless explicitly asked; keep apply_modifiers=False for editable stage objects.

Write Saved/Audit/melodia_gn_editability.json with before/after socket lists and eval vert counts.
```

---

### Prompt C — Melodia Studio UI / Gate 3

```text
Focus: Melodia Studio N-panel IA and stability.

Read: Docs/MELODIA_STUDIO_GATE3_UI_UNLOCK.md, deploy/surreal_arch/genome_carousel.py, branding.py, tutorial.py, icon_loader.py, stage_visibility.py.

Tasks:
1. Ensure tutorial.py never uses invalid Blender 5.1 icons (use TRIA_LEFT/RIGHT, FILE_REFRESH, etc.).
2. When active object is _edit_SM_Orn_*, Studio surfaces surreal_arch_props for that arch_type and MelodiaGN sockets if present.
3. Optional: load Figma-exported icons via icon_loader.py for Stage/Wardrobe/Photo headers.
4. Demote leftover monolith PROPERTIES drawers that compete with Melodia Studio.
5. Sync + MCP smoke: open N-panel draw without Python traceback.

Do not redesign Unreal HUD in this pass.
```

---

### Prompt D — Editable ornaments stage pass

```text
Focus: live editable ornaments on Melodia_Portfolio_Stage_v4.blend.

Scripts: Tools/spawn_editable_ornament_gn.py, Tools/cleanup_stage_keep_editable_gn.py.
Collections: OrnamentGN_Editable, MusicalGN_Editable.
MCP port 9877.

Tasks:
1. Ensure MCP connected; open stage filepath.
2. Run cleanup or spawn so all intended gothic + musical _edit_* exist (include MusicalCorner + MelodyToken_01–03).
3. apply_modifiers=False, auto_update=True, but avoid regenerate cascade storms.
4. Isolate viewport to Studio/Cameras/Lights_Nikki + the two GN editable collections.
5. Save stage. Write Saved/Audit/editable_ornament_gn_spawn.json.

Do not recreate MusicalOrnaments_Review / OrnamentFix_Review as SSOT. Do not overwrite flat Kitbash FBX.
```

---

### Prompt E — Website + portfolio honesty

```text
Focus: website / dossier continuity with Melodia Studio GN story.

Paths: my-site-clean/wix/, my-site-clean/generated/geometry_nodes_pipelines.json, FIGMA_SITE_SYNC.md.
Plans: Docs/MELODIA_FIGMA_AAA_SYSTEMS_PLAN_2026-07-12.md.

Tasks:
1. Update geometry_nodes_pipelines.json if editable Melodia GN / MusicalGN_Editable is now the live authoring story.
2. Keep sheets honest: Melodia Studio = SurrealArch product skin; Melodia GN = preferred route; no fake GN_UniversalScatter claims.
3. Ensure melodia-melusina / hub links still match FIGMA_GRANDMASTER type SSOT (Syne stack).
4. Do not flip store_live. Do not invent Figma API automation that is not wired.

Deliver a short PR-style summary of site file diffs only.
```

---

### Prompt F — Figma + Studio chrome bridge

```text
Focus: Figma Grandmaster → Melodia Studio / web chrome.

File key: Yx8ud7n39NdWZvnNvo4Xlf
Docs: FIGMA_GRANDMASTER.md, pipeline/figma/, deploy/surreal_arch/icon_loader.py.
Use Figma MCP (plugin-figma-figma) with /figma-use skill before use_figma writes.
Respect ART_SOURCE.json locks for Batch N ornate atlases.

Tasks:
1. Inventory Game/MusicalFiligree + NoteGlyph assets needed for Studio icons or web.
2. Export or map icons into icon_loader expected folder; wire 2–3 Studio panel headers.
3. Confirm Code Connect map entries for any new web classes.
4. Do not publish library overwrite without user OK. Do not regenerate ornate atlas without --force flags.

Output: manifest of icon paths + which Studio panels consume them.
```

---

### Prompt G — Blender MCP reconnect / triage

```text
Blender MCP triage for Melodia.

Expected: Blender 5.1, Melodia_Portfolio_Stage_v4.blend, BlenderMCP on 9877.
Tool: Cursor MCP user-blender execute_blender_code.
Script: Tools/ensure_blender_mcp.py
Live Link 9876 is unrelated — do not stop it unless asked.

1. If MCP fails, instruct user to Start Server on 9877; run ensure_blender_mcp.py in Blender.
2. Probe filepath, addon surreal_architecture_gen enabled, melodia_studio panels present.
3. List _edit_SM_Orn_* and eval vert counts for TrebleClef + one gothic.
4. Catch any N-panel draw exceptions (tutorial icons).
5. Report blockers only; then stop.
```

---

### Prompt H — UE ornament / HUD follow-up (after Blender stable)

```text
Only after Melodia Studio editable GN is stable.

UE side:
- gothic: py Content/Python/import_ornament_fbx.py --prep
- musical: py Content/Python/import_ornament_fbx.py --musical --prep
- Mobile HUD shell: Content/Python/author_melodia_battle_mobile.py (BindWidgets = designer)
Docs: Docs/BLENDER_MELODIA_COCKPIT.md, Docs/MELODIA_FIGMA_AAA_SYSTEMS_PLAN_2026-07-12.md

Do not use Live Link for ornament SSOT. Do not dual-lineage Minimal HUD for Melusina.
```

---

## 11. Definition of done (Melodia system v1)

- [ ] Melodia Studio N-panel draws with zero tutorial/icon tracebacks on Blender 5.1  
- [ ] All intended `_edit_SM_Orn_*` present under OrnamentGN_Editable / MusicalGN_Editable  
- [ ] Musical arches prefer Melodia GN with **editable sockets** OR clear Studio RNA that regenerates without cascade  
- [ ] Selecting an editable ornament makes the edit path obvious in Melodia Studio (not “empty Geometry only”)  
- [ ] deploy ↔ live sync clean; no dual `sys.path` deploy ghost module  
- [ ] MCP 9877 documented and working; Live Link 9876 untouched for SKU  
- [ ] Website GN pipeline JSON honest  
- [ ] Figma Grandmaster remains token/Game UI SSOT; Studio icons optionally bridged  
- [ ] Kitbash flat FBX only updated when user requests bake/export  

---

## 12. Quick commands cheat sheet

```powershell
# Sync addon
powershell -ExecutionPolicy Bypass -File "G:\EnvironmentPortfolio\BS_GodFile\deploy\sync_surreal_to_live.ps1"

# Spawn editable GN (in Blender or -P)
# blender KitbashExport/Melodia_Portfolio_Stage_v4.blend -P Tools/spawn_editable_ornament_gn.py

# Cleanup keep editable
# blender ... -P Tools/cleanup_stage_keep_editable_gn.py

# Figma sync (optional post)
.\Tools\sync_figma_design_doc.ps1
```

```python
# Blender: ensure MCP
exec(open(r"G:\EnvironmentPortfolio\BS_GodFile\Tools\ensure_blender_mcp.py").read())
```

---

*End of handoff. Prefer this file + MONOLITH_CONTRACT over chat memory.*
