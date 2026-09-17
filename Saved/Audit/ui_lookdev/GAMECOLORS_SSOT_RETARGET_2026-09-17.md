# GameColors / KeybindColors SSOT retarget — 2026-09-17

Generator `Content/Python/generate_melodia_design_tokens.py` no longer hardcodes
Figma-wiring / Nikki leftover hexes. GameColors and KeybindColors resolve from
`melodia-design-system/tokens.json` through the same flatten path as Colors.

No new hexes were invented. RGB always comes from a named primitive. Plate/border
roles keep their previous alpha, composed onto that SSOT RGB.

**IriCyan:** tokens.json has no cyan / iris-cyan / resonance primitive. Closest
named Melodia blue is `primitives.astral.300` (also `semantic-dark.color.accent.astral`).

Equivalent semantics (same hex): `semantic-light.color.rule.gold` =
`semantic-light.color.accent.primary` = gold.500; `semantic-dark.color.text.accent`
= gold.300; `semantic-light.color.accent.iris` = iris.500.

## GameColors

| Role | Old | New (emitted) | SSOT token | SSOT hex |
|---|---|---|---|---|
| VoidPlate | `#0B0A13` | `#1C1426` | `primitives.plum.900` | `#1C1426` |
| ParchmentField | `rgba(56,41,59,0.92)` `#38293B` | `rgba(46,36,56,0.92)` | `primitives.plum.700` | `#2E2438` |
| ParchmentFill_Start | `#F2E6CF` | `#F0E6D2` | `primitives.gold.100` | `#F0E6D2` |
| ParchmentFill_End | `#E3D3AD` | `#DDC79B` | `primitives.gold.300` | `#DDC79B` |
| GoldBorder | `rgba(235,184,87,0.8)` `#EBB857` | `rgba(201,168,106,0.8)` | `primitives.gold.500` Champagne Gold | `#C9A86A` |
| GoldText | `#F2D69E` | `#DDC79B` | `primitives.gold.300` | `#DDC79B` |
| IriCyan | `#78EBFF` | `#8AA9D6` | `primitives.astral.300` | `#8AA9D6` |
| PlumButton | `rgba(77,46,61,0.95)` `#4D2E3D` | `rgba(70,58,84,0.95)` | `primitives.plum.600` | `#463A54` |
| Ink | `#291A21` | `#241B2E` | `primitives.plum.800` Midnight Plum | `#241B2E` |
| CardGold | `rgba(232,199,140,0.95)` `#E8C78C` | `rgba(221,199,155,0.95)` | `primitives.gold.300` | `#DDC79B` |

## KeybindColors

| Role | Old | New | SSOT token | SSOT hex |
|---|---|---|---|---|
| Interact | `#E8A9A1` Nikki rose | `#D6A9B0` | `primitives.sakura.500` | `#D6A9B0` |
| Attack | `#D9A566` Nikki amber | `#C9A86A` | `primitives.gold.500` | `#C9A86A` |
| Skill | `#B6A6D9` | `#9F94C6` | `primitives.lavender.500` | `#9F94C6` |
| Ultimate | `#8FC9BD` Nikki seafoam | `#6E5AA6` | `primitives.iris.500` Iris / Amethyst | `#6E5AA6` |
| Menu | `#F2E6CF` Nikki parchment | `#F0E6D2` | `primitives.gold.100` | `#F0E6D2` |
| Back | `#3B2A22` Nikki ink | `#241B2E` | `primitives.plum.800` | `#241B2E` |

## Output

- Regenerated: `Saved/Audit/melodia_design_tokens_ue.json`
- Flatten also resolves semantic `{primitives.*}` refs to hex (Colors now 80 resolved)
- Live `DA_MelodiaDesignTokens` re-import is editor-side; this PR does not touch `.uasset`
