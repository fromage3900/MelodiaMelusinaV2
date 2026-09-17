# VFX Fix A risks — flipbook double-scrub (2026-09-17)

**Type:** documentary audit (not a live editor read).
**Home:** `Docs/VFX/` (matches the 2026-09-14 Melodia Niagara docs).
**Status authority:** `CURRENT_STATE.md`. This file does not claim live pin state.

Fix A is a **non-binding hypothesis** until a Monolith pass confirms renderer
`SubImageSize`, the presence of `SubUVAnimation`, and the MI's `FlipFPS` /
`GridRows` / `GridCols` / `SubImage` knobs on the same system.

## 0. What Fix A is

**Risk:** a material instance owns flipbook scrub (`Grid` / `SubImage` / `FlipFPS`)
**and** the Niagara emitter has `SubUVAnimation` enabled and/or sprite
`SubImageSize ≠ 1×1`. Both clocks advance the atlas. Playback looks broken
(double-speed, skipped cells, torn frames).

**Fix A:** the material owns scrub. Disable Niagara `SubUVAnimation`. Set
renderer `SubImageSize` to `1×1`.

Do **not** invert that without an owner look call: Niagara-owns-scrub
(`SubUVAnimation` + `SubImageSize` matching the sheet, material sampling the
full UV) is a valid single-owner design. Double-scrub is the defect.

## 1. Risks / unknowns first

| Item | Why it is first | In-repo evidence | `fix_a_status` |
|---|---|---|---|
| **`NS_ChoralSheep_BeatBurst` + `MI_NS_ChoralSheep_BeatStar`** | Only named system with a written SubUV pin history **and** a flipbook MI | `Saved/Audit/BATCH_B_SHEEP_2026-09-12.md`: renderer `SubImageSize` went **1×1 → 4×2**, **`SubUVAnimation` added**, 8 frames, on `T_Spark_Twinkle8`. That is Niagara-owns-scrub. Owner later says Fix A was applied (material owns; SubUV off; 1×1). **Those two statements disagree.** This checkout has only the LFS pointer, so neither live pin can be read. | **RISK** + `LIVE_MONOLITH_PENDING` |
| **`NS_Melodia_LeafPileLoop` + `MI_Leaves`** | Authored with Niagara SubUV on purpose | `Docs/VFX_ASSET_MANIFEST.md`: Sprite SubUV 2×2 / `MI_Leaves`. `Tools/author_endless_loops.py` injects `SubUVAnimation`. Double-scrub **only if** `MI_Leaves` also FlipFPS-scrubs. `MI_Leaves` is not in this clone (`/Game/Effects/Environments/Leaves/...`). | **RISK** (conditional) + `LIVE_MONOLITH_PENDING` |
| **Flipbook consumers under `Content/Melodia/VFX/`** | Same master as BeatBurst's donor | Manifest 2026-08-15: `NS_Melodia_ClickSparkle`, `NS_Melusina_EyeSparkle`, `NS_Melusina_Globules`, `NS_Melusina_Splash` consume `M_Niagara_MelodiaFlipbook` (FlipFPS=15, Grid 4×4). Folder is **gitignored**; zero `.uasset` bodies here. Sibling of BeatBurst. | **UNKNOWN** + `LIVE_MONOLITH_PENDING` |
| **`NS_SakuraPetals_v2` SubUV + `MI_Niagara_Petal`** | Docs say Niagara SubUV **and** a sprite MI | `Docs/SAKURA_PETAL_NIAGARA.md`: SubUV across `T_Sakura_Petal` / `T_Sakura_Blossom`, assign `MI_Niagara_Petal`. If that MI (parent `M_Niagara_SakuraSprite`) also scrubs, it is the same defect class. | **UNKNOWN** + `LIVE_MONOLITH_PENDING` |
| **Owner names with no asset** | Cannot audit what does not exist | `HybridSparkles`, `PetalCascade`, `MotionTrails`, `FluidSplash` — **zero** hits as `NS_` / `MI_` paths in git, disk, or `BRANCH_LEDGER`. Closest guesses are listed in the inventory; they are guesses. | **UNKNOWN** (alias rows) |
| **`MI_Niagara_Melodia_Static_StateB` parent** | Two masters = two scrub contracts | Ecosystem spec 2026-09-14: reparent onto the flipbook master **or** bless Cosmic. Unresolved. | **UNKNOWN** |
| **Grid vs sheet mismatch** | Cheapest broken look, adjacent to Fix A | Spec 2026-09-14: every water/fluid MI `Rows`/`Cols`/`FlipFPS` vs true 4×4 sheets. Not the same as double-scrub, but will look like it. | not scored; `LIVE_MONOLITH_PENDING` |
| **This cloud clone cannot read Niagara graphs** | Hard limit | Tracked VFX `.uasset` files are Git LFS pointers (~130 B). `Content/Melodia/VFX/*.uasset` and `Content/EnvSandbox/VFX/Systems/**` are gitignored. No `Saved/Audit/niagara_ecosystem_review.json` / `live_niagara_audit.json` in this tree. | every NS row |

