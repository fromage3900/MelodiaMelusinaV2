# Marvelous Designer Python Surface Probe — 2026-09-02

**Probe target:** scriptable integration seam with the Marvelous Designer Enterprise Online install.
**Install:** `C:/Program Files/Marvelous Designer Enterprise OnlineAuth/`
**Mode:** offline, read-only. No editor, no `.uasset`, no MD execution.
**Evidence JSON:** `Saved/Audit/universal_garment/md_python_surface_probe.json` (seed `20260902`).

---

## 1. Does MD export a Python API module? **NO.**

Honest capacity report. I inspected the full bundled Python surface headlessly with
`./.venv/Scripts/python.exe` (Python 3.11) reading `python37.zip` and `file`/`strings`
over the install. Findings:

| Surface | Finding | Verdict |
|---|---|---|
| `python37.zip` | 612 entries, **pure stdlib CPython 3.7** (precompiled `.pyc`). Unknown-toplevel scan returns only stdlib noise: `__phello__.foo`, `macpath`, `site-packages`(→ only `README.txt`), `tty`. `site-packages/` is **empty**. | Stdlib only — **no custom module** |
| `PythonLib/` | **Empty directory** (no files). | No user module surface |
| `.py` files anywhere | `find` over whole install → **zero** `.py`, zero `.pyc` outside the zip. | No scripts |
| `site-packages` dirs | None anywhere in install. | No extension packages |
| `usd/plugins/omniverse` | Only `resources/plugInfo.json` — an empty USD plugin manife, no `md`/garment export plugin and no Python plugin. | No MD python plugin |
| `boost_python37-vc141-mt-x64-1_68.dll` + `python37.dll` | Present. `strings` shows **no** `marvelous`/`md.py`/`import md` binding symbols. | Embedded interpreter infra only |
| CLI / batch / headless | Only executables: `MarvelousDesigner_Enterprise_Online.exe` (a Qt5WebEngine **GUI** PE32+), `QtWebEngineProcess.exe`, `Uninstall.exe`. No `mdcl`, no `.sh`/`.bat` automation entrypoint. | **No headless/CLI surface** |

**Conclusion:** MD bundles a private embedded CPython 3.7 + Boost.Python + full USD
(`usd.dll`, `usdGeom`, `usdSkel`, `tf.dll`, Alembic, libfbxsdk) for its **internal**
(Omni/USD partner) use only. It exposes **no** file-based, importable Python API module,
**no** user scripting entrypoint, and **no** command-line/batch automation hook.

Because there is no CLI executable and the product is a Qt5WebEngine GUI, I did **not**
attempt to run MD headless — I could not prove it runs without a display, so per task
rules I say so plainly: **headless MD execution is unproven and very likely requires a
display. Not attempted.**

The only scriptable seams present are **file-based interchange**, not a Python API:
- **IN:** OBJ (already have), Alembic, FBX.
- **OUT:** USD (bundled usd step), FBX (bundled libfbxsdk), Alembic.
That is the realistic automation envelope. Everything *inside* MD (draft pattern, arrange,
simulate, export) is manual GUI work.

---

## 2. Integration micro-steps — Melodia garment loop (Shorewake slotted dress)

Source asset: `Saved/Audit/melusina_lookdev/bake/night_pkg_2026-08-31/SM_ShorewakeDress_48MAT_v2_slotted.obj`
(28,865,117 bytes) + matching `.mtl` + `_garment.obj` (29,461,463 bytes). FBX also present
(`SM_ShorewakeDress_48MAT_v2_slotted.fbx`, 8,045,196 bytes).

| # | Step | Mechanism | Status | Reason |
|---|---|---|---|---|
| a | Export dress → pattern flat source | Drag/drop the `.obj` into MD → auto unpack to 2D patterns ("File > Import" / center-tool drag). OBJ `T_DressShorewake_PanelID_4K.png` helps map the 48 panels → 10 garments. | **MANUAL-GUI** | No MD CLI/API; import only via GUI. OBJ prep itself is **AUTOMATABLE** (already produced) — the "take .obj into MD" action is manual. |
| b | Simulate a drape | In MD 3D viewport: arrange on chosen avatar/hanger → Run Simulation. | **MANUAL-GUI** | Core physical solve; only via GUI. No headless solver, no proven display-free run. |
| c | Export USD / FBX back | `File > Save As` → `.usd`/`.usda` or `.fbx`. MD ships full USD (usd.dll, usdSkel, plugInfo) + libfbxsdk. | **MANUAL-GUI** | Export entry exists and is USD-native, but user-triggered. **BLOCKED for headless** — no CLI. Round-trip of *a stock sample* via this path is a good human verification step before trusting it for the dress. |
| d | Import to UE | Take exported `.usd`/`.fbx` → UE datasmith/FBX import (editor commandlet). | **AUTOMATABLE** (UE-side, editor-bound) | This side has a real automation entry (UE import commandlet → `.uasset`). Requires editor to run the commandlet; per working agreement refused here. |

**Feasibility flags (per step, recorded in JSON):**
- `a_export_flatsource`: feasible=false (GUI), note "OBJ prep automatable, MD import manual"
- `b_simulate_drape`: feasible=false (GUI)
- `c_export_usd_fbx`: feasible=false headless / "BLOCKED — no CLI; verify via stock-sample roundtrip"
- `d_import_ue`: feasible=true ("UE editor import commandlet; editor-bound, not run here")

---

## 3. #1 practical integration action

**Do not build on an MD Python API — none exists.** The single highest-value action is
to route the Shorewake dress through MD **once, by hand**, purely to validate the file
envelope: a human opens MD → imports the existing slotted `.obj` (Step a) → simulates a
drape (Step b) → exports `.usd`+`.fbx` (Step c) → and we confirm Step d (UE ingest) is
viable from the exported file. That proves the only automatable contract (files in/out),
which the pipeline can then wrap with scripts on our side (OBJ prep now, UE ingest after)
without ever depending on a nonexistent MD scripting API. If a repeatable, high-frequency
MD solve is ever required, the honest automation path is **not** MD via Python — it is a
Houdini Vellum/SOP solve (hython) on the same OBJ, which is the neighboring track
`Docs/Art/UNIVERSAL_GARMENT_FABRIC_DRAPERY_2026-09-02.md`.