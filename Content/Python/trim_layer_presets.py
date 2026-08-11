"""Height-aware layer blend presets for ZenTrim / ClothTrim trimsheet instances.

LayerBlendMode: 0=manual LayerBlend, 1=height compete, 2=height+manual mix.
"""
from __future__ import annotations

# Height compete — cracks bite into recessed displacement of Base4K
LERP_HEIGHT_CRACK: dict[str, float] = {
    "LayerBlendMode": 1.0,
    "LayerHeightBias": 0.06,
    "LayerHeightSharpness": 5.5,
    "LayerBlendSoftness": 0.14,
    "LayerNormalBlend": 0.78,
    "LayerRoughnessBlend": 0.88,
    "LayerManualMix": 0.4,
}

LERP_HEIGHT_CRACK_HEAVY: dict[str, float] = {
    "LayerBlendMode": 1.0,
    "LayerHeightBias": 0.1,
    "LayerHeightSharpness": 6.2,
    "LayerBlendSoftness": 0.1,
    "LayerNormalBlend": 0.82,
    "LayerRoughnessBlend": 0.92,
    "LayerManualMix": 0.55,
}

LERP_HEIGHT_CRACK_POM: dict[str, float] = {
    **LERP_HEIGHT_CRACK,
    "LayerHeightSharpness": 5.0,
    "LayerBlendSoftness": 0.16,
    "LayerNormalBlend": 0.8,
}

# Organic flower overlays — soft height falloff, gentle normals
LERP_HEIGHT_FLOWER_LIGHT: dict[str, float] = {
    "LayerBlendMode": 1.0,
    "LayerHeightBias": -0.08,
    "LayerHeightSharpness": 2.6,
    "LayerBlendSoftness": 0.34,
    "LayerNormalBlend": 0.48,
    "LayerRoughnessBlend": 0.62,
    "LayerManualMix": 0.28,
}

LERP_HEIGHT_FLOWER_MID: dict[str, float] = {
    "LayerBlendMode": 1.0,
    "LayerHeightBias": -0.05,
    "LayerHeightSharpness": 3.0,
    "LayerBlendSoftness": 0.28,
    "LayerNormalBlend": 0.55,
    "LayerRoughnessBlend": 0.7,
    "LayerManualMix": 0.38,
}

LERP_HEIGHT_FLOWER_HEAVY: dict[str, float] = {
    "LayerBlendMode": 1.0,
    "LayerHeightBias": -0.02,
    "LayerHeightSharpness": 3.4,
    "LayerBlendSoftness": 0.24,
    "LayerNormalBlend": 0.62,
    "LayerRoughnessBlend": 0.75,
    "LayerManualMix": 0.5,
}

# Wet sheen — height pools + manual gloss control
LERP_HEIGHT_WET: dict[str, float] = {
    "LayerBlendMode": 2.0,
    "LayerHeightBias": 0.12,
    "LayerHeightSharpness": 4.2,
    "LayerBlendSoftness": 0.22,
    "LayerNormalBlend": 0.68,
    "LayerRoughnessBlend": 1.0,
    "LayerManualMix": 0.58,
}

# Colour wash — even height-aware tint over stone base
LERP_HEIGHT_COLOUR: dict[str, float] = {
    "LayerBlendMode": 1.0,
    "LayerHeightBias": 0.0,
    "LayerHeightSharpness": 3.5,
    "LayerBlendSoftness": 0.26,
    "LayerNormalBlend": 0.72,
    "LayerRoughnessBlend": 0.75,
    "LayerManualMix": 0.42,
}

# Cloth trims — fabric-friendly blends (embroidery height, satin sheen)
LERP_CLOTH_DEFAULT: dict[str, float] = {
    "LayerBlendMode": 1.0,
    "LayerHeightBias": -0.04,
    "LayerHeightSharpness": 3.2,
    "LayerBlendSoftness": 0.3,
    "LayerNormalBlend": 0.58,
    "LayerRoughnessBlend": 0.72,
    "LayerManualMix": 0.45,
}

LERP_CLOTH_EMBROIDERY: dict[str, float] = {
    "LayerBlendMode": 1.0,
    "LayerHeightBias": 0.08,
    "LayerHeightSharpness": 4.5,
    "LayerBlendSoftness": 0.2,
    "LayerNormalBlend": 0.72,
    "LayerRoughnessBlend": 0.65,
    "LayerManualMix": 0.5,
}

LERP_CLOTH_SATIN: dict[str, float] = {
    "LayerBlendMode": 2.0,
    "LayerHeightBias": 0.05,
    "LayerHeightSharpness": 3.8,
    "LayerBlendSoftness": 0.25,
    "LayerNormalBlend": 0.55,
    "LayerRoughnessBlend": 0.95,
    "LayerManualMix": 0.52,
}

LERP_CLOTH_FRAY: dict[str, float] = {
    "LayerBlendMode": 1.0,
    "LayerHeightBias": 0.12,
    "LayerHeightSharpness": 5.0,
    "LayerBlendSoftness": 0.18,
    "LayerNormalBlend": 0.75,
    "LayerRoughnessBlend": 0.82,
    "LayerManualMix": 0.48,
}


def merge_scalars(base: dict[str, float], preset: dict[str, float]) -> dict[str, float]:
    out = dict(base)
    out.update(preset)
    return out


def zen_layer_preset(layer_b: str, *, heavy: bool = False) -> dict[str, float]:
    if layer_b == "CrackedToHell":
        return dict(LERP_HEIGHT_CRACK_HEAVY if heavy else LERP_HEIGHT_CRACK)
    if layer_b == "FlowersLIttleBit":
        return dict(LERP_HEIGHT_FLOWER_LIGHT)
    if layer_b == "FlowersMid":
        return dict(LERP_HEIGHT_FLOWER_MID)
    if layer_b == "FlowersLOTS":
        return dict(LERP_HEIGHT_FLOWER_HEAVY)
    if layer_b == "Wet":
        return dict(LERP_HEIGHT_WET)
    if layer_b == "ColourShift":
        return dict(LERP_HEIGHT_COLOUR)
    return dict(LERP_HEIGHT_COLOUR)


def cloth_layer_preset(variant: str) -> dict[str, float]:
    key = variant.lower()
    if "embroid" in key or "stitch" in key or "gold" in key:
        return dict(LERP_CLOTH_EMBROIDERY)
    if "satin" in key or "silk" in key or "sheen" in key:
        return dict(LERP_CLOTH_SATIN)
    if "fray" in key or "worn" in key or "tear" in key:
        return dict(LERP_CLOTH_FRAY)
    if "lace" in key:
        return dict(LERP_CLOTH_DEFAULT) | {"LayerHeightSharpness": 4.0, "LayerBlendSoftness": 0.22}
    return dict(LERP_CLOTH_DEFAULT)
