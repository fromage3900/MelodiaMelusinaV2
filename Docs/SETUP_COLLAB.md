# Live Collaborative Level Designer -- 5-Minute Setup

> **Blender-only checkout. No Unreal project or plugin content.** Set up the
> Blender <-> UE5 live bridge for collaborative level design using sparse
> checkout. Only downloads the scripts, addons, and tools you need -- ~120 MB
> total. For MeshBlend, PCGEx, or any Unreal plugin work, use
> `bash deploy/collaborator_onboarding.sh lightweight` from
> [COLLABORATOR_SETUP.md](../COLLABORATOR_SETUP.md).

---

## Option A: Sparse Checkout (Recommended -- 50 MB)

```powershell
git clone --filter=blob:none --no-checkout https://github.com/fromage3900/MelodiaMelusinaV2.git MelodiaCollab
cd MelodiaCollab
git sparse-checkout init --cone
git sparse-checkout set `
  deploy/surreal_arch `
  deploy/surreal_world `
  deploy/surreal_os `
  deploy/surreal_greybox `
  Content/Python/gmm `
  Content/Python/material_lib.py `
  Tools `
  Docs/ONBOARDING_LIVE_COLLAB.md `
  Docs/ZUNZUN_FAMILY_INTEGRATION.md `
  Docs/ZUNDAMON_DESIGN_BIBLE.md `
  Docs/ZUNDAMON_NPC_SPEC.md `
  README.md `
  DOC_INDEX.md
git checkout
```

**What you get (~120 MB, verified 2026-08-11):**
- (check) SurrealArch Blender addon (procedural generation, live bridge, material bridge)
- (check) GMM game systems (Python combat/rhythm/roguelike rules)
- (check) All pipeline tools and scripts
- (check) Full documentation
- Γ¥î No .uasset files, .blend files, textures, or UE content

---

## Option B: Collaboration Kit Zip (If git sparse checkout is unavailable)

The `deploy/surreal_arch/` folder IS the Blender addon. Copy it to:
```
C:\Users\<you>\AppData\Roaming\Blender Foundation\Blender\5.2\scripts\addons\surreal_arch\
```

Also copy the root registration module:

```
deploy/surreal_architecture_gen.py
  -> Blender addons/surreal_architecture_gen.py
```

Then copy the companion folders:
```
deploy/surreal_world/  -> Blender addons/surreal_world/
deploy/surreal_os/     -> Blender addons/surreal_os/
deploy/surreal_greybox/-> Blender addons/surreal_greybox/
```

---

## Prerequisites

| Tool | Version | Download |
|------|---------|----------|
| Blender | 5.2+ | [blender.org](https://www.blender.org/) |
| Unreal Engine | 5.8 | Epic Games Launcher |
| VOICEVOX | 0.25+ | [voicevox.hiroshiba.jp](https://voicevox.hiroshiba.jp/) |
| VRM Importer (Blender) | 4.4+ | [GitHub](https://github.com/saturday06/VRM-Addon-for-Blender/releases) |

---

## Step-by-Step

### 1. Optional Unreal host
```
Use a separate full or UE-capable lightweight checkout for the Unreal host.
```
This Blender-only checkout intentionally does not contain
`BS_GodFile.uproject` or the project plugins. Do not use it to diagnose
MeshBlend or PCGEx installation failures.

### 2. Open Blender -- Verify the Addon
```
Open any .blend -> N-panel -> "Melodia Studio" tab should appear.
```
If it doesn't: Edit -> Preferences -> Add-ons -> search
`surreal_architecture_gen` -> enable **Melodia Studio**.

### 3. Start the Bridge
```
N-panel -> Melodia Studio -> Live Bridge -> Refresh Status -> Start Server
```
You should see: `Γ£ô LiveLink  Γ£ô BL MCP  Γ£ô UE MCP`

### 4. Generate & Send
```
1. Genome Carousel -> pick style -> Apply
2. Material Bridge -> Scan Slots -> Auto-Match
3. Live Bridge -> Send + Materials
4. In Unreal: /Game/LiveLink/ -- geometry with correct materials
```

---

## Two-Designer Workflow

| Role | Tool | What They Do |
|------|------|-------------|
| **Geometry Designer** | Blender | Procedural gen, mesh editing, materials, live sync |
| **Level Scripter** | Unreal | Blueprints, encounters, lighting, PCG, NPCs |

---

## Port Map

| Port | Service | Direction |
|------|---------|-----------|
| `9876` | BlenderMCP and LiveLink (shared port; use one live bridge at a time) | Blender <-> UE |
| `9316` | Monolith MCP | Any -> UE |
| `9317` | Legacy adapter | Do not use |
| `50021` | VOICEVOX -- NPC voices | Any -> VOICEVOX |

---

## Troubleshooting

| Problem | Fix |
|---------|-----|
| Melodia Studio tab missing | Enable `surreal_architecture_gen` / **Melodia Studio** in Blender preferences |
| Port 9876 "in use" | Close extra Blender instances via Task Manager |
| Materials gray in UE | `resolve_material_crosswalk.resolve_all()` in UE Python |
| No voices | Start VOICEVOX, run `Tools/generate_all_voices.py` |

---

Full guide: [Docs/ONBOARDING_LIVE_COLLAB.md](Docs/ONBOARDING_LIVE_COLLAB.md)
Character integration: [Docs/ZUNZUN_FAMILY_INTEGRATION.md](Docs/ZUNZUN_FAMILY_INTEGRATION.md)
NPC Blueprint spec: [Docs/ZUNDAMON_NPC_SPEC.md](Docs/ZUNDAMON_NPC_SPEC.md)


