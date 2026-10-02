# ANMN301 animatic — canonical character rebuild

Everything here is reproducible from the canonical rig. Nothing needs the
600 MB intermediates to be re-derived.

## Source of truth

```
D:\MelodiaMelusina\MelusinaFinalRig\FinalUERig43.blend    851 MB, 2026-08-11
  (identical tree on the portable G: drive, which the repo names as canonical
   at Tools/melodia_stage_paths.py:39)
```

`character_rig` — 759 bones / 234 deform — plus the 28 meshes that deform off
it, and the hair-strand armatures.

## Rebuild order

```
1. tools/extract_char.py      FinalUERig43.blend -> proxy/MELUSINA_CHARACTER_rig43.blend
                              keeps character_rig + 28 meshes, packs every image,
                              drops the other 352 props/environment meshes.
                              851 MB -> 706 MB, pixel-faithful (0.003% delta)

2. tools/swap_char.py         SHOREWAKE_ANIMATIC_working_scene.blend
                              + MELUSINA_CHARACTER_rig43.blend
                              -> proxy/SHOREWAKE_swap_test.blend
                              removes the grey EXPORT_* character, appends the
                              canonical one, aligns it to the same volume
                              (rotate 90Z, scale 0.98311, feet to z=0.797)

3. render_all_panels.py       17 panels -> proxy/panels_v5/
4. burn_cards.py              -> panels_final/ (numbering + title/end cards)
5. build_vse.py               -> SHOREWAKE_VSE_animatic_v04.blend + the MP4
```

Both steps 1 and 2 are one-shot. If `MELUSINA_CHARACTER_rig43.blend` and
`SHOREWAKE_swap_test.blend` are present, you can start at step 3.

## Verification

```
tools/verify_mp4_spec.py             spec gate: 1920x1080, 24fps, 1560 frames,
                                     65.000s, silent, h264
tools/verify_cut_matches_panels.py   compares exported frames against the exact
                                     panels_final/ files the VSE consumed.
                                     Catches the double-tonemap class of bug:
                                     a green spec check hides a colour shift.
tools/contact_sheet.py               17-panel sheet for eyeballing the board
tools/probe_rig.py                   rig inventory: bones, deform count, textures
```

Run the panel comparison after every VSE rebuild. It is the check that found the
AgX double-application; the spec gate passed while the cut was 18 levels dark.

## Why the intermediates are not in git

```
proxy/MELUSINA_CHARACTER_rig43.blend   674 MB
proxy/SHOREWAKE_swap_test.blend        509 MB
```

Both are re-derivable in two script runs from a file that lives on D:/G:, and
committing them would put ~1.2 GB of LFS history in the repo for no gain. The
scripts that produce them ARE committed. The four small blends that the previous
commit already tracked (`SHOREWAKE_VSE_animatic_v04.blend` at 1 MB,
`SHOREWAKE_ANIMATIC_working_scene.blend` at 8 MB) stay tracked.

If you want them in git anyway, they are LFS-tracked already and the pre-commit
hook will accept them:

```
git add -f Humber_FinalYear_Prep/ANMN301_Animatic/proxy/MELUSINA_CHARACTER_rig43.blend
git add -f Humber_FinalYear_Prep/ANMN301_Animatic/proxy/SHOREWAKE_swap_test.blend
```

## Known gaps

- 14 texture maps (`bow_*`, `SHAWL_*`, `DPM2.004_BaseColor`, `Material.020_*`)
  have no source files anywhere — gone upstream. The bow and shawl render flat.
  They must be re-exported from the desktop to be fixed.
- `L_Cornea` / `R_Cornea` ship with `hide_render=True` in FinalUERig43. The
  render script flips it per-run; the source flag is still wrong.