// MonolithUITemplateActions.cpp
#include "MonolithUITemplateActions.h"
#include "MonolithUIInternal.h"
#include "MonolithParamSchema.h"

void FMonolithUITemplateActions::RegisterActions(FMonolithToolRegistry& Registry)
{
    Registry.RegisterAction(
        TEXT("ui"), TEXT("create_hud_element"),
        TEXT("Create a pre-built HUD element widget hierarchy (crosshair, health bar, ammo counter, etc.)"),
        FMonolithActionHandler::CreateStatic(&HandleCreateHudElement),
        FParamSchemaBuilder()
            .RequiredAssetPath(TEXT("asset_path"), TEXT("Widget Blueprint asset path to modify"))
            .Required(TEXT("element_type"), TEXT("string"), TEXT("Element type: crosshair, health_bar, ammo_counter, stamina_bar, interaction_prompt, damage_indicator, compass, subtitles, flashlight_battery"))
            .Optional(TEXT("widget_name_prefix"), TEXT("string"), TEXT("Prefix for generated widget names (default: element type)"))
            .Optional(TEXT("compile"), TEXT("boolean"), TEXT("Compile after creating"), TEXT("true"))
            .Build()
    );

    Registry.RegisterAction(
        TEXT("ui"), TEXT("create_menu"),
        TEXT("Create a menu widget blueprint (main menu, pause, death screen, credits)"),
        FMonolithActionHandler::CreateStatic(&HandleCreateMenu),
        FParamSchemaBuilder()
            .RequiredAssetPath(TEXT("save_path"), TEXT("Asset path for the new Widget Blueprint"))
            .Required(TEXT("menu_type"), TEXT("string"), TEXT("Menu type: main_menu, pause_menu, death_screen, credits"))
            .Optional(TEXT("buttons"), TEXT("array"), TEXT("Array of button label strings"))
            .Build()
    );

    Registry.RegisterAction(
        TEXT("ui"), TEXT("create_settings_panel"),
        TEXT("Create a tabbed settings panel with Apply/Revert/Back"),
        FMonolithActionHandler::CreateStatic(&HandleCreateSettingsPanel),
        FParamSchemaBuilder()
            .RequiredAssetPath(TEXT("save_path"), TEXT("Asset path for the new Widget Blueprint"))
            .Optional(TEXT("tabs"), TEXT("array"), TEXT("Tab names: graphics, audio, controls, gameplay, accessibility (defaults to all)"))
            .Build()
    );

    Registry.RegisterAction(
        TEXT("ui"), TEXT("create_dialog"),
        TEXT("Create a confirmation dialog widget"),
        FMonolithActionHandler::CreateStatic(&HandleCreateDialog),
        FParamSchemaBuilder()
            .RequiredAssetPath(TEXT("save_path"), TEXT("Asset path for the new Widget Blueprint"))
            .Optional(TEXT("title"), TEXT("string"), TEXT("Dialog title text"), TEXT("Confirm"))
            .Optional(TEXT("body"), TEXT("string"), TEXT("Dialog body text"), TEXT("Are you sure?"))
            .Optional(TEXT("confirm_text"), TEXT("string"), TEXT("Confirm button text"), TEXT("Yes"))
            .Optional(TEXT("cancel_text"), TEXT("string"), TEXT("Cancel button text"), TEXT("No"))
            .Build()
    );

    Registry.RegisterAction(
        TEXT("ui"), TEXT("create_notification_toast"),
        TEXT("Create a notification toast widget"),
        FMonolithActionHandler::CreateStatic(&HandleCreateNotificationToast),
        FParamSchemaBuilder()
            .RequiredAssetPath(TEXT("save_path"), TEXT("Asset path for the new Widget Blueprint"))
            .Optional(TEXT("position"), TEXT("string"), TEXT("Position: top_right, bottom_right, top_left, bottom_left, top_center"), TEXT("top_right"))
            .Build()
    );

    Registry.RegisterAction(
        TEXT("ui"), TEXT("create_loading_screen"),
        TEXT("Create a loading screen widget"),
        FMonolithActionHandler::CreateStatic(&HandleCreateLoadingScreen),
        FParamSchemaBuilder()
            .RequiredAssetPath(TEXT("save_path"), TEXT("Asset path for the new Widget Blueprint"))
            .Optional(TEXT("show_progress"), TEXT("boolean"), TEXT("Include a progress bar"), TEXT("true"))
            .Optional(TEXT("show_tips"), TEXT("boolean"), TEXT("Include a tips text block"), TEXT("true"))
            .Optional(TEXT("show_spinner"), TEXT("boolean"), TEXT("Include a loading spinner image"), TEXT("true"))
            .Build()
    );

    Registry.RegisterAction(
        TEXT("ui"), TEXT("create_inventory_grid"),
        TEXT("Create an inventory grid layout widget"),
        FMonolithActionHandler::CreateStatic(&HandleCreateInventoryGrid),
        FParamSchemaBuilder()
            .RequiredAssetPath(TEXT("save_path"), TEXT("Asset path for the new Widget Blueprint"))
            .Optional(TEXT("columns"), TEXT("integer"), TEXT("Number of columns"), TEXT("5"))
            .Optional(TEXT("rows"), TEXT("integer"), TEXT("Number of rows"), TEXT("4"))
            .Optional(TEXT("slot_size"), TEXT("integer"), TEXT("Slot size in pixels"), TEXT("64"))
            .Build()
    );

    Registry.RegisterAction(
        TEXT("ui"), TEXT("create_save_slot_list"),
        TEXT("Create a save slot selector widget"),
        FMonolithActionHandler::CreateStatic(&HandleCreateSaveSlotList),
        FParamSchemaBuilder()
            .RequiredAssetPath(TEXT("save_path"), TEXT("Asset path for the new Widget Blueprint"))
            .Optional(TEXT("max_slots"), TEXT("integer"), TEXT("Number of save slots to create"), TEXT("3"))
            .Build()
    );
}

