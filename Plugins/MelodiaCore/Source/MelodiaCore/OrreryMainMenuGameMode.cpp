// OrreryMainMenuGameMode.cpp
#include "OrreryMainMenuGameMode.h"
#include "Blueprint/UserWidget.h"
#include "Components/AudioComponent.h"
#include "Components/Button.h"
#include "Components/TextBlock.h"
#include "Components/Widget.h"
#include "Engine/GameInstance.h"
#include "Engine/World.h"
#include "GameFramework/PlayerController.h"
#include "Kismet/GameplayStatics.h"
#include "GameFramework/SaveGame.h"
#include "MelodiaAuthorityLocator.h"
#include "MelodiaStorySequenceData.h"
#include "MelodiaStorySequenceWidget.h"
#include "Subsystems/GameInstanceSubsystem.h"
#include "UObject/UnrealType.h"

namespace
{
    constexpr TCHAR StockSaveClassPath[] = TEXT("/Game/TurnBasedJRPGTemplate/Blueprints/Controllers/BP_JRPGSaveGame.BP_JRPGSaveGame_C");
    constexpr TCHAR NarrativeSubsystemClassPath[] = TEXT("/Script/BS_GodFile.MelodiaNarrativeSubsystem");
    constexpr TCHAR SaveRecoverySubsystemClassPath[] = TEXT("/Script/BS_GodFile.MelodiaSaveRecoverySubsystem");

    UGameInstanceSubsystem* FindProjectSubsystem(UGameInstance* GameInstance, const TCHAR* ClassPath)
    {
        if (!GameInstance)
        {
            return nullptr;
        }

        UClass* SubsystemClass = LoadClass<UGameInstanceSubsystem>(nullptr, ClassPath);
        return SubsystemClass ? GameInstance->GetSubsystemBase(SubsystemClass) : nullptr;
    }

    void AssignStockSaveToGameInstance(UGameInstance* GameInstance, USaveGame* Save, const FString& SlotName)
    {
        if (!GameInstance)
        {
            return;
        }
        if (FStrProperty* SlotProperty = FindFProperty<FStrProperty>(GameInstance->GetClass(), TEXT("slotName")))
        {
            SlotProperty->SetPropertyValue_InContainer(GameInstance, SlotName);
        }
        if (FObjectPropertyBase* SaveProperty = FindFProperty<FObjectPropertyBase>(GameInstance->GetClass(), TEXT("jRPGSaveGame")))
        {
            SaveProperty->SetObjectPropertyValue_InContainer(GameInstance, Save);
        }
    }

    void ResetNarrativeForNewGame(UGameInstance* GameInstance)
    {
        if (!GameInstance)
        {
            return;
        }

        UClass* NarrativeSubsystemClass = LoadClass<UGameInstanceSubsystem>(nullptr,
            TEXT("/Script/BS_GodFile.MelodiaNarrativeSubsystem"));
        UGameInstanceSubsystem* NarrativeSubsystem = NarrativeSubsystemClass
            ? GameInstance->GetSubsystemBase(NarrativeSubsystemClass)
            : nullptr;
        if (NarrativeSubsystem)
        {
            if (UFunction* ResetNarrativeRecord = NarrativeSubsystem->FindFunction(TEXT("ResetNarrativeRecord")))
            {
                NarrativeSubsystem->ProcessEvent(ResetNarrativeRecord, nullptr);
            }
        }
    }

    bool InvokeNarrativeSaveObjectFunction(UGameInstance* GameInstance, const TCHAR* FunctionName, USaveGame* Save)
    {
        UGameInstanceSubsystem* NarrativeSubsystem = FindProjectSubsystem(GameInstance, NarrativeSubsystemClassPath);
        if (!NarrativeSubsystem || !Save)
        {
            return false;
        }

        UFunction* Function = NarrativeSubsystem->FindFunction(FunctionName);
        if (!Function)
        {
            return false;
        }

        FObjectPropertyBase* SaveParameter = nullptr;
        for (TFieldIterator<FProperty> It(Function); It; ++It)
        {
            if (It->HasAnyPropertyFlags(CPF_Parm)
                && !It->HasAnyPropertyFlags(CPF_ReturnParm)
                && CastField<FObjectPropertyBase>(*It))
            {
                SaveParameter = CastField<FObjectPropertyBase>(*It);
                break;
            }
        }
        if (!SaveParameter)
        {
            return false;
        }

        uint8* Parameters = static_cast<uint8*>(FMemory_Alloca(Function->ParmsSize));
        FMemory::Memzero(Parameters, Function->ParmsSize);
        SaveParameter->SetObjectPropertyValue_InContainer(Parameters, Save);
        NarrativeSubsystem->ProcessEvent(Function, Parameters);

        if (FBoolProperty* ReturnProperty = FindFProperty<FBoolProperty>(Function, TEXT("ReturnValue")))
        {
            return ReturnProperty->GetPropertyValue_InContainer(Parameters);
        }
        return true;
    }

