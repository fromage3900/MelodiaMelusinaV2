# OVERALL STATUS + NEXT-AGENT HANDOFF — 2026-08-18 ~11:00 ET

**Read this first.** Then `_SESSION_HANDOFF.md` (Melusina/UE 08-16, still valid below the TOP note) and `Docs/BLENDER_MELODIA_COCKPIT.md` (Blender cockpit).

Verified on disk this stamp. Do **not** spawn Blender or Unreal. Do **not** save v22. Rhythm + Quill stay locked.

| | |
|--|--|
| **Stamp** | 2026-08-18 ~11:00 ET |
| **Game repo** | `C:\EnvironmentPortfolio\BS_GodFile` · `feature/repo-lockin-20260813` · HEAD `02910d70` · origin `d37fde7f` (**12 ahead, unpushed**) · remote `legacy-melodia` |
| **Website repo** | `C:\EnvironmentPortfolio\my-site-clean` · local `fix/pages-validate-missing-refs` `c1039dc` (ahead 7) · **live** `origin/main` `046797f` |
| **Live site** | https://fromage3900.github.io/my-site/ (PR [#1](https://github.com/fromage3900/my-site/pull/1) + [#2](https://github.com/fromage3900/my-site/pull/2) merged 2026-08-13) |

---

## Machine NOW (do not ignore)

| Process | PID | Started | Responding | WS |
|--|--:|--|--|--:|
| `blender.exe` | **45856** | ~08:17 ET | **Unknown** | ~6.4 GB |
| `UnrealEditor` | **2320** | ~08:17 ET | **Unknown** | ~5.5 GB |
| `UnrealTraceServer` | 22144 | ~08:17 ET | True | — |

Old hung PIDs from 08-17 (8492, 47760, 25384) are gone. Two **new** processes replaced them. Treat the machine as **occupied**. One Blender. One Unreal. Never launch a second of either.

**Stale conversation claim (corrected):** "AppData synced after killing PID 92616" is **false** (08-17). Live addon CHANGELOG is still **v2.68.0 / 2026-08-11**. Deploy CHANGELOG is 2026-08-17 173/12. AppData `__pycache__` newest ~15:04 ET (08-17 hung GUI load), not a sync.

---

## Do not (every lane)

- Spawn Blender or Unreal. Do not "fresh start" 5.2 while `blender.exe` still exists.
- Save v22 unless owner sets `MELODIA_ALLOW_STAGE_SAVE=1` **and** asks.
- Flip rebake. Do not compensate hair transforms. Do not re-wire Blender idle (`MELUSINA_WIRE_BLENDER_IDLE` off).
- Touch Rhythm highway graphs or Quill widget graphs (OWNER LOCK WORKED).
- `install_melodia_studio.ps1` / `sync_surreal_to_live.ps1` while any `blender.exe` is up.
- Sync & Reload in a live 5.2 (self-reload crashed 5.2 historically). After a real quit: **fresh-start 5.2**, not that button.
- Invent git tag `v2.68.0`. Live `bl_info` is `(2, 131, 0)`.
- Mix website commits into `BS_GodFile`. Force-push. Commit this handoff into a 342-path dirty tree.
- Mix BlenderMCP **:9876** (N → BlenderMCP → Connect) with LiveLink Start Server (same port). Legacy **9317 / 9877** retired.

---

## Melodia Studio

### Now

- Product: Blender 5.2 addon, N-panel **Melodia Studio**, module `surreal_architecture_gen`, operators `surreal_arch.*`.
- **Registry 173 / 12** (freeze 165 → greybox 169 → musical heroes 173). `bl_info` still `(2, 131, 0)`.
- Hidden **27** `them_*` + PCG v1 aliases (ids kept). Visible GN Stack **146** (173−27). Ship-checklist "142" is the pre-heroes leftover.
- Set Dressing frozen at **39**. Structures **12**. Presets **42 builders / 127 looks**.
- Musical heroes (+4 trees; sheet_rail rewritten in place):
  - `MEL_music_key_unit`, `MEL_music_piano_roll`, `MEL_music_harp`, `MEL_music_room_shell`
  - `MEL_music_sheet_rail` rewrite: walkable posts + five swept staff lines + notes
