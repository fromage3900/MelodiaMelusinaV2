// MonolithUIStylingActions.cpp
#include "MonolithUIStylingActions.h"
#include "MonolithJsonUtils.h"
#include "MonolithUIInternal.h"
#include "MonolithParamSchema.h"
#include "Styling/SlateTypes.h"
#include "Styling/StyleColors.h"
#include "Engine/Font.h"
#include "Engine/Texture2D.h"
#include "Materials/MaterialInterface.h"

void FMonolithUIStylingActions::RegisterActions(FMonolithToolRegistry& Registry)
{
    Registry.RegisterAction(
        TEXT("ui"), TEXT("set_brush"),
        TEXT("Configure a slate brush on any widget property (background, fill image, etc.)"),
        FMonolithActionHandler::CreateStatic(&HandleSetBrush),
        FParamSchemaBuilder()
            .RequiredAssetPath(TEXT("asset_path"), TEXT("Widget Blueprint asset path"))
            .Required(TEXT("widget_name"), TEXT("string"), TEXT("Target widget name"))
            .Required(TEXT("property_name"), TEXT("string"), TEXT("Brush property: Background, BarFillStyle.FillImage, etc."))
            .Optional(TEXT("draw_type"), TEXT("string"), TEXT("Draw type: Image, Box, Border, RoundedBox, NoDrawType"), TEXT("Image"))
            .Optional(TEXT("tint_color"), TEXT("string"), TEXT("Tint color as hex (#RRGGBB) or r,g,b,a floats"))
            .Optional(TEXT("image_size"), TEXT("object"), TEXT("Image size: {\"x\": 64, \"y\": 64}"))
            .Optional(TEXT("margin"), TEXT("object"), TEXT("9-slice margin: {\"left\":0, \"top\":0, \"right\":0, \"bottom\":0}"))
            .Optional(TEXT("corner_radius"), TEXT("object"), TEXT("Corner radius: {\"top_left\":0, \"top_right\":0, \"bottom_right\":0, \"bottom_left\":0}"))
            .Optional(TEXT("outline_color"), TEXT("string"), TEXT("Outline color as hex or r,g,b,a"))
            .Optional(TEXT("outline_width"), TEXT("number"), TEXT("Outline width in pixels"))
            .OptionalAssetPath(TEXT("texture_path"), TEXT("Texture asset path to set on the brush"))
            .OptionalAssetPath(TEXT("material_path"), TEXT("Material asset path to set on the brush"))
            .Optional(TEXT("compile"), TEXT("boolean"), TEXT("Compile after setting"), TEXT("false"))
            .Build()
    );

    Registry.RegisterAction(
        TEXT("ui"), TEXT("set_font"),
        TEXT("Set font properties on a text widget (TextBlock, RichTextBlock, EditableText, etc.)"),
        FMonolithActionHandler::CreateStatic(&HandleSetFont),
        FParamSchemaBuilder()
            .RequiredAssetPath(TEXT("asset_path"), TEXT("Widget Blueprint asset path"))
            .Required(TEXT("widget_name"), TEXT("string"), TEXT("Target widget name (must be a text widget)"))
            .Optional(TEXT("font_size"), TEXT("integer"), TEXT("Font size in points"))
            .Optional(TEXT("font_family"), TEXT("string"), TEXT("Font asset path"))
            .Optional(TEXT("typeface"), TEXT("string"), TEXT("Typeface: Regular, Bold, Italic, Light"), TEXT("Regular"))
            .Optional(TEXT("letter_spacing"), TEXT("integer"), TEXT("Letter spacing in design units"))
            .Optional(TEXT("outline_size"), TEXT("integer"), TEXT("Font outline size"))
            .Optional(TEXT("outline_color"), TEXT("string"), TEXT("Font outline color as hex or r,g,b,a"))
            .Optional(TEXT("compile"), TEXT("boolean"), TEXT("Compile after setting"), TEXT("false"))
            .Build()
    );

    Registry.RegisterAction(
        TEXT("ui"), TEXT("set_color_scheme"),
        TEXT("Set EStyleColor User1-16 slots for widget theming"),
        FMonolithActionHandler::CreateStatic(&HandleSetColorScheme),
        FParamSchemaBuilder()
            .Required(TEXT("colors"), TEXT("object"), TEXT("Color slot map: {\"User1\": \"#0A0A14\", \"User2\": \"#E6B822\", ...}"))
            .Build()
    );

    Registry.RegisterAction(
        TEXT("ui"), TEXT("batch_style"),
        TEXT("Apply a property value to all widgets of a given class in a Widget Blueprint"),
        FMonolithActionHandler::CreateStatic(&HandleBatchStyle),
        FParamSchemaBuilder()
            .RequiredAssetPath(TEXT("asset_path"), TEXT("Widget Blueprint asset path"))
            .Required(TEXT("widget_class"), TEXT("string"), TEXT("Widget class to target: TextBlock, Button, Image, etc."))
            .Required(TEXT("property_name"), TEXT("string"), TEXT("Property name to set"))
            .Required(TEXT("value"), TEXT("string"), TEXT("Property value as string"))
            .Optional(TEXT("compile"), TEXT("boolean"), TEXT("Compile after setting"), TEXT("false"))
            .Build()
    );

    Registry.RegisterAction(
        TEXT("ui"), TEXT("set_text"),
        TEXT("Convenience: set text, color, size, justification on a TextBlock or RichTextBlock"),
        FMonolithActionHandler::CreateStatic(&HandleSetText),
        FParamSchemaBuilder()
            .RequiredAssetPath(TEXT("asset_path"), TEXT("Widget Blueprint asset path"))
            .Required(TEXT("widget_name"), TEXT("string"), TEXT("Target TextBlock or RichTextBlock name"))
            .Optional(TEXT("text"), TEXT("string"), TEXT("Text content to set"))
            .Optional(TEXT("text_color"), TEXT("string"), TEXT("Text color as hex (#RRGGBB) or r,g,b,a"))
            .Optional(TEXT("font_size"), TEXT("integer"), TEXT("Font size in points"))
            .Optional(TEXT("justification"), TEXT("string"), TEXT("Text justification: Left, Center, Right"))
            .Optional(TEXT("compile"), TEXT("boolean"), TEXT("Compile after setting"), TEXT("false"))
            .Build()
    );

    Registry.RegisterAction(
        TEXT("ui"), TEXT("set_image"),
        TEXT("Convenience: set texture or material on an Image widget"),
        FMonolithActionHandler::CreateStatic(&HandleSetImage),
        FParamSchemaBuilder()
            .RequiredAssetPath(TEXT("asset_path"), TEXT("Widget Blueprint asset path"))
            .Required(TEXT("widget_name"), TEXT("string"), TEXT("Target Image widget name"))
            .OptionalAssetPath(TEXT("texture_path"), TEXT("Texture asset path"))
            .OptionalAssetPath(TEXT("material_path"), TEXT("Material asset path"))
            .Optional(TEXT("tint_color"), TEXT("string"), TEXT("Tint color as hex or r,g,b,a"))
            .Optional(TEXT("size"), TEXT("object"), TEXT("Desired size: {\"x\": 64, \"y\": 64}"))
            .Optional(TEXT("compile"), TEXT("boolean"), TEXT("Compile after setting"), TEXT("false"))
            .Build()
    );
}

