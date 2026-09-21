# GN House Close-out Evidence — 2026-09-20 (laptop, session 20260918_214925_b2872e)

## Payload files committed for UE staging

| File | State |
|---|---|
| deploy/surreal_arch/melodia_gn/paris_wall_detail.py | md5 9a6ae693, deploy = live addon (AppData), 717 lines, ast.parse OK |
| HOUSE_GN_FINAL_PLAN_2026-09-18.md | 233 lines; sweep results, wreck/recovery, doorway verdict, UE staging checklist |
| Saved/Audit/nikki_decor/CLOSEOUT_EVIDENCE_20260920.md | this note |

## Verification chain (all re-runnable)

- Gate (authoritative, kit-only base): Saved/Audit/nikki_decor/nikki_gate2.py —
  ALL PASS, 14 walls + 15 slabs, W001 1928 verts (first COMPLETE gothic build),
  W002 760, W015 632, slab dz within tolerance.
- Blend state: Melusinas_Study_FullNikkiDecorated.blend saved 00:36 Sep 20 —
  GN_PARIS_WallDetail 177 nodes / SlabTrim 33 nodes, both Group Outputs wired,
  every ParisDetail modifier assigned (nikki_dump_state.py).
- Renders: Saved/Audit/nikki_decor/renders/ — W001_gothic_front/_BACK/_3qtr/_thru,
  house_N/S/E/W/HI, user_view.png (vision-analyzed: archway passage clear).
- Doorway probes: nikki_doorprobe.py, nikki_holes.py (boundary loops),
  nikki_holereg.py, nikki_overshoot.py (max overshoot 0.12m symmetric),
  nikki_cmp_dump.py (vs Sep 18 backup: nothing removed/hidden/moved).

## Root cause chain fixed this session

1. Floating trim: world-space BBox inputs applied mesh-local → mesh-local
   GeometryNodeBoundBox in WallDetail (~218-221) + SlabTrim (~532-533).
2. Quoin staircase: MeshLine END_POINTS mode swallowed by try/except in 5.2 →
   explicit per-step offsets (Count 12, step (z1-z0)/11).
3. Bevel bomb: end-of-chain bevel on degenerate duplicates → scoped to band
   cubes at jband join (WallDetail); SlabTrim bevel retained deliberately.
4. Medallion overhang: fit filter |x - center| <= W/2 - 0.72 (threshold 0.716)
   before instancing.
5. 5.2 crash (the 00:32 wreck): Delete Geometry has NO Domain/Mode INPUT
   sockets in Blender 5.2 (node properties, defaults POINT/ALL) — invalid
   assignments removed; any rebuild now completes (177/33 nodes wired).

## Defects found, not fixed (recorded, out of scope)

- Gate count discrepancy: "15 walls + 5 slabs" (09-19 report) vs "14 walls +
  15 slabs" (09-20 re-run). Unexplained; counts recorded verbatim.
- p5 verify rows report broken local-vs-world deltas (dx -2.84 / dy -4.80);
  gate2 is the authoritative measurement.
- Overnight cron fleet re-saves blends in Saved/MelusinasHouse (FlowerBrooch
  00:48) — any job touching paris groups must gate + introspect after save.
