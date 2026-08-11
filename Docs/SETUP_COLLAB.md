# Live Collaborative Level Designer -- 5-Minute Setup

> **No 300 GB download. No Unreal content.** Set up Blender <-> UE5 live bridge for collaborative level design using sparse checkout or the tiered onboarding scripts. Only downloads the scripts, addons, and tools you need -- ~50 MB to ~10 GB depending on tier.

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

**What you get (~50 MB):**
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

### 1. Open the Unreal Project
```
C:\EnvironmentPortfolio\BS_GodFile\BS_GodFile.uproject
```
Wait for shader compilation. The Monolith MCP starts automatically on port `:9316`.

### 2. Open Blender -- Verify the Addon
```
Open any .blend -> N-panel -> "Melodia Studio" tab should appear.
```
If it doesn't: Edit -> Preferences -> Add-ons -> search "surreal_arch" -> enable.

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
| `9876` | LiveLink -- FBX streaming | Blender -> UE |
| `9316` | UE MCP -- Python execution | Any -> UE |
| `9317` | Blender MCP -- genome control | Any -> Blender |
| `50021` | VOICEVOX -- NPC voices | Any -> VOICEVOX |

---

## Troubleshooting

| Problem | Fix |
|---------|-----|
| Melodia Studio tab missing | Enable surreal_arch addon in Blender preferences |
| Port 9876 "in use" | Close extra Blender instances via Task Manager |
| Materials gray in UE | `resolve_material_crosswalk.resolve_all()` in UE Python |
| No voices | Start VOICEVOX, run `Tools/generate_all_voices.py` |

---

Full guide: [Docs/ONBOARDING_LIVE_COLLAB.md](Docs/ONBOARDING_LIVE_COLLAB.md)
Character integration: [Docs/ZUNZUN_FAMILY_INTEGRATION.md](Docs/ZUNZUN_FAMILY_INTEGRATION.md)
NPC Blueprint spec: [Docs/ZUNDAMON_NPC_SPEC.md](Docs/ZUNDAMON_NPC_SPEC.md)


