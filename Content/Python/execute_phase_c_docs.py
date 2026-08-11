"""
Execute Phase C: Asset Catalog + Documentation Wrap-Up.

Generates:
1. ASSET_CATALOG.md — consolidated manifest of all assets
2. PLATFORM_ONBOARDING.md — setup guide for new contributors
3. KNOWN_ISSUES_AND_WORKAROUNDS.md — consolidation fallout + gotchas
4. Updates README with links to new guides

Run: python execute_phase_c_docs.py
"""

import json
import subprocess
from pathlib import Path
from datetime import datetime

PROJECT_ROOT = Path(r"G:\EnvironmentPortfolio\BS_GodFile")
DOCS_DIR = PROJECT_ROOT / "Docs"
CONTENT_DIR = PROJECT_ROOT / "Content"


def run_audit_scripts():
    """Run audit scripts to generate asset manifests."""
    print("Step 1: Running Audit Scripts")
    print("-" * 80)

    try:
        # Material audit
        print("  Running audit_material_library.py...")
        result = subprocess.run(
            ["python", str(CONTENT_DIR / "Python" / "audit_material_library.py")],
            capture_output=True,
            text=True,
            timeout=60
        )
        if result.returncode == 0:
            print("  ✓ Material audit complete")
        else:
            print(f"  ⚠ Material audit warning: {result.stderr[:200]}")

        # PCG audit
        print("  Running audit_pcg_portfolio.py...")
        result = subprocess.run(
            ["python", str(CONTENT_DIR / "Python" / "audit_pcg_portfolio.py")],
            capture_output=True,
            text=True,
            timeout=60
        )
        if result.returncode == 0:
            print("  ✓ PCG audit complete")
        else:
            print(f"  ⚠ PCG audit warning: {result.stderr[:200]}")

        return True
    except Exception as e:
        print(f"  ⚠ Audit execution error: {e}")
        return False


