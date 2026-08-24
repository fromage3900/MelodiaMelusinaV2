# Melodia Studio — Musical Geometry Overnight Ledger

**Loop start:** 2026-08-23 (overnight session) · **Cadence:** dynamic ~20 min ticks · **Stop:** `stop-loop` or backlog exhausted
**Contract:** every tick = implement → headless verify (zero GN WARNs) → EEVEE render ×2 angles → contact sheet regenerated w/ notes → ledger append → mirror `deploy/`→`ClaireonTest/deploy/` (copy-only, NEVER /MIR) → sync live addons. **Zero git writes.**

---

## Grounding math (verified sources)

| Phenomenon | Formula | Use |
|---|---|---|
| Free-free beam (chimes/tubes) | `f ∝ 1/L²` → `L₂ = L₁√(f₁/f₂)` | Tube length from target pitch |
| Suspension node | **22.4%** of L from either end | Hang-ring placement |
| Tube overtones | ×**2.756**, ×**5.404** fundamental | Shimmer-band detail marks |
| Equal temperament | `f = A4 · 2^((s−9)/12)`, s = semitone index | Degree → Hz from ♪ Score panel |
| Church-bell partials | hum .5 : prime 1 : tierce 1.2 : quint 1.5 : nominal 2 | Bell profile thickness bands |
| Mersenne (strings/harp/piano) | `f ∝ 1/L`; octave = half length | Harp string pyramid, piano speaking lengths |
| Piano hammer strike | notch at **L/7–L/8** | Key/string strike marking |
| Damped harmonograph | `x=A₁sin(f₁t+φ)e^(−d₁t)`, y likewise; interval ratios 2:1, 3:2, 4:3 | Harmonograph tracery builder |
| Additive tone | saw `Σsin(nt)/n`, square odd `1/n`, tri odd `1/n²` | Waveform wall amplitudes |
| Vinyl groove | Archimedean `r=a+bθ`, constant pitch (LP≈0.1mm/rev) | Groove spacing truth |

## Backlog queue (tick order)

1. ☐ **Chime row (Tick 0)** — ET-tuned tube set from ♪ Score, nodal hangs, shimmer bands, top beam
2. ☑ **Harmonograph tracery (Tick 1)** — damped Lissajous, Score-interval ratios
3. ☐ Bell (church partials lathe profile)
4. ☐ Harp v2 — parabolic soundboard, Mersenne string pyramid
5. ☐ Waveform wall v2 — MeshToCurve fix + additive 1/n^k amplitude law
6. ☐ Vinyl v2 — true constant-pitch grooves, lead-in/out ramps
7. ☐ Shapekey pass A — Strike/_Pluck/_Press morphs on keys+bells, FBX export doc
8. ☐ Shapekey pass B — _Shimmer (bell), _Damp variants; UE morph-target import notes
9. ☐ Komikaze material sweep across all pieces + beauty lighting preset operator
10. ☐ Contact-sheet master review + morning summary

## Tick log

### Tick 0 — Chime Row ✅ DONE (2026-08-23)
*   **Shipped:** `deploy/surreal_arch/chime_row.py` → `surreal_arch.generate_chime_row`; button in ♪ Score panel (Musical Kit box); registered/unregistered via music_ui.
*   **Math applied:** ET degrees `f=A4·2^((s−9)/12)` from Score key/mode; beam law `L=L_ref√(f_min/f)`; hang rings @ **22.4%** L; shimmer bands at **L/2.756** & **L/5.404**; cord drops; top beam rail.
*   **Verify:** headless PASS ×3 (op/object/Komikaze) · v=2864 f=2666 · build 0.37 s · mat=`Voronoi Shader (3 Tones)` via monolith `_komikaze_link`.
*   **Renders:** `MEL_chime_row_A.png` (¾ view), `_B.png` (front-low). Contact sheet regenerated.
*   **Lessons:**
    1. *Visual compression is physics, not a bug:* one octave of pitch = only ×1.41 length change on free-free beams (√2). Don't "fix" it toward air-column halves — the subtlety IS the authenticity. If drama is wanted, add an artistic "Exaggerate Lengths" multiplier param later, default 1.0.
    2. **Control-flow lesson:** material assignment must sit OUTSIDE the fallback branch — when Komikaze succeeds, an append nested under `if mat is None:` silently skips (cost one verify cycle).
    3. Monolith already ships `_komikaze_link(name, link=False)` + blend path on G: — always probe existing bridges before writing new ones.
    4. Test-harness thresholds are product decisions: v>3000 gate was arbitrary; 2864 is correct for 7×(56 ring + 3 tori + cord) + beam. Record expected vert ranges per piece in backlog items.
*   **Known deviation:** operator-built bmesh instead of GN-stack tree — deliberate (exact ET lookup tables are unnatural in pure GN). A GN twin can follow using Switch-ladder mode selection if stack-consistency demands it.
