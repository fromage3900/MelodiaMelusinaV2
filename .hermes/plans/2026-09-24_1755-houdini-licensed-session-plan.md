# Houdini session plan — licensed cook runbook + tonight prep (updated 2026-09-24)

**Status authority:** `CURRENT_STATE.md`. This file is the session runbook for the next time
Houdini is licensed (college visit or student Education license); it does not restate project status.
**Built from tonight's docs:** CURRENT_STATE "Houdini live staging 2026-09-24 (license-blocked)",
`hda/README.md`, `Docs/WorldGen/HOUDINI_ENGINE_SMOKE_SPEC_2026-08-27.md` (§4 spec, §5 wiring,
§6 musical gate), `Docs/Handoffs/HOUDINI_SEA_ABOVE_P0_AND_AAA_POLISH_PLAN_2026-08-28.md` (B0
license-verdict rule), `Saved/Audit/p4_cathedral_houdini_mi_spec_confirm_2026-09-11.json`,
HandpaintPrep 2026-09-23/24 receipts, and tonight's live probes (hserver, editor, plugin log).

---

## Jev audit — 2026-09-24 (source: jev-live, one call, confidence 0.88)

| Question | Verdict | Distribution (top) |
|---|---|---|
| First block | **LICENSE_AND_SMOKE_FIRST** | 0.91 (ARPEGGIO_COOK_FIRST 0.06, EVIDENCE_HARNESS 0.03, CATHEDRAL_HDA 0.00) |
| Riskiest assumption | **LICENSE_CLASS_COMPAT** | 0.98 (COLLEGE_ACCESS_ONLY 0.02) |
| Needs human | **true** | 0.76 — license acquisition/verification is owner-only |
| Readiness | **2 / 4** — "All assets staged + offline smoke green; cook blocked by license with a named fix (lease + class check)" | |

Log: `Prototypes/JevHoudiniSessionPlan/audit_log.json` (prototype folder — delete to remove).
Reading: verify the lease before any cook; the license **class** (not the server) is the 0.98 risk.

---

## What tonight's docs establish (facts this plan runs on)

| Fact | Evidence |
|---|---|
| ArpeggioStair HDA built + imported; placeholder actor in `L_MelusinaMorning` at (400,0,100) left for diagnosis | CURRENT_STATE 2026-09-24; `hda/ArpeggioStair_1.0.hda` (8096 B, 12:03); `Content/HDA/ArpeggioStair_1_0.uasset` |
| License server reachable; **no license leased** — `Used Licenses: None`; HARS died `License failed: No License Found` | `hserver -l` re-probed 2026-09-24 17:45; CURRENT_STATE |
| Offline smoke green; plugin `HoudiniEngine` 22.0.368 loads in the live editor (libHAPIL from HFS path) and mounts | plugin log this session; smoke spec; `hda/README.md` |
| Gate to prove next: cook → bake → musical PIE chain (`SetPressedForActor` → `PlayMusicalNote` → ScoreState `total=64 hit=1 streak=1`) | smoke spec §5–6 |
| Cathedral: 8 `SM_P4_Cathedral_*` meshes imported; **MI materialization pending = editor work, NOT Houdini** | `p4_cathedral_houdini_mi_spec_confirm_2026-09-11.json` |
| HDA files are work-tree only (`hda/` untracked; Content allowlist) | `git status`: `?? hda/ArpeggioStair_1.0.hda`, `?? hda/backup/` |

---

## License path (owner-only; pick one)

1. **Student Houdini Education — $95 USD/yr (recommended).** SideFX opened direct student rental in
   July 2026 (Proxi.ID verification; non-commercial). It includes the Houdini FX Education GUI and a
   Houdini Engine Education license → **author/rebuild HDAs AND cook on this machine**, no college
   dependency. This is the clean path to the cook proof.
2. **College lab Education licenses.** Floating and campus-bound; fine for a lab-machine smoke proof,
   but it cannot license this home machine off-campus (and this project/editor live here).
3. **Free "Houdini Engine for Unity and Unreal" license (10/studio).** Cook-only tier for assets
   authored with Houdini FX/Core or Education; it does not provide the GUI/hython batch and does not
   run Apprentice-authored assets. Keep as background, not as the session plan.

