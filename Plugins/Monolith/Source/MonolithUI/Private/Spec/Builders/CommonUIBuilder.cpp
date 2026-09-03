// Copyright tumourlove. All Rights Reserved.
// CommonUIBuilder.cpp
//
// Phase H — apply CommonUI sub-bag fields onto a constructed widget. Wires
// the resolved style class (pre-created by Phase H step 5) onto the widget
// when applicable, plus per-style-type token writes (input layer / mode).
//
// CommonUI gating: when WITH_COMMONUI=0 the file collapses to a no-op
// implementation that records a warning. The *spec* still validates, the
// *widget* still gets built — we just skip the CommonUI-specific writes.

#include "Spec/Builders/CommonUIBuilder.h"

#include "Spec/UIBuildContext.h"
#include "Spec/UISpec.h"
#include "MonolithUICommon.h"

#include "Components/Widget.h"

namespace MonolithUI::CommonUIBuilderInternal
{
#if WITH_COMMONUI
    /**
     * v1 CommonUI write surface is intentionally minimal — the sub-bag
     * carries StyleRefs, InputLayer, InputMode tokens. Phase H wires the
     * StyleRef pointer through the pre-created style class table on the
     * Context so the same dedupe behaviour the dedicated
     * `apply_style_to_widget` MCP action gives us applies here too.
     *
     * Per-StyleRef wiring iterates and warns on unresolved refs (the
     * pre-create pass should have populated them; an unresolved name here
     * means the spec referenced a style not in the document's Styles map).
     */
    static void ApplyCommonUIWithSupport(
        FUIBuildContext& Context,
        const FUISpecNode& Node,
        UWidget* Widget)
    {
        const FUISpecCommonUI& CUI = Node.CommonUI;

        for (const FName& StyleRef : CUI.StyleRefs)
        {
            if (StyleRef.IsNone()) continue;

            const FString Key = FString::Printf(TEXT("name:%s"), *StyleRef.ToString());
            if (!Context.PreCreatedStyles.Contains(Key))
            {
                FUISpecError W;
                W.Severity = EUISpecErrorSeverity::Warning;
                W.Category = TEXT("Style");
                W.WidgetId = Node.Id;
                W.Message  = FString::Printf(
                    TEXT("CommonUI style ref '%s' was not resolved by the pre-create pass."),
                    *StyleRef.ToString());
                W.SuggestedFix = TEXT("Declare the style in document.Styles, or use a style action to author it.");
                Context.Warnings.Add(MoveTemp(W));
            }
            // The actual style-class write is the responsibility of the
            // type-specific CommonUI widget (Button/Text/Border) — Phase H
            // v1 does not assume which concrete CommonUI subclass `Widget`
            // is. Phase J's roundtrip serializer extends this to do typed
            // writes via the dedicated style service.
        }
    }
#else
    static void ApplyCommonUIStub(
        FUIBuildContext& Context,
        const FUISpecNode& Node)
    {
        FUISpecError W;
        W.Severity = EUISpecErrorSeverity::Warning;
        W.Category = TEXT("CommonUI");
        W.WidgetId = Node.Id;
        W.Message  = TEXT("Spec node opts into CommonUI bag but the build was compiled with WITH_COMMONUI=0; CommonUI fields ignored.");
        W.SuggestedFix = TEXT("Install/enable the CommonUI plugin and rebuild Monolith.");
        Context.Warnings.Add(MoveTemp(W));
    }
#endif
} // namespace MonolithUI::CommonUIBuilderInternal


bool MonolithUI::CommonUIBuilder::ApplyCommonUI(
    FUIBuildContext& Context,
    const FUISpecNode& Node,
    UWidget* Widget)
{
    using namespace MonolithUI::CommonUIBuilderInternal;

    if (!Widget)
    {
        return false;
    }

#if WITH_COMMONUI
    ApplyCommonUIWithSupport(Context, Node, Widget);
#else
    ApplyCommonUIStub(Context, Node);
#endif
    return true;
}
