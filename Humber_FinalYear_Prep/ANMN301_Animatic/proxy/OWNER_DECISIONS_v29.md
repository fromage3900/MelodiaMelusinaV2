# OWNER DECISION PACKET — SHOREWAKE starskiff (tip v29_polish, 2026-09-18 run17)

Tip: `SHOREWAKE_proxy_v29_polish.blend` (209 objs / 53 mats).
Loop: `SHOREWAKE_LOOP_v4.blend` (rebased onto v29, seamless: f1/f120 deltas 0, pixel mean 0.0000/1px).
All renders below are in `Saved/Audit/` (gitignored, on disk). Fresh tip-state views
from this run (50% EEVEE, f150): `owner_packet_wide/tier/deck.png`.
Vision tool 500'd this run — owner eyeball pending on all four calls.

## D1 — Sail kiss: pick A or B (tip still carries the original kiss)

- Tip sail roll (`Boom_FurledSail`) top z = 2.7296, x -0.337..1.036 — unchanged since v21.
- Standing kiss (run03): bow stay min-z 2.66 vs sail top 2.729 at x~1.03 (0.0083 m graze).
- Variant A `SHOREWAKE_proxy_v22A_saildrop.blend`: boom group -0.244 Z, roll 2.285..2.485
  (brief-box center), gap 0.1549 m. Renders: `loop_v22A_saildrop_{wide,sail}.png`.
- Variant B `SHOREWAKE_proxy_v22B_stays.blend`: bow stay + pearl seaward +0.130 Z,
  gap 0.0689 m. Renders: `loop_v22B_stays_{wide,sail}.png`.
- Pearl beads already clear (1.19 m) — no kiss. Ribbon stays (`LIS_ribbon_stay_bow/ stern`,
  192v each) span z 0.89..3.04 and cross the sail band — re-check whichever variant wins.
- DECISION NEEDED: A (drop sail to brief box) or B (lift stays)? Loop then rebases the tip.

## D2 — Carillon vs pagoda: pick one (tip ships carillon visible)

- Tip now: `Tier2_Carillon` 2016v, x[-0.155..0.844] z[2.800..3.449], hide_render=False.
- `Tier2_Pagoda` 1920v, x[-0.086..0.775] z[2.800..3.716], hide_render=True (viewport visible).
- Co-located: wide/close pairs near-identical (328 px delta) — judge from the tier closeups:
  `loop_v24A_tier.png` vs `loop_v24B_tier.png` (46% pixels differ, decision-readable).
- Fresh tip view: `owner_packet_tier.png` (carillon closeup on current geometry).
- DECISION NEEDED: carillon or pagoda? (hide_render flip, one line, loop will ship a variant.)

## D3 — MoonWell basin vs spec'd seating well: keep or rework?

- Built (run11, fit-to-hull — spec well x 1.95..3.05 / y ±0.34 did NOT fit live beam ±0.27
  max, ±0.10 at foredeck; forcing it overhangs):
  - `DeckWell_BrassRim` x 2.259..2.941, z 0.805..0.825; `DeckWell_CoamingOuter` z 0.710..0.810;
    `DeckWell_ScryingPool` x 2.38..2.82, z 0.7405..0.7555; 4 cheek blocks; glow marker;
    specimen tray; rail arc; stern platform (boards x -4.15..-3.35, 4 posts, 2 hinges).
- Fresh tip view: `owner_packet_deck.png` (aimed x 2.6, z 0.77).
- DECISION NEEDED: keep the MoonWell scrying basin, or rework toward the plan's seating well?

## D4 — Legacy-mesh deletion approval (loop deletes NOTHING without this)

Hidden render-invisible meshes on the tip (all hide_render=True):
- `WakeTrail_legacy_flat` 36v — KEYED (1 of 11 keyed holders; seam suspect, flagged run16).
- `ProxySkiffHull` 8v, `Sail_MK33` 529v, `Pennant` 4v (old), `Pennant_Sim` 81v (bake source,
  re-hidden per cloth-bake rules), `FLIP Domain` 8v, 5 guide curves + 3 swag profile objects.
- `Heart_Template_L` 697v — REQUIRED by the heart-chain kit. DO NOT delete.
- `Tier2_Pagoda` — hidden only if carillon wins D2.
- Keyed holders (11): FoamCollar, Pivot_PennantSway, ProxyLyreNeck, ProxyLyreRing,
  ProxyWater, Ripple_Ring_1/2, Starskiff_MK38, TurbField, WakeTrail_legacy_flat, WindField.
- DECISION NEEDED: delete list (suggest: ProxySkiffHull, Sail_MK33, old Pennant,
  WakeTrail_legacy_flat AFTER loop re-keys without it, FLIP Domain)? Guides/profiles stay.

## Also open (not decisions, FYI)

- `SHOREWAKE_proxy_v28_insets.blend` (operator live pass, +534 KB, untracked branch).
- 3b-bake atlas wiring onto hull mats; creative-expansion lane (perch/caustics/kit).