    bool HasNarrativeSaveObjectFunction(UGameInstance* GameInstance, const TCHAR* FunctionName)
    {
        UGameInstanceSubsystem* NarrativeSubsystem = FindProjectSubsystem(GameInstance, NarrativeSubsystemClassPath);
        if (!NarrativeSubsystem)
        {
            return false;
        }

        UFunction* Function = NarrativeSubsystem->FindFunction(FunctionName);
        if (!Function)
        {
            return false;
        }

        for (TFieldIterator<FProperty> It(Function); It; ++It)
        {
            if (It->HasAnyPropertyFlags(CPF_Parm)
                && !It->HasAnyPropertyFlags(CPF_ReturnParm)
                && CastField<FObjectPropertyBase>(*It))
            {
                return true;
            }
        }
        return false;
    }

    void InvokeRecoveryBoundary(UGameInstance* GameInstance, const TCHAR* FunctionName, const FString& Reason)
    {
        UGameInstanceSubsystem* RecoverySubsystem = FindProjectSubsystem(GameInstance, SaveRecoverySubsystemClassPath);
        if (!RecoverySubsystem)
        {
            UE_LOG(LogTemp, Warning, TEXT("OrreryMainMenuGameMode: save/recovery subsystem unavailable for %s."), FunctionName);
            return;
        }

        UFunction* Function = RecoverySubsystem->FindFunction(FunctionName);
        if (!Function)
        {
            UE_LOG(LogTemp, Warning, TEXT("OrreryMainMenuGameMode: save/recovery boundary %s is unavailable."), FunctionName);
            return;
        }

        FStrProperty* ReasonParameter = nullptr;
        for (TFieldIterator<FProperty> It(Function); It; ++It)
        {
            if (It->HasAnyPropertyFlags(CPF_Parm)
                && !It->HasAnyPropertyFlags(CPF_ReturnParm)
                && CastField<FStrProperty>(*It))
            {
                ReasonParameter = CastField<FStrProperty>(*It);
                break;
            }
        }
        if (!ReasonParameter)
        {
            UE_LOG(LogTemp, Warning, TEXT("OrreryMainMenuGameMode: save/recovery boundary %s has no FString reason parameter."), FunctionName);
            return;
        }

        uint8* Parameters = static_cast<uint8*>(FMemory_Alloca(Function->ParmsSize));
        FMemory::Memzero(Parameters, Function->ParmsSize);
        ReasonParameter->SetPropertyValue_InContainer(Parameters, Reason);
        RecoverySubsystem->ProcessEvent(Function, Parameters);
    }

    bool CanBeginCanonicalLoad(UGameInstance* GameInstance)
    {
        if (!GameInstance)
        {
            return false;
        }

        UFunction* LoadThisGame = GameInstance->FindFunction(TEXT("LoadThisGame"));
        if (!LoadThisGame)
        {
            return false;
        }
        for (TFieldIterator<FProperty> It(LoadThisGame); It; ++It)
        {
            if (It->HasAnyPropertyFlags(CPF_Parm)
                && It->GetFName() == TEXT("jRPGSaveGame")
                && CastField<FObjectPropertyBase>(*It))
            {
                return HasNarrativeSaveObjectFunction(GameInstance, TEXT("RestoreNarrativeRecordFromSave"));
            }
        }
        return false;
    }

