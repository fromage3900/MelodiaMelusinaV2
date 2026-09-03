// Copyright tumourlove. All Rights Reserved.
// PanelBuilder.h
//
// Phase H — sub-builder for multi-child panel widgets (UVerticalBox,
// UHorizontalBox, UCanvasPanel, UOverlay, UWrapBox, UScrollBox, UGridPanel,
// UUniformGridPanel, ...). Constructs the panel widget, attaches it to its
// parent slot, recurses into children. Slot-side property writes (padding,
// alignment, anchors) flow through `FUIReflectionHelper` against the
// parent's slot class.
//
// Lives under Private/ — not part of the public surface; only invoked by
// `FUISpecBuilder` via `BuildNode` dispatch. Header is here only because
// the dispatch table forward-declares the entry point.

#pragma once

#include "CoreMinimal.h"

class UPanelWidget;
class UWidget;
struct FUIBuildContext;
struct FUISpecNode;

namespace MonolithUI::PanelBuilder
{
    /**
     * Build a panel widget from `Node`, attach it under `ParentPanel`, then
     * recurse children. Returns the constructed UWidget* (the panel) on
     * success; nullptr on failure (errors pushed into Context.Errors).
     *
     * `ParentPanel` may be nullptr when this node IS the root of the WBP —
     * the dispatcher routes nullptr to "set as WidgetTree::RootWidget".
     *
     * `WidgetClass` is pre-resolved by the dispatcher so we don't repeat the
     * type-registry lookup here.
     */
    UWidget* BuildPanel(
        FUIBuildContext& Context,
        const FUISpecNode& Node,
        UClass* WidgetClass,
        UPanelWidget* ParentPanel);
}