// --- create_hud_element ---
FMonolithActionResult FMonolithUITemplateActions::HandleCreateHudElement(const TSharedPtr<FJsonObject>& Params)
{
    FString AssetPath = Params->GetStringField(TEXT("asset_path"));
    FString ElementType = Params->GetStringField(TEXT("element_type"));
    if (ElementType.IsEmpty())
    {
        return FMonolithActionResult::Error(TEXT("Missing required param: element_type"));
    }

    FString Prefix = MonolithUIInternal::GetOptionalString(Params, TEXT("widget_name_prefix"));
    if (Prefix.IsEmpty()) Prefix = ElementType;

    FMonolithActionResult Err;
    UWidgetBlueprint* WBP = MonolithUIInternal::LoadWidgetBlueprint(AssetPath, Err);
    if (!WBP) return Err;
    if (!WBP->WidgetTree || !WBP->WidgetTree->RootWidget)
    {
        return FMonolithActionResult::Error(TEXT("Widget Blueprint has no widget tree or root widget"));
    }

    UPanelWidget* Root = Cast<UPanelWidget>(WBP->WidgetTree->RootWidget);
    if (!Root)
    {
        return FMonolithActionResult::Error(TEXT("Root widget is not a panel — cannot add children"));
    }

    int32 WidgetsCreated = 0;

    // --- CROSSHAIR ---
    if (ElementType == TEXT("crosshair"))
    {
        // Overlay centered, with 4 Image widgets for cross lines
        UOverlay* Container = WBP->WidgetTree->ConstructWidget<UOverlay>(UOverlay::StaticClass(), FName(*(Prefix + TEXT("_Container"))));
        Root->AddChild(Container);
        MonolithUIInternal::ConfigureCanvasSlot(Container->Slot, TEXT("center"), FVector2D::ZeroVector, FVector2D(64, 64), false, FVector2D(0.5f, 0.5f));

        UImage* CenterDot = WBP->WidgetTree->ConstructWidget<UImage>(UImage::StaticClass(), FName(*(Prefix + TEXT("_Dot"))));
        Container->AddChild(CenterDot);
        if (UOverlaySlot* OS = Cast<UOverlaySlot>(CenterDot->Slot))
        {
            OS->SetHorizontalAlignment(HAlign_Center);
            OS->SetVerticalAlignment(VAlign_Center);
        }
        WidgetsCreated = 2;
    }
    // --- HEALTH_BAR ---
    else if (ElementType == TEXT("health_bar"))
    {
        // CanvasPanel child: VerticalBox → ProgressBar + TextBlock label
        UVerticalBox* VBox = WBP->WidgetTree->ConstructWidget<UVerticalBox>(UVerticalBox::StaticClass(), FName(*(Prefix + TEXT("_Container"))));
        Root->AddChild(VBox);
        MonolithUIInternal::ConfigureCanvasSlot(VBox->Slot, TEXT("bottom_left"), FVector2D(20, -80), FVector2D(300, 60), false, FVector2D(0.f, 1.f));

        UProgressBar* Bar = WBP->WidgetTree->ConstructWidget<UProgressBar>(UProgressBar::StaticClass(), FName(*(Prefix + TEXT("_Bar"))));
        VBox->AddChild(Bar);
        Bar->SetPercent(1.0f);
        if (UVerticalBoxSlot* VS = Cast<UVerticalBoxSlot>(Bar->Slot))
        {
            VS->SetHorizontalAlignment(HAlign_Fill);
            VS->SetPadding(FMargin(0, 0, 0, 2));
        }

        UTextBlock* Label = WBP->WidgetTree->ConstructWidget<UTextBlock>(UTextBlock::StaticClass(), FName(*(Prefix + TEXT("_Label"))));
        VBox->AddChild(Label);
        Label->SetText(FText::FromString(TEXT("HEALTH")));
        if (UVerticalBoxSlot* VS = Cast<UVerticalBoxSlot>(Label->Slot))
        {
            VS->SetHorizontalAlignment(HAlign_Left);
        }
        WidgetsCreated = 3;
    }
    // --- AMMO_COUNTER ---
    else if (ElementType == TEXT("ammo_counter"))
    {
        UHorizontalBox* HBox = WBP->WidgetTree->ConstructWidget<UHorizontalBox>(UHorizontalBox::StaticClass(), FName(*(Prefix + TEXT("_Container"))));
        Root->AddChild(HBox);
        MonolithUIInternal::ConfigureCanvasSlot(HBox->Slot, TEXT("bottom_right"), FVector2D(-20, -40), FVector2D(200, 40), false, FVector2D(1.f, 1.f));

        UTextBlock* Current = WBP->WidgetTree->ConstructWidget<UTextBlock>(UTextBlock::StaticClass(), FName(*(Prefix + TEXT("_Current"))));
        HBox->AddChild(Current);
        Current->SetText(FText::FromString(TEXT("30")));
        if (UHorizontalBoxSlot* HS = Cast<UHorizontalBoxSlot>(Current->Slot))
        {
            HS->SetVerticalAlignment(VAlign_Center);
        }

        UTextBlock* Separator = WBP->WidgetTree->ConstructWidget<UTextBlock>(UTextBlock::StaticClass(), FName(*(Prefix + TEXT("_Separator"))));
        HBox->AddChild(Separator);
        Separator->SetText(FText::FromString(TEXT(" / ")));
        if (UHorizontalBoxSlot* HS = Cast<UHorizontalBoxSlot>(Separator->Slot))
        {
            HS->SetVerticalAlignment(VAlign_Center);
            HS->SetPadding(FMargin(4, 0, 4, 0));
        }

        UTextBlock* Reserve = WBP->WidgetTree->ConstructWidget<UTextBlock>(UTextBlock::StaticClass(), FName(*(Prefix + TEXT("_Reserve"))));
        HBox->AddChild(Reserve);
        Reserve->SetText(FText::FromString(TEXT("120")));
        if (UHorizontalBoxSlot* HS = Cast<UHorizontalBoxSlot>(Reserve->Slot))
        {
            HS->SetVerticalAlignment(VAlign_Center);
        }
        WidgetsCreated = 4;
    }
    // --- STAMINA_BAR ---
    else if (ElementType == TEXT("stamina_bar"))
    {
        UVerticalBox* VBox = WBP->WidgetTree->ConstructWidget<UVerticalBox>(UVerticalBox::StaticClass(), FName(*(Prefix + TEXT("_Container"))));
        Root->AddChild(VBox);
        MonolithUIInternal::ConfigureCanvasSlot(VBox->Slot, TEXT("bottom_left"), FVector2D(20, -150), FVector2D(300, 40), false, FVector2D(0.f, 1.f));

        UTextBlock* Label = WBP->WidgetTree->ConstructWidget<UTextBlock>(UTextBlock::StaticClass(), FName(*(Prefix + TEXT("_Label"))));
        VBox->AddChild(Label);
        Label->SetText(FText::FromString(TEXT("STAMINA")));

        UProgressBar* Bar = WBP->WidgetTree->ConstructWidget<UProgressBar>(UProgressBar::StaticClass(), FName(*(Prefix + TEXT("_Bar"))));
        VBox->AddChild(Bar);
        Bar->SetPercent(1.0f);
        if (UVerticalBoxSlot* VS = Cast<UVerticalBoxSlot>(Bar->Slot))
        {
            VS->SetHorizontalAlignment(HAlign_Fill);
        }
        WidgetsCreated = 3;
    }
    // --- INTERACTION_PROMPT ---
    else if (ElementType == TEXT("interaction_prompt"))
    {
        UVerticalBox* VBox = WBP->WidgetTree->ConstructWidget<UVerticalBox>(UVerticalBox::StaticClass(), FName(*(Prefix + TEXT("_Container"))));
        Root->AddChild(VBox);
        MonolithUIInternal::ConfigureCanvasSlot(VBox->Slot, TEXT("bottom_center"), FVector2D(0, -120), FVector2D(400, 60), false, FVector2D(0.5f, 1.f));

        UTextBlock* ActionText = WBP->WidgetTree->ConstructWidget<UTextBlock>(UTextBlock::StaticClass(), FName(*(Prefix + TEXT("_Action"))));
        VBox->AddChild(ActionText);
        ActionText->SetText(FText::FromString(TEXT("Pick Up")));
        ActionText->SetJustification(ETextJustify::Center);
        if (UVerticalBoxSlot* VS = Cast<UVerticalBoxSlot>(ActionText->Slot))
        {
            VS->SetHorizontalAlignment(HAlign_Center);
        }

        UTextBlock* KeyHint = WBP->WidgetTree->ConstructWidget<UTextBlock>(UTextBlock::StaticClass(), FName(*(Prefix + TEXT("_KeyHint"))));
        VBox->AddChild(KeyHint);
        KeyHint->SetText(FText::FromString(TEXT("[E]")));
        KeyHint->SetJustification(ETextJustify::Center);
        if (UVerticalBoxSlot* VS = Cast<UVerticalBoxSlot>(KeyHint->Slot))
        {
            VS->SetHorizontalAlignment(HAlign_Center);
            VS->SetPadding(FMargin(0, 4, 0, 0));
        }
        WidgetsCreated = 3;
    }
    // --- DAMAGE_INDICATOR ---
    else if (ElementType == TEXT("damage_indicator"))
    {
        // Full-screen overlay Image for directional damage vignette
        UOverlay* Container = WBP->WidgetTree->ConstructWidget<UOverlay>(UOverlay::StaticClass(), FName(*(Prefix + TEXT("_Container"))));
        Root->AddChild(Container);
        MonolithUIInternal::ConfigureCanvasSlot(Container->Slot, TEXT("stretch_fill"));

        UImage* DamageVignette = WBP->WidgetTree->ConstructWidget<UImage>(UImage::StaticClass(), FName(*(Prefix + TEXT("_Vignette"))));
        Container->AddChild(DamageVignette);
        DamageVignette->SetRenderOpacity(0.f); // hidden by default, driven by gameplay
        if (UOverlaySlot* OS = Cast<UOverlaySlot>(DamageVignette->Slot))
        {
            OS->SetHorizontalAlignment(HAlign_Fill);
            OS->SetVerticalAlignment(VAlign_Fill);
        }
        WidgetsCreated = 2;
    }
    // --- COMPASS ---
    else if (ElementType == TEXT("compass"))
    {
        USizeBox* SBox = WBP->WidgetTree->ConstructWidget<USizeBox>(USizeBox::StaticClass(), FName(*(Prefix + TEXT("_Container"))));
        Root->AddChild(SBox);
        MonolithUIInternal::ConfigureCanvasSlot(SBox->Slot, TEXT("top_center"), FVector2D(0, 20), FVector2D(400, 40), false, FVector2D(0.5f, 0.f));
        SBox->SetWidthOverride(400.f);
        SBox->SetHeightOverride(40.f);

        UOverlay* Inner = WBP->WidgetTree->ConstructWidget<UOverlay>(UOverlay::StaticClass(), FName(*(Prefix + TEXT("_Inner"))));
        SBox->AddChild(Inner);

        UImage* Strip = WBP->WidgetTree->ConstructWidget<UImage>(UImage::StaticClass(), FName(*(Prefix + TEXT("_Strip"))));
        Inner->AddChild(Strip);

        UTextBlock* Bearing = WBP->WidgetTree->ConstructWidget<UTextBlock>(UTextBlock::StaticClass(), FName(*(Prefix + TEXT("_Bearing"))));
        Inner->AddChild(Bearing);
        Bearing->SetText(FText::FromString(TEXT("N")));
        Bearing->SetJustification(ETextJustify::Center);
        if (UOverlaySlot* OS = Cast<UOverlaySlot>(Bearing->Slot))
        {
            OS->SetHorizontalAlignment(HAlign_Center);
            OS->SetVerticalAlignment(VAlign_Center);
        }
        WidgetsCreated = 4;
    }
    // --- SUBTITLES ---
    else if (ElementType == TEXT("subtitles"))
    {
        UBorder* Container = WBP->WidgetTree->ConstructWidget<UBorder>(UBorder::StaticClass(), FName(*(Prefix + TEXT("_Container"))));
        Root->AddChild(Container);
        MonolithUIInternal::ConfigureCanvasSlot(Container->Slot, TEXT("stretch_horizontal"), FVector2D(100, -80), FVector2D(-200, 60), false, FVector2D(0.f, 1.f));
        // Offsets: left=100, right=100 (symmetric), bottom anchored
        if (UCanvasPanelSlot* CS = Cast<UCanvasPanelSlot>(Container->Slot))
        {
            CS->SetAnchors(FAnchors(0.f, 1.f, 1.f, 1.f)); // stretch bottom
            CS->SetOffsets(FMargin(100, -80, 100, 20)); // left, top, right, bottom
        }
        Container->SetBrushColor(FLinearColor(0.f, 0.f, 0.f, 0.5f)); // semi-transparent black

        UTextBlock* SubText = WBP->WidgetTree->ConstructWidget<UTextBlock>(UTextBlock::StaticClass(), FName(*(Prefix + TEXT("_Text"))));
        Container->AddChild(SubText);
        SubText->SetText(FText::FromString(TEXT("Subtitle text goes here.")));
        SubText->SetJustification(ETextJustify::Center);
        WidgetsCreated = 2;
    }
    // --- FLASHLIGHT_BATTERY ---
    else if (ElementType == TEXT("flashlight_battery"))
    {
        UHorizontalBox* HBox = WBP->WidgetTree->ConstructWidget<UHorizontalBox>(UHorizontalBox::StaticClass(), FName(*(Prefix + TEXT("_Container"))));
        Root->AddChild(HBox);
        MonolithUIInternal::ConfigureCanvasSlot(HBox->Slot, TEXT("bottom_right"), FVector2D(-20, -100), FVector2D(180, 30), false, FVector2D(1.f, 1.f));

        UImage* Icon = WBP->WidgetTree->ConstructWidget<UImage>(UImage::StaticClass(), FName(*(Prefix + TEXT("_Icon"))));
        HBox->AddChild(Icon);
        if (UHorizontalBoxSlot* HS = Cast<UHorizontalBoxSlot>(Icon->Slot))
        {
            HS->SetVerticalAlignment(VAlign_Center);
            HS->SetPadding(FMargin(0, 0, 8, 0));
        }

        UProgressBar* Battery = WBP->WidgetTree->ConstructWidget<UProgressBar>(UProgressBar::StaticClass(), FName(*(Prefix + TEXT("_Bar"))));
        HBox->AddChild(Battery);
        Battery->SetPercent(0.75f);
        if (UHorizontalBoxSlot* HS = Cast<UHorizontalBoxSlot>(Battery->Slot))
        {
            HS->SetVerticalAlignment(VAlign_Center);
            HS->SetSize(FSlateChildSize(ESlateSizeRule::Fill)); // Fill
        }
        WidgetsCreated = 3;
    }
    else
    {
        return FMonolithActionResult::Error(
            FString::Printf(TEXT("Unknown element_type: '%s'. Valid types: crosshair, health_bar, ammo_counter, stamina_bar, interaction_prompt, damage_indicator, compass, subtitles, flashlight_battery"), *ElementType));
    }

    MonolithUIInternal::ReconcileWidgetVariableGuids(WBP);
    FBlueprintEditorUtils::MarkBlueprintAsStructurallyModified(WBP);

    const bool bCompile = MonolithUIInternal::GetOptionalBool(Params, TEXT("compile"), true);
    if (bCompile) FKismetEditorUtilities::CompileBlueprint(WBP);

    TSharedPtr<FJsonObject> Result = MakeShared<FJsonObject>();
    Result->SetStringField(TEXT("asset_path"), AssetPath);
    Result->SetStringField(TEXT("element_type"), ElementType);
    Result->SetStringField(TEXT("prefix"), Prefix);
    Result->SetNumberField(TEXT("widgets_created"), WidgetsCreated);
    Result->SetBoolField(TEXT("compiled"), bCompile);
    return FMonolithActionResult::Success(Result);
}