- Greybox Structures: openings / corridor / junction / composer (+ hollow `MEL_greybox_room_kit` rewrite).
- Headless smoke (factory-startup 5.2, no GUI spawn): stubs **14/14**, music heroes **7/7**.
- Deploy tree holds the 173 work. **AppData does not.** Live GUI still on old addon files.
- **New 08-17 commit `02910d70`:** toggleables ledger P1-P4 + Komikaze tiler + audit engine. Re-registers `surreal_arch.toggle_genshin`, P1 accessory visibility (16-slot BoolVector), P2 stats overlay (GPU viewport HUD), P4 library visibility, Komikaze `NTTiler → Tiler [Komp]` (real group name), audit iterates `bpy.data.objects` with `linked_in_scene` flag + GREASEPENCIL as renderable type. Verified live in 5.2. `toggle_genshin` lands on next fresh start (no live monolith reload per crash rule).

### Do next

1. Owner quits **both** hung `blender.exe` (45856). Do not kill Unreal from a Studio lane unless the owner asks.
2. Then `deploy/sync_surreal_to_live.ps1` (or install script). Confirm AppData `CHANGELOG.md` shows **173 / 12**.
3. **Fresh-start** Blender 5.2 once. Do not Sync & Reload. N → BlenderMCP → Connect **:9876**.
4. B3: eyeball 17 `_edit_SM_Orn_*` on live **v22** (`MELODIA_ALLOW_STAGE_SAVE=1` only if writing the stage). v4.blend is absent.
5. Fresh-install GUI: no red traceback on first N-panel draw (blocked until AppData is free).
6. Optional later: L4 Figma icons; greybox snap/composer placement; `FILIGREE_*` monolith stays deferred.

### Evidence

- `Saved/Audit/gn_stub_rewrite_2026-08-17_1335.json` — 14/14, registry 169, hidden 27
- `Saved/Audit/gn_music_heroes_2026-08-17_1437.json` — 7/7, registry 173
- `deploy/surreal_arch/Docs/GN_EXPANSION_PLAN_2026-08-17.md`
- `deploy/surreal_arch/CHANGELOG.md` (v2.131.0 musical heroes)
- `Docs/MELODIA_STUDIO_SHIP_CHECKLIST.md`
- `Saved/Audit/melodia_studio_final_review_2026-08-17.md` — early-day 165/12; **superseded** by 173 evidence above
- Canvas (bumped 08-17): `C:\Users\froma\.cursor\projects\c-EnvironmentPortfolio\canvases\melodia-studio-final-review.canvas.tsx`

---

## v22 / Blender

### Now

- Live stage SSOT: `G:\EnvironmentPortfolio\BS_GodFile\Melodia_Portfolio_Stage_v22_ZenRebuild_WIP.blend`
- Save policy: **do not save** unless `MELODIA_ALLOW_STAGE_SAVE=1` and owner asks.
- Agent MCP: port **9876**, N-panel **BlenderMCP → Connect** after every restart. Melodia Studio **Live Bridge → Start Server** is LiveLink, not MCP.
- Cam_Beauty on live v22 **reads bald**: Flip cache globules below scalp (existing 1–240, not a new bake). That is the published caption.
- Nikki/Genshin FACE/BODY maps landed in Blender (custom normals, vertex Col, Light Map G, UV1). Not on Flip / Hair PRO.
- Review_Queue `RQ_MEL_*` still **165** on live v22 (not resynced this pass).

### Do next

- After hung GUIs die: AppData sync + one 5.2 restart on v22 (read-only unless owner allows save).
- B3 ornament collections on v22.
- Do not open a second blender on v22 "to check."

### Evidence

- `Docs/BLENDER_MELODIA_COCKPIT.md`
- `Docs/Handoffs/NIKKI_GENSHIN_BLENDER_2026-08-13.md`
- Live site Cam_Beauty caption (website section)

---

## Website

### Now

