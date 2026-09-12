# SeaAbove Git and project review — 2026-09-04

## Current checkout

The working checkout is `llm/fromage/BS_GodFile/shorewake-chapter-loop` at `b8d3a7c6`, while local `main` contains the SeaAbove work through `53216f24`. `HEAD..main` contains the SeaAbove convergence commits and their plans; `main..HEAD` has no commits. The working tree retains many files from that newer line as unstaged LFS pointer changes. This is a branch-state issue, not evidence that the assets are absent.

Do not merge, reset, clean, or commit this state while the editor owns assets. The local branch has 19 unrelated LFS changes (wardrobe, general masters, stained glass, ocean and membrane) alongside the SeaAbove material, function, map and PCG changes. `Content/EnvSandbox/PCG/Greybox/BP_MonolithBlockoutVolume.uasset` is untracked in this checkout. The intended SeaAbove LFS pointers match the newer `main` content for the landscape master and map; verify with `git show main:<path>` before staging.

## Authority findings

The authoritative project docs say PCG graphs belong under `Universal/`, `Greybox/`, `Collections/` or `Styles/<Style>/`; the SeaAbove derivative is correctly under `Styles/SeaAbove/`. They also require one editor, no bulk save, evidence in `Saved/`, and no shared graph mutation. The SeaAbove handoff explicitly says Oceanology vendor inputs are held, the Sakura parallax fish is excluded, and VDM is deferred until the dressed terrain reads well.

The earlier handoff says weightmaps had never reached UE and recommends importing them. Later live inspection contradicted that: the LandscapeComponent already references Snow/Water/Rock data, and the Base semantic layer was the material binding mismatch. Treat current live UE readback and `Saved/Audit/sea_above_water_target.json` as newer evidence; do not rerun the old import blindly.

The project has one C++ cymatics writer (`MelodiaCymaticsWriterSubsystem`) and the landscape must remain a consumer of `MPC_Cymatics_Driver`. Existing material edits added optional branches and proof assets; they are not a substitute for level lighting, close/far, six-face normal, active permutation, or PIE audio validation.

## Execution implications

The correct next mutation after the editor is responsive is a targeted SeaAbove PCG transaction: verify the existing actor and derivative graph, place the derivative at a screened eastern candidate, generate, ground-check and save only its external actor. Then validate the route from arrival, not just the local east plateau. Material optional features remain disabled until active variant costs and terrain captures are measured.

The review is intentionally non-destructive. It records branch and documentation hazards without changing Git history or discarding any working-tree asset.
