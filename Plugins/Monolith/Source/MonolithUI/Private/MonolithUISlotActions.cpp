// MonolithUISlotActions.cpp
#include "MonolithUISlotActions.h"
#include "MonolithUIInternal.h"
#include "MonolithParamSchema.h"

void FMonolithUISlotActions::RegisterActions(FMonolithToolRegistry& Registry)
{
    Registry.RegisterAction(
        TEXT("ui"), TEXT("set_slot_property"),
        TEXT("Set a slot property on a widget (anchors, offsets, padding, alignment, z-order)"),
        FMonolithActionHandler::CreateStatic(&HandleSetSlotProperty),
        FParamSchemaBuilder()
            .RequiredAssetPath(TEXT("asset_path"), TEXT("Widget Blueprint asset path"))
            .Required(TEXT("widget_name"), TEXT("string"), TEXT("Target widget name"))
            .Optional(TEXT("anchors"), TEXT("object"), TEXT("Canvas anchors: {\"min_x\":0, \"min_y\":0, \"max_x\":1, \"max_y\":1}"))
            .Optional(TEXT("offsets"), TEXT("object"), TEXT("Canvas offsets: {\"left\":0, \"top\":0, \"right\":0, \"bottom\":0}"))
            .Optional(TEXT("position"), TEXT("object"), TEXT("Canvas position: {\"x\":0, \"y\":0}"))
            .Optional(TEXT("size"), TEXT("object"), TEXT("Canvas size: {\"x\":200, \"y\":50}"))
            .Optional(TEXT("alignment"), TEXT("object"), TEXT("Canvas alignment: {\"x\":0.5, \"y\":0.5}"))
            .Optional(TEXT("z_order"), TEXT("integer"), TEXT("Canvas z-order"))
            .Optional(TEXT("auto_size"), TEXT("boolean"), TEXT("Canvas auto-size"))
            .Optional(TEXT("h_align"), TEXT("string"), TEXT("Horizontal alignment: Left, Center, Right, Fill"))
            .Optional(TEXT("v_align"), TEXT("string"), TEXT("Vertical alignment: Top, Center, Bottom, Fill"))
            .Optional(TEXT("padding"), TEXT("object"), TEXT("Slot padding: {\"left\":0, \"top\":0, \"right\":0, \"bottom\":0}"))
            .Optional(TEXT("compile"), TEXT("boolean"), TEXT("Compile after setting"), TEXT("false"))
            .Build()
    );

    Registry.RegisterAction(
        TEXT("ui"), TEXT("set_anchor_preset"),
        TEXT("Set anchor to a named preset (center, top_left, stretch_fill, etc.)"),
        FMonolithActionHandler::CreateStatic(&HandleSetAnchorPreset),
        FParamSchemaBuilder()
            .RequiredAssetPath(TEXT("asset_path"), TEXT("Widget Blueprint asset path"))
            .Required(TEXT("widget_name"), TEXT("string"), TEXT("Target widget name"))
            .Required(TEXT("preset"), TEXT("string"), TEXT("Preset name: top_left, top_center, top_right, center_left, center, center_right, bottom_left, bottom_center, bottom_right, stretch_horizontal, stretch_vertical, stretch_fill, stretch_top, stretch_bottom, stretch_left, stretch_right"))
            .Optional(TEXT("compile"), TEXT("boolean"), TEXT("Compile after setting"), TEXT("false"))
            .Build()
    );

    Registry.RegisterAction(
        TEXT("ui"), TEXT("move_widget"),
        TEXT("Move a widget to a different parent panel"),
        FMonolithActionHandler::CreateStatic(&HandleMoveWidget),
        FParamSchemaBuilder()
            .RequiredAssetPath(TEXT("asset_path"), TEXT("Widget Blueprint asset path"))
            .Required(TEXT("widget_name"), TEXT("string"), TEXT("Widget to move"))
            .Required(TEXT("new_parent_name"), TEXT("string"), TEXT("New parent panel name"))
            .Optional(TEXT("compile"), TEXT("boolean"), TEXT("Compile after moving"), TEXT("true"))
            .Build()
    );
}

