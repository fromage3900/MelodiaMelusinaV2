# Melodia Melusina — September 4 lookdev session

Prepared from the current checkout, September 4 handoffs, saved evidence, source contracts, and a read-only Monolith inspection. This is session preparation, not a new visual approval or shipping certification. No game assets, editor settings, or Git history were changed.

## Direction

Melodia is a rhythm JRPG with meaningful wardrobe and music-as-key exploration. QuillScript owns narrative; the TurnBased JRPG template owns combat and saves. The visual bar is Infinity Nikki, with OMORI shaping the game and Zelda informing musical interaction. Preserve authored surrealism while making character, route, and material identity readable.

The opening lookdev question is: **Can Melusina and the next landmark read clearly against Sea Above while the materials retain their character?** Start with material response and value hierarchy, then atmosphere and controlled musical accents. More scatter or shader complexity is not yet the most useful first move.

## Current baseline and evidence

- Live Monolith: version 0.20.3, UE 5.8, project BS_GodFile; one UnrealEditor process observed. The former modal-blocked state described on September 3 is not the current state: the read-only actor query answered successfully.
- Open world: `/Game/EnvSandbox/Monoliths/SeaAbove/Prototype/LV_SeaAbove_Prototype`, with 342 loaded actors. This count is the loaded editor set, not the full World Partition inventory.
- Live oceans: `SeaAbove_InfiniteOcean_Canopy` and `SeaAbove_InfiniteOcean_Canopy2`. Rediscover full object identities before any later edits; do not choose by an assumed default object name.
- Live `PPV_NikkiDream`: one blendable, `MI_StorybookOutline_Premium_Hero_Dream`, weight 1.0. The three-slot Grandmaster gameplay stack is a target in `Content/Python/ppv_contract.py`, not the observed loaded stack.
- Nested Unreal checkout HEAD observed at `00f464b6`; the outer portfolio repository is separate. Many Unreal materials, the Sea Above map, scripts, and documentation are modified or untracked. `.gitignore` is already staged. Preserve this existing work; neither an old commit summary nor an old branch report describes all current assets.
- Saved grounding evidence directly inspected: `Saved/Audit/sea_above_attached_mesh_grounding_disk_verified_2026-09-04.json` records 184 matched actors, 184 landscape hits, zero misses, maximum remaining contact delta 0.15 cm. That is saved placement evidence; it does not prove slope alignment or composition.

## September 4 changes that matter

### Sea Above terrain and dressing

The phase-2 report describes four terrain-grounded cells: east scree (1,020 instances), terrace garden (215), Atlantis grove (191), and phyllotaxis ridge (140). These are report values, not regenerated counts from this preparation. The landscape spans approximately 499,504 cm, or 5 km, across; 249,752 cm is its half-extent. Preserve that scale and use districts and sightlines to make the route legible.

Eight pivot-corrected Atlantis derivatives preserve vendor assets; 54 architecture material instances were reparented to texture-authored counterparts. The current saved colonnade image still warrants an artistic material pass. Grounding and restored texture wiring are foundations, not finished lookdev.

### Gaea: texture import, paint, and shader routing are distinct

The September 4 root-cause report supersedes the earlier intake-closed claim. Masks multiply landscape paint: zero paint cannot gain coverage from a mask. Snow/Water/Rock now have semantic lanes; Flow remains inactive. Out-of-range mask weights and extreme normal strength were reported repaired, but the writer that caused drift is not established.

The Rock export reportedly peaks at 31/255 and needs a normalized Gaea export if stronger rock coverage is intended. Water occupies only 0.76% of the terrain; inspect known bright-mask locations rather than concluding absence from a sparse uniform sample. Do not blindly rerun historical imports or treat raising blend weights above 1 as an artistic control.

### Ocean and audio

The September 3 notes locate ocean color in actor/preset scattering, not the orphan hero MI. Current C++ also drives runtime MID parameters and contains an aqua DeepScatteringColor baseline. Therefore, inspect both authored actor/preset values and runtime presentation before tuning darkness; the old claim that all MI work is irrelevant is too broad for the present source.

The sole palette writer is `UMelodiaAudioReactivePresentationSubsystem`; `UMelodiaCymaticsWriterSubsystem` owns `MPC_Cymatics_Driver`. Materials consume those values. Oceanology remains the surface authority. A source baseline does not prove the running binary contains it.

### Character and wardrobe

September 3 garment measurements found TextureWeight more effective than escalating DreamTint; the residual shirt discrepancy was predominantly blue. Reuse a fixed garment region and matching lighting/camera, not a background-difference mask. Do not use global exposure to hide a dark albedo.

September 4 commits add the Shorewake catalog record, canonical skeleton reassignment, and DAWN CHORUS gown work. The September 3 ledger's absent-Shorewake statement is consequently historical. Visual fit, deformation, translucency, and outfit identity still need current captures; commit titles alone do not establish those results.

