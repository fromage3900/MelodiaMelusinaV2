# FlowerSpring → Substance Painter pipeline (verified 2026-09-01)

Full authoring chain: Houdini geometry → baked variant maps → Blender assembly/FBX →
**automated Substance Painter .spp generation**. Every stage below has been run
end-to-end; the .spp files exist and open with fills pre-wired.

> Status: 5/5 FlowerSpring variants saved (`all_saved=true` in
> `painter_build_done.json`). Wired per dress set: BaseColor / Normal / Height /
> Roughness / Metallic + uniform gold (crown) / uniform blush (wings).
> Open TODO: add Emissive + AO channels to the dress texture sets (see §7).
>
> **2026-09-01 addition:** the same pipeline (adapted in
> `Tools/Houdini/sea_above_reef/shorewake_painter_startup.py`) also built the
> original Shorewake dress as a 48-texture-set project —
> `substance_staging/Shorewake48/spp/Shorewake48.spp`, wired with the
> 2026-08-31 bake-of-record maps. Succeeded first run using this doc's
> gotchas table. See `substance_staging/Shorewake48/README_Shorewake48.md`.

## 1. Stage map (run order)

| # | Stage | Script (repo) | Output |
|---|-------|---------------|--------|
| 1 | Skirt silhouette presets | `Tools/Houdini/sea_above_reef/flowerspring_skirt_silhouette.py` | `flowers_outfit/FS_SkirtDraped_{cascade,tulip,bloom}.obj` |
| 2 | Crown + wings rebuild | `Tools/Houdini/sea_above_reef/flowerspring_crown_wings_v2.py` | `FS_Crown_v2.obj`, `FS_Wings_v2.obj` |
| 3 | Blender assembly + QA renders + FBX export | `Tools/Houdini/sea_above_reef/flowerspring_assemble_qa_v3.py` | `substance_staging/FlowerSpring/meshes/*.fbx` + `flowers_outfit/qa_v3/` |
| 4 | Variant maps (5 × 8 @2048) | `Tools/Houdini/sea_above_reef/flowerspring_variant_maps.py` | `substance_staging/FlowerSpring/textures/<V>/T_<V>_*.png` |
| 5 | ORM split (R/G/B → AO/Rough/Metal) | `Tools/Houdini/sea_above_reef/flowerspring_orm_split.py` | `T_<V>_AO/_Roughness/_Metallic.png` |
| 6 | Painter .spp builder | `Tools/Houdini/sea_above_reef/flowerspring_painter_startup.py` (deployed as startup module) | `substance_staging/FlowerSpring/spp/FlowerSpring_<V>.spp` ×5 |

Commands (PowerShell, from repo root):

```powershell
$H = "C:/Program Files/Side Effects Software/Houdini 22.0.368/bin/hython.exe"
& $H Tools/Houdini/sea_above_reef/flowerspring_skirt_silhouette.py
& $H Tools/Houdini/sea_above_reef/flowerspring_crown_wings_v2.py
& "C:/Program Files/Blender Foundation/Blender 4.5/blender.exe" -b --factory-startup -noaudio `
    --python Tools/Houdini/sea_above_reef/flowerspring_assemble_qa_v3.py