// --- set_slot_property ---
FMonolithActionResult FMonolithUISlotActions::HandleSetSlotProperty(const TSharedPtr<FJsonObject>& Params)
{
    FString AssetPath = Params->GetStringField(TEXT("asset_path"));
    FString WidgetName = Params->GetStringField(TEXT("widget_name"));

    FMonolithActionResult Err;
    UWidgetBlueprint* WBP = MonolithUIInternal::LoadWidgetBlueprint(AssetPath, Err);
    if (!WBP) return Err;

    UWidget* Widget = WBP->WidgetTree->FindWidget(FName(*WidgetName));
    if (!Widget)
    {
        // Phase K
        FUISpecError E = MonolithUIInternal::MakeSpecError(
            TEXT("Lookup"),
            TEXT("/widget_name"),
            FString::Printf(TEXT("Widget '%s' not found in WBP '%s'."), *WidgetName, *AssetPath),
            TEXT("Call ui::get_widget_tree to enumerate live widget names."));
        E.WidgetId = FName(*WidgetName);
        return MonolithUIInternal::MakeErrorFromSpecError(E);
    }

    UPanelSlot* Slot = Widget->Slot;
    if (!Slot)
    {
        // Phase K — root widget has no slot. Common LLM mistake; suggested_fix
        // calls out the typical cause.
        FUISpecError E = MonolithUIInternal::MakeSpecError(
            TEXT("Slot"),
            TEXT("/widget_name"),
            FString::Printf(TEXT("Widget '%s' has no slot — likely the WidgetTree root."), *WidgetName),
            TEXT("Slot properties only apply to non-root widgets. Use a parent panel and address its child."));
        E.WidgetId = FName(*WidgetName);
        return MonolithUIInternal::MakeErrorFromSpecError(E);
    }

    int32 PropsSet = 0;

    if (UCanvasPanelSlot* CS = Cast<UCanvasPanelSlot>(Slot))
    {
        const TSharedPtr<FJsonObject>* AnchorObj = nullptr;
        if (Params->TryGetObjectField(TEXT("anchors"), AnchorObj))
        {
            FAnchors A(
                (*AnchorObj)->GetNumberField(TEXT("min_x")),
                (*AnchorObj)->GetNumberField(TEXT("min_y")),
                (*AnchorObj)->GetNumberField(TEXT("max_x")),
                (*AnchorObj)->GetNumberField(TEXT("max_y"))
            );
            CS->SetAnchors(A);
            PropsSet++;
        }

        const TSharedPtr<FJsonObject>* OffsetObj = nullptr;
        if (Params->TryGetObjectField(TEXT("offsets"), OffsetObj))
        {
            FMargin Offsets(
                (*OffsetObj)->GetNumberField(TEXT("left")),
                (*OffsetObj)->GetNumberField(TEXT("top")),
                (*OffsetObj)->GetNumberField(TEXT("right")),
                (*OffsetObj)->GetNumberField(TEXT("bottom"))
            );
            CS->SetOffsets(Offsets);
            PropsSet++;
        }

        const TSharedPtr<FJsonObject>* PosObj = nullptr;
        if (Params->TryGetObjectField(TEXT("position"), PosObj))
        {
            CS->SetPosition(FVector2D((*PosObj)->GetNumberField(TEXT("x")), (*PosObj)->GetNumberField(TEXT("y"))));
            PropsSet++;
        }

        const TSharedPtr<FJsonObject>* SizeObj = nullptr;
        if (Params->TryGetObjectField(TEXT("size"), SizeObj))
        {
            CS->SetSize(FVector2D((*SizeObj)->GetNumberField(TEXT("x")), (*SizeObj)->GetNumberField(TEXT("y"))));
            PropsSet++;
        }

        const TSharedPtr<FJsonObject>* AlignObj = nullptr;
        if (Params->TryGetObjectField(TEXT("alignment"), AlignObj))
        {
            CS->SetAlignment(FVector2D((*AlignObj)->GetNumberField(TEXT("x")), (*AlignObj)->GetNumberField(TEXT("y"))));
            PropsSet++;
        }

        if (Params->HasField(TEXT("z_order")))
        {
            CS->SetZOrder(static_cast<int32>(Params->GetNumberField(TEXT("z_order"))));
            PropsSet++;
        }

        if (Params->HasField(TEXT("auto_size")))
        {
            CS->SetAutoSize(Params->GetBoolField(TEXT("auto_size")));
            PropsSet++;
        }
    }

    // Alignment for box/overlay slots
    FString HAlign = Params->GetStringField(TEXT("h_align"));
    FString VAlign = Params->GetStringField(TEXT("v_align"));
    auto ParseHAlign = [](const FString& S) -> EHorizontalAlignment {
        if (S == TEXT("Left")) return HAlign_Left;
        if (S == TEXT("Center")) return HAlign_Center;
        if (S == TEXT("Right")) return HAlign_Right;
        return HAlign_Fill;
    };
    auto ParseVAlign = [](const FString& S) -> EVerticalAlignment {
        if (S == TEXT("Top")) return VAlign_Top;
        if (S == TEXT("Center")) return VAlign_Center;
        if (S == TEXT("Bottom")) return VAlign_Bottom;
        return VAlign_Fill;
    };

    if (UVerticalBoxSlot* VS = Cast<UVerticalBoxSlot>(Slot))
    {
        if (!HAlign.IsEmpty()) { VS->SetHorizontalAlignment(ParseHAlign(HAlign)); PropsSet++; }
        if (!VAlign.IsEmpty()) { VS->SetVerticalAlignment(ParseVAlign(VAlign)); PropsSet++; }
    }
    else if (UHorizontalBoxSlot* HS = Cast<UHorizontalBoxSlot>(Slot))
    {
        if (!HAlign.IsEmpty()) { HS->SetHorizontalAlignment(ParseHAlign(HAlign)); PropsSet++; }
        if (!VAlign.IsEmpty()) { HS->SetVerticalAlignment(ParseVAlign(VAlign)); PropsSet++; }
    }
    else if (UOverlaySlot* OS = Cast<UOverlaySlot>(Slot))
    {
        if (!HAlign.IsEmpty()) { OS->SetHorizontalAlignment(ParseHAlign(HAlign)); PropsSet++; }
        if (!VAlign.IsEmpty()) { OS->SetVerticalAlignment(ParseVAlign(VAlign)); PropsSet++; }
    }

    // Padding
    const TSharedPtr<FJsonObject>* PadObj = nullptr;
    if (Params->TryGetObjectField(TEXT("padding"), PadObj))
    {
        FMargin Pad(
            (*PadObj)->GetNumberField(TEXT("left")),
            (*PadObj)->GetNumberField(TEXT("top")),
            (*PadObj)->GetNumberField(TEXT("right")),
            (*PadObj)->GetNumberField(TEXT("bottom"))
        );
        if (UVerticalBoxSlot* VS = Cast<UVerticalBoxSlot>(Slot)) { VS->SetPadding(Pad); PropsSet++; }
        else if (UHorizontalBoxSlot* HS = Cast<UHorizontalBoxSlot>(Slot)) { HS->SetPadding(Pad); PropsSet++; }
        else if (UOverlaySlot* OS = Cast<UOverlaySlot>(Slot)) { OS->SetPadding(Pad); PropsSet++; }
    }

    if (PropsSet == 0)
    {
        // Phase K — surface the legal property keys in valid_options so the
        // LLM doesn't have to retry guess-by-guess.
        return MonolithUIInternal::MakeErrorFromSpecError(MonolithUIInternal::MakeSpecError(
            TEXT("MissingInput"),
            TEXT("/"),
            TEXT("No slot properties were set. Provide at least one slot property parameter."),
            TEXT("Pass one or more of the listed parameter keys with the appropriate JSON shape."),
            { TEXT("anchors"), TEXT("offsets"), TEXT("position"), TEXT("size"), TEXT("alignment"),
              TEXT("z_order"), TEXT("auto_size"), TEXT("h_align"), TEXT("v_align"), TEXT("padding") }));
    }

    FBlueprintEditorUtils::MarkBlueprintAsModified(WBP);

    bool bCompile = false;
    if (Params->HasField(TEXT("compile"))) bCompile = Params->GetBoolField(TEXT("compile"));
    if (bCompile) FKismetEditorUtilities::CompileBlueprint(WBP);

    TSharedPtr<FJsonObject> Result = MakeShared<FJsonObject>();
    Result->SetStringField(TEXT("widget"), WidgetName);
    Result->SetStringField(TEXT("slot_type"), Slot->GetClass()->GetName());
    Result->SetNumberField(TEXT("properties_set"), PropsSet);
    Result->SetBoolField(TEXT("compiled"), bCompile);
    return FMonolithActionResult::Success(Result);
}