### UI

Use `melodia-design-system/tokens.json` and `UMelodiaDesignTokens`; retain the UIBridge single-writer path. The September 2 UI status lists token-to-WBP audit, result-widget runtime path, judgment/combo presentation, and Quill background behavior as follow-ups. These were not revalidated here. Treat them as a secondary session lane after scene and character readability.

## Visual assessment of the available frame

Inspected `Saved/Audit/sea_above_colonnade_2026-09-04.png` (1280 × 720). Tall reflective columns carry saturated red/magenta lower regions and cool upper reflections. Pale architecture and terrain sit close in value; visible terrain diagonals compete with the landmark silhouette. This is an observation of that saved frame, not a diagnosis of the current viewport or proof of a particular shader defect.

Proposed artistic response: establish the intended material identity of the columns, preserve deliberate magical accents, and give the landmark a cleaner hierarchy of broad values and smaller detail. Compare the same shot before and after one material change. Avoid trying to resolve every surface with stronger bloom or a global grade.

## Session order and capture contract

1. **Baseline, 10 minutes.** Record current camera transform, FOV, resolution, exposure mode/value, AA/upscaler, light settings, PPV blendables, and exact edited asset identities. Capture arrival, the BellTree approach, colonnade, ocean horizon, and Melusina at gameplay distance. Save before-state parameters next to images.
2. **Terrain and architecture, 20 minutes.** At fixed exposure, inspect known Snow/Water/Rock mask locations, large-scale tiling, triplanar normal continuity, and the column reflections. Resolve the largest value/material issue first. Keep existing district footprint and navigation clearance.
3. **Ocean, 15 minutes.** Read each ocean's current preset/scattering and runtime overrides. Compare still frames and a short camera move for horizon continuity, absorption, shallow/deep transitions, and beat response. Swimming remains a separate gameplay verification.
4. **Character, 15 minutes.** Capture face, torso, full outfit, and gameplay-distance silhouette in the same world lighting. Compare neutral and authored lighting; inspect cloth/metal/hair separation and Shorewake deformation. Tune the responsible material input rather than compensating globally.
5. **PPV and motion, 20 minutes.** Evaluate the current premium outline before migrating. Grandmaster target: outline 1.0, gameplay color grade 0.69, ink 1.0. Its contract requires deterministic edge geometry, minimum width at least one pixel, no audio-driven UV/radius changes, at most 369 pixel instructions and 6 estimated texture samples. Test 1080p/1440p/4K, still and orbit views, foliage, thin silhouettes, translucency, and bounded audio response. Do not claim zero jitter from one screenshot.
6. **Closeout, 10 minutes.** Select one hero frame and one gameplay frame, compare against baseline, save only edited packages, re-read state, and record unresolved issues. PIE and packaged evidence are separate from this artistic acceptance.

The 90-minute allocation is a proposed working session. If the first material issue consumes the time, finish that bounded improvement and its evidence rather than rushing the remaining lanes.

## Certification boundary

The ledger contains newer evidence than the August-only summaries: static gates on August 29, wardrobe on September 1, package boot on September 2, and wardrobe state proof on September 3. The latest real-input runtime row inspected remains August 13. A package boot and state-only outfit swap do not certify the changed September 4 visual baseline. No build, PIE run, package run, token audit, or new render comparison was performed during preparation.

## Source trail

- `PROJECT.md` at repository root; `_AGENT_WORKING_AGREEMENT.md`; `AGENTS.md`.
- `Docs/LookDev/LOOKDEV_PREP_2026-09-03.md` and `GAEA_MASKS_ROOT_CAUSE_2026-09-04.md`.
- `Docs/Plans/SEA_ABOVE_PHASE2_PCG_ATLANTIS_2026-09-04.md`, `SEA_ABOVE_ASSET_GROUNDING_2026-09-04.md`, and `SEA_ABOVE_GIT_REVIEW_2026-09-04.md`.
- `Docs/Handoffs/PPV_GRANDMASTER_OUTLINE_CYMATICS_CONVERGENCE_2026-09-04.md`; `Content/Python/ppv_contract.py`.
- `Docs/Research/EMERGING_TOOLCHAIN_MASTER_INDEX_2026-08-31.md`; `Docs/LookDev/MELODIA_PERCEPTUAL_LOD_LOOKDEV_ARCHITECTURE.md` (specification, not proof of every implementation).
- `Docs/UI/UI_LOOKDEV_STATUS_2026-09-02.md`; `.claude/skills/melodia-ui-artist/SKILL.md`.
- `Saved/gate_ledger.json`; saved grounding JSON and colonnade PNG cited above; `Source/BS_GodFile/MelodiaIntegration/MelodiaAudioReactivePresentationSubsystem.cpp`.
