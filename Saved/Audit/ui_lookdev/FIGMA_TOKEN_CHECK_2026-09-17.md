# FIGMA_TOKEN_CHECK — 2026-09-17

**Verdict: PARTIAL (misaligned on recent Figma Atelier / SoftMG Nikki leftovers / UE GameColors gold)**

Audited from Grok Bot box via GitHub + public `my-site` raw assets. **No Fromage PC local shell** in this executor (MachineId `6402dab1-…` permission exists in settings, but Shell here is Linux box-only). Could not mtime-scan `C:\Users\froma\my-site` or write directly to `C:\EnvironmentPortfolio\BS_GodFile\Saved\Audit\ui_lookdev\`. Copy this receipt onto the PC path if needed.

Audit time: **2026-09-17 ~15:27 EDT**.

---

## Sources checked

| Source | Path / ref | Status |
|---|---|---|
| Token SSOT | `fromage3900/MelodiaMelusinaV2` → `melodia-design-system/tokens.json` (git) | **Loaded** |
| UE generator | `Content/Python/generate_melodia_design_tokens.py` | **Loaded** (defines GameColors) |
| Live UE JSON | `Saved/Audit/melodia_design_tokens_ue.json` | **Not on git / not readable here** — reconstructed from generator |
| Native DA receipt | `Saved/Audit/ui_lookdev/TOKEN_NATIVE_DA_IMPORT_2026-09-17.md` | **Not on git** — owner context: 80 colors, `primitives.gold.500=#C9A86A` |
| SoftMG / Figma packs | `fromage3900/my-site` → `generated/assets/melodia-game-ui/` (+ `figma_pull/`, `figma_complete/`) | **Loaded** |
| ART_SOURCE | `…/melodia-game-ui/ART_SOURCE.json` | **Loaded** — `last_full_export=2026-08-03` (outside 7-day window) |
| Recent Figma pack | `generated/assets/figma/atelier-figma-pack-2026-09-14/` (commits 2026-09-14…16) | **Loaded** — newest Figma-related surface |
| Web SSOT CSS | `wix/melodia-tokens.css`, `wix/melodia-game-ui.css` | **Loaded** |
| Painterly P0 | `tools/fromage-webgl-kit/accessory-viewer/p0-painterly.css` (2026-09-16) | **Loaded** |
| SoftMG PNGs | SoftMG_Parchment / Hitline / LaneInk / PillowChip / SealSP | **Sampled** |
| Figma REST | Magical Girl Theme `Wz9xwBr1Rd5gXmaD7SHhck` | **FAIL** — `403 Invalid token` (no FIGMA_API_KEY on box) |
| Melusina Menu UI `ewS0yt17hiWq2KXPa5RfCX` | — | **Not pulled** (API dead) |
| PC mtime last ~7 days | `C:\Users\froma\my-site\generated\…` | **Could not check** |

---

## SSOT key hexes (from `tokens.json`)

| Token | Hex |
|---|---|
| `primitives.gold.500` (Champagne Gold) | **`#C9A86A`** |
| `primitives.gold.300` / `.100` / `.700` | `#DDC79B` / `#F0E6D2` / `#A7884E` |
| `primitives.plum.800` (ink primary light) | `#241B2E` |
| `primitives.ivory.100` | `#F7F4EF` |
| `primitives.lavender.500` / `.300` | `#9F94C6` / `#C2BAE0` |
| `primitives.sakura.300` | `#E7C9CE` |
| `primitives.astral.500` / `.300` | `#3C5C9E` / `#8AA9D6` |
| `primitives.iris.500` | `#6E5AA6` |
| Spacing | `global.space` 4/8/16/24/32/48/64/96/128 |

Accent.primary (light+dark) → `{primitives.gold.500}` = `#C9A86A`.

---

## PASS / FAIL by surface

### 1) Melodia design-system SSOT + web token CSS — **PASS (primitives)**

`wix/melodia-tokens.css` carries correct:

- `--primitive-gold-500: #C9A86A`
- `--primitive-gold-300/100/700` match SSOT
- `--color-accent-primary` / `--color-rule-gold` bind to gold.500

Evidence: `my-site/wix/melodia-tokens.css` lines ~18–21, ~138, ~144.

### 2) Native DA (`DA_MelodiaDesignTokens_Native`) — **PASS (claimed)**

Owner/import context: 80 colors including `primitives.gold.500=#C9A86A`. Live asset not re-read in this run (no Monolith / no PC). Treat as aligned for **primitive Colors**; GameColors map is a separate FAIL below.

### 3) UE `GameColors` / `KeybindColors` (generator → UE JSON) — **FAIL**

From `generate_melodia_design_tokens.py` “Figma wiring plan” block — **not** SSOT gold:

| Key | Value | Nearest SSOT | Δ | Note |
|---|---|---|---|---|
| `GoldBorder` | `#EBB857` (rgba 235,184,87) | gold.500 `#C9A86A` | ~42 | **Wrong gold** |
| `GoldText` | `#F2D69E` | gold.300 `#DDC79B` | ~26 | Wrong gold text |
| `IriCyan` | `#78EBFF` | astral.300 `#8AA9D6` | ~80 | Off-palette cyan |
| `VoidPlate` | `#0B0A13` | plum.900 `#1C1426` | ~27 | Near-black void |
| `Ink` | `#291A21` | plum.800 `#241B2E` | ~14 | Near-miss ink |
| `Ultimate` keybind | `#8FC9BD` | (no seafoam in SSOT) | — | **Nikki leftover** |
| `Attack` | `#D9A566` | gold.500 | ~17 | Near-miss / Nikki amber |
| `Back` | `#3B2A22` | plum.700 | ~26 | Nikki ink |

