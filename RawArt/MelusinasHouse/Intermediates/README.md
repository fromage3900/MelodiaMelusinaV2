# Melusina House — recovered intermediate blends

Extracted from archived laptop tip `archive/branches/2026-09-05/recovery/laptop-main-20260904` (`Saved/MelusinasHouse/`).

`Saved/` stays gitignored (Unreal). These source `.blend` files live under `RawArt/` so a laptop 3D lane can track them on current `main` without fighting the UE ignore rule.

Canonical editable source remains:

`RawArt/MelusinasHouse/MelusinasHouse_V7_Base.blend`

Use this folder for lineage / lookdev archaeology (greybox → mansion v3–v6 → staged/lookdev). Do not treat intermediates as a second authority over V7.

## Lineage ledger — what each file is, alive or dead

Statuses read from each file's own era per the 09-04 session notes and the V7 plan
(`Docs/MelodiaStudio/MELUSINA_HOUSE_V7_PLAN.md`). "Dead branch" = superseded experiment
kept for archaeology; nothing here is an edit target except V7 Base (and the Study, when
it lands from `feature/grandmaster-melodia-studio`).

| File | Era | What it is | Status |
|---|---|---|---|
| `House_Greybox.blend` | v0 | first massing boxes | dead branch — archaeology |
| `MelusinasBase.blend` | v0 | pre-mansion base house | dead branch — archaeology |
| `House_Facade_v2.blend` | v1–v2 | facade component study | dead branch — archaeology |
| `House_Mansion_WindowDoor.blend` | v1–v2 | window/door component split | dead branch — feeds v3 kit |
| `House_Mansion_RailingAwning.blend` | v1–v2 | railing/awning component split | dead branch — feeds v3 kit |
| `House_Mansion_Rocaille.blend` | v1–v2 | rocaille ornament study | dead branch — trim genome ancestor |
| `House_Mansion_Tower.blend` | v1–v2 | tower component | dead branch — feeds v3 kit |
| `House_Mansion_Rooms.blend` | v1–v2 | room layout draft | dead branch — mh6 shell ancestor |
| `House_Mansion_Expansion.blend` | v1–v2 | wing expansion draft | dead branch — archaeology |
| `House_Mansion_FoliageInterior.blend` | v1–v2 | foliage + interior draft | dead branch — archaeology |
| `House_RoofRibbon.blend` | roofing | roof-ribbon component study | dead branch — ancestor of converged SurrealRoof path |
| `House_ShinglePatch.blend` | roofing | shingle patch material study | dead branch — superseded by `M_MH_Roof_IridescentBlue` |
| `House_Mansion_Master.blend` | v3 | first unified mansion master | dead branch — replaced by v3_Master |
| `House_Mansion_v3_Master.blend` | v3 | unified master, pre-v4 staging | dead branch — replaced by v4 |
| `House_Mansion_v4_Shell.blend` | v4 | shell-only stage | dead branch — staging step |
| `House_Mansion_v4_Dressing.blend` | v4 | dressing pass (`house_dress` family ancestor) | dead branch — lineage of dressing builders |
| `House_Mansion_v4_Garden.blend` | v4 | garden pass | dead branch — staging step |
| `House_Mansion_v4_SCALLOP.blend` | v4 | scalloped-roof experiment | dead branch — scallop kit ancestor |
| `House_Mansion_v4_STAGED.blend` | v4 | staged assembly | dead branch — staging step |
| `House_Mansion_v4_STAGED2.blend` | v4 | second staging pass | dead branch — pre-LOOKDEV |
| `House_Mansion_v4_STAGED2_checkpoint.blend` | v4 | mid-session checkpoint | **dead** — literal autosave checkpoint, zero authority |
| `House_Mansion_v4_LOOKDEV.blend` | v4 | lookdev hero | dead branch — lookdev reference only |
| `House_Mansion_v4_LOOKDEV2.blend` | v4 | lookdev hero, second pass | dead branch — lookdev reference only |
| `House_Mansion_v4_FINAL.blend` | v4 | v4-era terminus | dead branch — last word of the v4 line |
| `House_Mansion_v5_Interior.blend` | v5 | interior push | dead branch — superseded by round-interior work |
| `House_Mansion_v5_RoundInterior.blend` | v5 | rounded-flow interior draft | dead branch — mh6 curve-bend ancestor |
| `House_Mansion_v5_RoundInterior2.blend` | v5 | second round-interior pass | dead branch — same lineage |
| `House_Mansion_v6_lego.blend` | v6 | genome/lego parametric experiment | dead branch — concept folded into `melodia_house.py` |
| `House_Mansion_v6_p1.blend` | v6 | v6 convergence pass 1 | dead branch — last word before V7 |

**Terminus:** everything above converges into `../MelusinasHouse_V7_Base.blend`
(85,520 verts, U-massing, converged roofing — see `Docs/MelodiaStudio/SESSION_NOTES_2026-09-04.md`).

LFS note: these are `*.blend` lockable files. A checkout without `git lfs pull` shows
3-line pointer stubs — that is not corruption.
