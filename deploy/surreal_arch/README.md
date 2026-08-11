# Melodia Studio

Procedural architecture, ornament, and music-motif generator for Blender 5.1. Generates geometry via Geometry Nodes, exports flat FBX for Unreal/UE5, and includes stage visibility controls meant for portfolio and kitbash workflows.

**Product:** Melodia Studio
**Module id:** `melodia_studio`
**Operators:** `surreal_arch.*`
**Install folder:** `surreal_arch/`

---

## Install

1. Copy the folder `deploy/surreal_arch/` into Blender’s addons directory:
   - `%APPDATA%\Blender Foundation\Blender\5.1\scripts\addons\surreal_arch\`
2. In Blender: `Edit → Preferences → Add-ons → Search "Melodia Studio" → Enable`.
3. If you had the old `surreal_architecture_gen` addon enabled before, your Higgsas/Synthia paths migrate automatically on first enable.

---

## First generation

1. Open `Melodia_Portfolio_Stage_v4.blend` or any `.blend` with a mesh object selected.
2. Press `N` → `Melodia Studio` tab.
3. Use **Architecture Picker** to choose an arch type, then press **Generate**.
4. For music/ornament motifs, route through the Melodia GN path in the Genome Carousel.

---

## N-panel tour

- **Genome Carousel** — top-level panel; generate, starlight stage preset, solo object.
- **Architecture Picker** — search/filtered browser for arch types, style genomes, and categories.
- **Level Design** — greybox room tools, trim modes, snap metadata, QA validation.
- **Style Genome (OS)** — active genome, catalog, apply/spawn graph.
- **UV / Trimsheet** — UV proxy, MioUV / UVPM pack, bake trim colors.
- **Asset Browser** — publish greybox assets, export catalog enum stub.
- **Research presets** — romanesque, brutalist, venetian, scifi airlock presets.
- **Export** — UE5 bake/export, snap JSON, trim attributes, Beavel Pro.
- **Viewport** — toggle snap overlay.

---

## Known limitations

- Melodia Studio is a Blender 5.1 addon. Other Blender versions are not supported.
- Optional dependencies are not required for core generation: Higgsas, Synthia, Beavel Pro, Sverchok, and MioUV/UVPM unlock additional workflows but are not installed by default.
- `NOTE_HEAD` and `SHEET_MUSIC_RAIL` Melodia GN bake may require Blender 5.1-specific Vector/Translation API handling; verify in your environment before relying on it for productionFBX export.
- FILIGREE_* monolith rewrites are deferred post-v1. If your workflow depends on filigree generators, treat them as planned, not shipped.

---

## Support

For project context, see:
- `Docs/MELODIA_STUDIO_SHIP_CHECKLIST.md`
- `Docs/BLENDER_MELODIA_COCKPIT.md`
- `Docs/HANDOFF_SURREAL_TO_MELODIA_SYSTEM_2026-07-12.md`