- Live: https://fromage3900.github.io/my-site/
- PR **#1** merged 2026-08-13: sendoff + Cam_Beauty Nikki still + Flip glam + honest Studio facts (`portfolio-sendoff-20260813`)
- PR **#2** merged 2026-08-13: Pages validate so sendoff can deploy (`fix/pages-validate-missing-refs`)
- `origin/main` **`046797f`** — `Skip dead Figma and product refs so Pages validate can deploy.`
- Local checkout is **not** on `main`. Branch `fix/pages-validate-missing-refs` **`c1039dc`**, tracking origin same name, **ahead 7** (atelier/a11y/seo work after the merged PR #2).
- Local `main` `e705ee5` is **behind 17** vs `origin/main`.
- Cam_Beauty bald-cache caption is in `content/site-copy.json`, `content/site-plates.json`, README, passports.

### Do next

- Treat GitHub Pages as shipped from **origin/main `046797f`**, not from the 7 local unpushed commits on `fix/pages-validate-missing-refs`.
- Recruiter sendoff pages already exist (`wix/recruiter-one-sheet.html`, hiring dossier). Do not invent a new micro-site.
- Unreal B2 Cam_Beauty plates still not published — do not fake them.
- Local dirt: `?? generated/assets/character/melusina_stage_beauty.png`, `?? public/melodia/status/` — do not mix into the game repo.

### Evidence

- `Docs/Handoffs/WEBSITE_SENDOFF_2026-08-13.md`
- https://github.com/fromage3900/my-site/pull/1
- https://github.com/fromage3900/my-site/pull/2

---

## Unreal / game

### Now

- Branch `feature/repo-lockin-20260813`. **Pushed through `d349d0f1`** (2026-08-13 lock-in). Origin tip now **`d37fde7f`**. Local HEAD **`02910d70`** = **12 unpushed** commits (Melusina finger/cornea, ARKit 35 keys, wardrobe catalog DA, path migrate C:, tests, studio toggleables).
- **Cine hair** = Geometry Cache frames **1–240** + Niagara drip on `head_x` (inverse bind). SK hair is fallback. **Idle** = `A_Melusina_Idle_Mocap_RootX` at blendspace speed 0. Do not Flip-rebake. Do not compensate hair transforms.
- Rhythm OWNER LOCK WORKED · QuillScript OWNER LOCK WORKED. Scan-only.
- `_SESSION_HANDOFF.md` (08-16): Melusina locomotion **staged, 0 `.uasset` written**. AnimGraph has no ground-locomotion state (`Idle → JumpStart → Airborne → Land`). Drivers dry-run clean; first `--apply` needs a **responding** editor. `save_asset` returning saved is **not** a disk write — stat the uasset.
- Current `UnrealEditor` PID **2320** is **new** (old 25384 from 08-17 is gone). Do not assume Monolith/Python-remote is healthy. Do not start a second editor.
- `BS_GodFile.uproject` dirty hunk: **`Oceanology_Plugin` `Enabled: false`** (added). Leave uncommitted unless owner asks. Re-enable only to test a build, then disable before editor start (missing-modules modal wedges the game thread).
- `MelodiaWardrobe` is **`Enabled: true`** in the working uproject (08-13 "Enabled: false uncommitted" is stale). Plugin sources are also dirty. 08-13 load-failure modal is a known hazard if the module fails to init.
- Water **gameplay** authority is native C++ (`MelodiaIntegration`), not Oceanology. Oceanology 5.4→5.8 port residual = ray-tracing `GetDynamicRayTracingInstances` collector migration only. Do not compile the RT path out (`r.RayTracing=True`).
- Quaternius `A_Q_Melusina_*.uasset` (42 files) exist on disk but asset registry finds **zero** — `wire_melusina_quaternius_actions.py` needs rework before use.

### Do next (only with a responding editor, never a second one)

1. If 2320 stays wedged: owner-kill, then **one** editor. Do not `--pack all --force` (OOM 68.5 GB / Kenney 6,059 files).
2. PIE idle proof: speed 0 = mocap, not collapsed. Deliverable `Saved/Audit/pie_idle_proof_*.md`.
3. Morning hair presence on `L_MelusinaMorning` / `BP_Melusina` (GC + Niagara). Do not copy onto `BP_MelusinaJRPGCharacter` unless owner asks.
4. Apply staged Melusina locomotion stack **in order** (`_SESSION_HANDOFF.md` §6) once schemas are live. Abort on first mismatch; do not guess twice. Verify uasset mtime.
5. Do not wait on Oceanology for water puzzle/platform T3D wiring.

### Evidence

- `_SESSION_HANDOFF.md` (08-16 Melusina / Oceanology / persist-nothing)
- `Docs/Handoffs/NEXT_AGENTS_PARALLEL_2026-08-13.md`
- `Docs/Handoffs/RHYTHM_GAME_LOCKED_2026-08-12.md`
- `Docs/Handoffs/QUILLSCRIPT_LOCKED_2026-08-12.md`
- `git log origin/feature/repo-lockin-20260813..HEAD` (12 commits)

Unpushed (do not push unless owner asks):

```
02910d70 fix(studio): close toggleables ledger P1-P4 + Komikaze tiler + audit engine
19907a8a docs: postmortem on the Melusina finger/cornea defect
9cdd704f feat(wardrobe): author DA_MelodiaCosmeticCatalog with the five V2 pieces
a13bcd3d docs(wardrobe): closed-editor rebuild prep + gameplay wiring order
6dd01ebb fix(melusina): rebind orphan finger controllers at export time, not in the stage
d6a83359 fix(tests): ollama health mock was missing a contract model
39ce7f3a feat(melusina): populate 35 ARKit shape keys from FACS; finalization plan
6788f012 feat(melusina): weight-paint base applied; correct the addon intake
a18f069a fix(melusina): fix finger orphans in the contract, not the weights; ARP export green
e455a507 fix(melusina): orphan skin bindings 41 -> 0, proven in the exported FBX
70e5c89c Docs: migrate G:/EnvironmentPortfolio to C:/EnvironmentPortfolio + environment cleanup
5adeb8fd fix(melusina): re-bind cornea and finger geometry off root-parented bones
```

---

## Leftover dirt

**Do not commit** as a dump. 342 porcelain paths. This handoff is the only intended write this stamp.

### BS_GodFile (`feature/repo-lockin-20260813`, 12 ahead)

| Bucket | Approx | Notes |
|--|--:|--|
| Modified tracked | ~195 | Mass EnvSandbox MIs/MFs, `BS_GodFile.uproject` (Oceanology disabled), MelodiaWardrobe C++/headers, Studio deploy py + ship docs |
| Untracked | ~147 | Probe scripts `Content/Python/_probe_*`, integration BPs, locomotion drivers, `deploy/_gn_music_heroes_smoke.py`, `deploy/_stub_rewrite_smoke.py`, `deploy/surreal_arch/melodia_gn/music_heroes.py`, `GN_EXPANSION_PLAN_2026-08-17.md`, specs/fixtures |
| Deleted | 1 | `Content/EnvSandbox/Environments/Sakura/L_SakuraPath.umap` |

Studio 173 work is **in the working tree, not in HEAD**. `Docs/MELODIA_STUDIO_SHIP_CHECKLIST.md`, `Docs/BLENDER_MELODIA_COCKPIT.md`, `deploy/surreal_arch/*` are modified/untracked. Next Studio agent: keep that tree; do not revert to committed 165.

Leave alone unless owner asks: `Oceanology_Plugin` uproject hunk, MelodiaWardrobe plugin dirt, material MI churn, untracked `_probe_*`.

### my-site-clean

- Branch `fix/pages-validate-missing-refs` ahead 7 of its remote (post-merge #2 local continuation).
- Untracked: `generated/assets/character/melusina_stage_beauty.png`, `public/melodia/status/`.
- Local `main` behind origin/main 17. Do not unrelated-history merge.

---

## Fact-check vs conversation prompt

| Claim | Disk |
|--|--|
| Registry 173/12 after musical heroes (+4 ids; sheet_rail rewrite) | **True** — `gn_music_heroes_2026-08-17_1437.json` |
| Hidden 27 them_*/PCG v1 | **True** |
| Greybox openings/corridor/junction/composer | **True** — stub smoke 14/14 |
| Smoke 14/14 then 7/7 | **True** |
| AppData synced after killing PID 92616 | **False** — AppData CHANGELOG still v2.68.0; new blender PID 45856 exists |
| Owner fresh-start 5.2 (not Sync & Reload) | **Still the rule**; cannot until blender.exe is gone |
| Live site + PR #1+#2 + bald-cache caption | **True** |
| Game branch pushed `d349d0f1` | **True as ancestor**; origin now `d37fde7f`; local **12 ahead** at `02910d70` |
| Cine hair GC 1–240 + Niagara; idle mocap | **True** — do not Flip rebake / compensate hair |
| `MELODIA_ALLOW_STAGE_SAVE=1`; MCP 9876; Rhythm/Quill locked | **True** |
| Studio toggleables P1-P4 + Komikaze tiler + audit engine | **True** — commit `02910d70`, verified live 08-17 |

---

## Start here (next agent)

1. `Get-Process blender, UnrealEditor` yourself. If either exists, you do not launch another.
2. Pick **one** lane: Studio (no GUI until hung blender dies) · Website (sibling repo) · Unreal (only if 2320 is actually usable, else wait) · docs-only.
3. Done = named evidence under `Saved/Audit/` plus a line on this file or `_SESSION_HANDOFF.md`.
