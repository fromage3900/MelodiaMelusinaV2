# ♬ The Traveling Folio — a little 3D memory book

This is Melodia's browser-side **3D UI laboratory**: part travel journal, part dressmaker's pattern book, part Starskiff mailbox, part tiny museum of things the player has actually lived through.

The important rule is cute and boring at the same time:

> **The Folio may look alive. It is still presentation.** ♪

It can unfold, glow, spin a model, open a parcel, follow a golden Thread, and make the UI feel like an object from the world. It does not get to own inventory, progression, Wardrobe, rewards, or save state.

---

## ♪ Run it

From the repository root:

```powershell
python -m http.server 8080
```

Open the stable route:

```text
http://127.0.0.1:8080/Prototypes/Web/MelodiaFolio3D/
```

Or the softer Mara-style presentation pass:

```text
http://127.0.0.1:8080/Prototypes/Web/MelodiaFolio3D/mara.html
```

Do **not** double-click `index.html` through `file://`. The viewer needs HTTP so it can fetch `models.json`, `mailbox.json`, and tracked repository geometry.

---

## ♫ What lives in the Folio right now

- a tactile 3D book / page / parcel / Thread scene;
- raycast interaction that emits **UI intents** instead of changing gameplay truth;
- a local offline Starskiff mailbox fixture for future Gifts / Reveries;
- a manifest-driven repository model turntable;
- OBJ + FBX loading, with GLTF / GLB as the preferred future showcase format;
- automatic centering and scale normalization so unrelated source models fit the same little stage;
- visible failure instead of silent nonsense when an LFS binary is not hydrated.

The `mara.html` route pushes the same viewer toward the project's softer illustrative language: lavender paper, cool blue / pink light, toon treatment, outlines, restrained resonance bloom.

---

## ♬ Real models already wired in

The manifest currently points at actual tracked Melodia assets:

- `Content/EnvSandbox/Monoliths/SeaAbove/Prototype/Reef/Meshes/SM_Island_A.obj`
- `Content/EnvSandbox/Monoliths/SeaAbove/Prototype/Reef/Meshes/SM_Island_B.obj`
- `Content/EnvSandbox/Monoliths/SeaAbove/Prototype/Reef/Meshes/SM_Island_C.obj`
- `UpdatedShirt.fbx`

The Sea Above meshes are the reliable browser lane today because OBJ is already tracked and simple to serve.

`UpdatedShirt.fbx` is the Wardrobe / FBX compatibility canary. It may need:

```powershell
git lfs pull
```

before the local server has the real binary instead of an LFS pointer.

---

## 𝄞 The tiny model contract

`models.json` stays deliberately boring and engine-neutral:

```json
{
  "id": "sea_above.island_a",
  "label": "Sea Above — Reef Island A",
  "format": "obj",
  "path": "../../../Content/.../SM_Island_A.obj",
  "source_path": "Content/.../SM_Island_A.obj",
  "category": "environment"
}
```

For future intentional browser exports, prefer **GLB**. Do not convert the entire game repository just because a turntable exists. One lovely Starskiff, outfit mannequin, creature, or chapter diorama at a time is enough.

---

## ♪ A parcel is not an inventory system

The interaction boundary is:

```text
canonical Melodia state
        ↓
UI view model
        ↓
3D page / parcel / charm / thread
        ↓
player clicks it
        ↓
UI intent
        ↓
real owning subsystem performs or refuses the action
```

So:

- a parcel may emit `ui.post.open_requested`; it **cannot grant inventory**;
- an outfit model may emit `ui.wardrobe.inspect_requested`; it **cannot equip itself**;
- a Chapter page may emit `ui.chapter.selected`; it **cannot author progression**.

The Unreal version should keep routing player-facing surfaces through `UMelodiaUIBridgeSubsystem` and the existing Narrative / Wardrobe / reward authorities.

That lets the visual layer get wonderfully strange without becoming another state machine we have to debug at 3 AM.

---

## ♫ The browser family

The Folio has two siblings now:

- `Prototypes/Web/MusicKey3D/` — ♪ the little world-interaction lab;
- `Docs/Tools/puzzle-sandbox/` — 𝄞 **Cymatic Sanctuary**, the 12-instrument Music-as-Key sandbox.

They should feel like three pages from the same art book:

```text
MusicKey3D        = does the world interaction feel right?
Cymatic Sanctuary = how far can the music-key grammar stretch?
Traveling Folio   = how does the game remember and present the journey?
```

Unreal still decides what is real.

---

## ♬ Files

- `index.html` — stable Folio + model-viewer route;
- `mara.html` — stylized art-direction variant;
- `models.json` — tracked-model manifest;
- `mailbox.json` — dev-only local Post / Gift / Reverie fixture.

---

## ♪ Next good experiments

1. Export one intentional **Starskiff GLB** and make it the first proper Folio keepsake.
2. Export one canonical outfit / mannequin GLB.
3. Let a Chapter page unfold into a tiny 3D diorama using real Melodia geometry.
4. Add deterministic `FMelodiaUIIntent`-shaped fixtures that can be compared against UE tests.
5. Make the physical Starskiff parcel shelf and the Folio mailbox consume the same Post view model.
6. Promote the Mara visual language only after comparing it in the browser on the actual workstation.

> **The Folio should feel like the journey left fingerprints on it.** ♫
