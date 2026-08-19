# Live Collaborative Level Designer — 5-Minute Setup

> **Blender-only checkout. No Unreal project or plugin content.** Sets up the
> Blender ↔ UE5 live bridge for collaborative level design via sparse checkout —
> only the scripts, addons, and tools you need, ~120 MB. For MeshBlend, PCGEx, or
> any Unreal plugin work, use `bash deploy/collaborator_onboarding.sh lightweight`
> from [COLLABORATOR_SETUP.md](../COLLABORATOR_SETUP.md).

**Last verified: 2026-08-14.** Repo: `github.com/fromage3900/MelodiaMelusinaV2` (private).

---

## Option A: Sparse Checkout (Recommended — ~120 MB)

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

**What you get:**

- ✅ SurrealArch Blender addon (procedural generation, live bridge, material bridge)
- ✅ GMM game systems (Python combat/rhythm/roguelike rules)
- ✅ All pipeline tools and scripts
- ✅ Full documentation
- ❌ No `.uasset`, `.blend`, textures, or UE content

---

## Option B: Collaboration Kit Zip (if sparse checkout is unavailable)

The `deploy/surreal_arch/` folder **is** the Blender addon. Copy it to:

```
C:\Users\<you>\AppData\Roaming\Blender Foundation\Blender\5.2\scripts\addons\surreal_arch\
```

Also copy the root registration module:

```
deploy/surreal_architecture_gen.py  ->  Blender addons/surreal_architecture_gen.py
```

Then the companion folders:

```
deploy/surreal_world/    ->  Blender addons/surreal_world/
deploy/surreal_os/       ->  Blender addons/surreal_os/
deploy/surreal_greybox/  ->  Blender addons/surreal_greybox/
```

---

## Art assets — the S3 art drop

**This is the part that surprises people.** `Content/` is 65 GB on disk but only
~2,700 files (~2.7 GB) are in git. `.gitignore` blankets `Content/*` and re-includes a
hand-curated list, deliberately — see `.gitignore:116-159` for the reasoning.

**Consequence:** `L_KaleidoNave` and `L_MelusinaMorning` are tracked, but many meshes,
textures, and material instances they reference are **not**. A fresh clone opens those
levels with missing references and grey/pink assets. **That is expected.** It is not an
LFS fault and **no `git lfs pull` will fix it** — those assets were never committed.
Ignore any older troubleshooting text that blames LFS.

The authored environment art lives in S3 instead:

```bash
aws s3 sync s3://melodia-artdrop-322037002075/EnvSandbox/ Content/EnvSandbox/ --profile artdrop
```

**6,720 objects, 3.06 GiB** — authored art only. Egress is about **$0.28** for a full
pull; sync only the subfolders you need if you are iterating.

**Deliberately absent:** Megascans, Brushify, `_ThirdParty` (~38 GB) and
`Library/Migrated`. Those are vendor packs you re-fetch from Quixel/Brushify yourself —
this project does not redistribute them.

**Getting access:** ask the owner for a key on the IAM user `melodia-artdrop-reader`.
It is read-only (`s3:GetObject`, `s3:ListBucket`), scoped to that one bucket, and
revocable per person without affecting anyone else. Then:

```bash
aws configure --profile artdrop     # region: ca-central-1
```

Requires the AWS CLI v2. Verify with `aws --version` before asking for a key.

> The toon spine **is** tracked as of 2026-08-13 — 121 master materials and all 18
> `TP_*` toon profiles under `Content/EnvSandbox/Materials/{Masters,ToonProfiles}`
> (8.6 MB). Before that date they were excluded, which is why the material "fold"
> commits of 2026-08-12 contain zero `.uasset` files.

---

## Prerequisites

| Tool | Version | Download |
|------|---------|----------|
| Blender | 5.2+ | [blender.org](https://www.blender.org/) |
| Unreal Engine | 5.8 | Epic Games Launcher |
| AWS CLI | v2 | [aws.amazon.com/cli](https://aws.amazon.com/cli/) — only for the art drop |
| VOICEVOX | 0.25+ | [voicevox.hiroshiba.jp](https://voicevox.hiroshiba.jp/) |
| VRM Importer (Blender) | 4.4+ | [GitHub](https://github.com/saturday06/VRM-Addon-for-Blender/releases) |

> **Blender 5.1 is not supported** — that install is empty. Only 4.3, 4.5 and **5.2**
> have executables, and the full addon set runs on 5.2.

---

## Step-by-Step

### 1. Optional Unreal host

Use a separate full or UE-capable lightweight checkout for the Unreal host. This
Blender-only checkout intentionally does not contain `BS_GodFile.uproject` or the
project plugins — **do not use it to diagnose MeshBlend or PCGEx failures.**

### 2. Open Blender — verify the addon

```
Open any .blend -> N-panel -> "Melodia Studio" tab should appear.
```

If it doesn't: Edit → Preferences → Add-ons → search `surreal_architecture_gen` →
enable **Melodia Studio**.

### 3. Start the bridge

```
N-panel -> Melodia Studio -> Live Bridge -> Refresh Status -> Start Server
```

You should see: `✓ LiveLink   ✓ BL MCP   ✓ UE MCP`

### 4. Generate & send

```
1. Genome Carousel  -> pick style -> Apply
2. Material Bridge  -> Scan Slots -> Auto-Match
3. Live Bridge      -> Send + Materials
4. In Unreal: /Game/LiveLink/ -- geometry with correct materials
```

---

## Two-Designer Workflow

| Role | Tool | What they do |
|------|------|--------------|
| **Geometry Designer** | Blender | Procedural gen, mesh editing, materials, live sync |
| **Level Scripter** | Unreal | Blueprints, encounters, lighting, PCG, NPCs |

> **No file locking yet.** `GitSourceControl` is not enabled in the project (2,224
> lockable files, 0 locks ever held), so two people editing the same `.uasset` will
> conflict with no warning. Until it is enabled, coordinate by hand before touching
> shared assets.

---

## Port Map

| Port | Service | Direction |
|------|---------|-----------|
| `9876` | BlenderMCP and LiveLink (shared port — one live bridge at a time) | Blender ↔ UE |
| `9316` | Monolith MCP | Any → UE |
| `9317` | Legacy adapter | Do not use |
| `50021` | VOICEVOX — NPC voices | Any → VOICEVOX |

---

## Troubleshooting

| Problem | Fix |
|---------|-----|
| Melodia Studio tab missing | Enable `surreal_architecture_gen` / **Melodia Studio** in Blender preferences |
| Port 9876 "in use" | Close extra Blender instances via Task Manager |
| Materials grey in UE | `resolve_material_crosswalk.resolve_all()` in UE Python |
| Grey/pink assets after a fresh clone | Expected — run the S3 art drop sync above. Not an LFS problem. |
| `aws: command not found` | Install AWS CLI v2; the art drop needs it |
| `AccessDenied` on the art bucket | Your key is not on `melodia-artdrop-reader`, or you omitted `--profile artdrop` |
| No voices | Start VOICEVOX, run `Tools/generate_all_voices.py` |
| New C++ plugin not loading | New modules with reflected types need a **closed-editor** `Build.bat` pass — Live Coding cannot register them |

---

Full guide: [ONBOARDING_LIVE_COLLAB.md](ONBOARDING_LIVE_COLLAB.md)
Character integration: [ZUNZUN_FAMILY_INTEGRATION.md](ZUNZUN_FAMILY_INTEGRATION.md)
NPC Blueprint spec: [ZUNDAMON_NPC_SPEC.md](ZUNDAMON_NPC_SPEC.md)
