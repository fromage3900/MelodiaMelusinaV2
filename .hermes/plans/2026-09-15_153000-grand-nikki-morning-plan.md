# Grand Nikki Morning — Execution Plan

> **For Hermes:** execute track by track; owner viewport gates every beauty claim; ledger == manifest == disk always.

**Goal:** Make L_MelusinaMorning feel like Nikki designed the room and Melusina lives in it — vertical furniture route with Dawnmote collectibles, a wardrobe-powered glide loop to the sheep, house PCG systems with rules behind them, Megascans that obey the toon master.

**Architecture:** Ability outfits are exploration verbs (translation doc §2); layered specialization over giant systems (principle 1); cheapest representation that preserves the hero requirement. PCG where it generates, Python generators where the gallery is hollow, direct placement nowhere without a manifest.

**Tech Stack:** UE 5.8, Monolith editor Python, 4 proven-live PCG graphs, house-dell generator family, toon masters, audit JSON.

---

## 1. Standing evidence (do not re-derive)

- PCG LIVE (spawner present, generated on demand): `PCG_Hero_BellTreeGarden` (14/1), `PCG_Hero_ArpeggioBridge` (16/1, 24 nodes in Morning), `PCG_Hero_ResonanceCathedral` (24/1), `PCG_Hero_XylophoneTrail` (12/1, needs spline coverage), `PCG_SeaAbove_BellTreeGarden` (19/1). `PCG_Hero_TeaGarden` (16/1) generates nothing without its missing input — parked.
- PCG HOLLOW (0 spawners, pretty names only): all `PCG_Nikki_Mandala*`, `PCG_Nikki_Phyllotaxis*` (+`_Walkable`), `PCG_Bezier*` avenue/terrace family, `PCG_WallGardenPath`, `PCG_TerraceGarden`, `PCG_SeaAbove_East_Phyllotaxis*`. Never wire these; never build a 755th binary graph to compete — extend the generator family instead.
- Proven in Morning today: heatmap→manifest→apply→reload-proof loop; actor-spawner counting (ISMs lie, headcounts don't); PCG volumes ignore position (graph-local layout — stage output by transform); WP payload saves need explicit package lists; deleted-actor husks don't save (repurpose, don't delete); lake BP won't code-spawn, native `OceanologyLake` does and the BP is an empty shell.
- Morning state: dell lived (24 arp steps bed→sheep, 18 bells, native lake, ChoirStone bed, 71 house-dell scatter), FXAA lock b6d5b032, PPV frozen four, Sir stencil 4.
- Traversal already proven project-wide: wardrobe Glide/Dash/Swim (`wardrobe_gameplay_hook` PASS) — the glide loop spends existing capability, no new authority.
- Megascans open question: instances suspected of dead parameter names (overrides authored against old master). Unproven — Task 4 diagnoses before touching.

## 2. Tracks (order of execution)

### Track A — Vertical route + Dawnmotes + glide loop (the special)

- A1: Survey climbables live (bed, shelf, wardrobe, rafters, window ledges SM_Greybox_Wall_Window*): labels + top-surface Z via raycast; write `Saved/Audit/morning_vertical_survey.json`.
- A2: Author `morning_dawnmotes` generator (sibling of `Content/Python/morning_house_dell_build.py`): 7 Dawnmotes — 5 along the furniture route, 1 above the lake (glide bait), 1 behind the door (explorers' tax). Motes = small ISM/star mesh + PointLight-free emissive MI (no light budget burn; 7 lights already live).
- A3: Glide loop contract: wardrobe Glide from window ledge (1679, y~2500, z~-300) carries to sheep dell (-850, 2400, -650) — distance ~2.5k uu descending. Verify by `pie_call_function` LaunchCharacter arcs or owner playtest; tune ledge height, never the glide authority.
- A4: Viewport gate at portfolio cam + a high cam: route readable, motes visible, ink calm.

### Track B — House PCG systems (rules, not clutter)

- B1: `ShelfClutter` generator: phyllotaxis rows on shelf surfaces (books/trinkets from real meshes only, load-verified, seed-locked) — same manifest discipline as the dell.
- B2: `DustPlatforms`: floating dust-mote platforms inside the window light shaft (saw `FX_Morning_DustShafts_Threshold`): WPO bob via existing Niagara/MPC read (materials READ BeatPulse, never write — single-writer stands); platforms are visual rhythm, not collision promises until playtested.
- B3: `StarRail`: mote trail from bed to the climb start — guides without UI.
- B4: Underbed nook: one hidden Dawnmote + shrunk-scale dressing (no new shrink authority — dressing only).

### Track C — Megascans remediation (diagnose first)

- C1: Census Megascans MIs in Morning + dell meshes (`SM_RockScan_01`, `SM_BeachSandWithPebbles_*`, `SM_GrassGroundPatch_01`, `SM_ForestDeadTree_01`, `MI_MossyRock_21`, `MI_Rock_01`): read each MI's override names, diff against live `M_Master_Toon_Universal` params (scalar/vector/texture lists pulled once, saved to audit).
- C2: Dead names (e.g. `BaseColor` vs `Albedo`) get remapped per the safe-material-editing skill (re-map dead names → swap master default → add overrides; additive `set_instance_parameter` only, recompile, re-read verify).
- C3: Missing overrides (inherit marble/noise default) get real albedo + ShadowDream bless per the Greybox recipe. Never bulk-override multi-slot meshes (Atlantis trimsheet lesson).

### Track D — Sir, photo buddy (cozy beat, cheap)

- D1: Vanity/styling corner dressing where wardrobe changes happen in-world (one chair, mirror-ish reflective MI, warm point light IF budget allows — count first).
- D2: Sir idle perch near the vanity (stencil 4 ward holds; hull outlines stay his own).

## 3. Per-task execution contract (every placement task)

1. Manifest first (`melodia.morning_*` schema, seed, counts), load-verified meshes only.
2. Raycast-snap every point (clearance per kind); `no_ground` points reported, never forced.
3. `generate(True)` / spawn, then count the TRUE children (actors for spawners, ISM counts only for mesh splitters).
4. Save with explicit Morning package lists; never the stranger `MI_Universal_LayeredStone`.
5. Reload proof: counts identical before/after; then owner viewport.
6. Commit scripts + manifests with `--only` pathspecs (never bare `git commit` — other lanes stage here).

## 4. Validation

- Counts: manifest == apply report == reload proof == commit message, every track.
- Beauty: owner eyes at `CAM_MelusinaMorning_Portfolio` + one high cam; agent frames are technical only (brightness/litness), never beauty proof.
- Gates: glide loop needs a playtest sample (LaunchCharacter arc or owner flight), not a probe claim.

## 5. Risks

- Hollow-graph temptation: anyone proposing a new binary UPCG graph must show why the generator family can't carry it.
- Single editor holder; never commit mid-edit; dirty-check before kills/restarts.
- No new landscapes; no PPV surgery; no second audio writer; no skill-Blueprint Python touching.
- Scope guard: this plan does NOT include the Greybox 11-mat conversion or outline Task 2 — separate queue items (`greybox`, `inkwell` todos), same contract when they run.
