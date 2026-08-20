"""Add per-column MaterialExpressionComment notes to the four Melodia masters.

For every group in the canonical scheme (master_column_scheme.py) this script
creates a MaterialExpressionComment box labelled "MELODIA_COLUMN: <group>" with
a usage note, sized to the bounding box of the group's parameter nodes in the
graph editor. Idempotent: existing MELODIA_COLUMN comments are removed first
and only OUR comments are touched.

Usage note text is derived per group label from a small dictionary; groups not
in the dictionary fall back to their label.

Run in the UE editor (Monolith editor_query run_python):
  Content/Python/annotate_master_columns.py
"""
from __future__ import annotations

import importlib
import json

import unreal

MASTERS = {
    "M_Master_Toon_Universal": "/Game/EnvSandbox/Materials/Masters/M_Master_Toon_Universal",
    "M_Master_Toon_Landscape_HeightBlend": "/Game/EnvSandbox/Materials/Masters/M_Master_Toon_Landscape_HeightBlend",
    "M_Master_Nikki": "/Game/EnvSandbox/Materials/Masters/M_Master_Nikki",
    "M_Master_Nikki_Landscape": "/Game/EnvSandbox/Materials/Masters/M_Master_Nikki_Landscape",
}

TAG = "MELODIA_COLUMN:"