// --- set_brush ---
FMonolithActionResult FMonolithUIStylingActions::HandleSetBrush(const TSharedPtr<FJsonObject>& Params)
{
    FString AssetPath = Params->GetStringField(TEXT("asset_path"));
    FString WidgetName = Params->GetStringField(TEXT("widget_name"));
    FString PropertyName = Params->GetStringField(TEXT("property_name"));

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

    // Find the FSlateBrush property by name (supports nested like "BarFillStyle.FillImage")
    // Split on '.' for nested access
    void* ContainerPtr = Widget;
    UStruct* ContainerStruct = Widget->GetClass();
    FProperty* BrushProp = nullptr;

    TArray<FString> PathParts;
    PropertyName.ParseIntoArray(PathParts, TEXT("."));
    for (int32 i = 0; i < PathParts.Num(); ++i)
    {
        FProperty* Prop = ContainerStruct->FindPropertyByName(FName(*PathParts[i]));
        if (!Prop)
        {
            return FMonolithActionResult::Error(
                FString::Printf(TEXT("Property '%s' not found on %s"), *PathParts[i], *ContainerStruct->GetName()));
        }

        if (i < PathParts.Num() - 1)
        {
            // Navigate into struct
            FStructProperty* StructProp = CastField<FStructProperty>(Prop);
            if (!StructProp)
            {
                return FMonolithActionResult::Error(
                    FString::Printf(TEXT("'%s' is not a struct property — cannot navigate deeper"), *PathParts[i]));
            }
            ContainerPtr = Prop->ContainerPtrToValuePtr<void>(ContainerPtr);
            ContainerStruct = StructProp->Struct;
        }
        else
        {
            BrushProp = Prop;
        }
    }

    // Verify it's an FSlateBrush
    FStructProperty* BrushStructProp = CastField<FStructProperty>(BrushProp);
    if (!BrushStructProp || BrushStructProp->Struct->GetFName() != TEXT("SlateBrush"))
    {
        return FMonolithActionResult::Error(
            FString::Printf(TEXT("Property '%s' is not an FSlateBrush"), *PropertyName));
    }

    FSlateBrush* Brush = BrushProp->ContainerPtrToValuePtr<FSlateBrush>(ContainerPtr);
    if (!Brush)
    {
        return FMonolithActionResult::Error(TEXT("Failed to get brush pointer"));
    }

    int32 PropsSet = 0;

    // Draw type
    FString DrawType = Params->GetStringField(TEXT("draw_type"));
    if (!DrawType.IsEmpty())
    {
        // Phase K — pre-K behaviour silently ignored unknown draw_type tokens
        // (no PropsSet++ + no error). Now: explicit FUISpecError with the full
        // 5-token list so the LLM can self-correct.
        bool bMatched = true;
        if (DrawType == TEXT("Image"))           Brush->DrawAs = ESlateBrushDrawType::Image;
        else if (DrawType == TEXT("Box"))        Brush->DrawAs = ESlateBrushDrawType::Box;
        else if (DrawType == TEXT("Border"))     Brush->DrawAs = ESlateBrushDrawType::Border;
        else if (DrawType == TEXT("RoundedBox")) Brush->DrawAs = ESlateBrushDrawType::RoundedBox;
        else if (DrawType == TEXT("NoDrawType")) Brush->DrawAs = ESlateBrushDrawType::NoDrawType;
        else                                     bMatched = false;

        if (!bMatched)
        {
            FUISpecError E = MonolithUIInternal::MakeSpecError(
                TEXT("Enum"),
                TEXT("/draw_type"),
                FString::Printf(TEXT("Unknown draw_type token '%s'."), *DrawType),
                TEXT("Pick one of the ESlateBrushDrawType tokens. RoundedBox requires a corner_radius alongside."),
                { TEXT("Image"), TEXT("Box"), TEXT("Border"), TEXT("RoundedBox"), TEXT("NoDrawType") });
            E.WidgetId = FName(*WidgetName);
            return MonolithUIInternal::MakeErrorFromSpecError(E);
        }
        PropsSet++;
    }

    // Tint color
    FString TintColor = Params->GetStringField(TEXT("tint_color"));
    if (!TintColor.IsEmpty())
    {
        Brush->TintColor = FSlateColor(MonolithUIInternal::ParseColor(TintColor));
        PropsSet++;
    }

    // Image size
    const TSharedPtr<FJsonObject>* ImageSizeObj = nullptr;
    if (Params->TryGetObjectField(TEXT("image_size"), ImageSizeObj))
    {
        Brush->ImageSize = FVector2D((*ImageSizeObj)->GetNumberField(TEXT("x")), (*ImageSizeObj)->GetNumberField(TEXT("y")));
        PropsSet++;
    }

    // 9-slice margin
    const TSharedPtr<FJsonObject>* MarginObj = nullptr;
    if (Params->TryGetObjectField(TEXT("margin"), MarginObj))
    {
        Brush->Margin = FMargin(
            (*MarginObj)->GetNumberField(TEXT("left")),
            (*MarginObj)->GetNumberField(TEXT("top")),
            (*MarginObj)->GetNumberField(TEXT("right")),
            (*MarginObj)->GetNumberField(TEXT("bottom"))
        );
        PropsSet++;
    }

    // Corner radius (RoundedBox)
    const TSharedPtr<FJsonObject>* CornerObj = nullptr;
    if (Params->TryGetObjectField(TEXT("corner_radius"), CornerObj))
    {
        Brush->OutlineSettings.CornerRadii = FVector4(
            (*CornerObj)->GetNumberField(TEXT("top_left")),
            (*CornerObj)->GetNumberField(TEXT("top_right")),
            (*CornerObj)->GetNumberField(TEXT("bottom_right")),
            (*CornerObj)->GetNumberField(TEXT("bottom_left"))
        );
        Brush->OutlineSettings.RoundingType = ESlateBrushRoundingType::FixedRadius;
        PropsSet++;
    }

    // Outline
    FString OutlineColor = Params->GetStringField(TEXT("outline_color"));
    if (!OutlineColor.IsEmpty())
    {
        Brush->OutlineSettings.Color = FSlateColor(MonolithUIInternal::ParseColor(OutlineColor));
        PropsSet++;
    }
    if (Params->HasField(TEXT("outline_width")))
    {
        Brush->OutlineSettings.Width = static_cast<float>(Params->GetNumberField(TEXT("outline_width")));
        PropsSet++;
    }

    // Texture
    FString TexturePath = Params->GetStringField(TEXT("texture_path"));
    if (!TexturePath.IsEmpty())
    {
        UTexture2D* Tex = Cast<UTexture2D>(StaticLoadObject(UTexture2D::StaticClass(), nullptr, *TexturePath));
        if (Tex)
        {
            Brush->SetResourceObject(Tex);
            PropsSet++;
        }
        else
        {
            return FMonolithActionResult::Error(FString::Printf(TEXT("Texture not found: %s"), *TexturePath));
        }
    }

    // Material
    FString MaterialPath = Params->GetStringField(TEXT("material_path"));
    if (!MaterialPath.IsEmpty())
    {
        UMaterialInterface* Mat = Cast<UMaterialInterface>(StaticLoadObject(UMaterialInterface::StaticClass(), nullptr, *MaterialPath));
        if (Mat)
        {
            Brush->SetResourceObject(Mat);
            PropsSet++;
        }
        else
        {
            return FMonolithActionResult::Error(FString::Printf(TEXT("Material not found: %s"), *MaterialPath));
        }
    }

    if (PropsSet == 0)
    {
        // Phase K — list the legal property keys in valid_options.
        return MonolithUIInternal::MakeErrorFromSpecError(MonolithUIInternal::MakeSpecError(
            TEXT("MissingInput"),
            TEXT("/"),
            TEXT("No brush properties specified."),
            TEXT("Pass one or more of the listed parameter keys to mutate the SlateBrush."),
            { TEXT("draw_type"), TEXT("tint_color"), TEXT("image_size"), TEXT("margin"),
              TEXT("corner_radius"), TEXT("outline_color"), TEXT("outline_width"),
              TEXT("texture_path"), TEXT("material_path") }));
    }

    Widget->SynchronizeProperties();
    FBlueprintEditorUtils::MarkBlueprintAsModified(WBP);

    bool bCompile = false;
    if (Params->HasField(TEXT("compile"))) bCompile = Params->GetBoolField(TEXT("compile"));
    if (bCompile) FKismetEditorUtilities::CompileBlueprint(WBP);

    TSharedPtr<FJsonObject> Result = MakeShared<FJsonObject>();
    Result->SetStringField(TEXT("widget"), WidgetName);
    Result->SetStringField(TEXT("property"), PropertyName);
    Result->SetNumberField(TEXT("properties_set"), PropsSet);
    Result->SetBoolField(TEXT("compiled"), bCompile);
    return FMonolithActionResult::Success(Result);
}

