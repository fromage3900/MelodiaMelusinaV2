# Melusina's House V2 — Infinity Nikki Environment Lens

> Canonical parent: /melusinashouseplan.md (731 lines, 2026-09-02, still structural authority)
> This file: styling-journey overlay. It changes the ORDER, the ARRIVAL, and the CAMERA logic.
> It does not change the hero dimensions, the GN_MH_* names, or the ownership model.
> Branch: docs/2026-09-02-grand-master-plan. Authoring: Blender 5.2.1 headless-verified.

## 1. Thesis in one paragraph

V1 proved the grammar: concave shoulder, convex entry, concave shoulder, three roof ribbons,
tower counterweight, 13.2 x 9.8 x 3.42 m shell. V2 keeps every number and re-reads the house
the way an Infinity Nikki environment designer would: the house is not an object to look at,
it is a short cozy route to walk, styled in layers, with a photo beat every 8 to 12 meters,
no fail states, and every system earning its place as either path, threshold, backdrop, or
ritual. The four corridor/zen stubs we just closed are what make this reading possible —
before them there was no walkable arrival; now there is.

## 2. What V2 reuses, with receipts

All of these are built and headless-evaluated on Blender 5.2.1. No new builder bodies were
copied; house code wraps GROUP_BUILDERS per deploy/surreal_arch/README.md.

  Hero shell (unchanged dims, verified):
    GN_MH_02_CurvedWallShell_v2 — Tools/house_facade.py — 24 yawed modules on the 3-bay guide,
      door + 4 window boolean branch kept isolated, bevel on the wall branch only.
      Receipt: 800 verts / 820 faces, x [-6.48, 6.47] = 12.95 m, y [-0.94, 0.94] wave,
      z [0, 3.42] exact. Facade Wave 0.65, Wall 0.30, door 1.15 x 2.35.
    GN_MH_03_RoofRibbon shared builder — Tools/house_roof.py — one builder, three trees
      (headless 5.2 cannot set per-object modifier inputs, so params bake as tree defaults).
      Grid 25x13, profile sine(pi*u)^1.3 body + eave curl^2 + end lift^3 + skew.
      Extrude Offset driven BY NAME with Selection=True (inputs[1] is Selection — the 20%
      oversize bug came from driving Thickness by index). Bevel 0.03.
      Receipts: Main 9.0 x 6.0 rise 2.55, z 0.50-2.99; Wing 6.0 x 4.5 rise 1.9 at z 3.1;
      Porch 4.5 x 2.4 rise 1.1 at z 2.9.
    GN_MH_04_ScallopShingles patch — Tools/house_shingle_patch.py — UV-space 7x9 lattice,
      alternate-row 0.5 offset, Sample UV Surface for Position+Normal, squashed-sphere proxy
      tile 0.28 x 0.36 at 40% overlap. Receipt: 9v/4f base, 63/63 instances seated at z 0.000.
      Rule carried forward: prove the 2x2 m patch before touching hero roofs.

  Arrival kit (the newly closed stubs — this is what V2 is really about):
    MEL_allee_ribbon — deploy/surreal_arch/melodia_gn/ribbon.py:285 — the only ground ribbon
      in a registry of vertical strips. Grid strip bent S in plan by sin(2*pi*u)*0.5*S-Curve,
      crowned across width by Camber*(1-(2v-1)^2), Transform-scaled to Length/Path Width,
      extruded down by Thickness via Offset-by-name. Defaults Length 8.0, Path Width 2.2,
      S-Curve 1.0, Camber 0.08, Thickness 0.12. Receipt: 29 nodes, 520 verts, x +-4.0,
      z 0-0.20. Registry 246 -> 247 ids, category effects.
    build_zen_cherry_allee v2.74 — deploy/surreal_arch/zen_kit.py:457 — staggered trunks
      with deterministic height jitter (no flat colonnade ceiling), two canopy slabs per tree
      scaled by zen_canopy_spread, petal drift count from zen_petal_density (0.6 default).
      Receipt: 49 nodes, 184v/138f. Props: gb_length 6.0, gb_width 2.6, path slab W*0.55.
    build_zen_teahouse — deploy/surreal_arch/zen_kit.py:534 — delegation adapter over
      the polished monolith builder at deploy/surreal_architecture_gen.py:12995 (the
      unique authority: engawa platform + railings, corner posts, tatami, irimoya curved
      hip roof, bezier hip ridges, hoju finial, tokonoma, ro hearth). Translates
      teahouse_* graph props with gb_* fallbacks into the monolith prop contract.
      Receipt: 81 nodes, 3918v/3767f.
    GB_CORRIDOR_BEND + GB_CORRIDOR_T — deploy/surreal_greybox/shells.py via
      integration.py shape-matching adapters — the curved-building fix. L-bend 53 nodes /
      200v, T-tee 39 nodes / 144v. These give the interior its round-plan connectors so the
      inside never secretly becomes a rectangular sitcom house.
    ZEN_BRIDGE alias + build_zen_water_edge — zen_kit.py:601 — stream bed, raised banks,
      stepping stones at landings. ZEN_SANDO — zen_kit.py:648 — paving + border stones +
      lantern rhythm. Together they are the threshold kit between garden and door.

  Ownership boundaries (do not cross these in V2):
    Wardrobe owns outfit state and gameplay/identity hooks — Content/Python/
      wire_melusina_wardrobe_instances.py is the wiring manifest. The house provides only
      hooks: mirror dais, genkan change-step, tower vista perch, teahouse quiet seat.
      No outfit enums, no ability flags, no duplicate state in any GN tree.
    QuillScript owns narrative intents/flags/checkpoints. The house exposes named empties
      and trigger volumes; it never stores a flag.
    TurnBased JRPG template owns party/turns/damage/inventory/saves. The house is art.
    Convergence interprets cross-system relationships (petal -> motif, chime -> phrase).
      Petal scatter stores a trim:petal_scatter tag; interpretation lives downstream.
    Melodia rhythm rides on top of actions; Sample Sound Frequencies stays an offline
      lookdev proxy (lantern pulse) per plan s13. Unreal/MelodiaCore stays runtime authority.