# Per-column usage notes. Keyed by the group label WITHOUT the "NN | " prefix.
NOTES: dict[str, str] = {
    "Base Surface": "Master tint / UV / roughness-metallic base. UVScale + UVRotation/Offset are the mesh-space controls; everything above builds on this column.",
    "Triplanar": "World-aligned projection. bTriplanar_Active gates the lane (default OFF); slope mask + per-channel blend weights control how much world-space detail mixes with Layer A UVs.",
    "Texture Layer A": "Base PBR layer: Albedo/Normal/ORM/Height with separate Roughness/Metallic switches and an EmissiveMap. TextureWeight blends A over the flat base tint.",
    "Texture Layer B": "Second PBR layer blended over A by height (LayerBlend/HeightBias/Sharpness) or manual mix. The height-competition suite (AO/Color/Metallic/Height blend weights) lives here.",
    "Texture Layer C": "Third PBR layer stacked over A->B sequentially. Same blend suite as Layer B; bLayerC_Active gates it entirely.",
    "Parallax": "POM depth. ParallaxStrength/Scale/Height drive the offset; NormalStrength/Power reshape the sampled normal after the offset.",
    "Macro & Detail": "World-consistent macro breakup (WorldPosition-based, NOT UV — fixes per-mesh scale weirdness) plus a DetailNormal overlay.",
    "Temporal / Ink": "Animated UV boil / smear / wind for hand-drawn ink feel. All default 0; TemporalStrength is the master gate.",
    "Color Ramp": "Unified ramp implementation (MF_ColorRamp3 family): low/mid/high + contrast. RampStrength=0 bypasses. ShadowRamp variants tint the shadow band separately.",
    "Nikki Rim & Glow": "Signature toon rim: RimColor/Power/Width/Bias/Clamp, inner+outer glow, DreamRim variant with its own bloom band. bNikkiHero enables the hero-grade path.",
    "Nikki Dream Grade": "Dreamy color grade: pastel lift, saturation/contrast, shadow lift, dream warmth, flow + pulse animation. DreamIntensity gates the family.",
    "Nikki Sparkle": "Sparkle glint overlay on bright areas (SparkleMask alpha, threshold, drift/twinkle speed). bSparkleAdvanced enables color-lerped sparkles.",
    "Nikki Iridescence & Sheen": "Premium cloth/skin sheen: fresnel iridescence (RoughnessAtten) + anisotropic fabric sheen. bSheenUsesNormal picks normal-driven sheen.",
    "Gilding": "Curvature-driven gold leaf on edges: Strength + GoldTint/Roughness/Emissive. CurvatureSensitivity tunes the edge mask.",
    "Shadow Garden (Flowers)": "Animated petal shadow field projected onto the surface (strength/scale/color).",
    "Shadow Dream": "Custom N.L shadow band grading: tint + strength + softness for dreamy cel shadows.",
    "Celestial (Nebula)": "Space parallax: constellation ramp, star intensity/twinkle, nebula + galaxy arms. bCelestial_Active gates (default OFF).",
    "Fairy Dust": "Motif overlays (star/heart/moon/flower) on highlighted areas, driven by FairyGlyphMask + threshold.",
    "Magical (Henshin)": "Transform wipe + palette shift (MagicalTransform 0..1 drives the transition). MotifMask/Scale place the glyph.",
    "VeinGlow (Madoka)": "Voronoi vein glow + radial witch rings. Emissive lanes additive; MadokaBlendAmount is the master gate (MF_Madoka lane).",
    "InkWear (Itto)": "Procedural cracks/ink wear breakup (Truchet + wear masks). IttoBlendAmount is the master gate (MF_Itto lane).",
    "Impasto": "Paint-thickness relief via StrokeMask + Height for painterly surfaces. bImpasto_Active gates.",
    "Sigil": "Animated radial sigil/mandala overlay (sides/rings/speed/sharpness) for magical floors.",
    "Dawn & Mist": "Time-of-day dawn band (height-based sky tint) + drifting mist streaks.",
    "Glint & Halo": "High-frequency sparkle glints + fresnel halo ring. GlintStrength/HaloStrength gate.",
    "Character & SDF": "Skin SSS + face SDF depth fields (Strength/Tiling, bFaceSDF_UV1 picks UV1).",
    "Elemental": "Element type selector + emissive boost for element-themed props.",
    "World / Weather": "Wetness (darken + normal flatten), snow dust (up-bias mask), moss (concavity mask). bWeather_Active gates.",
    "Time of Day": "UDS/MPC-driven warmth hook (UseUDSTimeOfDay + TimeOfDayMPCStrength).",
    "Cinematic": "Contact rim, distance fade, dither dissolve with edge glow — used by hero/transition instances.",
    "DF Contact Blend": "Distance-field contact blending against terrain/seams: DFContactBlend distance/sharpness/strength + SDF seam blend.",
    "Gemstone & Stack": "Gemstone layer stack (IOR/dispersion/chromatic) with Stack2/3 albedo-normal-ORM layers.",
    "Mesh Blend": "MeshBlend activator + auto-blend IDs for per-mesh material blending.",
    "Global": "Project-global MPC-driven boosts (emissive/sparkle) + Melusina palette constants.",
    "Legacy / Diagnostic": "Dead/diagnostic leftovers — candidates for the unused-expression sweep.",
    "Palette": "Per-layer tint palette for the four terrain layers (Rock/Grass/Mud/Path) + snow + water-align tint.",
    "Blend": "Landscape blend engine: height-dot competition (HeightBlendStrength), painted-vs-procedural switch, UV mode.",
    "Layer PBR": "Painted terrain layer maps (albedo/normal/height per layer). ORM is packed-neutral until authored ORM imports.",
    "Surface": "Terrain surface response: layer roughness, normal strength, wetness.",
    "Macro": "Landscape macro breakup (world-space) per-layer strengths.",
    "Snow": "Snow cover by slope/up-bias.",
    "Path": "Path wear mask + strength for the Path overlay layer.",
    "Shore": "Shore wetness boost + water-palette alignment near water.",
    "Layer Ramp": "Landscape-specific ramp (low/mid/high/strength/driver) over the height competition.",
    "Atmospheric": "Distance atmosphere fade for the terrain (start/end/strength/color).",
    "Audio Reactive": "MPC-driven audio reactivity strength for rhythm-reactive terrain.",
    "Textures": "Nikki surface PBR slots (Albedo/Normal/ORM/Height).",
    "Atmosphere": "Depth-based atmosphere fade for Nikki surfaces.",
    "Emissive": "Nikki signature self-glow: EmissiveStrength + EmissiveFloor.",
    "Nikki Iridescence & Sheen": "Nikki-surface iridescence + fabric sheen modulators.",
    "Nikki Sticker Shade": "Anime sticker/cel flattening (bands + softness). Default OFF.",
    "Nikki Twinkle Iris": "Iridescent twinkle + pastel fabric sheen. Default ON.",
    "Nikki Pastel Grade": "Pastel grade: sakura ramp + dream bloom. Default ON.",
    "Nikki SDF Ribbon": "SDF band ribbon on silhouettes (scale/sharpness/edge). Default OFF.",
    "Nikki Pearl Sheen": "Dual-layer pearlescent sheen. Default OFF.",
    "Nikki Dream Watercolor": "Watercolor bleed in shadows (hue-rotating noise). Default OFF.",
    "Nikki Sticker Edge": "Anime sticker edge-light (Fwidth band + pastel rim). Default OFF.",
    "Nikki Glitter Halo": "World-aligned hash glitter + fresnel halo. Default OFF.",
    "Nikki Petal Shadow": "Blooming petal shadow field. Default OFF.",
    "Kawaii Squish": "Breathing WPO squish (sin*bob). bKawaiiSquish_Active + bNikkiSquishWPO_Active.",
    "Layer Textures": "Nikki-landscape painted layer maps (Rock/Ground/Grass, _NormalMap naming).",
    "Layer Surface": "Per-layer UV scale + roughness for the Nikki landscape variant.",
}


