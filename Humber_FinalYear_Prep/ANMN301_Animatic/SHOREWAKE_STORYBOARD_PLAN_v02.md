# SHOREWAKE — Fully Realized Posing & Storyboard Plan v02 (2026-09-17)

School: ANMN301 animatic A1, silent 1080p24, due Oct 9. Blender 5.2 only. No UE.
Source blend: proxy/SHOREWAKE_proxy_v01_posed.blend (1 keyed sit pose, 17 FK bones).
Stage blend (this plan's output): proxy/SHOREWAKE_proxy_v02_storyboard.blend.
Skiff upgrade: proxy/SHOREWAKE_proxy_v03_skiff.blend — MK38 AAA hull appended
(90 objects, Hull_Shell + keel + mast/sail + jewels + perch), aligned to the
proxy hull seat, proxy hidden as fallback. MK38 carries the audio-reactive GN
tree (MEL_starskiff_hull_audio, Sample Sound node, verified live but clip-less
= silent-neutral for stills) AND a form tree whose defaults bloat the hull
11.4m (measured, in the source file too): 5.2 exposes no Python path to GN
modifier inputs (no IDProperties on the modifier struct), so the form modifier
is MUTED and the authored 7.55m base mesh carries the shots. Revisit dials from
the GUI sliders, never headless.
Panels output: proxy/panels_v2/panel_01..17.png (1920x1080, on-panel numbers).
Cut + MP4 rebuild from v2 panels with identical timing (1560f, black title/end slugs).

## Rig control set (FK, all driven headless as base + delta, XYZ euler)

c_neck_x | head turns, bows, lifts — the acting bone, carries shots 02/06/11/12/17
c_spine_03_x | lean in/out with the neck, never more than 0.2
c_arm_fk_l/r + c_forearm_fk_l/r + c_hand_fk_l/r | offer (X -0.45/-0.25), play (-0.6/-0.45/-0.2)
c_thigh_fk / c_leg_fk | untouched, the sit stays seated throughout (boarding is
  root glide, not a stand — storyboard grade, honest, no fake walk)

Standing is OUT of scope for the animatic. Shots 14-15 move MelusinaRig object
toward + aboard the hull; the sit reads as "settled aboard" at storyboard distance.

## New proxies (built headless, storyboard grade)

Lyre proxy (owed since expert review): torus + cylinder neck, LyreGlow material,
  hidden shots 01-05, visible 06-17, parked before her hands.
LanternGlow material on ProxyLantern (was material-less): emission 0 asleep, 8 offered.
Wake states via Principled emission only: ProxyWater 0 > 0.5 ripple > 1.5/3 banks > 4
  open route; Sun energy 1 > 3 > 5 > 6; hull Z +0.3 on shot 13 (the wake lift).

## Shot table (durations locked from SHOREWAKE_BEAT_BOARD.md, total 1560f)

| Shot | Dur | Cam | Pose | Light/prop state |
|------|-----|-----|------|------------------|
| 00 title | 72f | — | — | black slug |
| 01 wide asleep | 120f | Wide | base sit | asleep: sun 1, water 0, lantern 0 |
| 02 at the rail | 96f | Intimate | head turn L (neck Y +0.35) | asleep |
| 03 slack rope | 48f | SkiffClose | base | asleep |
| 04 lantern offered | 48f | Intimate | arms offer | lantern 8 |
| 05 light dies | 72f | SkiffClose | arms half-mast (offer x0.5) | lantern 0, water 0 |
| 06 decision, lyre (*) | 120f | Intimate | head up + arms play, lyre visible | lantern 2, fade mark 1 |
| 07 first phrase | 48f | Intimate | play, head level | water 0.5 ripple |
| 08 water answers | 48f | Wide | play held | water 1.0 |
| 09 bells bank 1 | 48f | Wide | play held, head turn L | sun 3, water 1.5 |
| 10 bells bank 2 | 48f | Wide | play held | sun 5, water 3 |
| 11 doubt beat | 96f | Intimate | bow (neck X +0.45, spine +0.2), arms ease x0.5 | hold 10, then back to play |
| 12 second phrase | 120f | Intimate | head up full, play | sun 6, water 4, lantern 4 |
| 13 skiff wakes (*) | 72f | SkiffClose | base, hull Z +0.3 | fade mark 2 |
| 14 boarding | 96f | Wide | sit glided aboard (rig toward hull) | full held |
| 15 crossing | 120f | Wide | sit, rig+hull glide X | full held |
| 16 route opens | 120f | Wide | sit, look L | full held |
| 17 look-back (*) | 96f | Intimate | head turn R (neck Y -0.35) | warm held, fade mark 3 |
| 18 end | 72f | — | — | black slug |

(*) = the 3 allowed fades, marked for the VSE pass (Gamma Cross at 06/13/17 boundaries).

## 5.2 staging notes (traps already bitten)

--factory-startup always (LiquiFeel zombie addon hangs background Blender).
VSE API is strips/strips_all, new_effect takes length= not frame_end.
Render at 100% headless EEVEE (~1s/frame); absolute output paths, never /tmp.
Panels numbered on-panel with PIL after render (01-17 corner burn-in).
Lyre/hull/rig moves are object-level; armature pose is bone-level; never both on one frame.