// --- create_menu ---
FMonolithActionResult FMonolithUITemplateActions::HandleCreateMenu(const TSharedPtr<FJsonObject>& Params)
{
    FString SavePath = Params->GetStringField(TEXT("save_path"));
    if (SavePath.IsEmpty())
    {
        return FMonolithActionResult::Error(TEXT("Missing required param: save_path"));
    }

    FString MenuType = Params->GetStringField(TEXT("menu_type"));
    if (MenuType.IsEmpty())
    {
        return FMonolithActionResult::Error(TEXT("Missing required param: menu_type"));
    }

    // Default buttons per menu type
    TArray<FString> ButtonLabels;
    const TArray<TSharedPtr<FJsonValue>>* ButtonsArray = nullptr;
    if (Params->TryGetArrayField(TEXT("buttons"), ButtonsArray))
    {
        for (const auto& Val : *ButtonsArray)
        {
            ButtonLabels.Add(Val->AsString());
        }
    }

    if (ButtonLabels.Num() == 0)
    {
        if (MenuType == TEXT("main_menu"))
        {
            ButtonLabels = { TEXT("Continue"), TEXT("New Game"), TEXT("Settings"), TEXT("Credits"), TEXT("Quit") };
        }
        else if (MenuType == TEXT("pause_menu"))
        {
            ButtonLabels = { TEXT("Resume"), TEXT("Settings"), TEXT("Quit to Menu") };
        }
        else if (MenuType == TEXT("death_screen"))
        {
            ButtonLabels = { TEXT("Respawn"), TEXT("Load Save"), TEXT("Quit to Menu") };
        }
        else if (MenuType == TEXT("credits"))
        {
            ButtonLabels = { TEXT("Back") };
        }
        else
        {
            return FMonolithActionResult::Error(
                FString::Printf(TEXT("Unknown menu_type: '%s'. Valid types: main_menu, pause_menu, death_screen, credits"), *MenuType));
        }
    }

    // Create the widget blueprint
    FMonolithActionResult Err;
    UWidgetBlueprint* WBP = MonolithUIInternal::CreateNewWidgetBlueprint(SavePath, Err);
    if (!WBP) return Err;

    UCanvasPanel* Root = Cast<UCanvasPanel>(WBP->WidgetTree->RootWidget);

    // Background overlay (full-screen dim for pause/death, solid for main menu)
    UImage* BG = WBP->WidgetTree->ConstructWidget<UImage>(UImage::StaticClass(), TEXT("Background"));
    Root->AddChild(BG);
    MonolithUIInternal::ConfigureCanvasSlot(BG->Slot, TEXT("stretch_fill"));
    if (MenuType == TEXT("pause_menu") || MenuType == TEXT("death_screen"))
    {
        BG->SetColorAndOpacity(FLinearColor(0.f, 0.f, 0.f, 0.6f));
    }

    // Title text
    FString TitleText = MenuType == TEXT("main_menu") ? TEXT("LEVIATHAN") :
                        MenuType == TEXT("pause_menu") ? TEXT("PAUSED") :
                        MenuType == TEXT("death_screen") ? TEXT("YOU DIED") :
                        TEXT("CREDITS");

    UTextBlock* Title = WBP->WidgetTree->ConstructWidget<UTextBlock>(UTextBlock::StaticClass(), TEXT("TitleText"));
    Root->AddChild(Title);
    Title->SetText(FText::FromString(TitleText));
    Title->SetJustification(ETextJustify::Center);
    MonolithUIInternal::ConfigureCanvasSlot(Title->Slot, TEXT("top_center"), FVector2D(0, 80), FVector2D(600, 60), true, FVector2D(0.5f, 0.f));

    // Credits: scrolling text block instead of buttons
    if (MenuType == TEXT("credits"))
    {
        UScrollBox* CreditsScroll = WBP->WidgetTree->ConstructWidget<UScrollBox>(UScrollBox::StaticClass(), TEXT("CreditsScroll"));
        Root->AddChild(CreditsScroll);
        MonolithUIInternal::ConfigureCanvasSlot(CreditsScroll->Slot, TEXT("center"), FVector2D(0, 40), FVector2D(500, 400), false, FVector2D(0.5f, 0.5f));

        URichTextBlock* CreditsText = WBP->WidgetTree->ConstructWidget<URichTextBlock>(URichTextBlock::StaticClass(), TEXT("CreditsText"));
        CreditsScroll->AddChild(CreditsText);
    }

    // Button container
    UVerticalBox* ButtonBox = WBP->WidgetTree->ConstructWidget<UVerticalBox>(UVerticalBox::StaticClass(), TEXT("ButtonContainer"));
    Root->AddChild(ButtonBox);

    if (MenuType == TEXT("credits"))
    {
        MonolithUIInternal::ConfigureCanvasSlot(ButtonBox->Slot, TEXT("bottom_center"), FVector2D(0, -40), FVector2D(300, 60), true, FVector2D(0.5f, 1.f));
    }
    else
    {
        MonolithUIInternal::ConfigureCanvasSlot(ButtonBox->Slot, TEXT("center"), FVector2D(0, 40), FVector2D(300, 0), true, FVector2D(0.5f, 0.5f));
    }

    // Create buttons
    for (int32 i = 0; i < ButtonLabels.Num(); ++i)
    {
        FString BtnName = FString::Printf(TEXT("Btn_%s"), *ButtonLabels[i].Replace(TEXT(" "), TEXT("")));
        UButton* Btn = WBP->WidgetTree->ConstructWidget<UButton>(UButton::StaticClass(), FName(*BtnName));
        ButtonBox->AddChild(Btn);
        if (UVerticalBoxSlot* VS = Cast<UVerticalBoxSlot>(Btn->Slot))
        {
            VS->SetHorizontalAlignment(HAlign_Fill);
            VS->SetPadding(FMargin(0, 4, 0, 4));
        }

        FString LabelName = FString::Printf(TEXT("BtnLabel_%s"), *ButtonLabels[i].Replace(TEXT(" "), TEXT("")));
        UTextBlock* BtnLabel = WBP->WidgetTree->ConstructWidget<UTextBlock>(UTextBlock::StaticClass(), FName(*LabelName));
        Btn->AddChild(BtnLabel);
        BtnLabel->SetText(FText::FromString(ButtonLabels[i]));
        BtnLabel->SetJustification(ETextJustify::Center);
    }

    // Compile and save
    MonolithUIInternal::SaveAndCompileWidgetBlueprint(WBP, SavePath);

    TSharedPtr<FJsonObject> Result = MakeShared<FJsonObject>();
    Result->SetStringField(TEXT("asset_path"), SavePath);
    Result->SetStringField(TEXT("menu_type"), MenuType);
    Result->SetNumberField(TEXT("button_count"), ButtonLabels.Num());
    Result->SetBoolField(TEXT("compiled"), true);
    Result->SetBoolField(TEXT("saved"), true);
    return FMonolithActionResult::Success(Result);
}

