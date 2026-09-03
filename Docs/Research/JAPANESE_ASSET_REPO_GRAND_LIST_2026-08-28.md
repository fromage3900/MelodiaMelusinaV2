# Grand List — Niche Japanese repos for assets & pipelines (2026-08-28)

**Lane:** docs/author (no editor, no `Content/` writes).
**Scope decision (owner, 2026-08-28):** plugins + tools + assets, all three. Priorities:
**(1) surreal / magic systems, (2) Houdini/Blender pipelines, (3) VRM pipelines** — large-scale
content generation, NPC/enemy rig creation, animation, gameplay-building streamlining.
**Verification method:** live websearch/webfetch this session (github.com direct git is
unreliable from the workstation per `Docs/GIT_HEALTH_2026-08-19.md`).

Legend: ✅ license verified this session · 🟡 license file seen, exact type to confirm at
import · ❓ unverified — verify LICENSE + UE 5.8 path before anything enters the ledger.

---

## Tier 1 — Already in project or staged locally (provenance recorded)

| Repo / pack | Author | License | Role | Status |
|---|---|---|---|---|
| `ruyo/VRM4U` | ruyo | MIT | VRM loader; **generates bone/blendshape/spring-bone/collision/humanoid rig on import**, retargetable, MToon materials — the NPC/enemy VRM→UE pipeline backbone | On disk `Plugins/VRM4U`, built; **not enabled in `.uproject`** (owner decision, B1) |
| `pafuhana1213/KawaiiPhysics` ✅ | おかず @pafuhana1213 | MIT | Pseudo-physics for hair/skirt/cloth sway; UE 5.3–5.8 supported; used by many shipped titles | In F: staging; referenced by VFX cohesion report (pillar 4) |
| VRM SpringBone → KawaiiPhysics converter | yumetengu (BOOTH) | per-BOOTH page — verify | Converts VRM spring-bone setup into KawaiiPhysics bones (VRM→NPC sway pipeline) | Not acquired |
| `ysk424/cascadeur-mcp` | ysk424 | MIT | Cascadeur↔MCP bridge; animation lane | **Adopted** (`Docs/HANDOFF_CASCADEUR_MCP_BRIDGE_2026-08-08.md`) |
| SOYA (VRoid), obj001n101_cherryblossom, SummerAssets_FBX_Outline, young-lady-zundamon-lowpoly, Zundamon FBX/PMX, Live2D Zunko, GuttyKreum Japanese City, Roblox-Projects-Public (MIT) | various | per-pack (CREDITS.md § staging provenance) | Physically staged at `F:\Inbox\Downloads_Sweep_2026-07-11\Unzipped_Repos` + `F:\Library\Assets\Downloads_Zips` | Staged, not imported |

## Tier 2 — Japanese-authored, license verified this session

| Repo | Author | License | Verified use for Melodia |
|---|---|---|---|
| `alwei/PPCelShader` ✅ | alwei (あんじゅう铃) | **Unlicense (public domain)** | Post-process cel shader — UE 4.19 reference; port ideas into the toon spine, do not vendor UE4 content |
| `SPARK-inc/SPCRJointDynamicsUE4` ✅ | SPARK-inc | MIT (confirmed via Square Enix VoM license page) | Cloth/rope/chain dynamics — magic ribbons, robes, banner motion |
| `pafuhana1213/KawaiiPhysics` ✅ | (above) | MIT | — |
| `DietrichGebert/ponytail` + UE5.8 fork `prielgaier/ponytail-ue58` ✅ | DietrichGebert / prielgaier | MIT | AI-agent "lazy senior dev" ruleset, UE 5.8-aware (never hand-edit `.uasset`, BP/C++ boundary discipline). **INSTALLED 2026-08-28** — vendored at `Tools/vendor/ponytail-ue58/`, wired into `.opencode/opencode.jsonc` `plugin` |

## Tier 3 — Research-adopted references (verdicts already recorded in project docs)

Already carry adopt/adapt/reference verdicts in
`Docs/Research/Infinity_Nikki_VFX_Cohesion_Report.md` §10,
`Docs/Research/AAA_ANIME_UE_CHARACTER_PIPELINE_2026-08-15.md`,
`Docs/Research/UE58_TOON_SHADER_EXTERNAL_PRACTICES_2026-08-14.md`:

- `akasaki1211/sdf_shadow_threshold_map` — SDF face-shadow baker (**ADOPT**, anime pipeline pillar 1)
- `JasonMa0012/MooaToon` — cinematic toon (engine-fork model; reference only)
- `alwei/PPLineDrawing`, `alwei/SimpleChaos`, `historia-Inc/CustomRaytracingShader`
- `ssencho/flipbook2niagara` — **ADOPT** (flipbook import lane)
- `EricHu33/AnimeShadingPlus`, `NoiRC256/URPSimpleGenshinShaders`, `Dylanyz/ARKitRemap` — study only
- `markoleptic/BeatShot`, `vkmore2002/audio-reactive-environment`, `mushe/VFXBook`, `kisspread/DemoRoom`, `WeHome007/NextCAS-UE`, `liusida/UnrealMassMovementDemo`, `jcoder58/UE5MassResources`, `gtreshchev/RuntimeAudioImporter`

