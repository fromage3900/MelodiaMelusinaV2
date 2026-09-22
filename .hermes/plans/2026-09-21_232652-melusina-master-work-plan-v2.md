# Melusina Master Work Plan v2 — Loose Ends + Convergence (supersedes execution order)

> **For Hermes:** This is the execution order. The deep task detail lives in
> `.hermes/plans/2026-09-21_232320-melusina-vfx-waterhair-flip-convergence.md` (A–F) and
> `.hermes/plans/2026-09-21_composition-melusina-sheep-cameras-goo-decor.md` (Phases 1–7).
> Every gate = measured JSON / PNG+JSON pair, never prose. Live session (:9876, PID 30268)
> is authoritative; never save it; heavy work on copies; never headless with LiquiFeel enabled.

**Goal:** One ordered plan that closes every loose end found tonight and lands the VFX
convergence (wings, clockwork, FLIP water-hair globs) without parallel writers or lost work.

---

## Wave 0 — Protect tonight's work (BLOCKING, ~15 min)

### Task 0.1: Bank the file (owner save or Save-As bank)
On-disk save is 21:36; everything since is memory-only: wings dials, 3 clockwork rings,
cornea re-weight, Sir texture repoints, sheep placements. One crash loses all of it again.
**Gate:** WIP saved or `*_BANKED_20260921/22.blend` exists with current mtime.

### Task 0.2: Land tonight's evidence (house standard: PNG + JSON pairs)
Tonight's verification (wings bbox, rings build+motion) has NO artifacts in `Saved/Audit/` —
scratch scripts only. Copy `mcp_probe.py`, `wings_reapply.py`, `wings_state.py`,
`clockwork_rings_build.py`, `clockwork_rings_verify.py` into
`Saved/Audit/melusina_vfx_20260921/` and re-run the verify probe once, writing
`rings_verify.json` + one PNG (solid shading, no EEVEE) next to it.
**Gate:** evidence dir contains the JSON with `ok:true` + PNG pair.

### Task 0.3: G: capacity note
90 GB free (checked 23:26) — sufficient for the res-72, 240-frame FLIP cache. Re-check at Wave 2.

## Wave 1 — Geometry gate (clears every blocker before FX)

1. **Hair existence:** 8 SHP curve systems generate zero geometry — diagnose + fix on a copy
   (convergence plan A1/A2). Unhide `Hair Strand.004/.007/.010`; remove −8.34 cm offsets;
   kill 30 degenerate polys on `.007`.
2. **Single body:** owner picks Melusina.001 vs Retopo (composition Task 1.1); retire the
   0-vert `Retopo_Melusina_002` shell if superseded. Double body poisons renders AND FLIP collisions.
3. **Sheep horns dead dials:** `Curl Turns` (Socket_3), `Spread` (Socket_7), `Align To Body`
   (Socket_10) are unwired inside `MEL_S5_horns` + anchor math sits 0.69 m low. Wire the three
   sockets, lift the anchor to the skull (z≈1.03), re-verify via `mod.properties.inputs[id]["value"]`
   + `ob.update_tag()` (handoff §5/§7).
4. **Sir Melodious:** find/replace 3 missing textures (`Material.021_BaseColor/Normal`,
   `coat_BaseColor`), fill `SirMelodiousBody` empty material slot 0.
5. **Harp lights:** move the three e650/260/800 stage lights to `Harp_QA_Lights`, hide_render
   (composition Task 1.3); set render res back to 100%.
**Gates:** per-task JSON (vert counts, bbox, dial table, texture census, light census).

## Wave 2 — Water-hair FLIP + globs (convergence plan B/C/D, detail there)

1. Generational copy `waterhair_flip_v01.blend`; `--factory-startup`, LiquiFeel OFF; one Blender.
2. Wire domain (res 72, frames 1–240), bone-parent the `FF_MelusinaHair_Drip` emitter to hair
   deform bones, bake to the staged G: cache dir (create first).