// --- set_anchor_preset ---
FMonolithActionResult FMonolithUISlotActions::HandleSetAnchorPreset(const TSharedPtr<FJsonObject>& Params)
{
    FString AssetPath = Params->GetStringField(TEXT("asset_path"));
    FString WidgetName = Params->GetStringField(TEXT("widget_name"));
    FString Preset = Params->GetStringField(TEXT("preset"));

    FMonolithActionResult Err;
    UWidgetBlueprint* WBP = MonolithUIInternal::LoadWidgetBlueprint(AssetPath, Err);
    if (!WBP) return Err;

    UWidget* Widget = WBP->WidgetTree->FindWidget(FName(*WidgetName));
    if (!Widget)
    {
        // Phase K
        FUISpecError E = MonolithUIInternal::MakeSpecError(
            TEXT("Lookup"),
            TEXT("/widget_name"),
            FString::Printf(TEXT("Widget '%s' not found in WBP '%s'."), *WidgetName, *AssetPath),
            TEXT("Call ui::get_widget_tree to enumerate live widget names."));
        E.WidgetId = FName(*WidgetName);
        return MonolithUIInternal::MakeErrorFromSpecError(E);
    }

    UCanvasPanelSlot* CS = Cast<UCanvasPanelSlot>(Widget->Slot);
    if (!CS)
    {
        // Phase K — slot-class mismatch is a structural issue. valid_options is
        // empty; the suggested_fix names the only path forward (re-parent).
        FUISpecError E = MonolithUIInternal::MakeSpecError(
            TEXT("SlotClass"),
            TEXT("/widget_name"),
            FString::Printf(TEXT("Widget '%s' is not in a CanvasPanel — anchor presets only apply to CanvasPanel slots."), *WidgetName),
            TEXT("Re-parent the widget into a CanvasPanel, or use ui::set_slot_property with the appropriate slot-class fields (h_align/v_align/padding for box slots)."));
        E.WidgetId = FName(*WidgetName);
        return MonolithUIInternal::MakeErrorFromSpecError(E);
    }

    // Phase K — preset name validation. The pre-K code silently fell through
    // to FAnchors(0,0,0,0) on a miss, which left the LLM thinking the call
    // succeeded. Now: explicit FUISpecError with the full 16-entry valid_options
    // list so the LLM can self-correct on the next attempt.
    const TArray<FString>& KnownPresets = MonolithUIInternal::GetAnchorPresetNames();
    if (!KnownPresets.Contains(Preset))
    {
        FUISpecError E = MonolithUIInternal::MakeSpecError(
            TEXT("Enum"),
            TEXT("/preset"),
            FString::Printf(TEXT("Unknown anchor preset '%s'."), *Preset),
            TEXT("Pick one of the listed preset tokens — names are lowercase with underscore separators."),
            KnownPresets);
        E.WidgetId = FName(*WidgetName);
        return MonolithUIInternal::MakeErrorFromSpecError(E);
    }

    FAnchors Anchors = MonolithUIInternal::GetAnchorPreset(Preset);
    CS->SetAnchors(Anchors);

    FBlueprintEditorUtils::MarkBlueprintAsModified(WBP);

    bool bCompile = false;
    if (Params->HasField(TEXT("compile"))) bCompile = Params->GetBoolField(TEXT("compile"));
    if (bCompile) FKismetEditorUtilities::CompileBlueprint(WBP);

    TSharedPtr<FJsonObject> Result = MakeShared<FJsonObject>();
    Result->SetStringField(TEXT("widget"), WidgetName);
    Result->SetStringField(TEXT("preset"), Preset);
    Result->SetBoolField(TEXT("compiled"), bCompile);
    return FMonolithActionResult::Success(Result);
}