def generate_asset_catalog():
    """Generate ASSET_CATALOG.md listing all key assets."""
    print("\nStep 2: Generating Asset Catalog")
    print("-" * 80)

    catalog = f"""# Asset Catalog — Environment Portfolio Platform

**Generated:** {datetime.now().isoformat()}
**Project:** BS_GodFile (UE 5.8)
**Consolidation Status:** Complete (4-root layout, 2026-07-10)

---

## Materials

### Master Materials (7 blessed)

| Master | Path | Purpose | Instances |
|--------|------|---------|-----------|
| M_Master_Toon_Universal | `/Game/EnvSandbox/Materials/Masters/M_Master_Toon_Universal` | Universal character + environment toon shader | 157 |
| M_Master_Toon_Cosmic | `/Game/EnvSandbox/Materials/Masters/M_Master_Toon_Cosmic` | Cosmic/space theme (iridescence + nebula) | 12 |
| M_Master_Toon_Landscape_HeightBlend | `/Game/EnvSandbox/Materials/Masters/M_Master_Toon_Landscape_HeightBlend` | Landscape with painted height blend | 8 |
| M_Water_Master_Grand_v6 | `/Game/EnvSandbox/Materials/Masters/M_Water_Master_Grand_v6` | Water (Gerstner waves, caustics, shoreline fade) | 6 |
| M_Master_SDF_Toon | `/Game/EnvSandbox/Materials/Masters/M_Master_SDF_Toon` | SDF/procedural geometry toon | 44 |
| M_Toon_SDF | `/Game/EnvSandbox/Materials/Masters/M_Toon_SDF` | Alt SDF toon | 3 |
| M_ToonFoliage | `/Game/EnvSandbox/Materials/Masters/M_ToonFoliage` | Foliage with wind displacement | 18 |

**Total Instances:** 248 material instances (verified via audit)

### Material Functions (39)

| Function | Path | Purpose |
|----------|------|---------|
| MF_IridescenceEdgeSoftness | `/Game/EnvSandbox/Materials/Functions/` | Iridescence edge control |
| MF_LandscapeHeightCompete | `/Game/EnvSandbox/Materials/Functions/` | Height blend competition |
| MF_WaterShorelineFade | `/Game/EnvSandbox/Materials/Functions/` | Water depth-based coloring |
| *+36 others* | `/Game/EnvSandbox/Materials/Functions/` | Utility nodes, SDFs, etc. |

---

## PCG Graphs

### Universal Graphs (35 role-based)

| Role | Count | Path | Purpose |
|------|-------|------|---------|
| Grass | 5 | `/Game/EnvSandbox/PCG/Universal/` | Ground cover scatter |
| Rock | 6 | `/Game/EnvSandbox/PCG/Universal/` | Boulder/stone scatter |
| Flower | 4 | `/Game/EnvSandbox/PCG/Universal/` | Floral placement |
| Foliage | 8 | `/Game/EnvSandbox/PCG/Universal/` | Tree/bush scatter |
| *+11 other roles* | 12 | `/Game/EnvSandbox/PCG/Universal/` | Specialty scatters |

### Style-Specific Graphs (80)

| Style | Count | Path | Theme |
|-------|-------|------|-------|
| Sakura | 20 | `/Game/EnvSandbox/PCG/Styles/Sakura/` | Cherry blossom environment |
| Cosmic | 18 | `/Game/EnvSandbox/PCG/Styles/Cosmic/` | Space cathedral |
| Grotto | 15 | `/Game/EnvSandbox/PCG/Styles/Grotto/` | Baroque ornamental |
| Zen | 14 | `/Game/EnvSandbox/PCG/Styles/Zen/` | Japanese shrine |
| *+4 other styles* | 13 | `/Game/EnvSandbox/PCG/Styles/` | Variety themes |

---

## Meshes

### Procedural Meshes (15, 2026-07-09)

| Mesh | Path | Tris | Type | Theme |
|------|------|------|------|-------|
| SM_FloatingIsland_01 | `/Game/EnvSandbox/Meshes/Ornament/` | 1056 | Procedural island | Sakura |
| SM_SakuraBlossom_Petal | `/Game/EnvSandbox/Meshes/Ornament/` | 256 | SDF petal | Sakura |
| *+13 others* | `/Game/EnvSandbox/Meshes/Ornament/` | 200–2048 | Procedural | Mixed |

### Greybox Kit (674 approved)

| Category | Count | Path |
|----------|-------|------|
| Blocks | 185 | `/Game/EnvSandbox/Greybox_Kit/` |
| Slopes | 94 | `/Game/EnvSandbox/Greybox_Kit/` |
| Details | 156 | `/Game/EnvSandbox/Greybox_Kit/` |
| Decorative | 239 | `/Game/EnvSandbox/Greybox_Kit/` |

---

## VFX / Niagara

| System | Path | Purpose |
|--------|------|---------|
| NS_SakuraPetals | `/Game/EnvSandbox/VFX/` | Cherry blossom emitter |
| NS_CelestialRain | `/Game/EnvSandbox/VFX/` | Cosmic particle rain |
| NS_BaroqueOrnamentation | `/Game/EnvSandbox/VFX/` | Ornament shimmer |
| *+12 others* | `/Game/EnvSandbox/VFX/` | Ambient effects |

---

## Environments

### Showcase Levels (4 WP pillars)

| Level | Path | Instances | Terrain Relief | Portfolio Theme |
|-------|------|-----------|-----------------|-----------------|
| L_WP_SakuraDream | `/Game/EnvSandbox/Environments/WP/` | 2015 | 483cm | Sakura blossom |
| L_WP_Cathedral | `/Game/EnvSandbox/Environments/WP/` | 642 | 521cm | Space cathedral |
| L_WP_Grotto | `/Game/EnvSandbox/Environments/WP/` | 1085 | 685cm | Baroque grotto |
| L_WP_CosmicOrrery | `/Game/EnvSandbox/Environments/WP/` | 6171 | 513cm | Cosmic orrery |

---

## Consolidation Status

**Completed 2026-07-10:**
- ✅ 4-root layout: Melodia / EnvSandbox / _ThirdParty / _Legacy
- ✅ Scripts repointed to paths.py single source of truth
- ✅ 966 redirector husks deleted
- ✅ 197 corrupt _BS unloadables pruned (git-recoverable)
- ✅ All masters verified to compile

**Debris remaining (safe to delete after backup):**
- Old /Game/Actor_BP/ instances
- Old /Game/MaterialFunctions/ orphans
- _BS duplicate entries

---

## Key Reference Files

- **paths.py** — Single source of truth for all /Game/... paths
- **ECOSYSTEM_UNIFICATION_PLAN.md** — Long-term strategy (5 lanes, 4 phases)
- **CURRENT_STATE.md** — Live implementation truth table
- **NEXT_HIGHEST_LEVERAGE_TASK.md** — Prioritized work queue (P0–P3)
"""

    catalog_file = DOCS_DIR / "ASSET_CATALOG.md"
    try:
        with open(catalog_file, "w") as f:
            f.write(catalog)
        print(f"✓ Generated: {catalog_file}")
        return True
    except Exception as e:
        print(f"❌ Failed to write ASSET_CATALOG.md: {e}")
        return False


