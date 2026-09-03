# Pre-rebuild health pass — 2026-08-02

## PPV stack — all four levels now identical

**The handoffs were wrong about the current state.** `CLAUDE_TO_KIRO_STATE_2026-08-01.md` said
"PPV_NikkiDream runs the approved outline, the Portfolio Hero grade, and the Van Gogh sky." Measured,
none of the four levels had that. **Two had no blendables at all**, and no level had the sky.

### Before

| Level | PPV_NikkiDream blendables |
|---|---|
| `L_EscherAscent` | **0 — empty** |
| `L_InfiniteScore` | **0 — empty** |
| `L_FallenMoon` | `MI_Outline_PremiumV3_Hero` @ **0.08**, `M_PP_MeluColorGrade` @ 0.37 |
| `L_KaleidoNave` | `MI_PP_StorybookOutline` @ 1.0, `M_PP_MeluColorGrade` @ 1.0 |

Three separate defects: two empty levels; `L_FallenMoon` running the outline at **0.08** (effectively
invisible) and pointing at the raw `M_PP_MeluColorGrade` **material** rather than the Hero profile
instance; and `L_KaleidoNave` on `MI_PP_StorybookOutline`, whose parent is the **superseded**
`M_PP_StorybookOutline_FoliageSafe_Candidate`.

Canonical set chosen by asset mtime — `MI_Outline_PremiumV3_Hero` and `MI_StarryNight_Hero` are both
from the 16:02 batch, the newest; `MI_PP_StorybookOutline` is 14:00 on the old parent.

### After — applied and saved to all four

```
PPV_NikkiDream   priority 10, unbound
  MI_Outline_PremiumV3_Hero         w=1.00
  MI_MeluColorGrade_PortfolioHero   w=1.00
  MI_StarryNight_Hero               w=1.00
```

⚠️ **`L_FallenMoon`'s outline weight went 0.08 → 1.00.** If that 0.08 was deliberate tuning rather
than a leftover, revert that one value — everything else about the change stands. 0.08 is almost
certainly a stray, but it is a look decision and it is called out here rather than buried.

## "Duplicate" PPVs — NOT duplicates

Each level has a second unbound volume (`AscentPost` / `MoonPost` / `ScorePost` / `NavePost`) at
priority 0. They carry **zero blendables**, so they look redundant — but they hold real overridden
settings, so deleting them would change the look:

| Volume | Overridden settings |
|---|---:|
| `MoonPost` | **26** |
| `AscentPost` | 2 |
| `ScorePost` / `NavePost` | 1 each |

This is a valid two-layer setup: base grade at priority 0, blendable stack at priority 10. **Left
alone.** Worth noting for lookdev that `MoonPost`'s 26 overrides make `L_FallenMoon`'s baseline
materially different from the other three, which each have 1–2.

## PCG scale bug — found and fixed (owner-reported)

`L_KaleidoNave`'s colonnade rendered at **3200 m across**. Cause: `PCG_BaroqueColonnade` bakes a
**×100 scale into all 48 of its `CreatePoints` transforms** — compensation added when its meshes were
1/100 scale. Those meshes (`SM_wallhi` 601 uu, `SM_Block_Column_05` 50 uu, `SM_surrealtower1` 271 uu)
were Build-Scale-corrected in an earlier session, but the graph's compensation was never removed, so
the correction applied twice.

Fixed: 48 baked point scales 100 → 1. Colonnade now **32 m across**, 48 instances, scale 1.0.
`L_KaleidoNave` saved. **This predates today's mesh work** — none of the 18 meshes I rescaled today
are used by this graph.

### ⚠️ This is systemic — 15 more graphs carry the same pattern

Clear ×100 compensation, same family as the bug above:

- `Styles/Baroque/PCG_CathedralNave` — CreatePoints 100, 140, 120, 220, 110
- `Styles/Baroque/PCG_BezierCathedralAxis` — CreatePoints 100

Ambiguous (10–263×, could be intentional variation — **do not blanket-fix**):
`PCG_TerraceGarden`, `PCG_PenroseShrine`, `PCG_EscherDecks`, `PCG_EscherRecursiveRoom`,
`PCG_EscherRelativityRoom`, `PCG_FloatingStairways`, `PCG_GardenRuins`, `PCG_LanternGrove`,
`PCG_SplinePath`, `PCG_Universal_RockScatter`, `PCG_WaterEdgeScatter`, `PCG_BridgeArchipelago`,
`PCG_WallGardenPath`.

**Rule for the remaining mesh repairs: before Build-Scale-fixing any mesh, check whether the graphs
using it bake a compensating scale.** Fixing the mesh without removing the compensation multiplies
the error rather than correcting it. This is the real hazard in Part A — not hand-placed actors,
which turned out to be almost nonexistent.

## Duplicate level assets

Two levels exist at two paths each. Neither pair was reconciled:

- `/Game/L_InfiniteScore` **and** `/Game/EnvSandbox/Environments/L_InfiniteScore`
- `/Game/L_MelusinaMorning` **and** `/Game/Melodia/Levels/Opening/L_MelusinaMorning`

The PPV work above targeted the `EnvSandbox/Environments` copy of `L_InfiniteScore`. If the root-level
copy is the one actually loaded at runtime, it did **not** receive the stack. Worth resolving before
the rebuild — check which the GameMode / default map points at.

## State going into the rebuild

- 4 core levels: PPV stack applied and saved, verified identical.
- `L_KaleidoNave`: colonnade scale fixed, saved.
- `L_FallenMoon`: PCG intact (1898 instances), saved.
- `ZenForestTest`: hero nave placed but **deliberately unsaved** — still yours to keep or discard.
- 18 meshes Build-Scale-repaired; 6 safe remaining, 3 blocked on approval.
- `BP_MelodiaPCGControl` built and compiling; its knobs are **not yet functional** (attribute-name
  matching, documented in `PCG_RENDER_POLISH_AND_UNIVERSAL_2026-08-02.md`).