    /**
     * Keep the menu on the stock GameInstance load transaction. The stock
     * Blueprint event owns map/load flags and stock state. The native narrative
     * restore immediately after ProcessEvent closes the source-proven native
     * boundary without replacing any stock authority; the internal Blueprint
     * node order remains a runtime verification item.
     */
    bool BeginCanonicalLoad(UGameInstance* GameInstance, USaveGame* Save)
    {
        if (!Save || !CanBeginCanonicalLoad(GameInstance))
        {
            return false;
        }

        UFunction* LoadThisGame = GameInstance->FindFunction(TEXT("LoadThisGame"));

        FObjectPropertyBase* SaveParameter = nullptr;
        for (TFieldIterator<FProperty> It(LoadThisGame); It; ++It)
        {
            if (It->HasAnyPropertyFlags(CPF_Parm) && It->GetFName() == TEXT("jRPGSaveGame"))
            {
                SaveParameter = CastField<FObjectPropertyBase>(*It);
                break;
            }
        }
        if (!SaveParameter)
        {
            return false;
        }

        uint8* Parameters = static_cast<uint8*>(FMemory_Alloca(LoadThisGame->ParmsSize));
        FMemory::Memzero(Parameters, LoadThisGame->ParmsSize);
        SaveParameter->SetObjectPropertyValue_InContainer(Parameters, Save);
        GameInstance->ProcessEvent(LoadThisGame, Parameters);

        const bool bNarrativeRestored = InvokeNarrativeSaveObjectFunction(
            GameInstance, TEXT("RestoreNarrativeRecordFromSave"), Save);
        if (!bNarrativeRestored)
        {
            UE_LOG(LogTemp, Error,
                TEXT("OrreryMainMenuGameMode: canonical narrative restore failed after stock LoadThisGame."));
        }
        return bNarrativeRestored;
    }

    bool HasSavedMap(const USaveGame* Save)
    {
        if (!Save)
        {
            return false;
        }

        if (const FNameProperty* CurrentMapProperty = FindFProperty<FNameProperty>(Save->GetClass(), TEXT("currentMap")))
        {
            return CurrentMapProperty->GetPropertyValue_InContainer(Save) != NAME_None;
        }
        return false;
    }

    bool IsUsableCanonicalSave(UGameInstance* GameInstance, const FString& SlotName)
    {
        USaveGame* Save = UGameplayStatics::LoadGameFromSlot(SlotName, 0);
        UClass* ExpectedClass = LoadClass<USaveGame>(nullptr, StockSaveClassPath);
        if (!Save || !ExpectedClass || !Save->IsA(ExpectedClass))
        {
            return false;
        }

        // A fresh New Game slot intentionally has no map until the first stock
        // save. A populated slot must be able to use the canonical transaction;
        // otherwise Continue would silently fall back to the opening and appear
        // to discard the player's saved location.
        return !HasSavedMap(Save) || CanBeginCanonicalLoad(GameInstance);
    }