// --- create_settings_panel ---
FMonolithActionResult FMonolithUITemplateActions::HandleCreateSettingsPanel(const TSharedPtr<FJsonObject>& Params)
{
    FString SavePath = Params->GetStringField(TEXT("save_path"));
    if (SavePath.IsEmpty())
    {
        return FMonolithActionResult::Error(TEXT("Missing required param: save_path"));
    }

    // Parse tabs
    TArray<FString> Tabs;
    const TArray<TSharedPtr<FJsonValue>>* TabsArray = nullptr;
    if (Params->TryGetArrayField(TEXT("tabs"), TabsArray))
    {
        for (const auto& Val : *TabsArray)
        {
            Tabs.Add(Val->AsString());
        }
    }
    if (Tabs.Num() == 0)
    {
        Tabs = { TEXT("Graphics"), TEXT("Audio"), TEXT("Controls"), TEXT("Gameplay"), TEXT("Accessibility") };
    }

    FMonolithActionResult Err;
    UWidgetBlueprint* WBP = MonolithUIInternal::CreateNewWidgetBlueprint(SavePath, Err);
    if (!WBP) return Err;

    UCanvasPanel* Root = Cast<UCanvasPanel>(WBP->WidgetTree->RootWidget);

    // Main container: VerticalBox stretching most of the screen
    UVerticalBox* MainVBox = WBP->WidgetTree->ConstructWidget<UVerticalBox>(UVerticalBox::StaticClass(), TEXT("MainContainer"));
    Root->AddChild(MainVBox);
    MonolithUIInternal::ConfigureCanvasSlot(MainVBox->Slot, TEXT("stretch_fill"));
    if (UCanvasPanelSlot* CS = Cast<UCanvasPanelSlot>(MainVBox->Slot))
    {
        CS->SetOffsets(FMargin(40, 40, 40, 40)); // 40px margin all around
    }

    // Tab bar: HorizontalBox of buttons
    UHorizontalBox* TabBar = WBP->WidgetTree->ConstructWidget<UHorizontalBox>(UHorizontalBox::StaticClass(), TEXT("TabBar"));
    MainVBox->AddChild(TabBar);
    if (UVerticalBoxSlot* VS = Cast<UVerticalBoxSlot>(TabBar->Slot))
    {
        VS->SetHorizontalAlignment(HAlign_Fill);
        VS->SetPadding(FMargin(0, 0, 0, 8));
    }

    for (int32 i = 0; i < Tabs.Num(); ++i)
    {
        FString TabBtnName = FString::Printf(TEXT("TabBtn_%s"), *Tabs[i]);
        UButton* TabBtn = WBP->WidgetTree->ConstructWidget<UButton>(UButton::StaticClass(), FName(*TabBtnName));
        TabBar->AddChild(TabBtn);
        if (UHorizontalBoxSlot* HS = Cast<UHorizontalBoxSlot>(TabBtn->Slot))
        {
            HS->SetPadding(FMargin(0, 0, 4, 0));
        }

        FString TabLabelName = FString::Printf(TEXT("TabLabel_%s"), *Tabs[i]);
        UTextBlock* TabLabel = WBP->WidgetTree->ConstructWidget<UTextBlock>(UTextBlock::StaticClass(), FName(*TabLabelName));
        TabBtn->AddChild(TabLabel);
        TabLabel->SetText(FText::FromString(Tabs[i].ToUpper()));
        TabLabel->SetJustification(ETextJustify::Center);
    }

    // WidgetSwitcher for tab content panels
    UWidgetSwitcher* Switcher = WBP->WidgetTree->ConstructWidget<UWidgetSwitcher>(UWidgetSwitcher::StaticClass(), TEXT("TabSwitcher"));
    MainVBox->AddChild(Switcher);
    if (UVerticalBoxSlot* VS = Cast<UVerticalBoxSlot>(Switcher->Slot))
    {
        VS->SetSize(FSlateChildSize(ESlateSizeRule::Fill)); // Fill
        VS->SetHorizontalAlignment(HAlign_Fill);
    }

    // Create a ScrollBox panel for each tab
    for (int32 i = 0; i < Tabs.Num(); ++i)
    {
        FString PanelName = FString::Printf(TEXT("Panel_%s"), *Tabs[i]);
        UScrollBox* Panel = WBP->WidgetTree->ConstructWidget<UScrollBox>(UScrollBox::StaticClass(), FName(*PanelName));
        Switcher->AddChild(Panel);

        // Add a placeholder label
        FString PlaceholderName = FString::Printf(TEXT("Placeholder_%s"), *Tabs[i]);
        UTextBlock* Placeholder = WBP->WidgetTree->ConstructWidget<UTextBlock>(UTextBlock::StaticClass(), FName(*PlaceholderName));
        Panel->AddChild(Placeholder);
        Placeholder->SetText(FText::FromString(FString::Printf(TEXT("%s settings go here"), *Tabs[i])));
    }

    // Bottom bar: Apply / Revert / Back buttons
    UHorizontalBox* BottomBar = WBP->WidgetTree->ConstructWidget<UHorizontalBox>(UHorizontalBox::StaticClass(), TEXT("BottomBar"));
    MainVBox->AddChild(BottomBar);
    if (UVerticalBoxSlot* VS = Cast<UVerticalBoxSlot>(BottomBar->Slot))
    {
        VS->SetHorizontalAlignment(HAlign_Right);
        VS->SetPadding(FMargin(0, 8, 0, 0));
    }

    TArray<FString> BottomButtons = { TEXT("Apply"), TEXT("Revert"), TEXT("Back") };
    for (const FString& BtnText : BottomButtons)
    {
        FString BtnName = FString::Printf(TEXT("Btn_%s"), *BtnText);
        UButton* Btn = WBP->WidgetTree->ConstructWidget<UButton>(UButton::StaticClass(), FName(*BtnName));
        BottomBar->AddChild(Btn);
        if (UHorizontalBoxSlot* HS = Cast<UHorizontalBoxSlot>(Btn->Slot))
        {
            HS->SetPadding(FMargin(4, 0, 4, 0));
        }

        FString LblName = FString::Printf(TEXT("BtnLabel_%s"), *BtnText);
        UTextBlock* Lbl = WBP->WidgetTree->ConstructWidget<UTextBlock>(UTextBlock::StaticClass(), FName(*LblName));
        Btn->AddChild(Lbl);
        Lbl->SetText(FText::FromString(BtnText));
        Lbl->SetJustification(ETextJustify::Center);
    }

    MonolithUIInternal::SaveAndCompileWidgetBlueprint(WBP, SavePath);

    TSharedPtr<FJsonObject> Result = MakeShared<FJsonObject>();
    Result->SetStringField(TEXT("asset_path"), SavePath);
    Result->SetNumberField(TEXT("tab_count"), Tabs.Num());
    Result->SetBoolField(TEXT("compiled"), true);
    Result->SetBoolField(TEXT("saved"), true);
    return FMonolithActionResult::Success(Result);
}