## Priority lanes (owner 2026-08-28) — candidates

### A. Surreal / magic systems
| Repo / source | License | Fit |
|---|---|---|
| `ymt3d/UE5-StylizedPostProcess` ✅ **MIT verified 2026-08-28** (raw LICENSE read, JP+EN, © 2023 ymt3d) | MIT | Stylized PP: outlines, hatching, halftone — magic-grade over toon spine; complements ArtOfShader |
| `ymt3d/MPP-Blender-Addon`, `ymt3d/AutoActiveCameraSwitcher-Blender-Addon` ❓ | TBC | Blender-lane QoL for the surreal material pipeline |
| SDF/Gumroad SKU2 first-party suite (74 masters) | first-party | The magic SDF spine already exists — external repos are garnish, not replacement |
| Magic-circle sweep — **CLOSED 2026-08-28**. Findings: no dedicated open-source Japanese magic-circle repo exists; candidates are `mushe/NiagaraFractalTree`, `mushe/NiagaraFluid`, `mushe/NiagaraGameOfLife` (procedural surreal Niagara, same author as already-referenced VFXBook) and Epic's **free Niagara Examples Pack** on Fab (50+ systems, Epic EULA, UE 5.7+, adaptable). 魔法陣 circles remain **first-party SDF-spine work**; tutorial-only references (Techloria 2024). | — | Record adopt decisions before import |
| ⛔ **Pirated CG mirrors (cgtall.com, cgalpha.com, imaxcg.com, yunqiaowang.cn)** surfaced by the sweep — these redistribute paid Fab packs. **BANNED** same as datamine repos. | — | — |

### B. Houdini / Blender pipelines
| Repo / source | License | Fit |
|---|---|---|
| `sideeffects/HoudiniEngineForUnreal` — **STAGED+ENABLED by WorldGen lane** (found `Plugins/HoudiniEngine/` untracked + `"HoudiniEngine": true` in `.uproject` + `Docs/WorldGen/HOUDINI_ENGINE_SMOKE_SPEC_2026-08-27.md` + `Content/Python/smoke_houdini_engine_pcg.py`). Hands off — that lane owns verification per rule 22 (existing ≠ compiling). | SideFX terms (free for UE5) | Fit-score 10: HDAs → Nanite meshes; MeshTerrain bridge |
| `microsoft/TRELLIS` ✅ **MIT verified 2026-08-28** (raw LICENSE read, © Microsoft Corporation) | MIT | Local image→3D (`glb`) for content gen; feeds Blender cleanup → VRM/FBX. **Not installed** — WSL2/GPU (RTX 3060+, 12GB VRAM) + conda environment; install decision with owner (Pinokio path available) |
| `saturday06/VRM-Addon-for-Blender` ✅ **installed 2026-08-28**. Correct repo name uses dashes. License: **dual "MIT OR GPL-3.0-or-later"** (LICENSE_MAIN.txt; pick MIT by choosing OPTION1 — record choice). Supports Blender 2.93–5.2 → owner's 5.2 LTS ✅. Clone at `Tools/vendor/VRM-Addon-for-Blender/`; junction created at `%APPDATA%\Blender Foundation\Blender\5.2\extensions\user_default\vrm` → `src/io_scene_vrm`. **Blender restart + enable in Preferences → Extensions required.** Python automation API available for the VRM pipeline. | MIT (choose OPTION1) | VRM import/export/humanoid/MToon in Blender; closes TRELLIS→AccuRIG→VRM→UE loop |
| Blender surreal generators (owner pipeline, `melodia-design-system`, stage blends) | first-party | Already the EnvSandbox spine |

### C. VRM pipelines — NPC/enemy rig + animation at scale
| Repo / source | License | Fit |
|---|---|---|
| `ruyo/VRM4U` (Tier 1) | MIT | **ENABLED 2026-08-28** — `"VRM4U": true` added to `BS_GodFile.uproject` plugins (owner go-ahead "UE live go"). All 8 editor DLLs already built → **editor restart required, no rebuild**. After restart: verify no module error, then import one staged VRM (Zundamon FBX/PMX is FBX, SOYA is VRoid) as the NPC-pipeline smoke. Consider MPC material override per `VRM4U_NPC_PLACEHOLDERS_2026-08-14.md` |
| `pafuhana1213/KawaiiPhysics` + yumetengu SpringBone converter | MIT / BOOTH | VRM sway → UE physics bones without manual re-rigging. **yumetengu converter requires BOOTH acquisition by owner** (checkout is a purchase flow, not automatable): https://yumetengu.booth.pm/items/7943387 |
| TRELLIS + AccuRIG/Mixamo + VRM-Addon-for-Blender (now installed) | see above | Image/illustration → rigged VRM → UE NPC — the large-scale NPC generation loop (Qiita workflow 2025-12-14) |
| SSS LLC Zunko family / VRoid Hub (Tier-1 character terms) | non-commercial / per-model | Cast identity — non-commercial boundary applies to shipped game |
| `Dylanyz/ARKitRemap` | verify | MHA output → ARKit-blendshape NPCs (only if facial capture lane opens) |

