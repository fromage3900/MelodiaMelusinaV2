# 𝄞 Cymatic Sanctuary 𝄞

A small browser sanctuary for trying **Music-as-Key** ideas without making the browser another game runtime.

Twelve instruments sit around a cymatic pool. Touch them, build a phrase, and see whether the sanctuary answers.

> **Listen for shape, not speed. A phrase is a key only because the world remembers how it was answered.** ♪

---

## ♪ Run it

From the repository root:

```powershell
python -m http.server 8080
```

Then open:

```text
http://127.0.0.1:8080/Docs/Tools/puzzle-sandbox/
```

The page loads Three.js from a CDN, so the browser needs network access for the library unless the imports are vendored later.

---

## ♫ The 12 instruments

```text
C4  Lute of Harmonic Bloom
D4  Resonant Bell Staff
E4  Wire Harp of Tides
F4  Monolith Conductor
G4  Phase Drum
A4  Resonance Core
B4  Glass Chimes
C5  Tide Organ
D5  Thread Lyre
E5  Pearl Ocarina
F5  Cymatic Bowl
G5  Starskiff Bell
```

Current prototype phrases include:

- `C4 → E4 → G4` — Sea Above Gate;
- `D4 → F4 → A4` — Sanctuary Gate;
- `B4 → C5 → E5 → G5` — Glasswing Seam;
- `D5 → F5 → G5` — Far Fold.

These are **design phrases**, not newly canonized runtime content just because they exist here.

---

## ♬ What the sandbox can do

- click / raycast twelve musical nodes;
- build and reset a current phrase;
- play one random demo phrase;
- unlock four presentation-only barriers;
- show toon shading + ink-like outlines;
- watercolor-ish sanctuary floor + cymatic rings;
- restrained bloom + drifting particles;
- export compact prototype JSON using `melodia.music_key_sandbox.v1`.

The export marks itself:

```text
authority = prototype_only_unreal_remains_authoritative
```

on purpose.

---

## 𝄞 What it does **not** own

The real Music-as-Key implementation already lives in Unreal under `Source/BS_GodFile/Piano/` and its existing narrative bridge.

So the useful relationship is:

```text
Cymatic Sanctuary
      ♪
prototype phrase / layout / visual grammar
      ↓
compare against native contracts
      ↓
UE Music-as-Key system
      ↓
Narrative decides the durable consequence
```

The browser may suggest a phrase. It cannot unlock the real Sea Above route, write a save, grant a reward, or decide narrative truth.

---

## ♪ Provenance note

The requested destination was:

```text
Docs/Tools/puzzle-sandbox/index.html
```

with the commit:

```text
feat(tools): add Cymatic Sanctuary — 12-instrument Music-as-Key sandbox
```

That exact commit exists in this branch history.

The originally referenced local source path, `puzzle-sandbox-final/index.html`, was **not present anywhere accessible in the GitHub repository** during this pass. Rather than pretend a remote copy had happened, the checked-in sanctuary was built from the already-working `Prototypes/Web/MusicKey3D/` foundation and expanded into the 12-instrument version here.

If a distinct local `puzzle-sandbox-final/index.html` still exists on the workstation, **diff it against this file first**. Do not silently overwrite either version; keep whichever ideas are actually better.

---

## ♫ Related browser labs

- `Prototypes/Web/MusicKey3D/` — smaller world-interaction / watercolor-toon sandbox;
- `Prototypes/Web/MelodiaFolio3D/` — 3D Folio, Starskiff mailbox, UI intents, real repo-model turntable;
- `Prototypes/Web/MelodiaFolio3D/mara.html` — the softer Mara-art-direction variant.

Think of them as three questions:

```text
MusicKey3D         → does this world interaction feel right?
Cymatic Sanctuary  → can this musical grammar become interesting?
Traveling Folio    → how does the journey remember itself?
```

---

## ♬ Next useful move

Compare `melodia.music_key_sandbox.v1` against the native UE Music-as-Key data/bridge contract. Keep stable IDs, phrase representation, and presentation ideas only where they simplify the real game.

> **Browser toys are allowed to be fast and magical. Runtime truth still has one home.** ♫