    FText DescribeSavedJourney(const FString& SlotName)
    {
        USaveGame* Save = UGameplayStatics::LoadGameFromSlot(SlotName, 0);
        if (!Save)
        {
            return FText::FromString(TEXT("Begin a new journey to create your first save."));
        }

        FName CurrentMap = NAME_None;
        if (const FNameProperty* CurrentMapProperty = FindFProperty<FNameProperty>(Save->GetClass(), TEXT("currentMap")))
        {
            CurrentMap = CurrentMapProperty->GetPropertyValue_InContainer(Save);
        }

        FDateTime SaveDate;
        if (const FStructProperty* SaveDateProperty = FindFProperty<FStructProperty>(Save->GetClass(), TEXT("saveDate"));
            SaveDateProperty && SaveDateProperty->Struct == TBaseStructure<FDateTime>::Get())
        {
            SaveDate = *SaveDateProperty->ContainerPtrToValuePtr<FDateTime>(Save);
        }

        const FString Location = CurrentMap.IsNone() ? TEXT("the opening") : CurrentMap.ToString();
        if (SaveDate.GetTicks() > 0)
        {
            return FText::FromString(FString::Printf(TEXT("Saved in %s — %s."), *Location, *SaveDate.ToString(TEXT("%b %d, %Y %H:%M"))));
        }
        return FText::FromString(FString::Printf(TEXT("A saved journey is ready in %s."), *Location));
    }
}
AOrreryMainMenuGameMode::AOrreryMainMenuGameMode()
{
    // A front-end map must never spawn the gameplay pawn/HUD behind the menu.
    DefaultPawnClass = nullptr;
    HUDClass = nullptr;

    // Do not use ConstructorHelpers here. GameMode CDO construction occurs
    // during editor-side Blueprint compilation, where eagerly loading a UMG
    // class can recursively enter the UMG compiler. This reference is inert
    // until BeginPlay resolves it for the dedicated front-end map.
    MainMenuWidgetFallbackClass = TSoftClassPtr<UUserWidget>(
        FSoftObjectPath(TEXT("/Game/Melodia/UI/WBP_MainMenu.WBP_MainMenu_C")));
    SaveLoadPanelClass = TSoftClassPtr<UUserWidget>(
        FSoftObjectPath(TEXT("/Game/Melodia/UI/WBP_SaveLoadPanel.WBP_SaveLoadPanel_C")));
    SettingsPanelClass = TSoftClassPtr<UUserWidget>(
        FSoftObjectPath(TEXT("/Game/Melodia/UI/WBP_MelodiaSettings.WBP_MelodiaSettings_C")));
    OpeningSequenceWidgetFallbackClass = TSoftClassPtr<UMelodiaStorySequenceWidget>(
        FSoftObjectPath(TEXT("/Game/Melodia/UI/WBP_MelodiaOpeningSlideshow.WBP_MelodiaOpeningSlideshow_C")));
    OpeningSequenceAsset = TSoftObjectPtr<UMelodiaStorySequenceData>(
        FSoftObjectPath(TEXT("/Game/Melodia/Narrative/Sequences/DA_Opening_MelusinaMorning.DA_Opening_MelusinaMorning")));
    MenuClickSound = TSoftObjectPtr<USoundBase>(
        FSoftObjectPath(TEXT("/Game/Melodia/Audio/SFX/A_UI_Bubble.A_UI_Bubble")));
}

