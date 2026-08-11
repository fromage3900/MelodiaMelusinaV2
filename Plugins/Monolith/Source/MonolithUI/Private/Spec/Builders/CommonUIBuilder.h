// Copyright tumourlove. All Rights Reserved.
// CommonUIBuilder.h
//
// Phase H — sub-builder for nodes that opt into the FUISpecCommonUI sub-bag.
// Resolves StyleRefs through the pre-created style class table on the
// FUIBuildContext, applies the resolved class to the widget, then routes
// remaining writes through the standard reflection helper.
//
// Compile-time gated behind WITH_COMMONUI — when CommonUI is absent the
// implementation collapses to a "warn and skip" stub (the widget itself is
// still created via the LeafBuilder/PanelBuilder paths so the spec doesn't
// fully fail).

#pragma once

#include "CoreMinimal.h"

class UWidget;
struct FUIBuildContext;
struct FUISpecNode;

namespace MonolithUI::CommonUIBuilder
{
    /**
     * Apply CommonUI sub-bag fields onto an already-constructed widget.
     * Returns true on success; on failure pushes into Context.Errors.
     *
     * `Widget` is the live widget instance; the dispatcher already constructed
     * it via Panel/Leaf builders. We only handle the CommonUI-specific writes
     * here (style class wiring, input mode tokens).
     */
    bool ApplyCommonUI(
        FUIBuildContext& Context,
        const FUISpecNode& Node,
        UWidget* Widget);
}