// --- set_font ---
FMonolithActionResult FMonolithUIStylingActions::HandleSetFont(const TSharedPtr<FJsonObject>& Params)
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

    // Get font via getter/setter pattern (safer than raw reflection — respects property accessors)
    UTextBlock* TextBlock = Cast<UTextBlock>(Widget);
    URichTextBlock* RichText = Cast<URichTextBlock>(Widget);
    if (!TextBlock && !RichText)
    {
        // Phase K — class-mismatch with valid_options enumerating the
        // accepted text-widget tokens.
        FUISpecError E = MonolithUIInternal::MakeSpecError(
            TEXT("WidgetClass"),
            TEXT("/widget_name"),
            FString::Printf(TEXT("Widget '%s' (class %s) is not a text widget."),
                *WidgetName, *Widget->GetClass()->GetName()),
            TEXT("set_font targets text widgets only. For non-text widgets, set the relevant FSlateFontInfo struct field via set_widget_property."),
            { TEXT("TextBlock"), TEXT("RichTextBlock") });
        E.WidgetId = FName(*WidgetName);
        return MonolithUIInternal::MakeErrorFromSpecError(E);
    }

    FSlateFontInfo FontInfoCopy = TextBlock ? TextBlock->GetFont() :
                                  FSlateFontInfo(); // RichTextBlock uses style sets, apply via reflection fallback
    FSlateFontInfo* FontInfo = &FontInfoCopy;

    int32 PropsSet = 0;

    // Font size
    if (Params->HasField(TEXT("font_size")))
    {
        FontInfo->Size = static_cast<float>(Params->GetNumberField(TEXT("font_size")));
        PropsSet++;
    }

    // Font family (asset path)
    FString FontFamily = Params->GetStringField(TEXT("font_family"));
    if (!FontFamily.IsEmpty())
    {
        UObject* FontObj = StaticLoadObject(UFont::StaticClass(), nullptr, *FontFamily);
        if (FontObj)
        {
            FontInfo->FontObject = FontObj;
            PropsSet++;
        }
        else
        {
            return FMonolithActionResult::Error(FString::Printf(TEXT("Font asset not found: %s"), *FontFamily));
        }
    }

    // Typeface
    FString Typeface = Params->GetStringField(TEXT("typeface"));
    if (!Typeface.IsEmpty())
    {
        FontInfo->TypefaceFontName = FName(*Typeface);
        PropsSet++;
    }

    // Letter spacing
    if (Params->HasField(TEXT("letter_spacing")))
    {
        FontInfo->LetterSpacing = static_cast<int32>(Params->GetNumberField(TEXT("letter_spacing")));
        PropsSet++;
    }

    // Outline size
    if (Params->HasField(TEXT("outline_size")))
    {
        FontInfo->OutlineSettings.OutlineSize = static_cast<int32>(Params->GetNumberField(TEXT("outline_size")));
        PropsSet++;
    }

    // Outline color
    FString OutlineColor = Params->GetStringField(TEXT("outline_color"));
    if (!OutlineColor.IsEmpty())
    {
        FontInfo->OutlineSettings.OutlineColor = MonolithUIInternal::ParseColor(OutlineColor);
        PropsSet++;
    }

    if (PropsSet == 0)
    {
        // Phase K
        return MonolithUIInternal::MakeErrorFromSpecError(MonolithUIInternal::MakeSpecError(
            TEXT("MissingInput"),
            TEXT("/"),
            TEXT("No font properties specified."),
            TEXT("Pass one or more of the listed parameter keys to mutate FSlateFontInfo."),
            { TEXT("font_size"), TEXT("font_family"), TEXT("typeface"),
              TEXT("letter_spacing"), TEXT("outline_size"), TEXT("outline_color") }));
    }

    // Write back via setter (not raw reflection) to ensure Slate update
    if (TextBlock) TextBlock->SetFont(FontInfoCopy);
    Widget->SynchronizeProperties();
    FBlueprintEditorUtils::MarkBlueprintAsModified(WBP);

    bool bCompile = false;
    if (Params->HasField(TEXT("compile"))) bCompile = Params->GetBoolField(TEXT("compile"));
    if (bCompile) FKismetEditorUtilities::CompileBlueprint(WBP);

    TSharedPtr<FJsonObject> Result = MakeShared<FJsonObject>();
    Result->SetStringField(TEXT("widget"), WidgetName);
    Result->SetNumberField(TEXT("properties_set"), PropsSet);
    Result->SetBoolField(TEXT("compiled"), bCompile);
    return FMonolithActionResult::Success(Result);
}