## 3. The Nikki reading: house as a 90-second styling walk

Design target: a visitor in default dress walks from the lane to the tower lookout in about
90 seconds, passes 7 photo beats, never squeezes under 1.4 m clear, never climbs over 0.22 m
in one step, and can stop anywhere for a full 360-degree camera without clipping a wall.

  Beat 0 — Lane mouth (existing world, not this plan). First glimpse of tower cap at 10.5 m
    over the canopy. Nothing to build; protect the sightline.
  Beat 1 — Cherry allee tunnel, 8-12 m. MEL_allee_ribbon (Length 10-12, Path Width 2.2,
    S-Curve 1.0-1.4) under build_zen_cherry_allee (gb_length 8-12, spread 1.0-1.2,
    petal_density 0.6). Crowns stagger so dappled light breaks across the path, never a flat
    ceiling. Camera: over-shoulder walk, canopy frames top third. Photo: mid-allee, convex
    facade peeking through trunks.
  Beat 2 — Bridge + water edge threshold. ZEN_BRIDGE span across build_zen_water_edge
    (stream depth 0.35). Stepping stones land on the allee ribbon end. Sound cue hook only
    (Convergence maps water shimmer to a phrase downstream; no audio authority here).
    Camera: low three-quarter, aqua glass glinting behind.
  Beat 3 — Sando + lantern rhythm. build_zen_sando paving 2.2 wide, lanterns alternating
    sides every ~2.2 m. This is the Nikki slow-down: straight axis, flanked rhythm, porch
    drapes visible ahead. Evening variant: lantern emissive up, honey interior 2700K behind
    aqua glass (M_MH_AquaGlass + interior emission, already in palette).
  Beat 4 — Porch embrace. GN_MH_01_FoundationPorch per plan s2 (extrude 0.35-0.50, bevel
    0.05-0.08), deck 1.8 m deep, stair cheeks as C-curves into shell-finial posts, balusters
    at 0.32 spacing with every 4th/5th a shell accent (GN_MH_08). Lavender awning proof
    (GN_MH_09, grid 18x8/24x10, sag -Sag*sin(pi*u)^2) + tassels. Camera: seated height,
    sea-facing. Wardrobe hook: genkan step = the outfit-change beat; mirror dais inside
    entry, not on the porch (weather + clutter).
  Beat 5 — Convex entry. The facade v2 center bay pushes +0.94 m toward the visitor.
    Door 1.15 x 2.35 arched plank + brass inset + treble-clef ornament (reuse musical kit,
    GN_MH_12). C-curve surrounds on windows, richest shell/pearl statement ONLY here
    (GN_MH_07 rule: entrance richest, windows smaller, roof crests thin, 15-25% secondary
    omit always). Photo: centered door portrait, pearl plaster #F7D6E7 against roof blue.
  Beat 6 — Round interior loop. GN_MH_11 derives partitions from wall guides; connectors
    are GB_CORRIDOR_BEND (L) and GB_CORRIDOR_T (T), never square halls. Layout per plan s12:
    center entry/sitting + circular rug, left music/prayer nook, right kitchen+pantry,
    rear/right curved stair, loft left/center sleep + right writing desk, tower lookout niche.
    Furniture stays hero-authored; GN solves repetition and grammar only.
  Beat 7 — Teahouse quiet + tower vista. build_zen_teahouse sits rear/side as the still
    counterpart to the musical house (craft/rest fantasy vs performance fantasy). Tower
    (GN_MH_06: base, tapered shaft dia 1.8, lantern ring, spun cap, crest, chime arm +
    2-4 charms) tops at 10.5 m. Camera: 360-degree lookout, allee + roofs + sea in one pan.
    This is the route's payoff screenshot.

