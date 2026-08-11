// Copyright tumourlove. All Rights Reserved.
// LeafBuilder.h
//
// Phase H — sub-builder for leaf widgets that hold no children (UTextBlock,
// UImage, USpacer, UProgressBar, USlider, ...) and content widgets that hold
// at most one child (UBorder, USizeBox, UScaleBox, ...). Construction +
// content-bag write; for content widgets we recurse the (possibly empty)
// single child via the dispatcher.

#pragma once

#include "CoreMinimal.h"

class UPanelWidget;
class UWidget;
struct FUIBuildContext;
struct FUISpecNode;

namespace MonolithUI::LeafBuilder
{
    /** Build a leaf or content widget; attach under ParentPanel. */
    UWidget* BuildLeafOrContent(
        FUIBuildContext& Context,
        const FUISpecNode& Node,
        UClass* WidgetClass,
        UPanelWidget* ParentPanel);
}
