# BUILD_NEXT — parked 2026-09-24 closeout

Ladder parked after M1 + M2 SPEC/plugin (VNP 11 + Resonance Bloom 15).

**Next open:** Painter M2 apply on ZenLantern (see SESSION_CLOSEOUT_2026-09-24_HANDPAINT_LADDER.md).

Console: `import melodia_build_sms_handpaint as m; m.build_sms()`

v4 notes (2026-10-05): shelf SBSAR is now 4,691 B (SlopeBlur + EmissiveGlow + Curvature edge tools). Plugin repointed to the audit tree (KimiWork paths fixed), AO/Curvature mask generators auto-wire on the next `build_sms()` run, 15d still needs INVERT. Still manual: vcol.R/G/A multiplies on 03/04/06/15a, 15b/15c invert.

**Headless staging (2026-10-05):** `SHOWCASE_FBX` now points at Mr. Sheep (`Content\Melodia\Companions\ChoralSheep\choralsheep.fbx`). No `.spp` exists for Mr. Sheep yet and Painter has no headless Python runner — the auto-build env var `MELUSINA_AUTO_BUILD_SMS=1` fires `build_sms()` on plugin start (~20s) once a project/texture set is open. Launch Painter with that env var set (or paste the console one-liner after opening Mr. Sheep): the SMS layer stack + AO/Curvature mask wiring builds itself, then you Create smart material. Note: `vcol_melodia` is a ZenLantern attribute — it is NOT on the sheep mesh, so the AO x vcol.R / Curvature x vcol.G / vcol.A mask multiplies will still be TODO-black on Mr. Sheep unless that channel is baked/painted onto the sheep first. Painter has no vertex-color mesh-map bake, so this must be authored in Blender/UE, not Painter.

**vcol bake DONE (2026-10-05):** ran `Saved/Audit/choral_sheep/author_vcol_melodia_sheep.py` in headless Blender 4.5 (Blender 5.2's `--background --python-expr` hangs here). Wrote `Content/Melodia/Companions/ChoralSheep/choralsheep_vcol_melodia.fbx` (52,652 B, verified re-import carries `vcol_melodia`) + `choralsheep_vcol_melodia_receipt.json`. Lanes: R = BVH occlusion cavity proxy, G = 0 (manual), B = normalized world Z, A = sampled from `choralsheepbase_Emission.png` via UV (4096²). NOTE: Blender 5.2 hangs on headless python-expr in this environment — use Blender 4.5 for sheep headless work. When the sheep FBX is loaded in Painter, the FBX color layer is visible on the mesh but Painter still won't expose it as a mask generator — the AO/Curvature wiring from the plugin remains the live Painter mask path; vcol serves UE/UE-material lanes.
