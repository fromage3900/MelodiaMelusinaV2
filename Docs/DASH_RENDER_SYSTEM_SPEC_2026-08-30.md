# Dash 3D Render System — Scaffold Spec 2026-08-30

> **Naming resolution (2026-08-30 late):** the subsystem was renamed
> `MelodiaDashRenderSubsystem` → `MelodiaCaptureRenderSubsystem` to avoid colliding with the
> Polygonflow "Dash" environment-dressing tool reserved in the toolchain SSOT
> (`Docs/Research/AGENT_TOOLCHAIN_DISCOVERY_INDEX_2026-08-30.md`). This doc keeps its name for
> history; all code/class references use `CaptureRender`.

**Status:** SCAFFOLD — no `.uasset` writes, no master duplication. Editor is closed for the 8ca43d14 build window; this spec is offline only.
**Owner request:** "new 3d render system so id dash bro" — Dash is the name for the new 3D render path. Magpie remains undefined in-repo; this doc does not assume it.
**Authority:** `AGENTS.md` convergence rule — no parallel material masters, no `Content/_PROJECT/` writes. Dash orchestrates the *existing* toon spine (`M_Master_Toon_Universal`, Substrate Toon) and PPV stack; it does not replace them.

---

## 1. What Dash is (and is not)

| Aspect | Decision |
|---|---|
| **Existing capture** | `UMelodiaPrototypeCaptureSubsystem` — presentation-only, 3 surfaces (MainMenu/Exploration/Battle), `FScreenshotRequest`, transient `r.MotionBlur.Amount 0`. Proven but limited to viewport screenshots. |
| **Dash** | **SceneCapture-based offscreen 3D renderer** that lives alongside PrototypeCapture. Renders to `UTextureRenderTarget2D` (HDR), with material overrides, PPV-consistent tonemapping, and repeatable named surfaces. Used for: beauty/wireframe/material/PCG captures (per `WebsiteRenderArchive/RENDER_CAPTURE_CHECKLIST.md`), dash-trail ghost captures, and portfolio/site generation. |
| **Not a new master** | Dash never creates `M_Master_Dash_*`. It drives `M_Master_Toon_Universal` (1162 PS instr, 1762 instances) via `MPC_Melodia_Palette` and instance params, plus the canonical PPV stack (`PPV_NikkiDream` with `MI_MelodiaInk 1.0 / MI_MeluColorGrade 0.69 / MI_StarryNight_Hero 1.0`). No `Content/Melodia/_PROJECT/` writes. |
| **Relation to PrototypeCapture** | Prototype = quick viewport grab. Dash = controlled offscreen pipeline (resolution, capture source, show flags, post). Both call `FScreenshotRequest`/`SceneCapture`, but Dash owns the render-target lifecycle. |

## 2. Existing spine Dash reuses

- **Material spine:** `M_Master_Toon_Universal` — 365 params (255 scalar, 50 vector, 31 texture, 29 switch), Nikki params neutral-by-default (`PastelLift 0` etc, per `setup_master_universal.py:6`). Dash reads `Docs/MATERIAL_PIPELINE_AUDIT_2026-08-20.md` and `MATERIAL_HEALTH_AND_CONSOLIDATION_PLAN_2026-08-30.md` for the current known defects (M_PP_MelodiaInk unwired inputs, VanGogh domain bug, PPV drift) and *validates* them before capture rather than working around them.
- **PPV stack:** Single `PPV_NikkiDream` actor, 3 blendables at canonical weights (per `PPV_DRIFT_T3D_FIX_SPEC`). Dash asserts the stack before capture and logs drift as a warning; it does not silently fix it.
- **Capture checklist precedent:** `RENDER_CAPTURE_CHECKLIST.md` already defines the 4 required views per level (beauty, wireframe, material breakdown, PCG overlay) + stats. Dash automates that checklist via Monolith `capture_scene_preview` / `capture_material_grid` actions, not a parallel capture path.
- **Subsystems:** `MelodiaIntegration` module — `MelodiaPrototypeCaptureSubsystem` (GameInstance), `MelodiaPCGNarrativeChallengeBridgeComponent`, `MelodiaWater*` bridges. Dash follows the same `UGameInstanceSubsystem` pattern so it is available in PIE and in the editor utility world.

## 3. Dash API (scaffold)