**Class-compatibility note (Jev's 0.98 risk):** Apprentice assets are only compatible with Houdini
Engine **Education**; the repo already records "Apprentice HDAs do not work with Engine licenses."
The ArpeggioStair HDA was authored headlessly today under an unverified license class — so the runbook
**re-saves the HDA under the licensed Houdini before the first cook** (5-minute hython re-run). That
re-save is the cheap insurance against a second "License failed" run.

---

## Part A — tonight, no license needed

1. **Jev audit + this plan** — done tonight (`Prototypes/JevHoudiniSessionPlan/audit_log.json`).
2. **Keep the placeholder actor untouched** at (400,0,100). It is the diagnostic baseline; do not
   delete it before the licensed attempt, and do not re-run the trigger in a loop tonight.
3. **Pre-stage the evidence folder** `Saved/Audit/houdini_cook_<YYYYMMDD>/` with the capture steps in
   Part B (empty skeleton is fine; Signed-rung items get filled on the day).
4. **Owner: choose the license path now.** If path 1, start the Proxi.ID verification so the license
   is active before the trip (order-of-days, not order-of-minutes).
5. **Owner call (optional):** commit `hda/ArpeggioStair_1.0.hda` + `hda/backup/` to git (small text
   files; currently untracked work-tree only).
6. Unaffected parallel lanes tonight: Painter/SMS apply (ZenLantern) — prep complete, owner clicks.

---

## Part B — licensed session runbook (the day it's licensed)

**Step 0 — lease verdict (timebox 20 min).** Open Houdini License Administrator; get the Engine
license leased (`hserver -l` shows a license line, not `None`). Record the verdict JSON even if it
fails. Rule from the Sea Above handoff: **do not spend the session fighting `sesinetd` — log the
verdict and move on.**

**Step 1 — smoke.** `python Content/Python/smoke_houdini_engine_pcg.py` → all green. Confirm the
editor log shows the HoudiniEngine modules loading.

**Step 2 — re-save the HDA under the licensed class.**
```powershell
& "C:\Program Files\Side Effects Software\Houdini 22.0.368\bin\hython.exe" Content/Python/create_hda_arpeggio_stair.py --out hda/ArpeggioStair_1.0.hda
```
Back up the current file first (it already has `hda/backup/ArpeggioStair_1.0_bak1.hda`). Re-import
into `Content/HDA/` if the UE-side asset needs a refresh.

**Step 3 — cook.** Single editor. Open `L_MelusinaMorning`; select the `ArpeggioStair_1_0` actor at
(400,0,100); trigger the cook through the same live path used on 2026-09-24 (the editor-side
HoudiniPublicAPI/ProcessHDA route that produced the license failure — it must now produce geometry).
Capture: UE Output Log lines (license line + cook result), actor state before/after, output counts.

**Step 4 — bake.** Houdini Engine → Bake to Actors; verify actor count/transforms on disk. If the
field is interactive, assign `DL_Musical_HeroGameplay` (hda/README step 3).

**Step 5 — musical gate (PIE).** `SetPressedForActor` on one pad → `IsPressed` true;
`PlayMusicalNote` audible through `UMelodiaAudioComponent` (same clock, `MPC_Melodia_Palette`);
ScoreState `total=64 hit=1 perfect=0 score=50 streak=1` (16x4 pads). Save assertion JSON **next to**
the frames — frames without a report are not evidence.

**Step 6 — evidence bundle + receipt.** Under `Saved/Audit/houdini_cook_<date>/`:
`cook_log.txt` (License + cook lines), `actor_before.json`, `actor_after.json`, `bake_receipt.json`,
`musical_gate.json`, `frames/*.png`. Then update `CURRENT_STATE.md` Houdini entry **only** with the
evidence level actually reached.

**Stretch (only if Steps 0–6 are green and time remains):**
- `ChordGarden` HDA as the second musical proof (smoke spec §9; from `MUSICAL_PCG_NOTES.md`).
- Cathedral HDA authoring is a separate, unproven-value project. The cathedral's real next gate is
  the 8 `MI_P4_Cathedral_*` materializations in the editor — plan that as an editor session, not a
  Houdini session.

---

## Gates / anti-goals

- No `ALandscape` ever; HDA outputs meshes/HISM only (smoke spec §7).
- Cook at design time; **bake before** World Partition/HLOD builds (cooked actors don't participate
  in HLOD correctly).
- Never claim from smoke alone; the proof is cook + bake + musical gate as one run.
- One editor holder; no Monolith `save_packages`; owner Ctrl+S only.
- If the license verdict fails again: stop, keep the placeholder, log the verdict — do not loop the
  trigger.
- If cook succeeds but the musical gate fails: record a two-rung receipt (cook+bake proven; musical
  gate open) — do not upgrade the claim.

## Files / paths

| Thing | Path |
|---|---|
| HDA source | `hda/ArpeggioStair_1.0.hda` (+ `hda/backup/`) |
| HDA builder (hython) | `Content/Python/create_hda_arpeggio_stair.py` |
| UE HDA asset | `Content/HDA/ArpeggioStair_1_0.uasset` |
| Smoke | `Content/Python/smoke_houdini_engine_pcg.py` |
| Spec | `Docs/WorldGen/HOUDINI_ENGINE_SMOKE_SPEC_2026-08-27.md` |
| Jev audit log | `Prototypes/JevHoudiniSessionPlan/audit_log.json` |
| New evidence | `Saved/Audit/houdini_cook_<date>/` |

## Plan closes when

One green run of Steps 1–6 with the evidence bundle on disk = the Houdini lane's first proven cook;
`CURRENT_STATE.md` updated; the next session then carries ChordGarden and the cathedral MI pass.