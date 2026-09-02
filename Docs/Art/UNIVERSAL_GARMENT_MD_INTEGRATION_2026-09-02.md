# Marvelous Designer (MD) Integration Seam — Universal Garment System (2026-09-02)

**Status:** Seam spec + install audit — ON DISK, seed `20260902`. No editor, no `.uasset`, single audio writer untouched.
**Authority:** `AGENTS.md` evidence culture · `Docs/Research/EMERGING_TOOLCHAIN_MASTER_INDEX_2026-08-31.md` (external tool = *say-so, don't fake*) · `Docs/Art/CYMATIC_GARMENT_NIKKI_PIPELINE_2026-09-02.md` (48-panel → 10 garment layers → cymatic modes) · `Docs/Art/FARAWAY_MOTHER_CLOTH_TIERS_2026-09-02.md` (Nikki cloth tiers A–D).
**Manifest: `Saved/Audit/universal_garment/md_integration_report.json` sha256 `8d83569c69f0d6d17e207f7fe88171a40d0e6cb8cb342cea8c874986f754d63b` (seed `20260902`).**

---

## 0. The single most important honest finding

> **The installed Marvelous Designer is GUI-only and has NO headless/scriptable automation path.**
> Zero `.pyd`, zero `.py`, an EMPTY `PythonLib\` directory, stdlib-only embedded CPython 3.7
> (`python37.zip` holds only `.pyc`), and the only executables are the app,
> `QtWebEngineProcess.exe`, and `Uninstall.exe`. **We do NOT have an MD script API.** Any MD drape
> must be driven interactively (operator or desktop/UI automation). This install DOES ship real
> native USD import/export (Omniverse resolver + OmniUsd exporter) plus FBX / Alembic / OBJ, so MD
> works as an interactive drape-sim authoring tool with a solid round-trip — but the draping step
> is not automatable against this install. We will not pretend otherwise.

---

## 1. On-disk install audit

**Install root:** `C:/Program Files/Marvelous Designer Enterprise OnlineAuth/`
(edition: **Marvelous Designer Enterprise**, OnlineAuth variant — entitlement-authenticated launcher).

### 1.1 Exported executables (3)

| Exe | Size | sha256 (seed 20260902) | Role |
|---|---|---|---|
| `MarvelousDesigner_Enterprise_Online.exe` | 190,190,840 | `2e12fd29...c08e` | Main MD application (OnlineAuth edition). Single app entry point — **no console/headless sibling exists.** |
| `QtWebEngineProcess.exe` | 592,632 | `57eb567b...7867` | Qt WebEngine helper (embedded browser for OnlineAuth flows) |
| `Uninstall.exe` | 208,346 | `491b19c1...a432` | Uninstaller — not an automation surface |

### 1.2 USD plugin files

- `usd/plugInfo.json` — standard USD Python-bindings package manifest: `{"Includes": ["*/resources/"]}` (sha `c285a05d...bb2d`).
- 27 USD plugin resource dirs under `usd/`: `ar, glf, hd, hdSt, hdx, hgiGL, ndr, sdf, usd, usdGeom, usdHydra, usdImaging, usdImagingGL, usdLux, usdMedia, usdRender, usdRi, usdRiImaging, usdShade, usdSkel, usdSkelImaging, usdUI, usdVol, usdVolImaging` (each has a `resources/plugInfo.json`).
- `usd/plugins/omniverse/resources/plugInfo.json` (sha `c6821a94...d0fea`) + library `omni_usd_resolver.dll` (sha `e6b682ef...4a11`) defining **OmniUsdResolver** (`ArResolver`), **OmniUsdWrapperFileFormat** (`.omni`), **OmniUsdObjectFileFormat** (`.live`).
  - This is **NVIDIA's Omniverse USD integration** (resolver + omni/live bridge) — the mechanism behind MD's native USD import/export, NOT a user scripting API.
- **Native import/export confirmed** by `ChangeLog_MarvelousDesigner.txt`: *"Export garment simulation data to USD"*, *"USD Single/Multi Objects export option"*, *"USD file Compatibility"*, texture-into-UE fixes, skeleton-in-USD fix, *"USD: Support the Unified UV Coordinates"*.
- Other geometry engines verified on disk: `Alembic.dll`, `libfbxsdk.dll` (Autodesk FBX SDK) + native OBJ. → **MD can round-trip USD, FBX, Alembic, OBJ.**

### 1.3 Python / .pyd / script surfaces

| Surface | Present | sha256 | Meaning |
|---|---|---|---|
| `python37.dll` | yes | `89d96d30...1d6` | Embedded CPython 3.7 interpreter (stdlib only) |
| `python37.zip` | yes | `09ce140b...3a9` | CPython 3.7 stdlib, **precompiled `.pyc` only** (abc, argparse, …) — no MD module |
| `boost_python37-vc141-mt-x64-1_68.dll` | yes | `dce06de2...6ef6` | Boost.Python 1.68 bindings layer (legacy) |
| `PythonLib/` | **EMPTY** (0 entries) | `EMPTY_DIRECTORY` | Reserved for MD extension modules/scripts → **no MD API modules shipped** |
| `*.pyd` | **0** | — | none |
| `*.py` | **0** | — | none |
| `*.so` | **0** | — | none |
| CLI/batch/socket-automation exe | **none** | — | no `_Console`, no headless driver |

**Census:** 145 `.dll`, 3 `.exe`, **0** `.pyd`, **0** `.py`, 27 USD `plugInfo.json`.

**Automation-surface truth:** NO headless/scriptable path. Drape = **INTERACTIVE**.

---

## 2. Melodia Garment Drape Loop — recipe spec

Shorewake 48-panel slotted mesh → MD pattern/drape → USD/FBX back → UE.

**Source mesh (verified):**
`Saved/Audit/melusina_lookdev/bake/night_pkg_2026-08-31/SM_ShorewakeDress_48MAT_v2_slotted.obj`
(sha `5687c303...60f8`, Blender 5.2.1 LTS, **48 `g`-groups `SW_Dress_P01..P48`, 48 material slots, 183,741 verts, 186,955 faces**).

**Authoritative grouping:**
`Saved/Audit/melusina_lookdev/night_pkg_2026-08-31/garment_layers_manifest.json`
(sha `76fc9353...e00`) — **48 panels → 10 garment layers**: `M_Bodice_Torso/Front/Side/Upper`, `M_Collar`, `M_Shoulder_Trim`, `M_Shoulder_Ornament`, `M_Sleeve`, `M_Underskirt`, `M_Skirt_Full`.

| Step | Phase | Input → Action | Gate |
|---|---|---|---|
| 1 | Source prep (offline ✓) | Slotted OBJ → keep canonical; de-capped sewable panels per the 48→10 layer grouping | dry-run; MD project `.zpac` at `Saved/Audit/universal_garment/md_project/` |
| 2 | **Import into MD (INTERACTIVE)** | OBJ/FBX/USD → MD GUI auto-arrange → fabric presets per the 10 cymatic layers (bodice charmeuse/satin, skirt silk sheet, collar/ornament rigid lace) | operator session or desktop UI automation — **cannot be scripted** |
| 3 | Simulate drape | Patterns on Melusina silhouette (or scaled proxy) → MD drape sim; save `.zpac` | draped deformed mesh = the "true drape" |
| 4 | Export back (MD-native ✓) | Engines verified: **USD** (sim data, Single/Multi Objects, Unified UV), **FBX** (`libfbxsdk.dll`), **OBJ**, **Alembic** (`Alembic.dll`) | FBX primary for UE; USD where anim/flap sim cache matters |
| 5 | Import into UE (editor-bound) | Interchange (FBX) or engine USD importer → hook into verified family `M_Master_Nikki` / `M_Universal_Enhanced_Fabric` / `M_Master_Toon_Universal_Alpha`, per-layer MIs (naming per CYMATIC_GARMENT §4) | **never touch `Content/**/*.uasset` by script**; check Z-up/handedness on import |

### Chain diagram
```
[SM_ShorewakeDress_48MAT_v2_slotted.obj (48 panels, sha 5687c303)]
    │ 1. source prep (kept canonical)
    ▼
[garment_layers_manifest.json: 48 panels → 10 garment layers]
    │ 2. MD GUI import (INTERACTIVE — no automation)
    ▼
[MD drape sim on Melusina silhouette (.zpac project)]
    │ 3. native export: USD / FBX / OBJ / Alembic (engines verified)
    ▼
[Draped FBX/USD mesh]
    │ 4. UE Interchange / USD import (editor-gated)
    ▼
[10 MIs on M_Master_Nikki / M_Universal_Enhanced_Fabric / M_Master_Toon_Universal_Alpha]
    │ 5. cloth-tiers A–D binding (Chaos on Skirt_Full hero, WPO on support)
    ▼
[UNIVERSAL_GARMENT_MD_INTEGRATION_2026-09-02.md + md_integration_report.json (seed 20260902)]
```

---

## 3. Nikki doctrine §3 — cloth tiers A–D + MD seam policy

Cost ladder: `Material/WPO → Niagara/instanced → authored transform/spline → Chaos → Houdini VAT/cache → custom runtime`.
**Rule:** the piece carrying gameplay meaning gets the expensive solution; the rest support it cheaply.

| Garment | Tier | Solution | MD-drape role |
|---|---|---|---|
| `M_Bodice_Torso` | **C** | WPO micro-drape | low-interaction charmeuse; MD sims pose, WPO in-engine |
| `M_Bodice_Front` | **C** | WPO | yoke charmeuse |
| `M_Bodice_Side` | **C** | WPO | side torso |
| `M_Bodice_Upper` | **C** | WPO | bodice band |
| `M_Collar` | **A** | rigid authored | structured lace — MD outputs pattern only |
| `M_Shoulder_Trim` | **A** | rigid authored | armcap trim |
| `M_Shoulder_Ornament` | **A** | rigid studs | beads |
| `M_Sleeve` | **C** | WPO drape | MD sim gives rest pose |
| `M_Underskirt` | **C** | WPO | slip |
| `M_Skirt_Full` | **B** | **Chaos Cloth** (hero) | **MD drape is source of truth**; UE Chaos for collision |

**Seam policy:** MD supplies the **draped geometry** (rest/simulated pose). UE applies the cost:
A = rigid static from draped author pose · B/C = keep draped mesh, add Chaos (B) or WPO (C) · D = precomputed VAT where a drape-to-contraction event is authored (as in Faraway Mother terrain). Same cloth-tiers language as `FARAWAY_MOTHER_CLOTH_TIERS_2026-09-02.md` — no new authority.

---

## 4. Constraints honored

- No editor launched; no `Content/**/*.uasset` touched; no git clean/checkout. Offline specs/audits/manifests only.
- Single audio writer `MelodiaAudioReactivePresentationSubsystem` untouched — no second writer.
- Small verified master family only (`M_Master_Nikki / M_Universal_Enhanced_Fabric / M_Master_Toon_Universal_Alpha`); no new master.
- Every claimed fact verified on disk; sha256 recorded under seed `20260902`.
- Cross-ref: `Saved/Audit/universal_garment/_vellum_check.py` (prior-session Houdini Vellum presence probe — a headless *alternative* drape path outside MD; not wired here).