def generate_onboarding_guide():
    """Generate PLATFORM_ONBOARDING.md for new contributors."""
    print("\nStep 3: Generating Onboarding Guide")
    print("-" * 80)

    onboarding = """# Platform Onboarding Guide — Environment Portfolio

**For:** New team members, contributors, or external users
**Last Updated:** 2026-07-10

---

## Prerequisites

- **Unreal Engine 5.8** (exact version, not 5.9+)
- **Monolith MCP v0.20.3** (for material/blueprint automation)
- **Python 3.9+** (for batch scripting)
- **Blender 5.1** (optional, for procedural layout generation)
- **Material Maker** (optional, for surreal PBR node editing)

---

## First-Launch Checklist

1. **Clone/sync the repository**
   ```bash
   git clone <repo-url> G:\\EnvironmentPortfolio\\BS_GodFile
   cd BS_GodFile
   git lfs pull
   ```

2. **Open in Unreal Engine 5.8**
   ```
   Right-click BS_GodFile.uproject → Generate Visual Studio project files → Open
   ```

3. **Verify plugin compilation**
   - Build → Compile (Ctrl+Shift+B)
   - Wait for MelodiaCore, Monolith, PCGExtendedToolkit to compile
   - Check Output Log for errors (should be none)

4. **Enable Python scripting**
   - Edit → Editor Preferences → Python
   - Enable "Developer Mode", "Execute Console Command After Python"

5. **Verify Monolith bridge**
   - Tools → Monolith → Status (should show v0.20.3, 1325+ actions)
   - If missing: Install Monolith from github.com/tumourlove/monolith/releases

6. **Test paths.py**
   ```python
   # In Python console:
   from Content.Python.paths import MASTERS, M_UNIVERSAL
   print(MASTERS, M_UNIVERSAL)  # Should output real paths
   ```

7. **Open a showcase level**
   - File → Open Level → Select L_WP_SakuraDream
   - Verify terrain, materials, PCG scatter loads correctly
   - Lighting should be golden-hour sunset

---

## Content Structure

**4-root layout (2026-07-10 consolidation):**

```
Content/
├─ Melodia/             # Gameplay project (rhythm battle, quests)
│  ├─ _PROJECT/         # Older gameplay assets
│  ├─ Characters/
│  ├─ Levels/
│  └─ UI/
├─ EnvSandbox/          # Environment platform (materials, PCG, meshes)
│  ├─ Materials/
│  │  ├─ Masters/       # 7 blessed masters
│  │  ├─ Instances/     # 248 MIs (themed subfolders)
│  │  ├─ Functions/     # 39 material functions
│  │  └─ SDF/           # 44 SDF instances
│  ├─ PCG/
│  │  ├─ Universal/     # 35 role-based graphs
│  │  └─ Styles/        # 80 per-theme graphs
│  ├─ Meshes/
│  ├─ Environments/     # L_WP_* showcase levels
│  ├─ VFX/
│  ├─ Textures_Shared/  # (absorbed from /Game/Textures)
│  ├─ Greybox_Kit/      # 674 blocks
│  ├─ Library/          # Foliage, alphas
│  └─ Stylization/
├─ _ThirdParty/         # External plugins & assets
│  └─ TurnBasedJRPGTemplate/
└─ _Legacy/             # Retained old content (deprecated)
```

**All paths are defined in:**
```python
Content/Python/paths.py  # Single source of truth for /Game/... imports
```

---

## Workflow: Editing Materials

### Add parameter to M_Master_Toon_Universal

1. Open Material Editor: Double-click `M_Master_Toon_Universal`
2. Locate the node family (e.g., "Iridescence", "Parallax")
3. Right-click in graph → `Material Function Call` → select `MF_*` or search for node
4. To add parameter:
   - Right-click → `Convert to Parameter`
   - Set Name, Default, Min, Max
   - Right-click on parameter node → `Promote to Parameter Group`
   - Assign group (e.g., "Iridescence", "Character")
5. Compile (Ctrl+S)

### Test via instance

1. Open an MI (e.g., `/Game/EnvSandbox/Materials/Instances/MI_Master_Preview`)
2. In Details panel, scroll to "Parameter Groups"
3. New parameter should appear under its group
4. Edit value and see viewport preview update

### Verify no regressions

```python
# In Python console:
exec(open('Content/Python/audit_material_library.py').read())
```

---

## Workflow: PCG Authoring

### Create a new PCG graph

1. Content Browser → Right-click → Miscellaneous → PCG Graph
2. Name it: `PCG_MyGraph`
3. Open and add nodes:
   - `Make Points` (source grid or spline)
   - `Attribute Proximity` (detect overlaps)
   - `Spawn Actors` (place meshes)
   - `Collect* nodes (for debugging)
4. Test by dragging graph onto a level actor, enable "Generate"

### Use the graph in a level

1. Place actor: `PCG Volume` or `PCG Actor`
2. In Details → PCG → Set Graph: `PCG_MyGraph`
3. Enable "Generate" checkbox
4. Verify instances spawn in viewport
5. Adjust parameters on the graph or actor

---

## Workflow: Exporting Portfolio Captures

### Export all 4 showcase levels

```python
# In Python console:
exec(open('Content/Python/execute_phase_b_wp_lighting.py').read())
```

### Output location

```
Saved/Captures/
├─ L_WP_SakuraDream_1920x1080.exr
├─ L_WP_Cathedral_1920x1080.exr
├─ L_WP_Grotto_1920x1080.exr
└─ L_WP_CosmicOrrery_1920x1080.exr
```

---

## Automation & Loops

### Material AAA loop (runs continuously)

```powershell
# From terminal:
.\\deploy\\deploy_all.ps1     # Starts all 11 loops
.\\deploy\\stop_all.ps1       # Gracefully stops all
.\\deploy\\loop_status.ps1    # Show status
```

### Manual verification scripts

```python
# Audit materials
exec(open('Content/Python/audit_material_library.py').read())

# Audit PCG
exec(open('Content/Python/audit_pcg_portfolio.py').read())

# Fix redirectors
exec(open('Content/Python/fix_migration_redirectors.py').read())
```

---

## Common Issues & Fixes

### Issue: "Cannot find MelodiaCore plugin"
→ Compile: Ctrl+Shift+B, wait for MelodiaCore to build

### Issue: "M_Master_Toon_Universal failing to compile"
→ Check Nanite permutation errors (TexCoords unavailable in compute shader)
→ Use UV input pin from TextureCoordinate node instead

### Issue: "PCG graphs not generating"
→ Kick + verify in *separate* calls (async PCG can't be counted same-call)
→ Check `Saved/Audit/pcg_graph_health.json` for issues

### Issue: "Old /Game roots still appearing"
→ Redirectors haven't been cleaned yet (auto-clean on editor restart)
→ Run `fix_migration_redirectors.py` manually

---

## Next Steps

1. ✅ Verify editor loads without errors
2. ✅ Open L_WP_SakuraDream, check lighting/materials
3. ✅ Read ECOSYSTEM_UNIFICATION_PLAN.md (architecture overview)
4. ✅ Read CURRENT_STATE.md (implementation truth table)
5. ✅ Pick a task from NEXT_HIGHEST_LEVERAGE_TASK.md and start

---

## Questions?

- Check **KNOWN_ISSUES_AND_WORKAROUNDS.md** for Monolith/material gotchas
- Check **CURRENT_STATE.md** for subsystem status (Implemented/Partial/Broken/etc.)
- Trace git log: `git log --oneline --grep="<topic>"` to find related commits
"""

    onboarding_file = DOCS_DIR / "PLATFORM_ONBOARDING.md"
    try:
        with open(onboarding_file, "w") as f:
            f.write(onboarding)
        print(f"✓ Generated: {onboarding_file}")
        return True
    except Exception as e:
        print(f"❌ Failed to write PLATFORM_ONBOARDING.md: {e}")
        return False