// --- set_color_scheme ---
FMonolithActionResult FMonolithUIStylingActions::HandleSetColorScheme(const TSharedPtr<FJsonObject>& Params)
{
    const TSharedPtr<FJsonObject>* ColorsObj = nullptr;
    if (!Params->TryGetObjectField(TEXT("colors"), ColorsObj))
    {
        return FMonolithActionResult::Error(TEXT("Missing required param: colors (object with slot names as keys)"));
    }

    // Map slot names to EStyleColor values
    static TMap<FString, EStyleColor> SlotMap;
    if (SlotMap.Num() == 0)
    {
        SlotMap.Add(TEXT("User1"),  EStyleColor::User1);
        SlotMap.Add(TEXT("User2"),  EStyleColor::User2);
        SlotMap.Add(TEXT("User3"),  EStyleColor::User3);
        SlotMap.Add(TEXT("User4"),  EStyleColor::User4);
        SlotMap.Add(TEXT("User5"),  EStyleColor::User5);
        SlotMap.Add(TEXT("User6"),  EStyleColor::User6);
        SlotMap.Add(TEXT("User7"),  EStyleColor::User7);
        SlotMap.Add(TEXT("User8"),  EStyleColor::User8);
        SlotMap.Add(TEXT("User9"),  EStyleColor::User9);
        SlotMap.Add(TEXT("User10"), EStyleColor::User10);
        SlotMap.Add(TEXT("User11"), EStyleColor::User11);
        SlotMap.Add(TEXT("User12"), EStyleColor::User12);
        SlotMap.Add(TEXT("User13"), EStyleColor::User13);
        SlotMap.Add(TEXT("User14"), EStyleColor::User14);
        SlotMap.Add(TEXT("User15"), EStyleColor::User15);
        SlotMap.Add(TEXT("User16"), EStyleColor::User16);
    }

    int32 SlotsSet = 0;
    TArray<FString> SetNames;

    for (const auto& Pair : (*ColorsObj)->Values)
    {
        const FString PairKeyStr = MonolithKeyToString(Pair.Key);
        const EStyleColor* SlotColor = SlotMap.Find(PairKeyStr);
        if (!SlotColor)
        {
            return FMonolithActionResult::Error(
                FString::Printf(TEXT("Unknown color slot: '%s'. Valid: User1-User16"), *PairKeyStr));
        }

        FString ColorStr = Pair.Value->AsString();
        FLinearColor Color = MonolithUIInternal::ParseColor(ColorStr);
        USlateThemeManager::Get().SetDefaultColor(*SlotColor, Color);
        SlotsSet++;
        SetNames.Add(PairKeyStr);
    }

    if (SlotsSet == 0)
    {
        return FMonolithActionResult::Error(TEXT("No colors specified in the colors object"));
    }

    TSharedPtr<FJsonObject> Result = MakeShared<FJsonObject>();
    Result->SetNumberField(TEXT("slots_set"), SlotsSet);

    TArray<TSharedPtr<FJsonValue>> NamesArray;
    for (const FString& N : SetNames)
    {
        NamesArray.Add(MakeShared<FJsonValueString>(N));
    }
    Result->SetArrayField(TEXT("slot_names"), NamesArray);
    return FMonolithActionResult::Success(Result);
}