// --- move_widget ---
FMonolithActionResult FMonolithUISlotActions::HandleMoveWidget(const TSharedPtr<FJsonObject>& Params)
{
    FString AssetPath = Params->GetStringField(TEXT("asset_path"));
    FString WidgetName = Params->GetStringField(TEXT("widget_name"));
    FString NewParentName = Params->GetStringField(TEXT("new_parent_name"));

    FMonolithActionResult Err;
    UWidgetBlueprint* WBP = MonolithUIInternal::LoadWidgetBlueprint(AssetPath, Err);
    if (!WBP) return Err;

    UWidget* Widget = WBP->WidgetTree->FindWidget(FName(*WidgetName));
    if (!Widget)
    {
        return FMonolithActionResult::Error(
            FString::Printf(TEXT("Widget '%s' not found"), *WidgetName));
    }

    UWidget* NewParentWidget = WBP->WidgetTree->FindWidget(FName(*NewParentName));
    UPanelWidget* NewParent = Cast<UPanelWidget>(NewParentWidget);
    if (!NewParent)
    {
        return FMonolithActionResult::Error(
            FString::Printf(TEXT("New parent '%s' not found or not a panel"), *NewParentName));
    }

    // Remove from current parent
    int32 OldIndex = -1;
    UPanelWidget* OldParent = UWidgetTree::FindWidgetParent(Widget, OldIndex);
    if (OldParent)
    {
        OldParent->RemoveChild(Widget);
    }

    // Add to new parent
    UPanelSlot* NewSlot = NewParent->AddChild(Widget);

    FBlueprintEditorUtils::MarkBlueprintAsStructurallyModified(WBP);

    bool bCompile = true;
    if (Params->HasField(TEXT("compile"))) bCompile = Params->GetBoolField(TEXT("compile"));
    if (bCompile) FKismetEditorUtilities::CompileBlueprint(WBP);

    TSharedPtr<FJsonObject> Result = MakeShared<FJsonObject>();
    Result->SetStringField(TEXT("widget"), WidgetName);
    Result->SetStringField(TEXT("old_parent"), OldParent ? OldParent->GetName() : TEXT("none"));
    Result->SetStringField(TEXT("new_parent"), NewParentName);
    Result->SetStringField(TEXT("new_slot_type"), NewSlot ? NewSlot->GetClass()->GetName() : TEXT("none"));
    Result->SetBoolField(TEXT("compiled"), bCompile);
    return FMonolithActionResult::Success(Result);
}