Widths verified against the 1.7 m mannequin in MH_GUIDES: path 2.2, porch 1.8, door 1.15 —
all camera-safe. Keep the mannequin until the final silhouette pass per plan scale table.

## 4. System-by-system V2 deltas (what to actually build next)

  4a. Path system (new authority: allee ribbon + cherry allee + sando + bridge).
    Route spine: allee_ribbon Length 10-12 end-to-end from lane to sando, S-Curve 1.2 so the
    facade reveals in thirds. Cherry allee gb_length matches ribbon Length; trunks at
    W*0.42 offset so clear walk stays >= 1.6 m. Petals N = round(L*0.9*density)+1 along the
    walk only — never broadcast scatter. Sando takes the last 6-8 m straight; lanterns carry
    the rhythm the canopy drops. Bridge only where water crosses; one span, no feature creep.
    Exposed params: Length, Path Width, S-Curve, Camber, Thickness, zen_canopy_spread,
    zen_petal_density, zen_stream_depth. All live on the path trees, nowhere else.

  4b. Shell + roofs (no geometry change, one expansion).
    Facade v2, roof ribbons x3, tower stack stand as verified. Next step is the gated one
    from plan s6: expand the 63-instance shingle proof onto the three ribbons via Sample UV
    Surface. Requirements before expansion: clean non-overlapping UVs per roof, 3-5 scallop
    variants (Geometry to Instance, unrealized), hue drift blue/lavender/aqua + occasional
    blush, scale 0.95-1.05, overlap 40%. If rows slide on the eave curl, fix the UV, not the
    tile — never compensate with per-tile rotation hacks.

  4c. Threshold system (teahouse + porch + genkan).
    Teahouse is the quiet room, built by the monolith authority: engawa platform with
    railing posts, tatami mat, irimoya curved hip roof with upturned eaves, tokonoma
    alcove with tokobashira, sunken ro hearth. No kitchen, no bed, no second door
    family — it is one seat, one low table (hero props), one vista. Porch keeps the
    social load. The engawa edge is the physical wardrobe hook: step up = arrive, mirror dais just
    inside entry at sitting-room edge. Wire the dais empty to the wardrobe manifest; store
    nothing about outfits in the blend.

  4d. Interior connectors (the curved-building fix, applied).
    Wherever two round pods meet, use BEND or T — no square intersections, no custom halls.
    Corridor ribs carry the trim: corridor_rib_offset via _gb_trim_mode/_gb_trim_depth
    (RECESS default, 0.04 depth). Keep corridor width >= 1.4 m for camera. Partitions derive
    from CRV_MH_Footprint pods; if a partition wants to be straight for furniture, let the
    corridor absorb the curve, not the room.

  4e. Trim + ornament discipline (Nikki restraint, not maximalism).
    Rocaille library stays 6-10 source curves (C x2-3, S x2-3, shell fan, pearl string,
    clef/lyre). Pearl strings: Resample by Length -> Curve to Points -> Instance pearls.
    Seeded variation with composed asymmetry: omit 15-25% secondary, always keep hero
    crests (entry shell, corner finials, tower crest). Baluster accents every 4th/5th.
    Chimes/droplets on tower arm + porch corners only. If a surface already has shingle
    motion + fabric motion + petal motion in one frame, remove one — cozy reads through
    negative space (plan s11 rule: leave plaster readable).

  4f. Material + light as styling language (close-up moments).
    Six materials, no additions without a consumer: M_MH_PearlPlaster_Pink (blush #F7D6E7,
    pearl response), M_MH_Roof_IridescentBlue (blue #6E8AAF -> lavender #A8A0DD -> rose drift),
    M_MH_GoldBrass (#C6A15A, polished edges only), M_MH_WoodWarm (honey/walnut posts/floor),
    M_MH_LavenderFabric (awning/drape translucency), M_MH_AquaGlass (opalescent + warm
    interior emission). Nikki close-ups to art-direct: pearl plaster grain at door surround,
    scallop edge overlap at eave curl, brass clef inset, lavender weave sag, petal on path
    slab. Day: powder blue #9CC6E6 sky bounce; dusk: lantern + honey interior carry.
    No mirror metals, no candy plastic.

  4g. Collection + ritual loop (hooks only, Convergence owns meaning).
    Three collectible-feeling systems, all ambient: petal drift (density prop), chime sway
    (tower arm, offline sway only), lantern glow (emissive proxy, audio-reactive pulse is
    lookdev-only). Each stores a named attribute/tag (path_width, petal_scatter, crest id);
    Convergence maps them to motifs/phrases downstream. The house never counts, never gates,
    never saves — those are template/QuillScript authorities.

## 5. Master assembly + controls (boring join, expressive defaults)

  GN_MH_00_MasterAssembly stays the boring join per plan s13: FoundationPorch +
  CurvedWallShell + RoofRibbon x3 + Shingles + WindowDoorKit + Tower + Trim + Railing +
  Awning + Foliage + Interior toggle + NEW PathSpine (allee ribbon + cherry allee + sando +
  bridge/water) + Teahouse. Join Geometry -> visibility switches -> output.
  16 master controls per plan (Facade Wave, Wall Height/Thickness, Roof Rise/Curl, Eave,
  Tower Height/Diameter, Shingle Density/Scale, Trim Density, Asymmetry, Flower Density,
  Seed, Show Interior, Show Dressing, LOD) plus 4 path controls surfaced once
  (Path Length, S-Curve, Canopy Spread, Petal Density). One control, one owner — path
  width never appears on both the ribbon and the allee.

## 6. Build order (Nikki-prioritized, ~6 hours)

  1. Path spine first (60 min). Allee ribbon + cherry allee + sando stub in one WIP blend,
     walk the camera at 1.6 m eye height. Gate: 7 beats readable in clay, no trim, no color.
  2. Thresholds (45 min). Bridge/water + porch + genkan + teahouse shell. Gate: step heights
     <= 0.22, clears >= 1.4, eave shelters porch deck edge.
  3. Shell + roofs + shingle expansion (90 min). Facade v2 + 3 ribbons stand; UVs cleaned;
     63-proof expanded per roof. Gate: rows stable on curl, instances unrealized.
  4. Tower + trim + railing (60 min). Counterweight reads from lane mouth; entry gets the
     hero crest. Gate: silhouette unmistakably Melodia in front/3q/side.
  5. Fabric + foliage + materials + light (45 min). Awning sag, planter-only scatter
     (porch edges, tower base, window boxes, one stair side), six materials, honey interior.
     Gate: palette matches REF_01 without clutter.
  6. Photo pass + audit (30 min). Seven beats framed, screenshots to
     Saved/Audit/melusinashouse/, param audit, EXPORT duplicate only if approved.
  Cut first if time collapses: drape sim relax, interior dressing, tower charms. Never cut:
  path spine, facade wave, roof family, shingle proof, tower mass.

## 7. Verification status and next gate

  Proven on 5.2.1 headless: facade 800/820 + wave, roofs x3 dims, patch 63/63, allee ribbon
  29n/520v, cherry 49n/184v, teahouse 27n/96v, bend 53n/200v, tee 39n/144v, zero dangling
  graph ids (greybox_graph cross-check NONE). Harnesses: Tools/verify_ribbon_kit.py,
  Tools/verify_zenfix.py (purge installed surreal_arch from sys.modules before import —
  Blender preloads a shadow copy).
  Next gate: shingle expansion onto hero ribbons, then GN_MH_00 assembly. After that the
  route walkthrough on the laptop with the 1.7 m mannequin still in MH_GUIDES.

## 8. What V2 deliberately leaves out

  No outfit/ability logic in the blend (Wardrobe authority). No flags/checkpoints in trees
  (QuillScript authority). No second combat/rhythm authority — Sample Sound stays a lantern
  lookdev proxy. No p4 mother-category research stubs (declared stubs, out of scope).
  No EXPORT commits, no live v22 stage saves, no committed .blends without owner ask.
  New collections used: MH_GN_OUTPUT for path/house output; MH_GUIDES keeps footprint,
  facade, porch, 3 roof curves, rocaille, tower locator, cutters, plus the allee centerline.
  Guides are curves/empties only — never the boolean cutters themselves.

> House rule, V2 addendum: the walk is the house. If a detail cannot be seen, touched, or
> photographed from the 90-second route, it waits for a later pass. Make the arrival sing
> before adding notes to rooms nobody walks through.
