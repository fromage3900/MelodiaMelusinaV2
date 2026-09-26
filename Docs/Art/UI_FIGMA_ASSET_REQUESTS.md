# UI assets to make in Figma — Orrery hub / editorial Magical Girl lookbook

Source file: Figma "Melusina Menu UI / 2" (`ewS0yt17hiWq2KXPa5RfCX`). Direction: the Orrery is the hub;
one shared animated starfield; editorial lookbook type; beat-locked motion. Starter SVGs to drag in:
`Content/UI/AssetKit_20260926/` (starfield tile, medallion ×3 states, filigree frame, divider, orrery sigil;
generator `Tools/ui_asset_kit_orrery.py`).

## Export rules (so UE import is mechanical)
- **Components, not flat frames.** Every stateful thing is a component set with a `State` variant
  (`Default / Focused / Pressed / Locked / New`). The current file has 0 components — UE can only crop it.
- **No baked text or keys.** Labels, numbers, cooldowns and key letters are live UMG text. Export the
  glyph/frame only. (Today's HUD crops had "4.2", "Q", "E" baked in.)
- PNG @2×, transparent, trimmed to the component frame. Name `T_UI_<Surface>_<Name>_<State>`.
- Palette: indigo `#0B0920`/`#17123A`, pearl `#F4EEE6`, rose-gold `#E8B4A0`, lavender `#B9A6F0`,
  cyan `#9EE7F7` (one accent per screen). **Type: 2 families** — pick one display serif + one body
  (redesign uses 8; Times New Roman/Arimo there are missing-font fallbacks).
- The Bayer dither is a Figma code effect and does not export; state the final params
  (Canonical HUD uses Bayer 8×8, levels 8, contrast 1.18, brightness 106, pixel 2) and UE rebuilds it in
  the UI material.

## Motion (beat-locked, 128 BPM — scale by tempo)
| Beat | ms | Orrery unfold | Button press | Grade pop |
|---|---|---|---|---|
| 0 | 0 | closed | — | anticipation (scale 0.9) |
| 1/8 | 117 | latch | pressed inset | overshoot (1.15) |
| 1/4 | 234 | bloom | release | settle (1.0) |
| 1 | 469 | ignite | — | fade begins |
| 1½ | 703 | settle | — | gone |
Smart Animate between the variants using these durations; I read them back through the API.

## 1. Orrery hub (highest priority)
- World medallions ×4 (Sakura Dream, Grand Stage, Celestial Nave, Melodia Village) — `Locked / Unlocked / Focused / New`.
- System medallions ×4 (Journal, Compendium, Wardrobe, Settings) — same states; these orbit on the chassis rings.
- Title lockup "The Celestial Atlas" (kicker + display line) and a one-line caption style.
- Circular vignette/mask ring for the 3D view (replaces today's hard square).
- **Remove from the orrery frame:** extra backgrounds (3 → 1), constellation cross-lines, the core ornament square, footer panel/divider.

## 2. Shared starfield
- Parallax layers as separate exports: far stars, near stars, nebula wash, 4-point sparkle sprites (S/M/L).

## 3. Overworld HUD
- Skill icons ×4 (Sonic Scepter, Phase Bell, Crescendo Fan, Harmonize), clean glyph + states incl. `Cooldown` (radial veil only, no number).
- Keycap component: Q E R F, W A S D, Shift, Tab, M, Esc, J, 1, 2, Space, Enter.
- Bar kit: track, fill, end-cap for Vitality and Resonance.
- Quest card as a lookbook caption (kicker / title / body), and a 3-second "Quest updated" toast.
- Area caption lockup (shown on entry, fades on the beat).
- Orrery sigil button (M) — replaces the 1/2/J/Esc row.
- Minimap marker glyphs ×5 (Objective, NPC, Encounter, Exit, Save point). The dial itself is drawn in UE.

## 4. Rhythm highway (QWOP — 4 lanes)
- **Fix in the Redesign frame:** it draws 3 lanes "F · J · K"; the game is 4 lanes **Q W O P**.
- Lane frame, hit line, note head per lane, hold tail.
- Judgement lockups: Perfect / Great / Good / Miss. Grade-pop halo (see motion table). Combo numerals 0–9.

## 5. Calibration screen
- Pulse ring (idle / click / accent), result card ("You land N ms late").

## 6. Compendium
- Category glyphs ×7: Character, Motif Creature, Instrument, Place, Phenomenon, Song, Relic.
- Entry spread (artwork + field note + musical identity), locked-silhouette treatment.

## 7. Quill dialogue
- Caption card (speaker kicker + body), choice list states, advance indicator.