```cpp
UENUM(BlueprintType)
enum class EMelodiaDashSurface : uint8 {
    Gameplay,        // RHY + PPV on, beauty
    Wireframe,
    MaterialBreakdown,
    PCGOverlay,
    DashTrailGhost,  // dash mechanic — translucent history shell
    PortfolioHero    // void-gradient doctrine, for site generation
};

UCLASS()
class BS_GODFILE_API UMelodiaDashRenderSubsystem final : public UGameInstanceSubsystem {
    GENERATED_BODY()
public:
    UFUNCTION(BlueprintCallable, Category="Melodia|Dash")
    bool ConfigureSurface(EMelodiaDashSurface Surface, FIntPoint Resolution = FIntPoint(1920,1080));

    UFUNCTION(BlueprintCallable, Category="Melodia|Dash")
    bool CaptureToRenderTarget(UTextureRenderTarget2D* Target); // HDR, Substrate Toon path

    UFUNCTION(BlueprintCallable, Category="Melodia|Dash")
    bool CaptureToFile(const FString& LevelName, EMelodiaDashSurface Surface); // 4-view cycle

    UFUNCTION(BlueprintPure, Category="Melodia|Dash")
    bool IsPPVStackCanonical(FString& OutReason) const; // asserts before capture
};
```

- `ConfigureSurface` sets show flags + `r.MotionBlur.Amount 0` transiently, never mutates the level's PPV.
- `CaptureToRenderTarget` is the primitive; `CaptureToFile` loops the 4-view cycle.
- `IsPPVStackCanonical` is the pre-capture gate — failure is a warning, not an auto-fix (evidence standard).

## 4. Show-flag / PPV contract

| Surface | Show flags | PPV |
|---|---|---|
| Gameplay/PortfolioHero | defaults | canonical 3-blendable stack, validated |
| Wireframe | `ViewMode Wireframe` | PPV bypassed |
| MaterialBreakdown | `ViewMode Lit + BufferVisualization BaseColor` | PPV bypassed |
| PCGOverlay | `ShowFlag.PCG` | canonical |
| DashTrailGhost | `Translucency + MotionBlur` | canonical + ghost composite |

Resolution default 1920×1080, HDR `RTF_RGBA16f`. No `Content/_PROJECT/` output; files land under `Saved/DashCaptures/` (gitignored) or `my-site-deploy/generated/assets/landscape-loops/` (site pipeline).

## 5. Test scaffolding (no editor)

- `Tools/test_dash_capture.py` — dry-run that validates the API exists, PPV canonical JSON exists, and `M_Master_Toon_Universal` compiles. No `.uasset` writes.
- `Saved/Audit/dash_probe_<model>_*.json` — ledger rows (same Evidence standard as `test_claireon_toolcalls.py`). Claireon's 2-tool pattern is unrelated; Dash is not an MCP surface.
- Live proof (editor required): one `ConfigureSurface → IsPPVStackCanonical → CaptureToRenderTarget` cycle in PIE on `L_KaleidoNave`, with 4 PNGs + JSON report.

## 6. Relation to other named lanes

- **Claireon** — Believer's 600-tool MCP plugin (`Plugins/Claireon/` vendored @ `ed0b457`, 74M, `Installed:false`, never built). It is an *agent* surface, not a renderer. Dash never runs alongside Claireon on the main editor (single-MCP-surface rule, `Docs/CLAIREON_PREP_2026-08-20.md:7`). Claireon testing stays in `Melodia_ClaireonTest` worktree; Dash testing stays on `main`.
- **Magpie** — no matches anywhere. Awaiting owner definition. If Magpie is also a render-adjacent system, it must be scoped against this spec before any C++ lands (no parallel masters, single 9316 listener).
- **Traversal Dash mechanic** — the gameplay `dash` (Glide/Dash/Swim/Dive, `MelodiaTraversalCapabilityProvider`) is a *consumer* of this renderer for its ghost trail, not the renderer itself.

## 7. Guardrails

1. No new `M_Master_*` — Dash is a driver, not a master.
2. No `Content/_PROJECT/` or `Content/EnvSandbox/` writes - `Saved/DashCaptures/` only.
3. No `git clean -fd` / `git checkout -- .` / `delete_asset` on foreign assets.
4. No second MCP surface on one graph (Decision 025).
5. Spec precedes mutation — live wiring requires Momolith 9316 + single-editor lock + `unattended:true` saves.

## 8. Next steps (queued behind the 8ca43d14 build)

1. Validate this spec against `Docs/T3D_Baseline/`, `MATERIAL_TAKEOVER_RESEARCH_2026-08-29.md`, and the QOL queue order 1–6 (`Docs/Handoffs/QOL_EXECUTION_QUEUE_2026-08-30.md`) — PPV drift and dead-node cleanup are lower-risk and should land before Dash's PPV assert.
2. Implement the stub subsystem in `Source/BS_GodFile/MelodiaIntegration/` (header + cpp, `UGameInstanceSubsystem`, no Tick).
3. Add `Tools/test_dash_capture.py` probe.
4. Record the first ledger row from the probe (offline) + one live PIE capture cycle when the editor reopens.