void AOrreryMainMenuGameMode::BeginPlay()
{
    Super::BeginPlay();

    APlayerController* PC = GetWorld() ? GetWorld()->GetFirstPlayerController() : nullptr;
    // The dedicated front end always prefers the project-owned presentation.
    // MainMenuWidgetClass remains a recovery override only when the authored class
    // cannot load; this prevents a stale map/CDO value from silently restoring the
    // stock JRPG menu while keeping all button authority in this native host.
    UClass* WidgetClass = nullptr;
    if (!MainMenuWidgetFallbackClass.IsNull())
    {
        WidgetClass = MainMenuWidgetFallbackClass.LoadSynchronous();
    }
    if (!WidgetClass)
    {
        WidgetClass = MainMenuWidgetClass.Get();
        UE_LOG(LogTemp, Warning,
            TEXT("OrreryMainMenuGameMode: authored WBP_MainMenu unavailable; using configured recovery class %s."),
            *GetNameSafe(WidgetClass));
    }

    if (PC && WidgetClass && WidgetClass->IsChildOf(UUserWidget::StaticClass()))
    {
        UUserWidget* Widget = CreateWidget<UUserWidget>(PC, WidgetClass);
        if (Widget)
        {
            Widget->AddToViewport();

            UButton* NewGameButton = Cast<UButton>(Widget->GetWidgetFromName(TEXT("Btn_NewGame")));
            UButton* ContinueButton = Cast<UButton>(Widget->GetWidgetFromName(TEXT("Btn_Continue")));
            UButton* LoadGameButton = Cast<UButton>(Widget->GetWidgetFromName(TEXT("Btn_LoadGame")));
            UButton* SettingsButton = Cast<UButton>(Widget->GetWidgetFromName(TEXT("Btn_Settings")));
            SaveStateText = Cast<UTextBlock>(Widget->GetWidgetFromName(TEXT("SaveStateText")));
            UWidget* InitialFocus = NewGameButton;
            if (NewGameButton)
            {
                // The front-end host owns this boundary so stale Blueprint graph wiring
                // cannot leave the primary route inert or trigger it twice.
                NewGameButton->OnClicked.Clear();
                NewGameButton->OnClicked.AddDynamic(this, &AOrreryMainMenuGameMode::HandleNewGameClicked);
            }
            else
            {
                UE_LOG(LogTemp, Error, TEXT("OrreryMainMenuGameMode: Btn_NewGame was not found."));
            }

            const bool bCanonicalSaveUsable = IsUsableCanonicalSave(GetGameInstance(), CanonicalSaveSlot);
            if (ContinueButton)
            {
                ContinueButton->OnClicked.Clear();
                ContinueButton->OnClicked.AddDynamic(this, &AOrreryMainMenuGameMode::HandleContinueClicked);
                ContinueButton->SetIsEnabled(bCanonicalSaveUsable);
            }

            if (LoadGameButton)
            {
                LoadGameButton->OnClicked.Clear();
                LoadGameButton->OnClicked.AddDynamic(this, &AOrreryMainMenuGameMode::HandleLoadGameClicked);
                LoadGameButton->SetIsEnabled(bCanonicalSaveUsable);
            }

            if (SettingsButton)
            {
                SettingsButton->OnClicked.Clear();
                SettingsButton->OnClicked.AddDynamic(this, &AOrreryMainMenuGameMode::HandleSettingsClicked);
            }

            SetSaveStateFeedback(DescribeSavedJourney(CanonicalSaveSlot));

            FInputModeUIOnly InputMode;
            InputMode.SetWidgetToFocus(InitialFocus ? InitialFocus->TakeWidget() : Widget->TakeWidget());
            InputMode.SetLockMouseToViewportBehavior(EMouseLockMode::DoNotLock);
            PC->SetInputMode(InputMode);
            PC->SetShowMouseCursor(true);

            if (InitialFocus)
            {
                InitialFocus->SetUserFocus(PC);
            }

            UE_LOG(LogTemp, Log, TEXT("OrreryMainMenuGameMode: Main menu UI added to viewport."));
        }
    }
    else
    {
        UE_LOG(LogTemp, Error, TEXT("OrreryMainMenuGameMode: Main menu widget class or player controller is unavailable."));
    }

    if (MenuAmbienceSound && !AmbienceAudioComponent)
    {
        AmbienceAudioComponent = NewObject<UAudioComponent>(this);
        AmbienceAudioComponent->bAutoActivate = false;
        AmbienceAudioComponent->SetSound(MenuAmbienceSound);
        AmbienceAudioComponent->RegisterComponent();
        AmbienceAudioComponent->Play();
        UE_LOG(LogTemp, Log, TEXT("OrreryMainMenuGameMode: Menu ambience started."));
    }
}

void AOrreryMainMenuGameMode::PlayMenuClickSound()
{
    if (USoundBase* ClickSound = MenuClickSound.LoadSynchronous())
    {
        UGameplayStatics::PlaySound2D(this, ClickSound);
    }
}

void AOrreryMainMenuGameMode::SetSaveStateFeedback(const FText& Message)
{
    if (SaveStateText)
    {
        SaveStateText->SetText(Message);
    }
}

void AOrreryMainMenuGameMode::HandleLoadGameClicked()
{
    PlayMenuClickSound();
    if (ActiveSaveLoadPanel)
    {
        return;
    }

    APlayerController* PC = GetWorld() ? GetWorld()->GetFirstPlayerController() : nullptr;
    UClass* PanelClass = SaveLoadPanelClass.LoadSynchronous();
    if (!PC || !PanelClass || !PanelClass->IsChildOf(UUserWidget::StaticClass()))
    {
        SetSaveStateFeedback(FText::FromString(TEXT("Load panel is unavailable. Please use Continue.")));
        UE_LOG(LogTemp, Error, TEXT("OrreryMainMenuGameMode: Save/Load panel class is unavailable."));
        return;
    }

    ActiveSaveLoadPanel = CreateWidget<UUserWidget>(PC, PanelClass);
    if (!ActiveSaveLoadPanel)
    {
        SetSaveStateFeedback(FText::FromString(TEXT("Could not open the saved journeys panel.")));
        return;
    }

    ActiveSaveLoadPanel->AddToViewport(50);
    FInputModeUIOnly InputMode;
    InputMode.SetWidgetToFocus(ActiveSaveLoadPanel->TakeWidget());
    InputMode.SetLockMouseToViewportBehavior(EMouseLockMode::DoNotLock);
    PC->SetInputMode(InputMode);
    PC->SetShowMouseCursor(true);
    SetSaveStateFeedback(FText::FromString(TEXT("Choose your saved journey.")));
}