// --- batch_style ---
FMonolithActionResult FMonolithUIStylingActions::HandleBatchStyle(const TSharedPtr<FJsonObject>& Params)
{
    FString AssetPath = Params->GetStringField(TEXT("asset_path"));
    FString WidgetClassName = Params->GetStringField(TEXT("widget_class"));
    FString PropertyName = Params->GetStringField(TEXT("property_name"));
    FString Value = Params->GetStringField(TEXT("value"));

    FMonolithActionResult Err;
    UWidgetBlueprint* WBP = MonolithUIInternal::LoadWidgetBlueprint(AssetPath, Err);
    if (!WBP) return Err;

    UClass* TargetClass = MonolithUIInternal::WidgetClassFromName(WidgetClassName);
    if (!TargetClass)
    {
        return FMonolithActionResult::Error(
            FString::Printf(TEXT("Unknown widget class: %s"), *WidgetClassName));
    }

    TArray<UWidget*> AllWidgets;
    WBP->WidgetTree->GetAllWidgets(AllWidgets);

    int32 Modified = 0;
    TArray<FString> ModifiedNames;

    for (UWidget* Widget : AllWidgets)
    {
        if (!Widget || !Widget->IsA(TargetClass)) continue;

        FProperty* Prop = Widget->GetClass()->FindPropertyByName(FName(*PropertyName));
        if (!Prop) continue;

        void* PropAddr = Prop->ContainerPtrToValuePtr<void>(Widget);
        if (Prop->ImportText_Direct(*Value, PropAddr, Widget, PPF_None))
        {
            Widget->SynchronizeProperties();
            Modified++;
            ModifiedNames.Add(Widget->GetName());
        }
    }

    if (Modified == 0)
    {
        return FMonolithActionResult::Error(
            FString::Printf(TEXT("No %s widgets found with settable property '%s'"), *WidgetClassName, *PropertyName));
    }

    FBlueprintEditorUtils::MarkBlueprintAsModified(WBP);

    bool bCompile = false;
    if (Params->HasField(TEXT("compile"))) bCompile = Params->GetBoolField(TEXT("compile"));
    if (bCompile) FKismetEditorUtilities::CompileBlueprint(WBP);

    TSharedPtr<FJsonObject> Result = MakeShared<FJsonObject>();
    Result->SetNumberField(TEXT("widgets_modified"), Modified);
    Result->SetStringField(TEXT("widget_class"), WidgetClassName);
    Result->SetStringField(TEXT("property"), PropertyName);
    Result->SetStringField(TEXT("value"), Value);
    Result->SetBoolField(TEXT("compiled"), bCompile);

    TArray<TSharedPtr<FJsonValue>> NamesArray;
    for (const FString& N : ModifiedNames)
    {
        NamesArray.Add(MakeShared<FJsonValueString>(N));
    }
    Result->SetArrayField(TEXT("modified_widgets"), NamesArray);
    return FMonolithActionResult::Success(Result);
}

