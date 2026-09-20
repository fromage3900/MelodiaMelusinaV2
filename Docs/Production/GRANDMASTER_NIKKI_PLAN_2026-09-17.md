# Grandmaster Plan — Nikki Bar (2026-09-17)

**Status:** CURRENT. Replaces the 07-15 master plan v2 and the 09-03 lookdev reel plan as the working chart.
Stale sources, do not follow: `Docs/TD_GRANDMASTER_MELODIA_PLAN.md` (SUPERSEDED 2026-09-08),
`Docs/GRANDMASTER_MASTER_PLAN_V2.md` (07-15; cites forbidden :8000 lane, UE 5.7 plugin, Blender 5.1).
Live authorities: `CURRENT_STATE.md`, TD `MELODIA_LIVE_VISUAL_IDENTITY_CONTRACT_2026-09-08.md`,
`PORTS.md` (OSC :9000 single lane), `Docs/Reports/NIKKI_MASTER_MERGE_DROP_2026-09-09.md`.

## 1. What "Nikki master" means here (the bar, concretely)

Infinity Nikki is the wardrobe/visual bar per project law. For this plan it cashes out as five
checkable properties, not a vibe:

1. Hero silhouette reads at thumbnail scale (Melusina, Sheep, Starskiff unmistakable).
2. Toon bands are clean: stepped cel with halftone penumbra, no muddy terminator
   (TD `SHADER_BREAKDOWN_SPEC.md`: half-Lambert wrap, 2-3 bands, 45-degree dot lattice).
3. Materials answer music: Chladni/iridescence driven by the MPC palette, never a second audio writer.
4. Post identity is frozen: `PPV_NikkiDream` stack + hero stencil 4, tonemapped V7.1.
5. Cloth and hair move: secondary motion believable at rest and in motion (KawaiiPhysics runtime,
   baked keys for renders).

Do not plan around `M_Master_Nikki.uasset`: it left main in merge `f19b6459` (see merge-drop
record). Sheep stays parented to `M_Master_Toon_Character` with Chladni as a child. Restore a
dropped master with `git checkout f19b6459^1 -- <path>`, never a rewrite.

## 2. Lane A — Grease Pencil animation (Blender 5.2)

Purpose: hand-drawn motion layer for the animatic and capstone flourish (fx accents, motion
lines, facial acting passes over 3D proxy renders).

- Library: `Tools/sync_grease_pencil_asset_library.py` re-synced 2026-09-17 against Blender 5.2
  (fixed 5.1 source path + G:-drive fallback; audit: `Saved/Audit/grease_pencil_asset_inventory.json`).
  4 Essentials blends + catalogs live in user OneDrive lib and repo-local `Assets/GreasePencil/`
  (gitignored by design — un-ignore needs owner sign-off before the library is versioned).
- Workflow: proxy render (e.g. Shorewake panels) as reference underlay, GP layer over for
  accents; keep GP objects per-shot named `GP_<shot>_<pass>_v01`.
- Direct feed: ANMN301 animatic (silent 1080p24, Oct 9) — GP accents are how a 3D-proxy
  animatic reads as authored rather than viewport-captured. Capstone weeks 3-4 scratch.
- Proof: PNG sequence per shot in `Humber_FinalYear_Prep/ANMN301_Animatic/` + blend checked in
  (never the MP4 for versioning).

## 3. Lane B — Shader breakdown shots

Purpose: portfolio cards proving each master, one camera per card, deterministic.

- UE side: `Content/Python/setup_technical_breakdown_cameras.py` already defines the five cards
  (shader_master, material_instance, pcg_heatmap, trim_sheet, world_shader) writing
  `Saved/Portfolio/technical_breakdown_cameras.json`. Run in-editor, capture via Movie Pipeline.
- TD side: `SHADER_BREAKDOWN_SPEC.md` frags (nikki_atlus_cel, nikki_iridescent + audio phase
  term) render as their own breakdown cards from the `.tdn` networks.