void AOrreryMainMenuGameMode::HandleSettingsClicked()
{
    PlayMenuClickSound();
    if (ActiveSettingsPanel)
    {
        return;
    }

    APlayerController* PC = GetWorld() ? GetWorld()->GetFirstPlayerController() : nullptr;
    UClass* PanelClass = SettingsPanelClass.LoadSynchronous();
    if (!PC || !PanelClass || !PanelClass->IsChildOf(UUserWidget::StaticClass()))
    {
        SetSaveStateFeedback(FText::FromString(TEXT("Settings are unavailable.")));
        UE_LOG(LogTemp, Error, TEXT("OrreryMainMenuGameMode: Settings panel class is unavailable."));
        return;
    }

    ActiveSettingsPanel = CreateWidget<UUserWidget>(PC, PanelClass);
    if (!ActiveSettingsPanel)
    {
        SetSaveStateFeedback(FText::FromString(TEXT("Could not open Settings.")));
        return;
    }

    if (UButton* BackButton = Cast<UButton>(ActiveSettingsPanel->GetWidgetFromName(TEXT("Btn_SettingsBack"))))
    {
        BackButton->OnClicked.Clear();
        BackButton->OnClicked.AddDynamic(this, &AOrreryMainMenuGameMode::HandleSettingsBackClicked);
    }

    ActiveSettingsPanel->AddToViewport(75);
    FInputModeUIOnly InputMode;
    InputMode.SetWidgetToFocus(ActiveSettingsPanel->TakeWidget());
    InputMode.SetLockMouseToViewportBehavior(EMouseLockMode::DoNotLock);
    PC->SetInputMode(InputMode);
    PC->SetShowMouseCursor(true);
}

void AOrreryMainMenuGameMode::HandleSettingsBackClicked()
{
    PlayMenuClickSound();
    if (!ActiveSettingsPanel)
    {
        return;
    }

    ActiveSettingsPanel->RemoveFromParent();
    ActiveSettingsPanel = nullptr;
    APlayerController* PC = GetWorld() ? GetWorld()->GetFirstPlayerController() : nullptr;
    if (PC)
    {
        FInputModeUIOnly InputMode;
        InputMode.SetLockMouseToViewportBehavior(EMouseLockMode::DoNotLock);
        PC->SetInputMode(InputMode);
        PC->SetShowMouseCursor(true);
    }
}

void AOrreryMainMenuGameMode::HandleNewGameClicked()
{
    PlayMenuClickSound();
    UGameInstance* GameInstance = GetGameInstance();
    InvokeRecoveryBoundary(GameInstance, TEXT("BeginSaveBoundary"), TEXT("Orrery New Game"));

    UClass* SaveClass = LoadClass<USaveGame>(nullptr, StockSaveClassPath);
    USaveGame* NewSave = SaveClass ? UGameplayStatics::CreateSaveGameObject(SaveClass) : nullptr;
    ResetNarrativeForNewGame(GameInstance);
    if (!NewSave || !InvokeNarrativeSaveObjectFunction(GameInstance, TEXT("SyncNarrativeRecordToSave"), NewSave))
    {
        InvokeRecoveryBoundary(GameInstance, TEXT("EndSaveBoundary"), TEXT("Orrery New Game failed before serialization"));
        UE_LOG(LogTemp, Error, TEXT("OrreryMainMenuGameMode: canonical narrative sync failed for slot '%s'."), *CanonicalSaveSlot);
        return;
    }

    if (!UGameplayStatics::SaveGameToSlot(NewSave, CanonicalSaveSlot, 0))
    {
        InvokeRecoveryBoundary(GameInstance, TEXT("EndSaveBoundary"), TEXT("Orrery New Game stock serialization failed"));
        UE_LOG(LogTemp, Error, TEXT("OrreryMainMenuGameMode: failed to create canonical JRPG save slot '%s'."), *CanonicalSaveSlot);
        return;
    }

    InvokeRecoveryBoundary(GameInstance, TEXT("EndSaveBoundary"), TEXT("Orrery New Game"));
    AssignStockSaveToGameInstance(GameInstance, NewSave, CanonicalSaveSlot);

    UE_LOG(LogTemp, Log, TEXT("OrreryMainMenuGameMode: New Game created canonical slot '%s'; starting opening presentation."), *CanonicalSaveSlot);
    BeginOpeningSequence();
}