// --- set_text ---
FMonolithActionResult FMonolithUIStylingActions::HandleSetText(const TSharedPtr<FJsonObject>& Params)
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

    int32 PropsSet = 0;

    // TextBlock
    if (UTextBlock* TB = Cast<UTextBlock>(Widget))
    {
        FString Text = Params->GetStringField(TEXT("text"));
        if (!Text.IsEmpty())
        {
            TB->SetText(FText::FromString(Text));
            PropsSet++;
        }

        FString TextColor = Params->GetStringField(TEXT("text_color"));
        if (!TextColor.IsEmpty())
        {
            TB->SetColorAndOpacity(FSlateColor(MonolithUIInternal::ParseColor(TextColor)));
            PropsSet++;
        }

        if (Params->HasField(TEXT("font_size")))
        {
            FSlateFontInfo FontInfo = TB->GetFont();
            FontInfo.Size = static_cast<float>(Params->GetNumberField(TEXT("font_size")));
            TB->SetFont(FontInfo);
            PropsSet++;
        }

        FString Justification = Params->GetStringField(TEXT("justification"));
        if (!Justification.IsEmpty())
        {
            // Phase K — pre-K silently ignored unknown tokens. Now: explicit
            // FUISpecError with the 3-token list.
            bool bMatched = true;
            if (Justification == TEXT("Left"))        TB->SetJustification(ETextJustify::Left);
            else if (Justification == TEXT("Center")) TB->SetJustification(ETextJustify::Center);
            else if (Justification == TEXT("Right"))  TB->SetJustification(ETextJustify::Right);
            else                                      bMatched = false;

            if (!bMatched)
            {
                FUISpecError E = MonolithUIInternal::MakeSpecError(
                    TEXT("Enum"),
                    TEXT("/justification"),
                    FString::Printf(TEXT("Unknown justification token '%s'."), *Justification),
                    TEXT("Pick one of the ETextJustify tokens."),
                    { TEXT("Left"), TEXT("Center"), TEXT("Right") });
                E.WidgetId = FName(*WidgetName);
                return MonolithUIInternal::MakeErrorFromSpecError(E);
            }
            PropsSet++;
        }
    }
    // RichTextBlock
    else if (URichTextBlock* RTB = Cast<URichTextBlock>(Widget))
    {
        FString Text = Params->GetStringField(TEXT("text"));
        if (!Text.IsEmpty())
        {
            RTB->SetText(FText::FromString(Text));
            PropsSet++;
        }
    }
    else
    {
        // Phase K
        FUISpecError E = MonolithUIInternal::MakeSpecError(
            TEXT("WidgetClass"),
            TEXT("/widget_name"),
            FString::Printf(TEXT("Widget '%s' (class %s) is not a TextBlock or RichTextBlock."),
                *WidgetName, *Widget->GetClass()->GetName()),
            TEXT("set_text targets text widgets only. Use set_widget_property for direct property writes on other classes."),
            { TEXT("TextBlock"), TEXT("RichTextBlock") });
        E.WidgetId = FName(*WidgetName);
        return MonolithUIInternal::MakeErrorFromSpecError(E);
    }

    if (PropsSet == 0)
    {
        // Phase K
        return MonolithUIInternal::MakeErrorFromSpecError(MonolithUIInternal::MakeSpecError(
            TEXT("MissingInput"),
            TEXT("/"),
            TEXT("No text properties specified."),
            TEXT("Pass one or more of the listed parameter keys to mutate the text widget."),
            { TEXT("text"), TEXT("text_color"), TEXT("font_size"), TEXT("justification") }));
    }

    Widget->SynchronizeProperties();
    FBlueprintEditorUtils::MarkBlueprintAsModified(WBP);

    bool bCompile = false;
    if (Params->HasField(TEXT("compile"))) bCompile = Params->GetBoolField(TEXT("compile"));
    if (bCompile) FKismetEditorUtilities::CompileBlueprint(WBP);

    TSharedPtr<FJsonObject> Result = MakeShared<FJsonObject>();
    Result->SetStringField(TEXT("widget"), WidgetName);
    Result->SetNumberField(TEXT("properties_set"), PropsSet);
    Result->SetBoolField(TEXT("compiled"), bCompile);
    return FMonolithActionResult::Success(Result);
}