python Tools/Houdini/sea_above_reef/flowerspring_variant_maps.py
python Tools/Houdini/sea_above_reef/flowerspring_orm_split.py
# stage 6: see §5
```

## 2. Geometry contract

- Units: **meters end-to-end** (dress-meter space; no unit hacks anywhere).
- Seed: `20260831`. Head center `(0, -0.02, 1.52)`; wing anchors behind
  shoulder blades `y = +0.16` (behind = +Y back).
- UVs are **standard Houdini vertex-level `uv` attributes** (`hou.attribType.Vertex`,
  `hou.Vector3`). A *point-level* custom `uv` attrib does NOT export as OBJ `vt`.
- Source dress panels already carry `uv` (from the OBJ `vt`) — guard:
  `if geo.findVertexAttrib("uv") is None: geo.addAttrib(...)`.
- Procedural pieces must assign UV per **face vertex**: `vtx = f.addVertex(pt)`
  then `vtx.setAttribValue("uv", hou.Vector3(u, v, 0))`.
- Petal/vein/cup islands use reserved UV space (veins/cups at negative v,
  gems in a per-index 0.1-wide strip) so islands never overlap.

## 3. Verification one-liners (run after every geometry rebuild)

```powershell
# OBJ: UVs present AND every face line references vt
foreach($f in @("FS_SkirtDraped_cascade","FS_Crown_v2","FS_Wings_v2")){
  $p="Saved/Audit/melusina_lookdev/flowers_outfit/$f.obj"
  $vt=(Select-String -Path $p -Pattern "^vt " -AllMatches).Count
  $noVT=(Select-String -Path $p -Pattern "^f\s+v//" -AllMatches).Count
  "$f vt=$vt noVT=$noVT"   # vt>0 and noVT=0 required
}
```

```python
# FBX: import back in Blender headless and print uv_layers per object
# (pattern used in %TEMP%/opencode/uvcheck*.py — see scripts below)
bpy.ops.wm.read_homefile(use_factory_startup=True)
# purge default Cube first, then:
bpy.ops.wm.fbx_import(filepath=<fbx>)
for o in bpy.data.objects:
    if o.type == "MESH":
        print(f"UVCHK {o.name}: uvs={[l.name for l in o.data.uv_layers]} polys={len(o.data.polygons)}")
```

Rule 20 applies: presence checks above confirm coverage; Painter's own
project-creation is the absence check (it hard-refuses UV-less meshes).

## 4. Substance Painter facts (11.1.1, this workstation)

- **Install:** `C:/Program Files/Adobe/Adobe Substance 3D Painter/Adobe Substance 3D Painter.exe`
- **No `--python` CLI flag** in this build. Automation = **startup modules**.
- **Documents root is OneDrive-redirected**: startup modules live in
  `C:/Users/froma/OneDrive/Documents/Adobe/Adobe Substance 3D Painter/python/startup/`
  (NOT `C:/Users/froma/Documents/`). Confirmed via the Painter log at
  `C:/Users/froma/AppData/Local/Adobe/Adobe Substance 3D Painter/log.txt`.
- A `pythonjsonserver.qml` plugin exists in the log but does not open a
  listen port by default (checked via `netstat`) — not usable as-is.

## 5. The .spp builder (stage 6)

`flowerspring_painter_startup.py` is the master. Deployment cycle:

```powershell
Stop-Process -Name "Adobe Substance 3D Painter" -Force -ErrorAction SilentlyContinue
Start-Sleep -Seconds 3
Remove-Item "Saved/Audit/melusina_lookdev/substance_staging/FlowerSpring/painter_build_steps.log",
            "Saved/Audit/melusina_lookdev/substance_staging/FlowerSpring/painter_build_done.json" `
    -ErrorAction SilentlyContinue
Copy-Item Tools/Houdini/sea_above_reef/flowerspring_painter_startup.py `
    "C:/Users/froma/OneDrive/Documents/Adobe/Adobe Substance 3D Painter/python/startup/flowerspring_build_plugin.py" -Force