void AOrreryMainMenuGameMode::TravelToOpeningMap()
{
    // Routed through the authority locator (Decision 030) instead of a bare
    // OpenLevel -- this GameMode is MelodiaCore-native and cannot reach
    // UMelodiaTravelSubsystem directly (see MelodiaSharedAuthorityInterfaces.h
    // for why). Falls back to the old direct OpenLevel only if no travel
    // provider has registered, so a missing/misconfigured GameInstance
    // subsystem degrades instead of stranding the player on the menu.
    bool bRoutedThroughAuthority = false;
    if (UMelodiaAuthorityLocator* Locator = UMelodiaAuthorityLocator::Get(this))
    {
        TScriptInterface<IMelodiaTravelProvider> Travel = Locator->GetTravelProvider();
        if (Travel.GetObject())
        {
            bRoutedThroughAuthority = Travel->TravelTo(OpeningMap, NAME_None);
        }
    }

    if (!bRoutedThroughAuthority)
    {
        UE_LOG(LogTemp, Warning, TEXT("OrreryMainMenuGameMode: no travel provider registered, falling back to direct OpenLevel(%s)"),
            *OpeningMap.ToString());
        UGameplayStatics::OpenLevel(this, OpeningMap);
    }
}

void AOrreryMainMenuGameMode::BeginOpeningSequence()
{
    if (ActiveOpeningSequence)
    {
        return;
    }

    APlayerController* PC = GetWorld() ? GetWorld()->GetFirstPlayerController() : nullptr;
    UClass* WidgetClass = OpeningSequenceWidgetFallbackClass.LoadSynchronous();
    UMelodiaStorySequenceData* Sequence = OpeningSequenceAsset.LoadSynchronous();
    if (!PC || !WidgetClass || !WidgetClass->IsChildOf(UMelodiaStorySequenceWidget::StaticClass()) || !Sequence)
    {
        UE_LOG(LogTemp, Warning, TEXT("OrreryMainMenuGameMode: opening sequence is unavailable; falling back to %s."), *OpeningMap.ToString());
        TravelToOpeningMap();
        return;
    }

	ActiveOpeningSequence = CreateWidget<UMelodiaStorySequenceWidget>(PC, WidgetClass);
	if (!ActiveOpeningSequence)
	{
		UE_LOG(LogTemp, Warning, TEXT("OrreryMainMenuGameMode: opening sequence could not initialize; falling back to %s."), *OpeningMap.ToString());
		TravelToOpeningMap();
		return;
	}

	ActiveOpeningSequence->OnSequenceFinished.AddUniqueDynamic(this, &ThisClass::HandleOpeningSequenceFinished);
	if (!	ActiveOpeningSequence->SetSequence(Sequence))
	{
		ActiveOpeningSequence = nullptr;
		UE_LOG(LogTemp, Warning, TEXT("OrreryMainMenuGameMode: opening sequence could not initialize; falling back to %s."), *OpeningMap.ToString());
		TravelToOpeningMap();
		return;
	}
	ActiveOpeningSequence->AddToViewport(100);

    FInputModeUIOnly InputMode;
    InputMode.SetWidgetToFocus(ActiveOpeningSequence->TakeWidget());
    InputMode.SetLockMouseToViewportBehavior(EMouseLockMode::DoNotLock);
    PC->SetInputMode(InputMode);
    PC->SetShowMouseCursor(true);
    UE_LOG(LogTemp, Log, TEXT("OrreryMainMenuGameMode: opening sequence started: %s."), *Sequence->SequenceId.ToString());
}

