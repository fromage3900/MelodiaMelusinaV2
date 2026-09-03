// Copyright tumourlove. All Rights Reserved.
#pragma once

#include "CoreMinimal.h"
#include "MonolithToolRegistry.h"

/**
 * MonolithUI -- parameter-driven box-shadow compositor.
 *
 * apply_box_shadow inserts one or two sibling UImage widgets BEHIND a target
 * widget in an authored UMG tree. Each shadow sibling receives a transient
 * UMaterialInstanceDynamic parented to a CALLER-SUPPLIED shadow material. Zero
 * compile-time dep on any specific shadow material -- the parent must expose
 * (at minimum) a ShadowColor vector + BlurRadius scalar param. Optional
 * scalars: Spread, Inset. Optional vectors: Offset, ShadowSize.
 *
 * Multi-layer shadows (CSS `box-shadow: A, B, C`) are capped at 2 layers per
 * the design budget; additional layers are dropped with a warning.
 *
 * Editor-only -- UBaseWidgetBlueprint::WidgetTree is WITH_EDITORONLY_DATA.
 */
namespace MonolithUI
{
    struct FShadowActions
    {
        static void Register(FMonolithToolRegistry& Registry);

        static FMonolithActionResult HandleApplyBoxShadow(const TSharedPtr<FJsonObject>& Params);
    };
}