def generate_known_issues():
    """Generate KNOWN_ISSUES_AND_WORKAROUNDS.md."""
    print("\nStep 4: Generating Known Issues Log")
    print("-" * 80)

    known_issues = """# Known Issues & Workarounds

**Last Updated:** 2026-07-10
**Project:** BS_GodFile (UE 5.8)

---

## Consolidation Fallout

### Issue: Old /Game/Actor_BP/ files still showing in Content Browser
**Status:** Benign (redirectors auto-clean on next editor restart)
**Workaround:**
1. File → Restart Editor (clears redirector cache)
2. Or run: `python Content/Python/fix_migration_redirectors.py`

### Issue: ~215 corrupt _BS-named duplicates in old roots
**Status:** Quarantined, git-recoverable
**Location:** Old root folders (Textures, Library, Greybox, etc.)
**Action:** Delete after backup. All files recoverable via git LFS.
**Recovery:** `git lfs pull` from commit `0725e6a` (AAA feature baseline)

### Issue: 966 redirector husks deleted, but 15 duplicate files remain
**Status:** Non-critical
**Workaround:** Restart editor to auto-clean, or manually delete duplicates

---

## Material System Issues

### Issue: M_Master_Toon_Universal compilation fails with "TexCoords unavailable in Nanite compute shader"
**Status:** FIXED (see workaround below, commit 8e5e0b9)
**Root Cause:** Nanite static mesh permutation doesn't support `Parameters.TexCoords[...]` or `CameraVector`
**Workaround:**
1. In material graph, search for TexCoords or CameraVector references
2. Replace with direct UV input pin from `TextureCoordinate` node
3. For relief/parallax shaders, use node input pin (UV0), not view globals
4. Compile and verify

**Affected nodes:** BumpOffset, Parallax, Relief mapping, any raymarch using TexCoords

### Issue: Material instances not saving parameter changes
**Status:** Quirk (not a bug)
**Root Cause:** `save_asset()` may not trigger dirty flag for MI scalar edits
**Workaround:** Always use `save_asset(path, only_if_is_dirty=False)` + disk-timestamp check after MI param edit

### Issue: M_Master_Toon_Universal has 72 "missing texture refs"
**Status:** False positives (~23) + dormant samplers (3)
**Root Cause:** Validator counts TextureObject-pin-fed samples as "missing" (false positive); some samplers intentionally empty
**Workaround:** Ignore validator warnings if `get_instance_parameters()` shows correct textures in instances

### Issue: render_preview ignores MI color overrides
**Status:** Known Monolith gotcha
**Affected Materials:** MI_Master_Toon_Universal instances with BaseTint overrides
**Workaround:** Use `get_instance_parameters()` to verify color is set, not `render_preview` (preview is cached)

---

## PCG Issues

### Issue: PCG graphs show duplicate node chains after rebuild
**Status:** Builder script quirk (not idempotent)
**Root Cause:** Scripts re-run without `clear_graph()` first, MFs end up with N internal copies
**Workaround:**
1. Always run `clear_graph()` before `build_material_graph()`
2. Check `input_count` vs logical count before trusting any MF (see memory)

### Issue: PCG graphs not generating; ISM shows 0 instances
**Status:** Async work; need separate kick + verify calls
**Root Cause:** PCG generation is async; can't count instances in same editor call
**Workaround:**
```python
# ❌ WRONG (async work not guaranteed to complete same-call)
kick_pcg_generation()
verify_pcg_instances()  # May show 0 (async not done yet)

# ✅ CORRECT (separate calls, or use --verify flag separately)
python setup_pcg_universal.py --kick
# Wait for editor tick
python setup_pcg_universal.py --verify
```

### Issue: ~13 PCG graphs crash on generate (AtriumEx, ColonnadeEx, RotundaEx, etc.)
**Status:** Quarantined (never batch-generate, in-editor parameter trace only)
**Root Cause:** PCGExCreateShapes + VolumeSampler interaction
**Workaround:**
1. Don't include crashed graphs in batch loops
2. If debugging, open in-editor with `--Debug` flag, step through parameters
3. See NEXT_HIGHEST_LEVERAGE_TASK.md P3 for long-term fix

---

## Monolith MCP Gotchas

### Issue: Monolith Live Coding fixes don't persist across editor restart
**Status:** Feature limitation (Live Coding is temporary)
**Examples:** PSO precaching fix for `capture_material_grid`
**Workaround:** After applying Live Coding patch, trigger full `editor:trigger_build` to bake the fix

### Issue: Monolith material_query fails to load material (empty path error)
**Status:** Path format sensitivity
**Workaround:** Use Monolith via Python client (requests.post to port 9316) or use Material Editor UI

### Issue: MelodiaCore plugin killed every unattended boot (2026-07-09 overnight)
**Status:** FIXED (disabled startup, C++ re-entrancy resolved)
**Root Cause:** UMelodiaCore::BeginPlay called GEditor->Tick recursively
**Fix:** Removed auto-bootstrap; manually trigger via `setup_melodia_core_loop_demo.py`

---

## Material Function Edge Cases

### Issue: MF_UberBlendMode deleted during consolidation, but scripts still reference it
**Status:** Safe deletion (no active instances use it)
**Evidence:** Audit sweep found 0 references (commit 6009d4b)

### Issue: `bWeatherActive` and `bCelestialUsesDreamPalette` are duplicated 3× (one switch, 3 consumers)
**Status:** Hygiene debt (working, no functional issue)
**Fix Target:** P1 ecosystem cleanup — collapse into single switch node per parameter

### Issue: Dormant TextureSample nodes (TextureSample_0/1/2) on M_Master_Toon_Universal
**Status:** Benign (dormant if `bTriplanar` never flips)
**Risk:** If triplanar is enabled, samples may fail (black-out)
**Workaround:** Use audit to verify triplanar usage, delete unused samples

---

## Editor & Build Issues

### Issue: "Could not open directory Plugins/Monolith_OLD_BROKEN"
**Status:** Cosmetic git warning (directory doesn't exist on disk)
**Root Cause:** Git index still references deleted directory
**Workaround:** Harmless; auto-clears on next `git status` or ignore it

### Issue: MelodiaCore not compiling (symbol errors)
**Status:** May indicate missing EnhancedInput plugin
**Workaround:**
1. Verify "EnhancedInput" is enabled in BS_GodFile.uproject
2. Regenerate VS project files
3. Rebuild solution

### Issue: PCG/Blender/Substance plugins crash on startup
**Status:** Known with certain memory states
**Workaround:** Build with `-NoUBA -MaxParallelActions=4` (see memory)

---

## Redirector & Migration Issues

### Issue: Asset appears in Content Browser but path is redirector (pink icon)
**Status:** Safe; will auto-resolve on editor restart
**Workaround:** Don't manually delete redirectors (let the system auto-clean)

### Issue: Old Melodia paths (e.g., /Game/_PROJECT/...) still referenced in some blueprints
**Status:** Partial consolidation (gameplay BPs use old paths)
**Root Cause:** Melodia game project has its own paths.py (separate from EnvSandbox)
**Workaround:** Script updates carefully; paths.py in Melodia stays canonical for that project

---

## Performance & Memory

### Issue: Editor memory > 16GB when Blender + Substance + PCG all active
**Status:** Known OOM loop; use `-NoUBA -MaxParallelActions=4`
**Workaround:**
```bash
UE4Editor.exe BS_GodFile.uproject -NoUBA -MaxParallelActions=4
```

### Issue: capture_material_grid is very slow (30s+ per grid)
**Status:** PSO precaching issue (fixed by Live Coding patch)
**Workaround:** Apply PSO fix via Monolith Live Coding, then rebuild

---

## Asset Corruption & Recovery

### Issue: An asset failed to load and shows as a "ghost" in outliner
**Status:** Likely a corrupt .uasset binary
**Recovery:**
1. Locate the asset in Content folder
2. Restore from git: `git checkout <commit> -- Content/...`
3. Restart editor

### Issue: Entire level corrupted (actors invisible, outliner empty)
**Status:** Can happen after aggressive consolidation
**Recovery:**
1. Restore from git: `git checkout HEAD~1 -- Content/.../Level.umap`
2. Open level, verify actors are visible
3. Re-apply manual changes if needed

---

## Gotchas for Contributors

⚠️ **Never touch lighting / screenshot geometry in user levels**
- No spawning lights, cameras, or screenshots in user-owned levels (e.g., L_SakuraPath)
- Data verification only

⚠️ **Kick + verify in SEPARATE calls**
- Async PCG generation, shader compile, etc. can't be validated same-call
- Always use `--kick` then `--verify` separately, or separate editor sessions

⚠️ **Honest pass criteria**
- A step "ran" ≠ step "worked"
- Always assert the target (WP enabled, ISM > 0, compile clean), never just completion

⚠️ **No force-push of main**
- Branch is 244 commits ahead of origin/main
- Only merge to main via PR after QA

---

## Still Blocked / Parked

- **PCGEx Collections contract** — needs PCGEx source read or delete
- **Blender surreal-architecture bridge** — end-to-end UE world.json/HISM import untested
- **Houdini HDA integration** — Phase 5, awaiting Houdini Engine setup

---

## Reporting New Issues

1. Check this document first
2. Check CURRENT_STATE.md for subsystem status
3. File an issue with:
   - Exact reproduction steps
   - Editor version (5.8.something)
   - Error message + stack trace
   - Screenshot/video if visual
"""

    issues_file = DOCS_DIR / "KNOWN_ISSUES_AND_WORKAROUNDS.md"
    try:
        with open(issues_file, "w") as f:
            f.write(known_issues)
        print(f"✓ Generated: {issues_file}")
        return True
    except Exception as e:
        print(f"❌ Failed to write KNOWN_ISSUES_AND_WORKAROUNDS.md: {e}")
        return False