void AOrreryMainMenuGameMode::HandleOpeningSequenceFinished(UMelodiaStorySequenceData* FinishedSequence)
{
    if (!ActiveOpeningSequence)
    {
        return;
    }

    ActiveOpeningSequence->RemoveFromParent();
    ActiveOpeningSequence = nullptr;
	const FString FinishedSequenceId = FinishedSequence ? FinishedSequence->SequenceId.ToString() : TEXT("Unknown");
	UE_LOG(LogTemp, Log, TEXT("OrreryMainMenuGameMode: opening sequence finished: %s; opening %s."),
		*FinishedSequenceId, *OpeningMap.ToString());
    TravelToOpeningMap();
}

void AOrreryMainMenuGameMode::HandleContinueClicked()
{
    PlayMenuClickSound();
    UGameInstance* GameInstance = GetGameInstance();
    InvokeRecoveryBoundary(GameInstance, TEXT("BeginLoadBoundary"), TEXT("Orrery Continue"));

    if (!IsUsableCanonicalSave(GameInstance, CanonicalSaveSlot))
    {
        InvokeRecoveryBoundary(GameInstance, TEXT("EndLoadBoundary"), TEXT("Orrery Continue rejected"));
        SetSaveStateFeedback(FText::FromString(TEXT("This saved journey cannot be loaded safely. Start a new journey or choose another slot.")));
        UE_LOG(LogTemp, Error, TEXT("OrreryMainMenuGameMode: canonical slot '%s' failed class/load-contract validation."), *CanonicalSaveSlot);
        return;
    }

    USaveGame* LoadedSave = UGameplayStatics::LoadGameFromSlot(CanonicalSaveSlot, 0);
    if (!LoadedSave)
    {
        InvokeRecoveryBoundary(GameInstance, TEXT("EndLoadBoundary"), TEXT("Orrery Continue could not read slot"));
        SetSaveStateFeedback(FText::FromString(TEXT("The saved journey could not be read.")));
        UE_LOG(LogTemp, Warning, TEXT("OrreryMainMenuGameMode: no usable canonical JRPG save in slot '%s'."), *CanonicalSaveSlot);
        return;
    }

    AssignStockSaveToGameInstance(GameInstance, LoadedSave, CanonicalSaveSlot);

    // A populated stock save owns its destination map. Route through its
    // existing GameInstance event so stock map/load state remains authoritative;
    // BeginCanonicalLoad restores the canonical narrative record immediately
    // after that stock event returns.
    if (HasSavedMap(LoadedSave))
    {
        if (BeginCanonicalLoad(GameInstance, LoadedSave))
        {
            InvokeRecoveryBoundary(GameInstance, TEXT("EndLoadBoundary"), TEXT("Orrery Continue"));
            UE_LOG(LogTemp, Log, TEXT("OrreryMainMenuGameMode: loading canonical slot '%s' through the GameInstance transaction."), *CanonicalSaveSlot);
            return;
        }

        InvokeRecoveryBoundary(GameInstance, TEXT("EndLoadBoundary"), TEXT("Orrery Continue narrative restore failed"));
        SetSaveStateFeedback(FText::FromString(TEXT("The saved journey could not restore its narrative state safely.")));
        UE_LOG(LogTemp, Error, TEXT("OrreryMainMenuGameMode: canonical slot '%s' failed the post-stock narrative restore."), *CanonicalSaveSlot);
        return;
    }

    // A newly-created slot has no current map until its first stock save. It is
    // still valid, but restore its canonical record before the authored opening route.
    if (!InvokeNarrativeSaveObjectFunction(GameInstance, TEXT("RestoreNarrativeRecordFromSave"), LoadedSave))
    {
        InvokeRecoveryBoundary(GameInstance, TEXT("EndLoadBoundary"), TEXT("Orrery Continue fresh-slot narrative restore failed"));
        SetSaveStateFeedback(FText::FromString(TEXT("The new journey could not restore its narrative state safely.")));
        return;
    }

    InvokeRecoveryBoundary(GameInstance, TEXT("EndLoadBoundary"), TEXT("Orrery Continue fresh slot"));
    UE_LOG(LogTemp, Log, TEXT("OrreryMainMenuGameMode: canonical slot '%s' has no saved map; opening %s."), *CanonicalSaveSlot, *OpeningMap.ToString());
    TravelToOpeningMap();
}