// --- create_dialog ---
FMonolithActionResult FMonolithUITemplateActions::HandleCreateDialog(const TSharedPtr<FJsonObject>& Params)
{
    FString SavePath = Params->GetStringField(TEXT("save_path"));
    if (SavePath.IsEmpty())
    {
        return FMonolithActionResult::Error(TEXT("Missing required param: save_path"));
    }

    FString Title = MonolithUIInternal::GetOptionalString(Params, TEXT("title"));
    if (Title.IsEmpty()) Title = TEXT("Confirm");
    FString Body = MonolithUIInternal::GetOptionalString(Params, TEXT("body"));
    if (Body.IsEmpty()) Body = TEXT("Are you sure?");
    FString ConfirmText = MonolithUIInternal::GetOptionalString(Params, TEXT("confirm_text"));
    if (ConfirmText.IsEmpty()) ConfirmText = TEXT("Yes");
    FString CancelText = MonolithUIInternal::GetOptionalString(Params, TEXT("cancel_text"));
    if (CancelText.IsEmpty()) CancelText = TEXT("No");

    FMonolithActionResult Err;
    UWidgetBlueprint* WBP = MonolithUIInternal::CreateNewWidgetBlueprint(SavePath, Err);
    if (!WBP) return Err;

    UCanvasPanel* Root = Cast<UCanvasPanel>(WBP->WidgetTree->RootWidget);

    // Dim background
    UImage* DimBG = WBP->WidgetTree->ConstructWidget<UImage>(UImage::StaticClass(), TEXT("DimBackground"));
    Root->AddChild(DimBG);
    MonolithUIInternal::ConfigureCanvasSlot(DimBG->Slot, TEXT("stretch_fill"));
    DimBG->SetColorAndOpacity(FLinearColor(0.f, 0.f, 0.f, 0.5f));

    // Dialog box: Border centered
    UBorder* DialogBox = WBP->WidgetTree->ConstructWidget<UBorder>(UBorder::StaticClass(), TEXT("DialogBox"));
    Root->AddChild(DialogBox);
    MonolithUIInternal::ConfigureCanvasSlot(DialogBox->Slot, TEXT("center"), FVector2D::ZeroVector, FVector2D(450, 250), false, FVector2D(0.5f, 0.5f));
    DialogBox->SetBrushColor(FLinearColor(0.05f, 0.05f, 0.08f, 0.95f));

    // Inner layout: VerticalBox
    UVerticalBox* VBox = WBP->WidgetTree->ConstructWidget<UVerticalBox>(UVerticalBox::StaticClass(), TEXT("DialogContent"));
    DialogBox->AddChild(VBox);

    // Title
    UTextBlock* TitleText = WBP->WidgetTree->ConstructWidget<UTextBlock>(UTextBlock::StaticClass(), TEXT("DialogTitle"));
    VBox->AddChild(TitleText);
    TitleText->SetText(FText::FromString(Title));
    TitleText->SetJustification(ETextJustify::Center);
    if (UVerticalBoxSlot* VS = Cast<UVerticalBoxSlot>(TitleText->Slot))
    {
        VS->SetHorizontalAlignment(HAlign_Fill);
        VS->SetPadding(FMargin(20, 20, 20, 10));
    }

    // Body
    UTextBlock* BodyText = WBP->WidgetTree->ConstructWidget<UTextBlock>(UTextBlock::StaticClass(), TEXT("DialogBody"));
    VBox->AddChild(BodyText);
    BodyText->SetText(FText::FromString(Body));
    BodyText->SetJustification(ETextJustify::Center);
    if (UVerticalBoxSlot* VS = Cast<UVerticalBoxSlot>(BodyText->Slot))
    {
        VS->SetHorizontalAlignment(HAlign_Fill);
        VS->SetSize(FSlateChildSize(ESlateSizeRule::Fill)); // Fill
        VS->SetPadding(FMargin(20, 10, 20, 10));
    }

    // Spacer
    USpacer* Space = WBP->WidgetTree->ConstructWidget<USpacer>(USpacer::StaticClass(), TEXT("DialogSpacer"));
    VBox->AddChild(Space);
    if (UVerticalBoxSlot* VS = Cast<UVerticalBoxSlot>(Space->Slot))
    {
        VS->SetSize(FSlateChildSize(ESlateSizeRule::Fill)); // Fill remaining space
    }

    // Button row
    UHorizontalBox* BtnRow = WBP->WidgetTree->ConstructWidget<UHorizontalBox>(UHorizontalBox::StaticClass(), TEXT("DialogButtons"));
    VBox->AddChild(BtnRow);
    if (UVerticalBoxSlot* VS = Cast<UVerticalBoxSlot>(BtnRow->Slot))
    {
        VS->SetHorizontalAlignment(HAlign_Center);
        VS->SetPadding(FMargin(20, 10, 20, 20));
    }

    // Confirm button
    UButton* ConfirmBtn = WBP->WidgetTree->ConstructWidget<UButton>(UButton::StaticClass(), TEXT("Btn_Confirm"));
    BtnRow->AddChild(ConfirmBtn);
    if (UHorizontalBoxSlot* HS = Cast<UHorizontalBoxSlot>(ConfirmBtn->Slot))
    {
        HS->SetPadding(FMargin(0, 0, 8, 0));
    }
    UTextBlock* ConfirmLabel = WBP->WidgetTree->ConstructWidget<UTextBlock>(UTextBlock::StaticClass(), TEXT("ConfirmLabel"));
    ConfirmBtn->AddChild(ConfirmLabel);
    ConfirmLabel->SetText(FText::FromString(ConfirmText));
    ConfirmLabel->SetJustification(ETextJustify::Center);

    // Cancel button
    UButton* CancelBtn = WBP->WidgetTree->ConstructWidget<UButton>(UButton::StaticClass(), TEXT("Btn_Cancel"));
    BtnRow->AddChild(CancelBtn);
    if (UHorizontalBoxSlot* HS = Cast<UHorizontalBoxSlot>(CancelBtn->Slot))
    {
        HS->SetPadding(FMargin(8, 0, 0, 0));
    }
    UTextBlock* CancelLabel = WBP->WidgetTree->ConstructWidget<UTextBlock>(UTextBlock::StaticClass(), TEXT("CancelLabel"));
    CancelBtn->AddChild(CancelLabel);
    CancelLabel->SetText(FText::FromString(CancelText));
    CancelLabel->SetJustification(ETextJustify::Center);

    MonolithUIInternal::SaveAndCompileWidgetBlueprint(WBP, SavePath);

    TSharedPtr<FJsonObject> Result = MakeShared<FJsonObject>();
    Result->SetStringField(TEXT("asset_path"), SavePath);
    Result->SetStringField(TEXT("title"), Title);
    Result->SetStringField(TEXT("confirm_text"), ConfirmText);
    Result->SetStringField(TEXT("cancel_text"), CancelText);
    Result->SetBoolField(TEXT("compiled"), true);
    Result->SetBoolField(TEXT("saved"), true);
    return FMonolithActionResult::Success(Result);
}

