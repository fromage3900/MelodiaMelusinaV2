# Melodia MusicKey3D

A browser-side Three.js interaction lab for **music-as-key world puzzles** and the soft watercolor / cel-shaded visual language shown in Mara Elettra Vell concept work.

## Run

From repository root:

```powershell
python -m http.server 8080
```

Open:

```text
http://127.0.0.1:8080/Prototypes/Web/MusicKey3D/
```

## What this prototype is for

- test music-node spatial readability;
- test short phrase sequencing such as `C -> E -> G`;
- prototype barrier feedback and world-unlock presentation;
- prototype Mara/Melodia palette, toon ramp, outline, watercolor floor, bloom, floating particles, water-like hair motion, and musical tendrils;
- export compact JSON for design comparison with the native UE contract;
- give future browser experiments a concrete Melodia visual reference instead of generic Three.js presentation.

## What it does NOT own

This is **not** a second game runtime or puzzle authority.

The native project already has the live music-as-key pillar under `Source/BS_GodFile/Piano/`, including steppable note nodes, pattern scoring, PCG musical content, and the typed narrative bridge.

The browser sandbox may visualize or export proposed puzzle data, but Unreal remains authoritative for gameplay state and persistence.

```text
MusicKey3D interaction
      ↓
prototype phrase / layout / visual feedback
      ↓
compare or author data
      ↓
UE music-as-key implementation
      ↓
UMelodiaPCGNarrativeChallengeBridgeComponent
      ↓
Narrative / world consequence authority
```

## Relationship to `MelodiaFolio3D`

The two browser prototypes are siblings:

- `Prototypes/Web/MusicKey3D/` — **world interaction laboratory**;
- `Prototypes/Web/MelodiaFolio3D/` — **cozy UI / repository-model / evergreen-content laboratory**.

They should converge on one visual family:

- ivory / lavender paper-like surfaces;
- plum ink outlines;
- cool blue and violet shadows;
- sakura-pink accents;
- muted gold highlights;
- toon or illustrative shading rather than generic PBR tech-demo presentation;
- music notation, threads, ribbons, water and handwritten field-note motifs;
- soft bloom used only for resonance / magical state.

## Corrections made while preserving the supplied prototype

The committed version fixes a few runtime hazards from the original one-shot HTML:

- uses `THREE.PCFSoftShadowMap`;
- adds the secondary directional light correctly instead of attempting to add its `position` vector to the scene;
- uses `THREE.RedFormat` for the toon ramp texture;
- preserves barrier outline references when replacing `userData`;
- prevents locked barriers from accumulating vertical drift every frame;
- keeps repeated phrase notes removable one at a time;
- makes clipboard failure non-fatal.

## Next useful experiments

1. Replace the primitive Melusina/Ebenezer proxies with curated GLB exports from the real project.
2. Let `MelodiaFolio3D` reuse this toon/watercolor material language for its model turntable.
3. Add optional sound playback for note nodes without changing the phrase authority model.
4. Add an adapter that can read the existing progression/music-key JSON schema directly.
5. Keep browser export explicitly development-only until a stable schema contract is chosen.
