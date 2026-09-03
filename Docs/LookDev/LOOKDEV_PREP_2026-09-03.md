
---

## 9. Main menu — computed fix values (ready to apply)

`MenuWorldRosette` (anchor 1,0.5 · left -440 · top -220 · 430x430) gives a reference
centre at **(-225, -5)** in anchor-relative space. Making the orrery concentric with it
is defensible rather than an invented position — the orrery reads as the mechanism inside
the world rosette.

| Widget | Current | Fix |
|---|---|---|
| `OrreryStarfield` | anchor (0,0), 100x30 at 0,0, z -5 | anchors (0,0)-(1,1), offsets 0/0/0/0 — full screen |
| `OrreryCore` (240x240) | anchor (0,0), left -320, top -120 (off-screen) | anchor (1,0.5), **left -345, top -125** |
| `OrbitAstral1` (26x26) | same off-screen spot | anchor (1,0.5), **left -88, top -18** |
| `OrbitAstral2` | " | **left -238, top 132** |
| `OrbitAstral3` | " | **left -388, top -18** |
| `OrbitAstral4` | " | **left -238, top -168** |

Orbits sit on a radius-150 ring at 0/90/180/270 degrees around the rosette centre,
offset by half their 26px size.

### Deliberately NOT changing yet: the collapsed backdrops

`Background` (z -30) and `CosmicVoid` (z -29) are `Collapsed`, and it is tempting to
simply switch them on. But `NebulaParchment` — which is currently carrying the
background — sits at **z -47**, i.e. *behind* both. Un-collapsing them would render them
**in front of** the parchment and probably hide it. That may be why they were collapsed
in the first place. Test one at a time with a capture; do not enable both blind.