// --- set_image ---
FMonolithActionResult FMonolithUIStylingActions::HandleSetImage(const TSharedPtr<FJsonObject>& Params)
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

    UImage* ImageWidget = Cast<UImage>(Widget);
    if (!ImageWidget)
    {
        // Phase K
        FUISpecError E = MonolithUIInternal::MakeSpecError(
            TEXT("WidgetClass"),
            TEXT("/widget_name"),
            FString::Printf(TEXT("Widget '%s' (class %s) is not an Image widget."),
                *WidgetName, *Widget->GetClass()->GetName()),
            TEXT("set_image targets the UImage class only. For Border/Button backgrounds, use set_brush."),
            { TEXT("Image") });
        E.WidgetId = FName(*WidgetName);
        return MonolithUIInternal::MakeErrorFromSpecError(E);
    }

    int32 PropsSet = 0;

    // Texture
    FString TexturePath = Params->GetStringField(TEXT("texture_path"));
    if (!TexturePath.IsEmpty())
    {
        UTexture2D* Tex = Cast<UTexture2D>(StaticLoadObject(UTexture2D::StaticClass(), nullptr, *TexturePath));
        if (Tex)
        {
            ImageWidget->SetBrushFromTexture(Tex);
            PropsSet++;
        }
        else
        {
            return FMonolithActionResult::Error(FString::Printf(TEXT("Texture not found: %s"), *TexturePath));
        }
    }

    // Material
    FString MaterialPath = Params->GetStringField(TEXT("material_path"));
    if (!MaterialPath.IsEmpty())
    {
        UMaterialInterface* Mat = Cast<UMaterialInterface>(StaticLoadObject(UMaterialInterface::StaticClass(), nullptr, *MaterialPath));
        if (Mat)
        {
            ImageWidget->SetBrushFromMaterial(Mat);
            PropsSet++;
        }
        else
        {
            return FMonolithActionResult::Error(FString::Printf(TEXT("Material not found: %s"), *MaterialPath));
        }
    }

    // Tint color
    FString TintColor = Params->GetStringField(TEXT("tint_color"));
    if (!TintColor.IsEmpty())
    {
        ImageWidget->SetColorAndOpacity(MonolithUIInternal::ParseColor(TintColor));
        PropsSet++;
    }

    // Desired size
    const TSharedPtr<FJsonObject>* SizeObj = nullptr;
    if (Params->TryGetObjectField(TEXT("size"), SizeObj))
    {
        FVector2D DesiredSize((*SizeObj)->GetNumberField(TEXT("x")), (*SizeObj)->GetNumberField(TEXT("y")));
        ImageWidget->SetDesiredSizeOverride(DesiredSize);
        PropsSet++;
    }

    if (PropsSet == 0)
    {
        // Phase K
        return MonolithUIInternal::MakeErrorFromSpecError(MonolithUIInternal::MakeSpecError(
            TEXT("MissingInput"),
            TEXT("/"),
            TEXT("No image properties specified."),
            TEXT("Pass one or more of the listed parameter keys to mutate the UImage."),
            { TEXT("texture_path"), TEXT("material_path"), TEXT("tint_color"), TEXT("size") }));
    }

    ImageWidget->SynchronizeProperties();
    FBlueprintEditorUtils::MarkBlueprintAsModified(WBP);

    bool bCompile = false;
    if (Params->HasField(TEXT("compile"))) bCompile = Params->GetBoolField(TEXT("compile"));
    if (bCompile) FKismetEditorUtilities::CompileBlueprint(WBP);

    TSharedPtr<FJsonObject> Result = MakeShared<FJsonObject>();
    Result->SetStringField(TEXT("widget"), WidgetName);
    Result->SetNumberField(TEXT("properties_set"), PropsSet);
    Result->SetBoolField(TEXT("compiled"), bCompile);
    return FMonolithActionResult::Success(Result);
}
