# SHOREWAKE Boat — Master Plan v09 (step-back, 2026-09-17)

Supersedes as the working chart: BOAT_POLISH_PLAN_v05, BOAT_TOPOLOGY_STUDY,
BOAT_MOTION_PLAN_v08 (still valid for its motion systems; this plan sequences
and prioritizes everything). Owner lane: Melusina, wardrobe, panels of her.
This lane: the boat and everything on her.

Deadline: ANMN301 animatic A1 due **Oct 9**. The boat appears in shots
01 (wide mooring), 03 (skiff close), 13 (skiff wakes), 15 (crossing),
16 (route opens). Everything else is portfolio-bonus.

## 1. Evidence-based state (what is actually true tonight)

On disk — `SHOREWAKE_proxy_v07_decor.blend`:
  fresh GN hull trees live; 9 ribs U-seated (tips spring 0.32 above deck);
  balljoints at rib tips; star finial crown on the masthead lantern;
  star-pendant garlands along both rails.

Live-only in the open session (unsaved adds from tonight):
  BrightworkBolts (44 hex keel bolts + 32 dome rail rivets, parent-fixed);
  CrowsNest (platform, 8 posts + brass caps, rail hoop, 16-petal fringe);
  Pennant_Sim cloth + WindField/TurbField (sim moves, max 3.9 cm);
  Cam_BoltCheck, Cam_NestCheck (check cams); raytracing ON.

Toolchain truth:
  HardOps 26.1.5 ENABLED (315 ops, modal — owner's GUI passes).
  MACHIN3tools and MESHmachine FAIL TO REGISTER under 5.2 (older releases).
  FLIP Fluids disabled (errors every frame under 5.2); flip stays HOLD anyway.
  cloth_next / Jiggle_Maker / SwingyBone not enabled (enable on use).

## 2. Read critique — what still doesn't read (render + vision checks)

1. **Sail is the biggest unread surface.** Sail_MK33 = 529 verts,
   M_Sail_Pearl_Damask, bbox x -1.19..0.54, y -0.07..1.76, z 2.29..2.56 —
   a near-flat pearl sheet extending 1.76 m OUTBOARD to +y. Renders as a
   translucent grey plane. Decision needed: deployed (needs boom + rigging +
   wind shape) or stowed/furled (calm-night truth for shots 01-12).
2. **Brass reads dark.** Metallic 0.85 in a near-black world (0.03/0.04/0.08
   @0.6). Raytracing is now ON — unverified; a warm fill may still be needed.
3. **Pennant placement.** Now sits at z 2.33 beside the new nest — decide hang
   point (recommend: nest rail height, clear of the platform).
4. **Garland stars read as small white nubs** at distance — cord nearly
   invisible. Options: bigger stars / more pendants (GUI dials), or brass cord.
5. **Bolt rows sparse at closeup** (0.33 m spacing, reads scattered).
6. **Mast is bare** between boom and nest — wants bands/lashings/line work.
7. **Nest approved** (reads correctly, centered) but lacks connection to the
   deck: rope ladder + a hanging bell or sign are the natural next whimsy.

## 3. Workstreams (priority order against Oct 9)

A. READ-FIXERS (this week, before any new pretty):
   1. Sail decision + execute (deployed rig or stow).
   2. Brass look-check after raytracing; warm fill option in a copy.
   3. Pennant reseat clear of the nest.
   4. Garland legibility pass (star size/count dials are GUI; cord material
      or thicker cord ratio via a fresh tree if needed).
   5. Bolt density check on the closeup cam (keep 0.33 storybook, or 0.20).

B. WHIMSY LAYER (second story, continued):
   1. Rope ladder deck→nest (two rails + rungs, brass grommets).
   2. Hanging bell or little sign under the nest rim (kit filigree optional).
   3. Laundry line across the boom with two small cloths (cloths get cloth
      sim later if the wind system asks for it).
   4. Bow crest: kit filigree (filigree_panel / rosette family — note
      rosette defaults 1.2 m radius, GUI dial or scale at object level).
   5. Stern name plate (transom panel + gilt border).

C. HARDWARE / CAD FINISH:
   1. Mast bands (3 brass rings) + rope lashings at boom and nest.
   2. Hoop rework pass (Lantern_Hoop tri) — match the new nest hardware.
   3. Keel shoe end caps; two bolt sizes for variety.
   4. A dimension sheet: keep this table current in the plan (CAD discipline).

D. MOTION SYSTEMS (per v08 plan, unchanged): wind states, pennant bake,
   anchor rock keys, water tier 1 (ocean + ripples), the five promoted shots
   (01, 07, 08, 13, 15), cut rebuild.

E. GN/CAD WORKFLOW KIT (make deco repeatable instead of bespoke scripts):
   1. `raycast_place()` + `seat_by_iteration()` helpers as Saved/Audit tools.
   2. Reusable GN builders to add to the kit: scallop ring, gingerbread
      bracket, rope ladder, railing gen — so the next whimsy piece is
      instanced, not scripted from scratch.
   3. Pattern law (learned tonight): absolute-coord meshes get
      matrix_parent_inverse cancelled; guides stay unparented; hosts zero-vert.

F. INFRA HYGIENE: parent-inverse pattern (done in live fixes); .001 material
   sweep before each save; live-collab protocol — agent announces changes,
   owner announces undos; never enable broken addons (FLIP stays off).

## 4. Measured dimension sheet (keep current — CAD reference)

    Hull_Shell            7.55 x 2.51 x 0.99 (local), waterline ~z 0.57 world
    Deck / gunwale top    z ~1.30 (rib tips spring to 1.62)
    Rub rail band         z 0.83..0.88, half-width 0.36 (midship)
    Keel BrassShoe        z 0.28..0.31, x -3.87..3.33
    Rib stations (world)  -4.07, -3.12, -2.17, -1.22, -0.27, 0.69, 1.64, 2.59, 3.54
    Mast                  x 0.30..0.37 (center 0.333), z 0.93..3.13
    Masthead lantern      top z 3.51 | star finial 3.54..3.84
    CrowsNest (new)       z 2.30, r 0.34, posts 0.24, centered on mast
    Sail_MK33             x -1.19..0.54, y -0.07..1.76, z 2.29..2.56 (REVIEW)
    Pennant               z 2.33 area (RESEAT pending)
    Anchor (rock driver)  loc (-0.267, 0, 0.579), keys 10..170 (wake lift +0.3)

## 5. Schedule to the deadline

  Sep 18-24   Stream A read-fixers + C hardware; re-render boat beauty set +
              skiff panel stills; commit v08 generation.
  Sep 25-Oct1 Stream B whimsy + E workspace kit; commit v09.
  Oct 2-7     Stream D motion (five shots), VSE cut rebuild, owner eye pass.
  Oct 8-9     School-format deliverables + submission buffer.

## 6. Owner decisions needed (recommendations in bold)

  1. Sail: **stowed/furled for the animatic** (calm night; deployed implies
     under way, contradicting shots 01-12) — or deployed with full rigging.
  2. Pennant: **reseat above the nest rail**, clear of the platform.
  3. Brass mood: **warm fill trial in a copy** — the dark-bronze night is
     also defensible and yours to keep.
  4. Bolt density: **keep 0.33 storybook spacing**; densify only if closeups
     come back sparse again.
  5. Whimsy trio: **approve ladder + bell/sign + laundry line** as stream B.