// --- create_notification_toast ---
FMonolithActionResult FMonolithUITemplateActions::HandleCreateNotificationToast(const TSharedPtr<FJsonObject>& Params)
{
    FString SavePath = Params->GetStringField(TEXT("save_path"));
    if (SavePath.IsEmpty())
    {
        return FMonolithActionResult::Error(TEXT("Missing required param: save_path"));
    }

    FString Position = MonolithUIInternal::GetOptionalString(Params, TEXT("position"));
    if (Position.IsEmpty()) Position = TEXT("top_right");

    FMonolithActionResult Err;
    UWidgetBlueprint* WBP = MonolithUIInternal::CreateNewWidgetBlueprint(SavePath, Err);
    if (!WBP) return Err;

    UCanvasPanel* Root = Cast<UCanvasPanel>(WBP->WidgetTree->RootWidget);

    // Map position to anchor + offset + alignment
    FString AnchorPreset;
    FVector2D Offset;
    FVector2D Align;
    if (Position == TEXT("top_right"))        { AnchorPreset = TEXT("top_right");     Offset = FVector2D(-20, 20);   Align = FVector2D(1.f, 0.f); }
    else if (Position == TEXT("bottom_right")) { AnchorPreset = TEXT("bottom_right"); Offset = FVector2D(-20, -20);  Align = FVector2D(1.f, 1.f); }
    else if (Position == TEXT("top_left"))     { AnchorPreset = TEXT("top_left");     Offset = FVector2D(20, 20);    Align = FVector2D(0.f, 0.f); }
    else if (Position == TEXT("bottom_left"))  { AnchorPreset = TEXT("bottom_left");  Offset = FVector2D(20, -20);   Align = FVector2D(0.f, 1.f); }
    else if (Position == TEXT("top_center"))   { AnchorPreset = TEXT("top_center");   Offset = FVector2D(0, 20);     Align = FVector2D(0.5f, 0.f); }
    else
    {
        AnchorPreset = TEXT("top_right");
        Offset = FVector2D(-20, 20);
        Align = FVector2D(1.f, 0.f);
    }

    // Toast container: Border (rounded look)
    UBorder* Toast = WBP->WidgetTree->ConstructWidget<UBorder>(UBorder::StaticClass(), TEXT("ToastBorder"));
    Root->AddChild(Toast);
    MonolithUIInternal::ConfigureCanvasSlot(Toast->Slot, AnchorPreset, Offset, FVector2D(350, 60), false, Align);
    Toast->SetBrushColor(FLinearColor(0.1f, 0.1f, 0.15f, 0.9f));

    // Inner: HorizontalBox → Image (icon) + TextBlock (message)
    UHorizontalBox* HBox = WBP->WidgetTree->ConstructWidget<UHorizontalBox>(UHorizontalBox::StaticClass(), TEXT("ToastContent"));
    Toast->AddChild(HBox);

    UImage* Icon = WBP->WidgetTree->ConstructWidget<UImage>(UImage::StaticClass(), TEXT("ToastIcon"));
    HBox->AddChild(Icon);
    if (UHorizontalBoxSlot* HS = Cast<UHorizontalBoxSlot>(Icon->Slot))
    {
        HS->SetVerticalAlignment(VAlign_Center);
        HS->SetPadding(FMargin(8, 8, 12, 8));
    }

    UTextBlock* Message = WBP->WidgetTree->ConstructWidget<UTextBlock>(UTextBlock::StaticClass(), TEXT("ToastMessage"));
    HBox->AddChild(Message);
    Message->SetText(FText::FromString(TEXT("Notification text")));
    if (UHorizontalBoxSlot* HS = Cast<UHorizontalBoxSlot>(Message->Slot))
    {
        HS->SetVerticalAlignment(VAlign_Center);
        HS->SetSize(FSlateChildSize(ESlateSizeRule::Fill)); // Fill
        HS->SetPadding(FMargin(0, 8, 8, 8));
    }

    MonolithUIInternal::SaveAndCompileWidgetBlueprint(WBP, SavePath);

    TSharedPtr<FJsonObject> Result = MakeShared<FJsonObject>();
    Result->SetStringField(TEXT("asset_path"), SavePath);
    Result->SetStringField(TEXT("position"), Position);
    Result->SetBoolField(TEXT("compiled"), true);
    Result->SetBoolField(TEXT("saved"), true);
    return FMonolithActionResult::Success(Result);
}