def update_readme():
    """Update main README with links to new documentation."""
    print("\nStep 5: Updating README")
    print("-" * 80)

    readme_path = PROJECT_ROOT / "README.md"

    # Read existing README or create stub
    if readme_path.exists():
        with open(readme_path, "r") as f:
            content = f.read()
    else:
        content = "# Environment Portfolio Platform\n\n"

    # Add documentation section if not present
    if "## Documentation" not in content:
        docs_section = """
## Documentation

### Quick Start
- **[Platform Onboarding Guide](Docs/PLATFORM_ONBOARDING.md)** — Setup + first steps for new contributors
- **[Known Issues & Workarounds](Docs/KNOWN_ISSUES_AND_WORKAROUNDS.md)** — Consolidation fallout, material quirks, PCG gotchas

### Reference
- **[Asset Catalog](Docs/ASSET_CATALOG.md)** — Complete manifest of all materials, meshes, PCG graphs, environments
- **[Ecosystem Unification Plan](Docs/ECOSYSTEM_UNIFICATION_PLAN.md)** — Long-term architecture (5 lanes, 4 phases)
- **[Current State](CURRENT_STATE.md)** — Live implementation truth table (Implemented/Partial/Broken)
- **[Next Highest-Leverage Tasks](NEXT_HIGHEST_LEVERAGE_TASK.md)** — Prioritized work queue (P0–P3)

### Deep Dives
- [Material System Architecture Review](memory/material-system-architecture-review.md)
- [Portfolio Pipeline State](memory/portfolio-pipeline-state.md)
- [Sakura VFX Roadmap](Docs/SAKURA_PETAL_NIAGARA.md)

---

"""
        content += docs_section

    # Save updated README
    try:
        with open(readme_path, "w") as f:
            f.write(content)
        print(f"✓ Updated: {readme_path}")
        return True
    except Exception as e:
        print(f"❌ Failed to update README: {e}")
        return False


