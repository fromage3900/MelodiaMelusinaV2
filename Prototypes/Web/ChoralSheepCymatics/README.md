# Choral Sheep — Chladni Fleece Study

Browser presentation lab for the capstone spine:

```text
Creature → Motif → Harmony → World
```

It exists so TouchDesigner / After Effects / Unreal can share one visible C → E → G grammar without opening the editor.

It does **not** own the game. It is **not** a recruiter route. Do not put it on fromageart.xyz.

---

## Run it

From the repository root:

```bash
python -m http.server 8080
```

Then open:

```text
http://127.0.0.1:8080/Prototypes/Web/ChoralSheepCymatics/
```

Keys: `C` / `E` / `G` toggle pitches, `space` plays the authored bloom, `R` returns to REST.

Deep links for capture / TD alignment: `#`, `#C`, `#CE`, `#CEG`, `#WORLD`.

---

## What it is proving visually

Board 02 rule:

> Harmony becomes more ordered, not louder.

| State | What you should see |
|---|---|
| REST | lovable rounded sheep, dusty blush wool, musical curls, no effect required |
| HARMONIZE C | calm concentric / root rings; sand gathering on nodes |
| C + E | interference; the field is more complex and less settled |
| C + E + G | 2-fold + 3-fold lock toward a coherent blossom; **not** a brightness spike |
| WORLD | the same nodal language leaves the body as a quiet cyan water-light ring |

The on-screen **coherence** readout is a standing-wave contrast meter. It should dip on the interval and rise again when the triad resolves.

Circular-membrane modes used here:

- **C** — `J0(5.520 r)` concentric root
- **E** — `J2(5.136 r) cos(2θ)` diamond / third
- **G** — `J3(6.380 r) cos(3θ)` flowing fifth

That mapping is a presentation sketch of pitch identity, not a claim that Unreal is running this Bessel field.

---

## Authority rule

Read `Docs/References/ChoralSheepCapstone/AGENT_CONTEXT.md` before changing Sheep / Chladni work.

```text
browser experiment
      ♪
pattern / timing / palette idea
      ↓
TouchDesigner scene `chladni_fleece` / AE breakdown
      ↓
UE presentation via approved Nikki cymatics
MI_ChoralSheep_Body → MI_ChoralSheep_Body_Chladni_C
      ↓
C++ still owns Harmonize / pitch / world truth
```

Do not:

- revive `M_Chorus_Wool_Master`
- redesign the sheep away from Board 06
- treat this canvas as a second gameplay clock
- paste rainbow glow as a substitute for nodal structure

Steal timing, not branding. Hyperpop dramaturgy lives in the bloom sequence (C hold → E unrest → G order → world hit → afterimage), not in copied concert graphics.

---

## Sibling

`Prototypes/Web/MusicKey3D/` is the music-as-key interaction lab. This study should feel related: ivory paper, plum ink, blush / pearl / lilac fleece, restrained cyan only when the world answers.

Board 02 order check (no browser required):

```bash
node Prototypes/Web/ChoralSheepCymatics/test_order.js
```

It asserts REST is empty, C is more settled than C+E, and C+E+G is more ordered than the interval.