// --- create_loading_screen ---
FMonolithActionResult FMonolithUITemplateActions::HandleCreateLoadingScreen(const TSharedPtr<FJsonObject>& Params)
{
    FString SavePath = Params->GetStringField(TEXT("save_path"));
    if (SavePath.IsEmpty())
    {
        return FMonolithActionResult::Error(TEXT("Missing required param: save_path"));
    }

    const bool bShowProgress = MonolithUIInternal::GetOptionalBool(Params, TEXT("show_progress"), true);
    const bool bShowTips = MonolithUIInternal::GetOptionalBool(Params, TEXT("show_tips"), true);
    const bool bShowSpinner = MonolithUIInternal::GetOptionalBool(Params, TEXT("show_spinner"), true);

    FMonolithActionResult Err;
    UWidgetBlueprint* WBP = MonolithUIInternal::CreateNewWidgetBlueprint(SavePath, Err);
    if (!WBP) return Err;

    UCanvasPanel* Root = Cast<UCanvasPanel>(WBP->WidgetTree->RootWidget);

    // Full-screen background image
    UImage* BG = WBP->WidgetTree->ConstructWidget<UImage>(UImage::StaticClass(), TEXT("BackgroundImage"));
    Root->AddChild(BG);
    MonolithUIInternal::ConfigureCanvasSlot(BG->Slot, TEXT("stretch_fill"));
    BG->SetColorAndOpacity(FLinearColor(0.02f, 0.02f, 0.04f, 1.f));

    int32 WidgetsCreated = 1;

    // Progress bar at bottom
    if (bShowProgress)
    {
        UProgressBar* Progress = WBP->WidgetTree->ConstructWidget<UProgressBar>(UProgressBar::StaticClass(), TEXT("LoadingProgress"));
        Root->AddChild(Progress);
        if (UCanvasPanelSlot* CS = Cast<UCanvasPanelSlot>(Progress->Slot))
        {
            CS->SetAnchors(FAnchors(0.f, 1.f, 1.f, 1.f)); // stretch bottom
            CS->SetOffsets(FMargin(40, -60, 40, 40)); // left, top, right, bottom margins
        }
        Progress->SetPercent(0.f);
        WidgetsCreated++;
    }

    // Tip text above progress bar
    if (bShowTips)
    {
        UTextBlock* Tip = WBP->WidgetTree->ConstructWidget<UTextBlock>(UTextBlock::StaticClass(), TEXT("TipText"));
        Root->AddChild(Tip);
        MonolithUIInternal::ConfigureCanvasSlot(Tip->Slot, TEXT("bottom_center"), FVector2D(0, bShowProgress ? -100 : -60), FVector2D(600, 40), true, FVector2D(0.5f, 1.f));
        Tip->SetText(FText::FromString(TEXT("TIP: Stay in the light.")));
        Tip->SetJustification(ETextJustify::Center);
        WidgetsCreated++;
    }

    // Spinner image (rotated via animation in BP)
    if (bShowSpinner)
    {
        UImage* Spinner = WBP->WidgetTree->ConstructWidget<UImage>(UImage::StaticClass(), TEXT("SpinnerImage"));
        Root->AddChild(Spinner);
        MonolithUIInternal::ConfigureCanvasSlot(Spinner->Slot, TEXT("bottom_right"), FVector2D(-60, -60), FVector2D(48, 48), false, FVector2D(1.f, 1.f));
        WidgetsCreated++;
    }

    MonolithUIInternal::SaveAndCompileWidgetBlueprint(WBP, SavePath);

    TSharedPtr<FJsonObject> Result = MakeShared<FJsonObject>();
    Result->SetStringField(TEXT("asset_path"), SavePath);
    Result->SetBoolField(TEXT("has_progress"), bShowProgress);
    Result->SetBoolField(TEXT("has_tips"), bShowTips);
    Result->SetBoolField(TEXT("has_spinner"), bShowSpinner);
    Result->SetNumberField(TEXT("widgets_created"), WidgetsCreated);
    Result->SetBoolField(TEXT("compiled"), true);
    Result->SetBoolField(TEXT("saved"), true);
    return FMonolithActionResult::Success(Result);
}

// --- create_inventory_grid ---
FMonolithActionResult FMonolithUITemplateActions::HandleCreateInventoryGrid(const TSharedPtr<FJsonObject>& Params)
{
    FString SavePath = Params->GetStringField(TEXT("save_path"));
    if (SavePath.IsEmpty())
    {
        return FMonolithActionResult::Error(TEXT("Missing required param: save_path"));
    }

    int32 Columns = Params->HasField(TEXT("columns")) ? static_cast<int32>(Params->GetNumberField(TEXT("columns"))) : 5;
    int32 Rows = Params->HasField(TEXT("rows")) ? static_cast<int32>(Params->GetNumberField(TEXT("rows"))) : 4;
    int32 SlotSize = Params->HasField(TEXT("slot_size")) ? static_cast<int32>(Params->GetNumberField(TEXT("slot_size"))) : 64;
    Columns = FMath::Clamp(Columns, 1, 20);
    Rows = FMath::Clamp(Rows, 1, 20);
    SlotSize = FMath::Clamp(SlotSize, 16, 256);

    FMonolithActionResult Err;
    UWidgetBlueprint* WBP = MonolithUIInternal::CreateNewWidgetBlueprint(SavePath, Err);
    if (!WBP) return Err;

    UCanvasPanel* Root = Cast<UCanvasPanel>(WBP->WidgetTree->RootWidget);

    // ScrollBox → UniformGridPanel
    UScrollBox* Scroll = WBP->WidgetTree->ConstructWidget<UScrollBox>(UScrollBox::StaticClass(), TEXT("InventoryScroll"));
    Root->AddChild(Scroll);
    MonolithUIInternal::ConfigureCanvasSlot(Scroll->Slot, TEXT("center"),
        FVector2D::ZeroVector,
        FVector2D(Columns * SlotSize + 20, Rows * SlotSize + 20),
        false, FVector2D(0.5f, 0.5f));

    UUniformGridPanel* Grid = WBP->WidgetTree->ConstructWidget<UUniformGridPanel>(UUniformGridPanel::StaticClass(), TEXT("InventoryGrid"));
    Scroll->AddChild(Grid);
    Grid->SetMinDesiredSlotWidth(static_cast<float>(SlotSize));
    Grid->SetMinDesiredSlotHeight(static_cast<float>(SlotSize));

    // Create placeholder slot widgets (Border with SizeBox)
    for (int32 Row = 0; Row < Rows; ++Row)
    {
        for (int32 Col = 0; Col < Columns; ++Col)
        {
            int32 Index = Row * Columns + Col;
            FString SlotName = FString::Printf(TEXT("Slot_%d"), Index);
            UBorder* SlotBorder = WBP->WidgetTree->ConstructWidget<UBorder>(UBorder::StaticClass(), FName(*SlotName));
            Grid->AddChildToUniformGrid(SlotBorder, Row, Col);
            SlotBorder->SetBrushColor(FLinearColor(0.15f, 0.15f, 0.2f, 0.8f));

            FString IconName = FString::Printf(TEXT("SlotIcon_%d"), Index);
            UImage* SlotIcon = WBP->WidgetTree->ConstructWidget<UImage>(UImage::StaticClass(), FName(*IconName));
            SlotBorder->AddChild(SlotIcon);
            SlotIcon->SetRenderOpacity(0.3f); // placeholder opacity
        }
    }

    MonolithUIInternal::SaveAndCompileWidgetBlueprint(WBP, SavePath);

    TSharedPtr<FJsonObject> Result = MakeShared<FJsonObject>();
    Result->SetStringField(TEXT("asset_path"), SavePath);
    Result->SetNumberField(TEXT("columns"), Columns);
    Result->SetNumberField(TEXT("rows"), Rows);
    Result->SetNumberField(TEXT("slot_size"), SlotSize);
    Result->SetNumberField(TEXT("total_slots"), Columns * Rows);
    Result->SetBoolField(TEXT("compiled"), true);
    Result->SetBoolField(TEXT("saved"), true);
    return FMonolithActionResult::Success(Result);
}

