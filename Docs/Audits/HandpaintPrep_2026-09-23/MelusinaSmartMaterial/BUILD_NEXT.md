# BUILD_NEXT — parked 2026-09-24 closeout

Ladder parked after M1 + M2 SPEC/plugin (VNP 11 + Resonance Bloom 15).

**Next open:** Painter M2 apply on ZenLantern (see SESSION_CLOSEOUT_2026-09-24_HANDPAINT_LADDER.md).

Console: `import melodia_build_sms_handpaint as m; m.build_sms()`

v4 notes (2026-10-05): shelf SBSAR is now 4,691 B (SlopeBlur + EmissiveGlow + Curvature edge tools). Plugin repointed to the audit tree (KimiWork paths fixed), AO/Curvature mask generators auto-wire on the next `build_sms()` run, 15d still needs INVERT. Still manual: vcol.R/G/A multiplies on 03/04/06/15a, 15b/15c invert.

**Headless staging (2026-10-05):** `SHOWCASE_FBX` now points at Mr. Sheep (`Content\Melodia\Companions\ChoralSheep\choralsheep.fbx`). No `.spp` exists for Mr. Sheep yet and Painter has no headless Python runner — the auto-build env var `MELUSINA_AUTO_BUILD_SMS=1` fires `build_sms()` on plugin start (~20s) once a project/texture set is open. Launch Painter with that env var set (or paste the console one-liner after opening Mr. Sheep): the SMS layer stack + AO/Curvature mask wiring builds itself, then you Create smart material. Note: `vcol_melodia` is a ZenLantern attribute — it is NOT on the sheep mesh, so the AO x vcol.R / Curvature x vcol.G / vcol.A mask multiplies will still be TODO-black on Mr. Sheep unless that channel is baked/painted onto the sheep first. Painter has no vertex-color mesh-map bake, so this must be authored in Blender/UE, not Painter.