def note_for(label: str) -> str:
    for prefix, note in NOTES.items():
        if label.endswith(prefix):
            return note
    return f"{label} — see parameter tooltips."


def annotate_one(material_path: str, stem: str, boxes: dict[str, dict]) -> dict:
    import master_column_scheme as scheme

    scheme = importlib.reload(scheme)
    groups = scheme.groups_for(stem)

    material = unreal.load_asset(material_path)
    if material is None:
        return {"asset": material_path, "error": "load_failed"}

    exprs = unreal.MaterialEditingLibrary.get_material_expressions(material) or []
    # 1) Remove OUR previous comments plus empty stray comments (probe debris).
    removed = 0
    for e in exprs:
        if e.get_class().get_name() != "MaterialExpressionComment":
            continue
        try:
            text = str(e.get_editor_property("text") or "")
        except Exception:
            text = ""
        if text.startswith(TAG) or text.strip() == "":
            unreal.MaterialEditingLibrary.delete_material_expression(material, e)
            removed += 1

    # 2) Create one comment box per column using the precomputed rectangles
    #    (Tools/compute_column_boxes.py — node positions come from Monolith).
    created = 0
    for label, _names in groups:
        box = boxes.get(label)
        if not box:
            continue
        comment = unreal.MaterialEditingLibrary.create_material_expression(
            material, unreal.MaterialExpressionComment, box["x"], box["y"]
        )
        if comment is None:
            continue
        comment.set_editor_property("text", f"{TAG}{label}\n{note_for(label)}")
        try:
            comment.set_editor_property("comment_color", (0.06, 0.09, 0.14, 1.0))
        except Exception:
            pass
        created += 1

    unreal.MaterialEditingLibrary.recompile_material(material)
    unreal.EditorAssetLibrary.save_loaded_asset(material, only_if_is_dirty=False)
    unreal.log(f"[annotate_columns] {stem}: removed={removed} created={created}")
    return {"asset": material_path, "removed": removed, "created": created}


def main() -> int:
    import json as _json
    from pathlib import Path

    boxes_file = Path(__file__).resolve().parents[2] / "Saved" / "Audit" / "column_boxes.json"
    if not boxes_file.exists():
        unreal.log_error("[annotate_columns] column_boxes.json missing — run Tools/compute_column_boxes.py first")
        print("ANNOTATE_COLUMNS_RESULT []")
        return 1
    payload = _json.loads(boxes_file.read_text(encoding="utf-8"))
    boxes_by_master = {stem: (entry or {}).get("boxes", {}) for stem, entry in payload["masters"].items()}

    results = []
    for stem, path in MASTERS.items():
        try:
            results.append(annotate_one(path, stem, boxes_by_master.get(stem, {})))
        except Exception as exc:  # noqa: BLE001
            unreal.log_error(f"[annotate_columns] {stem}: {exc}")
            results.append({"asset": path, "error": str(exc)})
    print(f"ANNOTATE_COLUMNS_RESULT {json.dumps(results, default=str)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