// --- create_save_slot_list ---
FMonolithActionResult FMonolithUITemplateActions::HandleCreateSaveSlotList(const TSharedPtr<FJsonObject>& Params)
{
    FString SavePath = Params->GetStringField(TEXT("save_path"));
    if (SavePath.IsEmpty())
    {
        return FMonolithActionResult::Error(TEXT("Missing required param: save_path"));
    }

    int32 MaxSlots = Params->HasField(TEXT("max_slots")) ? static_cast<int32>(Params->GetNumberField(TEXT("max_slots"))) : 3;
    MaxSlots = FMath::Clamp(MaxSlots, 1, 20);

    FMonolithActionResult Err;
    UWidgetBlueprint* WBP = MonolithUIInternal::CreateNewWidgetBlueprint(SavePath, Err);
    if (!WBP) return Err;

    UCanvasPanel* Root = Cast<UCanvasPanel>(WBP->WidgetTree->RootWidget);

    // Main layout: VerticalBox centered
    UVerticalBox* MainVBox = WBP->WidgetTree->ConstructWidget<UVerticalBox>(UVerticalBox::StaticClass(), TEXT("SaveSlotContainer"));
    Root->AddChild(MainVBox);
    MonolithUIInternal::ConfigureCanvasSlot(MainVBox->Slot, TEXT("center"), FVector2D::ZeroVector, FVector2D(500, 0), true, FVector2D(0.5f, 0.5f));

    // Title
    UTextBlock* Title = WBP->WidgetTree->ConstructWidget<UTextBlock>(UTextBlock::StaticClass(), TEXT("SaveTitle"));
    MainVBox->AddChild(Title);
    Title->SetText(FText::FromString(TEXT("SAVE FILES")));
    Title->SetJustification(ETextJustify::Center);
    if (UVerticalBoxSlot* VS = Cast<UVerticalBoxSlot>(Title->Slot))
    {
        VS->SetHorizontalAlignment(HAlign_Fill);
        VS->SetPadding(FMargin(0, 0, 0, 16));
    }

    // ScrollBox with slot entries
    UScrollBox* SlotScroll = WBP->WidgetTree->ConstructWidget<UScrollBox>(UScrollBox::StaticClass(), TEXT("SaveSlotScroll"));
    MainVBox->AddChild(SlotScroll);
    if (UVerticalBoxSlot* VS = Cast<UVerticalBoxSlot>(SlotScroll->Slot))
    {
        VS->SetHorizontalAlignment(HAlign_Fill);
        VS->SetSize(FSlateChildSize(ESlateSizeRule::Fill));
    }

    for (int32 i = 0; i < MaxSlots; ++i)
    {
        FString EntryName = FString::Printf(TEXT("SaveEntry_%d"), i);
        UBorder* Entry = WBP->WidgetTree->ConstructWidget<UBorder>(UBorder::StaticClass(), FName(*EntryName));
        SlotScroll->AddChild(Entry);
        Entry->SetBrushColor(FLinearColor(0.1f, 0.1f, 0.15f, 0.8f));
        Entry->SetPadding(FMargin(12, 8, 12, 8));

        FString EntryBoxName = FString::Printf(TEXT("SaveEntryBox_%d"), i);
        UHorizontalBox* EntryBox = WBP->WidgetTree->ConstructWidget<UHorizontalBox>(UHorizontalBox::StaticClass(), FName(*EntryBoxName));
        Entry->AddChild(EntryBox);

        // Slot number
        FString NumName = FString::Printf(TEXT("SlotNum_%d"), i);
        UTextBlock* SlotNum = WBP->WidgetTree->ConstructWidget<UTextBlock>(UTextBlock::StaticClass(), FName(*NumName));
        EntryBox->AddChild(SlotNum);
        SlotNum->SetText(FText::FromString(FString::Printf(TEXT("Slot %d"), i + 1)));
        if (UHorizontalBoxSlot* HS = Cast<UHorizontalBoxSlot>(SlotNum->Slot))
        {
            HS->SetVerticalAlignment(VAlign_Center);
            HS->SetPadding(FMargin(0, 0, 16, 0));
        }

        // Info text (date/playtime placeholder)
        FString InfoName = FString::Printf(TEXT("SlotInfo_%d"), i);
        UTextBlock* SlotInfo = WBP->WidgetTree->ConstructWidget<UTextBlock>(UTextBlock::StaticClass(), FName(*InfoName));
        EntryBox->AddChild(SlotInfo);
        SlotInfo->SetText(FText::FromString(TEXT("Empty")));
        if (UHorizontalBoxSlot* HS = Cast<UHorizontalBoxSlot>(SlotInfo->Slot))
        {
            HS->SetVerticalAlignment(VAlign_Center);
            HS->SetSize(FSlateChildSize(ESlateSizeRule::Fill)); // Fill
        }

        // Thumbnail placeholder
        FString ThumbName = FString::Printf(TEXT("SlotThumb_%d"), i);
        UImage* Thumb = WBP->WidgetTree->ConstructWidget<UImage>(UImage::StaticClass(), FName(*ThumbName));
        EntryBox->AddChild(Thumb);
        if (UHorizontalBoxSlot* HS = Cast<UHorizontalBoxSlot>(Thumb->Slot))
        {
            HS->SetVerticalAlignment(VAlign_Center);
            HS->SetPadding(FMargin(8, 0, 0, 0));
        }
    }

    // Bottom bar: Load / Delete / Back
    UHorizontalBox* BottomBar = WBP->WidgetTree->ConstructWidget<UHorizontalBox>(UHorizontalBox::StaticClass(), TEXT("SaveBottomBar"));
    MainVBox->AddChild(BottomBar);
    if (UVerticalBoxSlot* VS = Cast<UVerticalBoxSlot>(BottomBar->Slot))
    {
        VS->SetHorizontalAlignment(HAlign_Right);
        VS->SetPadding(FMargin(0, 12, 0, 0));
    }

    TArray<FString> BottomButtons = { TEXT("Load"), TEXT("Delete"), TEXT("Back") };
    for (const FString& BtnText : BottomButtons)
    {
        FString BtnName = FString::Printf(TEXT("SaveBtn_%s"), *BtnText);
        UButton* Btn = WBP->WidgetTree->ConstructWidget<UButton>(UButton::StaticClass(), FName(*BtnName));
        BottomBar->AddChild(Btn);
        if (UHorizontalBoxSlot* HS = Cast<UHorizontalBoxSlot>(Btn->Slot))
        {
            HS->SetPadding(FMargin(4, 0, 4, 0));
        }

        FString LblName = FString::Printf(TEXT("SaveBtnLabel_%s"), *BtnText);
        UTextBlock* Lbl = WBP->WidgetTree->ConstructWidget<UTextBlock>(UTextBlock::StaticClass(), FName(*LblName));
        Btn->AddChild(Lbl);
        Lbl->SetText(FText::FromString(BtnText));
        Lbl->SetJustification(ETextJustify::Center);
    }

    MonolithUIInternal::SaveAndCompileWidgetBlueprint(WBP, SavePath);

    TSharedPtr<FJsonObject> Result = MakeShared<FJsonObject>();
    Result->SetStringField(TEXT("asset_path"), SavePath);
    Result->SetNumberField(TEXT("max_slots"), MaxSlots);
    Result->SetBoolField(TEXT("compiled"), true);
    Result->SetBoolField(TEXT("saved"), true);
    return FMonolithActionResult::Success(Result);
}
