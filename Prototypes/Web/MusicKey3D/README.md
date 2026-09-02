# ♪ MusicKey3D — a tiny Melodia world that listens

This is the browser-side **music-as-key interaction lab**: watercolor ground, toon shading, soft bloom, floating notes, strange little instrument nodes, barriers that answer phrases, and a deliberately simple Melusina / Ebenezer proxy.

It exists because sometimes it is much faster to answer **“does this feel like Melodia?”** in a browser than by opening Unreal and rebuilding half a map.

It does **not** own the game.

---

## ♫ Run it

From the repository root:

```powershell
python -m http.server 8080
```

Then open:

```text
http://127.0.0.1:8080/Prototypes/Web/MusicKey3D/
```

---

## ♬ What I use it for

- checking whether musical nodes read spatially;
- trying short phrases like `C → E → G` before committing them to a level;
- testing barrier / route-unlock feedback;
- testing the Mara / Melodia browser palette;
- toon ramps, ink-like outlines, watercolor surfaces, quiet bloom, musical tendrils, water-ish hair motion;
- exporting compact prototype JSON to compare with the native UE contract;
- making sure future Three.js experiments stop defaulting to generic black-background tech-demo aesthetics.

---

## 𝄞 The authority rule

The real project already has the music-as-key pillar under `Source/BS_GodFile/Piano/`: steppable note nodes, pattern scoring, PCG musical content, and the typed narrative bridge.

So the relationship is:

```text
browser experiment
      ♪
phrase / layout / visual idea
      ↓
compare or author data
      ↓
UE music-as-key implementation
      ↓
UMelodiaPCGNarrativeChallengeBridgeComponent
      ↓
Narrative decides what the world remembers
```

A browser barrier opening is presentation. Unreal remains authoritative for gameplay state and persistence.

---

## ♪ Its siblings

### 𝄞 Cymatic Sanctuary

`Docs/Tools/puzzle-sandbox/`

The bigger 12-instrument version: four phrase gates, radial sanctuary layout, prototype schema export, and the same “music can unlock the world without becoming another runtime authority” rule.

### ♫ Traveling Folio

`Prototypes/Web/MelodiaFolio3D/`

The cozy 3D UI / Starskiff-post / model-viewer lab.

The browser family should feel related:

- ivory + lavender surfaces;
- plum ink;
- cool blue / violet shadows;
- sakura-pink accents;
- muted gold;
- illustrative shading instead of generic PBR showroom lighting;
- notation, thread, ribbon, water, field-note and dress-pattern motifs;
- bloom only when something is actually resonating.

---

## ♬ Useful corrections already made

The checked-in version fixes a few hazards from the original one-shot prototype:

- `THREE.PCFSoftShadowMap`;
- correct secondary-light insertion;
- `THREE.RedFormat` toon ramp;
- preserved barrier outline references;
- no accumulating barrier vertical drift;
- repeated phrase notes can be removed one at a time;
- clipboard failure stays non-fatal.

---

## ♪ Next good experiments

1. Replace proxy figures with one or two **intentional GLB showcase exports** from the real project.
2. Share the watercolor/toon material language with the Folio turntable.
3. Add optional note audio without creating another clock or grading system.
4. Read an existing progression/music-key schema directly instead of hand-copying puzzle data.
5. Keep every export marked prototype-only until the native contract says otherwise.

> **The browser gets to dream quickly. Unreal gets to decide what is real.** ♫