- Card spec per master: beauty | wireframe/UV | isolated parameter sweep (e.g. band count 2/3,
  dot radius) | in-scene. Four frames, same camera, labeled.
- Priority order: `M_Master_Toon_Character` (Sheep-proven), `M_Master_Toon_Universal`,
  Oceanology water, SDF cathedral, frozen PPV stack.

## 4. Lane C — Demo reel cards

Reel law (from capstone tracker): 45-60 s total, best shot first, no filler, breakdown sheet
per shot, music low. Portfolio freeze holds except the isolated WebGL-kit lane.

Card queue (each card = shot + breakdown sheet + ledger row):
1. Melusina beauty (EEVEE, contact shadow + twilight env; prior rating 7/10, target 8.5).
2. Glam close-up (denoised skin, env rim; 8.5, target 9).
3. Sea Above golden spiral (PPV_NikkiDream, twilight key + cool rim, 4K24 Movie Pipeline).
4. Starskiff mooring hero (Shorewake sprint composition: processional/profile/wide, pick one).
5. Choral Sheep Harmonize (REST > ROOT_C > hit > REST, lit fleece — the open capture).
6. Shader cards sizzle (5 s montage of Lane B cards).

Assembly: Blender VSE at 1080p24 (same toolchain as the animatic — one skill, two uses).

## 5. Lane D — TD passes (live-performance layer)

Authority: `MELODIA_LIVE_VISUAL_IDENTITY_CONTRACT_2026-09-08.md` (CURRENT). Hierarchy per frame:
subject silhouette first, one musical structure second (Chladni ring / staff field / glyph),
atmosphere third (water-light, pearl particulate, restrained bloom), data/typography last and
only if structural. Palette: black-violet negative space, pearl, sea cyan, lavender; dusty pink
and brass as accents only. No rainbow, no cyberpunk RGB, no permanent magenta/cyan split.

Pass order in `td/grandmaster_melodia/`:
1. Silhouette pass (subject isolation, stencil-equivalent matte discipline carried from UE).
2. Musical-structure pass (Chladni fleece states: 6 harmonic states already landed 09-08).
3. Atmosphere pass (water-light + pearl particulate, water perf budget doc applies).
4. Grade pass (Nikki LUT-equivalent as offline `.tox` for UE loading; real-time lane stays
   OSC :9000 + Spout, never :8000, never a second channel).

Perf: `WATER_PERF_BUDGET.md` caps the water work; Envoy :9870 is the inspection door;
hand bridge :7001 untouched while running.

## 6. Capture & evidence standard

- UE: Movie Pipeline, 4K, 24 fps (matches reel + animatic frame rate; one conform pipeline).
- Blender: EEVEE stills at 100% for cards, 50% for proxy iteration; one headless process per
  frame; verify by on-disk byte diff, eye-check hero frames.
- TD: locked `.tdn` + stills in `docs/renders/`; no live-screenshots-as-proof without the
  network file that made them.
- Every card gets a ledger row or it did not happen.

## 7. Sequence (weeks, not wishes)

- Wk 2 (now): Lane A GP library re-sync + animatic panels feed; Lane B run breakdown-cam
  script in-editor once (needs the single :9316 session).
- Wk 3-4: Lane C cards 1-2 (Melusina beauty/glam) + Lane D silhouette pass lock.
- Wk 4-6: Lane C cards 3-5 + Lane D musical/atmosphere passes; sheep fleece capture closes.
- Sem 6: grade pass + reel assembly in VSE; premiere.

## 8. Non-goals (explicit)

No new material masters. No second audio writer, no second MPC contract, no second OSC lane.
No wholesale branch merges (cleanup + studio lanes stay scoped-PR only). No capstone-logic
changes to the rhythm/JRPG/Quill seams — this plan dresses the game, it does not rewire it.