Start-Process -FilePath "C:/Program Files/Adobe/Adobe Substance 3D Painter/Adobe Substance 3D Painter.exe"
# poll for the done marker:
$marker="Saved/Audit/melusina_lookdev/substance_staging/FlowerSpring/painter_build_done.json"
while(-not (Test-Path $marker)){ Start-Sleep -Seconds 25 }
```

Builder behavior:
1. Defers 12 s after launch (QTimer), closes any auto-restored session project,
2. For each variant `FlowerSpring, GildedLoom, SilkWaterfall, CherryBlossomWood, StarlitA Abyss`:
   `project.create(mesh, settings)` → `execute_when_not_busy(wire)` →
   import per-variant maps → insert fill per texture set → `set_source` per
   channel → `save_as(spp/<name>.spp)` → close (except variant 1, left open).
3. Writes `painter_build_done.json` (schema `v4`, per-variant `results` with
   per-stack `wired`/`skipped`) + `painter_build_steps.log`.
4. **Deletes the deployed startup module only on full success** — master stays
   in the repo, so a failed run is re-runnable without re-creating anything.

## 6. Painter Python API gotchas (each cost a debug cycle — do not re-learn)

| Gotcha | Fact |
|---|---|
| `project.create` is **asynchronous** | Returns immediately. Chain follow-up work with `project.execute_when_not_busy(cb)`. `is_busy()` can false-negative early (reported False at ~1 s while creation was still running). |
| `project.save_as` while busy | Throws `ProjectError` ("Save is disabled when Substance 3D Painter is busy"). Always wrap in `execute_when_not_busy`. |
| Session restore | Painter may auto-open a project at launch → `project.create` fails with "one is already opened". Call `project.close()` first if `project.is_open()`. |
| `textureset.all_texture_sets()` → `TextureSet` objects | `layerstack.InsertPosition.from_textureset_stack()` needs a **`Stack`** — use `ts.get_stack()`. |
| `resource.import_project_resource(path, Usage)` | Do NOT pass `name=`/`group=` (validation `ValueError`). |
| `res.identifier` | **Method — needs `()`**. Passing the bound method gives `ValueError: Unknown parameter type. Only resource.ResourceID, colormanagement.Color ...` |
| `fill.set_source(None, Color(...))` | `None` channel = mono-channel context only → "Only valid in mono channel context". For multi-channel sets: `fill.set_source(textureset.ChannelType.BaseColor, colormanagement.Color(r, g, b))`. |
| Emissive / AO | Not enabled by default on new texture sets → `EditionContextException: Channel N isn't valid in this context`. Fix: `stack.add_channel(ChannelType.Emissive, ChannelFormat...)` before wiring (TODO). |
| Startup double-fire | Module import AND `start_plugin()` both fire → guard with a module-level `_schedule_once()` flag. |
| Mesh without UVs | Project creation blocks forever on a modal ("mesh has no UVs") — the startup module hangs at "creating project". That stall IS the UV diagnostic. |

## 7. Known TODOs

- Add Emissive + AO channels to `M_FS_Shirt` / `M_FS_Skirt` sets and wire
  `T_<V>_Emissive.png` / `T_<V>_AO.png` (matters for StarlitAbyss star field).
- `uniform_fill` for crown sets only colors BaseColor; Roughness/Metallic
  starter values (e.g. 0.35 / 0.2) would give better first-paint feel.
- `flowerspring_painter_spp.py` (the pre-startup-module headless attempt) is
  superseded — kept only as reference for the non-UI path that 11.1.1 doesn't support.

## 8. Output inventory (authoritative paths)

```
Saved/Audit/melusina_lookdev/substance_staging/FlowerSpring/
  meshes/FS_FullAssembly_cascade.fbx    # 4 objects, all UV'd (crown+skirt+wings+shirt)
  meshes/FS_Dress_Draped_cascade.fbx    # skirt+shirt only
  meshes/FS_Crown_v2.fbx  FS_Wings_v2.fbx
  textures/<Variant>/T_<V>_{BaseColor,Normal,ORM,Height,Emissive,Iridescence,Sheen,Motif_N}.png
  textures/<Variant>/T_<V>_{AO,Roughness,Metallic}.png   # ORM split
  textures/FlowerSpring/v1_kit_legacy/                    # 9 v1 maps, kept
  spp/FlowerSpring_<Variant>.spp          # 5 files, ~54 MB each, fills pre-wired
  painter_build_done.json                 # per-variant results + wired/skipped detail
  painter_build_steps.log                 # execution trace
  export/<Variant>/                       # Painter export root (preset per project)

Saved/Audit/melusina_lookdev/flowers_outfit/
  FS_SkirtDraped_{cascade,tulip,bloom}.obj  FS_Crown_v2.obj  FS_Wings_v2.obj
  qa_v3/                                    # QA renders + assembly manifest
```

Variants: FlowerSpring (cream/gold/peach/blush), GildedLoom (champagne→deep gold,
metallic 0.45), SilkWaterfall (pearl/ice/silver-blue), CherryBlossomWood (petal
blush/rose + warm wood), StarlitAbyss (deep indigo, star-silver emissive).
Colour families reused from `Saved/Audit/copernicus_cymatic/`.