### 4) SoftMG / game UI Figma exports — **PARTIAL**

- `ART_SOURCE.json`: file `Yx8ud7n39NdWZvnNvo4Xlf`, SoftMG kit + RhythmReactivityBoard `41:242`, **`softmg_nikki_fab_pass`**, `last_full_export=2026-08-03` (stale vs 7-day window).
- PNG sample (opaque quantized):
  - SoftMG_Parchment / Hitline / PillowChip / LaneInk → mostly ivory/gold.100 **aligned**
  - SoftMG_SealSP dominant seafoam `#88C8B8` → **OFF** vs SSOT (Nikki seafoam family)
- `melodia-tokens.css` still defines explicit **`--primitive-nikki-*`** block (`#F2E6CF`, `#E3D3AD`, `#E8A9A1`, `#D9A566`, `#B6A6D9`, `#8FC9BD`, `#3B2A22`) + aliases `--color-nikki-*` / `--game-*`. UI artist skill: raw `#FFFFFF` / Nikki leftovers are OFF-palette.
- `melodia-game-ui.css` SoftMG sections reference `Saved/Audit/softmg_nikki_ref_notes.md` and bind nikki seafoam/amber.

### 5) Recent Figma Atelier pack (2026-09-14…16) — **FAIL vs Melodia SSOT**

Newest Figma-related commits on `my-site` (not Magical Girl Theme — Grandmaster Accessory Atelier on **same** game file `Yx8ud7n39NdWZvnNvo4Xlf` node `177:119`):

- Pack: `generated/assets/figma/atelier-figma-pack-2026-09-14/tokens.json`
- **Does not contain `#C9A86A`**
- Floral 13-swatch + finishes are a **parallel palette** (butter `#D2B878`, plum `#684057`, paper `#F5F0E8`, sea `#BFD3CC`, …)
- Typography: Times / Jost — **not** Fraunces / Inter from SSOT
- `p0-painterly.css` (2026-09-16) uses same Atelier RGBAs (`--p0-gold: rgba(222,209,173,…)`, `--p0-plum: rgba(104,64,87,…)`) — cream-gold, not champagne gold.500

Intentional accessory art-direction ≠ Melodia game HUD token SSOT. For Melodia P0 UI intake: **do not treat Atelier pack as Melodia SSOT**.

### 6) Magical Girl Theme (`Wz9xwBr1Rd5gXmaD7SHhck`) — **UNCHECKED**

Figma API: `{"status":403,"err":"Invalid token"}`. No PC `.env` / local export visible from this box. Prefer local re-export on Fromage PC, then re-run.

---

## Top concrete mismatches

1. **Wrong gold in UE GameColors:** `GoldBorder #EBB857`, `GoldText #F2D69E` vs SSOT `#C9A86A` / `#DDC79B` — `Content/Python/generate_melodia_design_tokens.py`
2. **IriCyan `#78EBFF`** — not in SSOT astral family
3. **Nikki leftovers still first-class in web tokens:** `--primitive-nikki-*` + SoftMG Seal seafoam + keybind Ultimate `#8FC9BD`
4. **Recent Atelier Figma pack** butter/cream golds (`#D2B878`, `#DED1AD`) and plum `#684057` — no `gold.500=#C9A86A`
5. SoftMG seal PNG seafoam cluster ≈ `#88C8B8` (Nikki-adjacent)

Aligned positives: web `--primitive-gold-500=#C9A86A`; SoftMG parchment PNGs read ivory/gold.100; native DA claimed gold.500 correct.

---

## Recommended fix

1. **Regenerate UE GameColors from SSOT only** — map:
   - GoldBorder / CardGold / rule → `primitives.gold.500` `#C9A86A` (alpha OK)
   - GoldText → `gold.300` `#DDC79B` or `gold.100` for bright chrome
   - Ink / VoidPlate → `plum.800` / `astral.900`
   - Drop or retarget IriCyan → `astral.300` `#8AA9D6` (or iris) unless a new SSOT primitive is added
2. **Deprecate `--primitive-nikki-*` / SoftMG Nikki aliases** in `melodia-tokens.css`; point keybinds at sakura/gold/lavender/iris/status tokens; keep SoftMG *textures* but tint via SSOT
3. **Atelier pack:** keep as accessory floral study OR add a `melodiaSsotBridge` map (`butter→gold.300`, etc.) — do not import into `UMelodiaDesignTokens` without remapping
4. On Fromage PC: refresh Figma export for Magical Girl Theme with valid `FIGMA_API_KEY`, dump Variables/styles JSON next to SoftMG pack, re-run this check
5. Re-import native DA after GameColors fix; leave Monolith / `save_packages` to owner session

---

## What could not be checked

- Live `C:\…\melodia_design_tokens_ue.json` bytes / mtime
- Live `TOKEN_NATIVE_DA_IMPORT_2026-09-17.md` body
- PC SoftMG / Magical Girl mtimes last 7 days
- Figma Variables API for all three file keys
- Melusina Menu UI file `ewS0yt17hiWq2KXPa5RfCX`
- WBP CDO color props (no editor / Monolith from this box)
- Writing this file to `C:\EnvironmentPortfolio\BS_GodFile\Saved\Audit\ui_lookdev\` (no PC write)

Box copies: `/workspace/melodia-figma-token-audit/FIGMA_TOKEN_CHECK_2026-09-17.md` and `/workspace/fromage-push/Audit/ui_lookdev/FIGMA_TOKEN_CHECK_2026-09-17.md`.