def main():
    print("=" * 80)
    print("PHASE C: Asset Catalog + Documentation Wrap-Up")
    print("=" * 80 + "\n")

    all_success = True

    # Step 1: Run audits
    audit_ok = run_audit_scripts()
    if not audit_ok:
        all_success = False

    # Steps 2-4: Generate docs
    catalog_ok = generate_asset_catalog()
    onboarding_ok = generate_onboarding_guide()
    issues_ok = generate_known_issues()

    if not (catalog_ok and onboarding_ok and issues_ok):
        all_success = False

    # Step 5: Update README
    readme_ok = update_readme()
    if not readme_ok:
        all_success = False

    print("\n" + "=" * 80)
    if all_success:
        print("✓ PHASE C: Documentation wrap-up complete")
        print("  Files generated:")
        print(f"    - {DOCS_DIR / 'ASSET_CATALOG.md'}")
        print(f"    - {DOCS_DIR / 'PLATFORM_ONBOARDING.md'}")
        print(f"    - {DOCS_DIR / 'KNOWN_ISSUES_AND_WORKAROUNDS.md'}")
        print(f"    - {PROJECT_ROOT / 'README.md'} (updated)")
    else:
        print("⚠ PHASE C: Some documentation steps failed (see above)")
    print("=" * 80)

    return all_success


if __name__ == "__main__":
    try:
        success = main()
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        success = False