3. Mesh sequence into `FLIPMeshes`, append into live session in-memory, owner scrubs.
4. `MEL_hair_water_glob` builder (house carrier pattern; beads/ico instances, scale-by-curvature);
   land in AppData package only with Blender CLOSED, then gate + deploy to repo (mirror of the
   Higgsas gate pattern — the AppData package is ~20 modules ahead of repo deploy; sync there).
5. LiquiFeel stays GUI-only on the 3 tip-drip hosts. `Water (Advance).002` stays the ONE
   hair-water material writer (extend it: transmission, iridescence, foam mask).
6. Goo GOOFLAPPY bakes for glob wobble on scratch duplicates (FLIP = fluid authority,
   Goo = jiggle authority — never two of either).
**Gates:** cache frame count == 240; emitter path length > 0; glob-surface adherence ≤ 2 cm;
material user census (hair-water = 1 family); PNG+JSON per step.

## Wave 3 — Composition & beauty (composition plan Phases 4–7, after Wave 1)

Camera reframe + gaze pose + second angles + neutral fill + 100% panel renders, PNG+JSON each.
Fold in: ring iridescence material pass, FX_Hero render-visibility audit (dressing-only rule),
bard regalia dangles (Task 6.2 registry: `MEL_nikki_star_pendant`, `MEL_nikki_bead_string`,
brooch hero per genome). Floating-regalia variant stays AFTER the stills — it is a motion
showpiece, not a beauty-frame dependency.

## Wave 4 — UE handoffs (parallel lanes, exclusive editor windows)

1. **Arrow/aim fix (today's measured defects):** staged root `ME_WaveHarp_R08_STAGE_Root` has
   zero rotation while she faces −Y (arrow flies +Y, 180° off); `SOCKET_Bow_Aim` coincident with
   `SOCKET_Bow_Grip` (zero direction vector for consumers). Fix sockets + staged rotation.
2. **Bowstring transform gap (Claireon §102):** Blender's continuous Draw/Release transformation
   does not exist in UE (static snapshots) — decide: bake shape-key action to UE morph targets
   or accept static + document.
3. **Water-hair port:** baked FLIP/globs down the `Content/Cinematics/MelusinaWaterHair` +
   `ABP_Melusina_WaterHair` lane; KawaiiPhysics stays runtime dangle authority; no new writer.
4. **Root-motion reexport (KIMI lane, already scoped):** walk source missing — report, don't
   fabricate; Run/Sprint from OneDrive takes; measure JSON is the acceptance test.
**Gates:** UE compile 0 errors + capture JSON per fix; export contracts per repo docs.

## Wave 5 — Closure

1. AppData ↔ repo `melodia_gn` sync (clockwork + glob builders + the ~20-module drift).
2. Git batch: ~186 modified + 141 untracked in tree; batch per `melodia-git-commit-merge` when
   owner says commit (Saved/Audit JSON/MD are pre-allowlisted by the pre-commit hook).
3. CURRENT_STATE.md touch only if a status claim changes; no new handoff docs beyond what exists.
4. Queue aftermath: draped shawl via wide-panel drape copies (XPBD never converged live) —
   schedule as its own pass, do not improvise it inside a beauty session.

## Standing rules folded in (all earlier suggestions, now ordered)
- Bank before building; evidence pairs everywhere; owner eyes = final gate.
- One writer per surface: Water (Advance).002 / FLIP / Goo / Kawaii each own one thing.
- Never headless the live GUI file; never install addons mid-session; LiquiFeel GUI-only.
- New GN builders: build via socket in-memory → owner eyeballs → land in package closed-Blender
  → gate → deploy to repo.
- Memory-of-record: tonight's crash lesson + 5.x API traps are already in
  `blender-live-session-audit`; keep following them.

## Owner GO gates (nothing runs without the word)
0.1 bank method (save-in-place vs Save-As) · A3 body choice · Wave 2 bake start (disk cost
acceptance) · glob builder landing · Wave 4 UE editor windows · Wave 5 git commit.