## 2. Owner claims, checked against repo text

| Owner claim | Repo text | How this audit treats it |
|---|---|---|
| `NS_ChoralSheep_BeatBurst` had double-scrub; **Fix A applied** | Last **written** pin state is Batch B: Niagara SubUV **on**. No later receipt records SubUV off / 1×1. | **RISK** until Monolith confirms the revert. Do not mark **FIXED** from the claim alone. |
| HybridSparkles / PetalCascade / MotionTrails / FluidSplash / WoolMotes ladder **Fix A clean** | WoolMotes: Batch B agrees (`SubImageSize` 1×1, single-frame). The other four **names are not assets**. | WoolMotes **CLEAN**. Four aliases **UNKNOWN**. |
| `NS_ConstellationDraw` Fix A OK; **Dream\*** user bus (not BeatPulse) | System is gitignored. Codex 2026-08-01: black isolated preview, CPU, dynamic bounds. Ecosystem contract includes `User.DreamVisibility` / `DreamIntensity` / `DreamTwinkleSpeed`. No SubUV pin text. | **CLEAN** for Fix A *as claimed*, with `LIVE_MONOLITH_PENDING`. Dream bus is a **separate** wiring gap, not a double-scrub proof. |

## 3. What is actually CLEAN from receipts

- **`NS_ChoralSheep_WoolMotes` / `MI_NS_ChoralSheep_WoolMote`:** Batch B 2026-09-12 verified `SubImageSize` 1×1, single-frame texture, left alone. That is Niagara **not** scrubbing an atlas. Still confirm the MI has `FlipFPS=0` / grid 1×1 so the material is not the only remaining clock on a static glint.
- **Ribbon / mesh systems** (`NS_Melusina_SwingTrail`, `NS_Melusina_Arc`, `NS_Melodia_PetalEndlessLoop`, Aurora / MagicTrail ribbons): Fix A is **N_A** — no sprite atlas clock.
- **SDF prototypes:** incomplete CPU sprites in the 2026-08-01 Codex audit; not the flipbook family.

## 4. Suggested live Monolith order (editor lane, not this PR)

1. `NS_ChoralSheep_BeatBurst` — read renderer `SubImageSize`, list modules for `SubUVAnimation`, read `MI_NS_ChoralSheep_BeatStar` `FlipFPS`/`Grid*`. If both clocks live, apply Fix A. If Niagara already 1×1 and SubUV gone, mark **FIXED** with a JSON receipt.
2. Donor + flipbook consumers: `NS_Melodia_ClickSparkle`, `EyeSparkle`, `Globules`, `Splash`, `Ripple`.
3. `NS_Melodia_LeafPileLoop` + `MI_Leaves` graph (Niagara-owns vs double).
4. `NS_SakuraPetals_v2` SubUV vs `MI_Niagara_Petal`.
5. Resolve StateB parent. Resolve the four alias names or drop them.
6. Write results back into `VFX_NIAGARA_INVENTORY_2026-09-17.csv` `fix_a_status`.

Do not run two MCP surfaces on the same graph. Do not Python-load skill Blueprints.
Do not treat probe-injected Niagara compiles as play proof.

## 5. Out of scope (do not call Fix A)

- UltraDynamicSky `Basic_SubUV_Animation`, TurnBasedJRPG `M_Fire_SubUV` / explosion sheets, ArtOfShader glitch NS, Greybox `NS_WaterFall_*`, Nikki fixture JSON systems that were never proven on disk (`NS_Nikki_*` in `Content/Python/gmm/fixtures/niagara_nikki_library.json`).
- Cloth/Copernicus flipbook masters (`MI_Copernicus_*_Flipbook`, PearlWoven frame stacks). Those are character/environment materials, not Niagara sprite systems.
- PPV / StarryNight (separate work order).
