# Three.js Web Recovery — 2026-09-05

## What was found

The Three.js work was split across current `main` and stale feature branches.

### Already on main
- root atmospheric `index.html`
- `Docs/Tools/puzzle-sandbox/index.html` (Cymatic Sanctuary)
- `Prototypes/Web/MusicKey3D/index.html`
- `Prototypes/Web/MelodiaFolio3D/index.html`

### Recovered exact ritual
The complete sensory opening exists on remote branch `feat/site-ink-breath-resonance`, commit `f6a95a2`:
`feat(site): Ink & Breath & Resonance — full sensory opening ritual`.

That branch was 69 commits behind `main`, so this recovery copies the exact HTML into:
`Prototypes/Web/InkBreathResonance/index.html`

The root website is intentionally unchanged.

### Recovered from draft PR #61
PR #61 contains a large Wix/site snapshot plus a reusable Three.js layer. The branch was 106 commits behind `main`, so only the reusable shared Three.js source has been recovered under:
`Prototypes/Web/_Recovered/PR61SharedThree/`

## Rule going forward

Do not merge PR #61 wholesale and do not replace the root site from the stale ritual branch.

Use current `main` as authority, treat recovered files as prototype/reference inputs, and promote individual systems only after testing against the current site shell.

## Recommended next integration order
1. Keep Ink & Breath & Resonance runnable as its own prototype.
2. Port the constellation interaction into the current root shell as an isolated module.
3. Port the orrery only where a dedicated mount exists.
4. Unify Three.js dependency/version strategy after the visual behavior is stable.
5. Retire or close stale branches only after this recovery PR lands.
