# Collaboration Workflow

## Repository lanes

Use focused branches: `gameplay`, `pcg-environment`, `materials-vfx`,
`character-melusina`, and `docs-onboarding`. Git tracks source, Python, C++,
contracts, docs, configuration, and small metadata. Git LFS is intended to be
selective: add large UE binaries only after ownership and history justify it;
do not expand the current broad attribute policy without a migration review.
Narrowing existing tracking is a separate follow-up because it changes clone
behavior and must be coordinated with remote history.

## Editor reservation

Only one editor writer owns a given `.umap`, `.uasset`, or plugin binary at a
time. Before opening the editor, announce the map/assets and expected lane in
the shared task handoff. Before handing off, close the editor when possible and
report validation commands, changed assets, and remaining warnings.

## Commit gates

- No `Saved/`, `Intermediate/`, `DerivedDataCache/`, bundles, or local machine paths.
- No unresolved merge markers.
- Run the relevant Python/GMM tests and audit scripts.
- Binary-heavy changes include an audit report or concise verification note.
- Do not force-push divergent project branches.
- Do not mix catalog-only documentation work with mass asset relocation.

## Ownership boundaries

GMM owns deterministic contracts and simulation. Unreal owns runtime assets,
Blueprints, materials, Niagara, WaterBody actors, and presentation. PCG owns
static support scatter; Niagara owns motion. Human artists own hero placement,
final composition, and authored landmark decisions.

## Handoff template

```text
Lane:
Editor: open | closed
Map/assets:
Expected files:
Validation:
Reports:
Known warnings:
Next owner:
```