### D. Directory / discovery repos
| Repo | License | Use |
|---|---|---|
| `toxsam/open-source-3D-assets` | directory (per-asset licenses) | ~1000 CC0 GLB assets; Japanese-community covered (gamemakers.jp 2026-02-17) |
| `madjin/awesome-cc0` | directory | Includes 300 CC0 VRM+FBX avatars — pairs with VRM4U NPC lane |
| 3dnchu / gamemakers.jp free-asset roundups | news | Weekly Japanese-curated UE5 asset feed |

## BANNED — do not use (red line, restated)

- **`zeroruka/GI-Assets`** and any other datamine/rip repos (Genshin/Nikki/etc.) — shipped-game asset dumps are illegal for Melodia (`ENV_PACK_RESEARCH_POINTER.md`, shortlist hard ban).
- `Hoyotoon/HoyoToon`-style datamine-derived shaders: study architecture only; never import assets from them.
- Never auto-dress `L_SakuraPath`; nothing under `Content/_PROJECT/`.

## Adoption rules (inherit from `MELODIA_EXTERNAL_ADAPTER_LEDGER.md`)

1. Any **plugin/tool** entering the UE build gets a ledger row first: URL, license file, engine
version, commit SHA, patch list, known issues. No live GitHub fetches during a build.
2. **Assets** enter via `Imports/<pack>/` + per-pack `PROVENANCE.md`, then `Tools/credits_gate.py`
must pass and `Docs/SOURCES_MATRIX.md` gains a row. No name guessing for credits.
3. Licenses marked ❓/🟡 stay OUT of the project until the LICENSE file is read at the pinned SHA.
4. One editor, one build lane; this list changes nothing at runtime by itself.

## Session record (2026-08-28)

**Morning (setup):**
- Verified this session ✅: KawaiiPhysics MIT (UE 5.3–5.8), PPCelShader Unlicense,
  SPCRJointDynamicsUE4 MIT (via Square Enix credit page), ponytail-ue58 MIT (ENGINE_VERSION 5.8).
- Installed: **ponytail-ue58** → `Tools/vendor/ponytail-ue58/` (shallow clone), registered in
  `.opencode/opencode.jsonc` → `plugin: ["./Tools/vendor/ponytail-ue58/.opencode/plugins/ponytail.mjs"]`.
  OpenCode restart required to load it. Commands: `/ponytail lite|full|ultra|off`, `/ponytail-review`, `/ponytail-audit`.

**Evening (execution pass, owner go-ahead "UE live go"):**
- ✅ **ymt3d/UE5-StylizedPostProcess license closed: MIT** (raw LICENSE read).
- ✅ **TRELLIS license closed: MIT** (© Microsoft). Not installed — GPU/WSL decision with owner.
- ✅ **Magic-circle sweep CLOSED.** No dedicated OSS JP magic-circle repo. Candidates:
  `mushe/NiagaraFractalTree|NiagaraFluid|NiagaraGameOfLife` (surreal procedural Niagara),
  Epic free **Niagara Examples Pack** (Fab, UE 5.7+, Epic EULA). 魔法陣 stays first-party SDF.
  Pirated CG mirrors (cgtall/cgalpha/imaxcg/yunqiaowang) surfaced by the sweep — **added to BANNED**.
- ✅ **VRM-Addon-for-Blender installed.** Correct name `saturday06/VRM-Addon-for-Blender` (dashes).
  Dual MIT OR GPL-3.0 → **choose MIT (OPTION1)**; Blender 2.93–5.2 supported. Cloned to
  `Tools/vendor/VRM-Addon-for-Blender/`; junction `%APPDATA%\Blender Foundation\Blender\5.2\extensions\user_default\vrm`.
  **Pending: Blender restart + enable extension in Preferences.**
- ✅ **VRM4U ENABLED (B1 cleared).** `"VRM4U": true` appended to `BS_GodFile.uproject` (additive,
  alongside the other lane's HoudiniEngine entry). All 8 `UnrealEditor-VRM4U*.dll` pre-built →
  **UE editor restart required, no rebuild**. Post-restart check per `VRM4U_NPC_PLACEHOLDERS_2026-08-14.md`:
  no module error in log; then a single staged-VRM import smoke.
- 🔲 **yumetengu VRM SpringBone→KawaiiPhysics converter**: BOOTH checkout is a purchase flow —
  **owner acquisition needed** (https://yumetengu.booth.pm/items/7943387). Staged as TODO, not download-able by agent.
- 📌 **HoudiniEngineForUnreal already live** — staged + enabled by the WorldGen lane
  (`Plugins/HoudiniEngine/`, `.uproject` entry, smoke spec + Python smoke). Not touched; that lane
  owns build verification.

**Restart checklist (both hosts):**
1. UE editor restart → confirm VRM4U modules load (no `LogModuleManager` errors) → try one VRM import.
2. Blender restart → Preferences → Extensions → enable "VRM Add-on for Blender" (it appears as `vrm`).
3. OpenCode restart → `/ponytail` should report lite (default).

