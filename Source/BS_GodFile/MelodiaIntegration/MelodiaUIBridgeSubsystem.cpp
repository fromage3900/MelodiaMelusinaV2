#include "MelodiaUIBridgeSubsystem.h"

#include "Engine/GameInstance.h"
#include "Engine/World.h"
#include "EngineUtils.h"
#include "GameFramework/Actor.h"
#include "GameFramework/PlayerController.h"
#include "TimerManager.h"
#include "UObject/UObjectIterator.h"
#include "UObject/UnrealType.h"
#include "Blueprint/UserWidget.h"
#include "MelodiaBattleKeyboardLegendWidget.h"
#include "MelodiaNarrativeSubsystem.h"
#include "MelodiaExternalJRPGBridgeSubsystem.h"
#include "MelodiaRhythmCombatSubsystem.h"
#include "MelodiaRhythmHUDWidget.h"
#include "MelodiaBattleResultsWidget.h"
#include "MelodiaBattleSession.h"

namespace
{
	// The asset lives under /UI/, not /Blueprints/. The old default pointed at a
	// path that has never existed, so the fallback silently resolved to nothing and
	// MelodiaBattleWidget stayed null whenever MelodiaBattleWidgetPath was unset.
	constexpr TCHAR DefaultMelodiaBattleWidgetPath[] = TEXT("/Game/MelodiaIntegration/UI/BP_MelodiaBattleUI.BP_MelodiaBattleUI_C");

	// V3 consolidation (2026-08-18): the quarantined AMelodiaGameMode used to spawn
	// the rhythm highway HUD. BP_MelodiaJRPGGameMode cannot (plain GameModeBase), so
	// the bridge -- which already owns battle UI lifetime -- spawns and binds it.
	// Tracked here (not as a UPROPERTY) so this stays a .cpp-only, Live-Coding-safe change.
	constexpr TCHAR DefaultMelodiaRhythmHUDPath[] = TEXT("/Game/Melodia/UI/WBP_Battle_Rhythm.WBP_Battle_Rhythm_C");

	// LiveResultsWidgetPath is EditDefaultsOnly on a native GameInstanceSubsystem: there is no
	// Blueprint asset to set it on, and UCLASS() carries no config specifier, so an ini entry
	// cannot reach it either. Initialize() backfilled MelodiaBattleWidgetPath but never this one,
	// so CreateLiveResultsWidgetInternal always failed its TryLoadClass and logged
	// "cannot load live-results widget class from " with an empty path. WBP_Battle_Results is
	// verified to derive from MelodiaBattleResultsWidget.
	constexpr TCHAR DefaultLiveResultsWidgetPath[] = TEXT("/Game/Melodia/UI/WBP_Battle_Results.WBP_Battle_Results_C");
	constexpr TCHAR RhythmPromptClassPath[] = TEXT("/Game/MelodiaIntegration/UI/BP_MelodiaRhythmPrompt.BP_MelodiaRhythmPrompt_C");
	constexpr int32 RhythmPromptZOrder = 100;
	constexpr int32 KeyboardLegendZOrder = 110;
	constexpr int32 LiveResultsWidgetZOrder = 80;
	TWeakObjectPtr<UMelodiaRhythmHUDWidget> GBridgeRhythmHUD;
}

// Lets the link be exercised from a live PIE session without authoring a single
// node -- run it during a battle and read the MELODIA_BATTLEUI_LINK line.
static FAutoConsoleCommandWithWorld GMelodiaLinkBattleUIController(
	TEXT("melodia.BattleUI.LinkController"),
	TEXT("Write the stock BP_BattleUI widget's battleController reference and report the result."),
	FConsoleCommandWithWorldDelegate::CreateLambda([](UWorld* World)
	{
		UGameInstance* GameInstance = World ? World->GetGameInstance() : nullptr;
		if (UMelodiaUIBridgeSubsystem* Bridge = GameInstance ? GameInstance->GetSubsystem<UMelodiaUIBridgeSubsystem>() : nullptr)
		{
			Bridge->EnsureStockBattleUIControllerReference();
		}
	}));

// Link Melodia UI widgets (melodiaBattleUI and MelodiaUI) to BP_BattleController
static FAutoConsoleCommandWithWorld GMelodiaLinkMelodiaWidgets(
	TEXT("melodia.BattleUI.LinkMelodiaWidgets"),
	TEXT("Link the Melodia battle widget and rhythm HUD to BP_BattleController's melodiaBattleUI and MelodiaUI variables."),
	FConsoleCommandWithWorldDelegate::CreateLambda([](UWorld* World)
	{
		UGameInstance* GameInstance = World ? World->GetGameInstance() : nullptr;
		if (UMelodiaUIBridgeSubsystem* Bridge = GameInstance ? GameInstance->GetSubsystem<UMelodiaUIBridgeSubsystem>() : nullptr)
		{
			Bridge->LinkWidgetsToBattleControllerPublic();
		}
	}));

UMelodiaUIBridgeSubsystem* UMelodiaUIBridgeSubsystem::Get(const UObject* WorldContextObject)
{
	if (WorldContextObject)
	{
		if (UWorld* World = WorldContextObject->GetWorld())
		{
			if (UGameInstance* GI = World->GetGameInstance())
			{
				return GI->GetSubsystem<UMelodiaUIBridgeSubsystem>();
			}
		}
	}
	return nullptr;
}

UMelodiaUIBridgeSubsystem::UMelodiaUIBridgeSubsystem()
{
	UE_LOG(LogTemp, Log, TEXT("MelodiaUIBridgeSubsystem::Constructor called"));
}

void UMelodiaUIBridgeSubsystem::Initialize(FSubsystemCollectionBase& Collection)
{
	Super::Initialize(Collection);
	UE_LOG(LogTemp, Log, TEXT("MelodiaUIBridgeSubsystem::Initialize called"));

	if (UGameInstance* GI = GetGameInstance())
	{
		NarrativeSubsystem = GI->GetSubsystem<UMelodiaNarrativeSubsystem>();
		ExternalBridge = GI->GetSubsystem<UMelodiaExternalJRPGBridgeSubsystem>();

		if (NarrativeSubsystem)
		{
			NarrativeSubsystem->OnBattleRequested.AddUniqueDynamic(this, &ThisClass::HandleBattleRequested);
			NarrativeSubsystem->OnBattleCompleted.AddUniqueDynamic(this, &ThisClass::HandleBattleCompleted);
			NarrativeSubsystem->OnBattleAborted.AddUniqueDynamic(this, &ThisClass::HandleBattleAborted);
			NarrativeSubsystem->OnFlagChanged.AddUniqueDynamic(this, &ThisClass::HandleNarrativeFlagChanged);
			NarrativeSubsystem->OnQuestStateCommitted.AddUniqueDynamic(this, &ThisClass::HandleQuestStateCommitted);
		}

		if (ExternalBridge)
		{
			ExternalBridge->OnJRPGBattleStarted.AddUniqueDynamic(this, &ThisClass::HandleExternalBattleStarted);
			ExternalBridge->OnJRPGBattleEnded.AddUniqueDynamic(this, &ThisClass::HandleExternalBattleEnded);
		}

		BattleSession = GI->GetSubsystem<UMelodiaBattleSession>();
		if (BattleSession)
		{
			BattleSession->OnEncounterEnded.AddUniqueDynamic(this, &ThisClass::HandleBattleSessionEnded);
			BattleSession->OnBattlePhaseChanged.AddUniqueDynamic(this, &ThisClass::HandleBattlePhaseChanged);
		}
	}

	if (MelodiaBattleWidgetPath.IsNull())
	{
		MelodiaBattleWidgetPath = FSoftClassPath(DefaultMelodiaBattleWidgetPath);
	}

	if (LiveResultsWidgetPath.IsNull())
	{
		LiveResultsWidgetPath = FSoftClassPath(DefaultLiveResultsWidgetPath);
	}
}

void UMelodiaUIBridgeSubsystem::Deinitialize()
{
	if (UWorld* World = GetWorld())
	{
		World->GetTimerManager().ClearTimer(StockDefeatCleanupTimer);
	}
	StockDefeatCleanupTicksRemaining = 0;
	RemoveBattleUIInternal();

	if (NarrativeSubsystem)
	{
		NarrativeSubsystem->OnBattleRequested.RemoveDynamic(this, &ThisClass::HandleBattleRequested);
		NarrativeSubsystem->OnBattleCompleted.RemoveDynamic(this, &ThisClass::HandleBattleCompleted);
		NarrativeSubsystem->OnBattleAborted.RemoveDynamic(this, &ThisClass::HandleBattleAborted);
		NarrativeSubsystem->OnFlagChanged.RemoveDynamic(this, &ThisClass::HandleNarrativeFlagChanged);
		NarrativeSubsystem->OnQuestStateCommitted.RemoveDynamic(this, &ThisClass::HandleQuestStateCommitted);
	}

	if (ExternalBridge)
	{
		ExternalBridge->OnJRPGBattleStarted.RemoveDynamic(this, &ThisClass::HandleExternalBattleStarted);
		ExternalBridge->OnJRPGBattleEnded.RemoveDynamic(this, &ThisClass::HandleExternalBattleEnded);
	}

	if (BattleSession)
	{
		BattleSession->OnEncounterEnded.RemoveDynamic(this, &ThisClass::HandleBattleSessionEnded);
		BattleSession->OnBattlePhaseChanged.RemoveDynamic(this, &ThisClass::HandleBattlePhaseChanged);
	}

	NarrativeSubsystem = nullptr;
	ExternalBridge = nullptr;
	BattleSession = nullptr;

	Super::Deinitialize();
}

UUserWidget* UMelodiaUIBridgeSubsystem::CreateMelodiaBattleUI(TSubclassOf<UUserWidget> MelodiaWidgetClass)
{
	if (!MelodiaWidgetClass)
	{
		return nullptr;
	}

	if (IsValid(MelodiaBattleWidget))
	{
		CreateBattlePresentationOverlaysInternal();
		return MelodiaBattleWidget;
	}

	UWorld* World = GetWorld();
	if (!World)
	{
		return nullptr;
	}

	MelodiaBattleWidget = CreateWidget<UUserWidget>(World, MelodiaWidgetClass);
	if (MelodiaBattleWidget)
	{
		MelodiaBattleWidget->AddToViewport(100);
		CreateBattlePresentationOverlaysInternal();
		UE_LOG(LogTemp, Log, TEXT("Melodia UI Bridge: created Melodia battle widget from explicit class."));
	}

	return MelodiaBattleWidget;
}

void UMelodiaUIBridgeSubsystem::DestroyMelodiaBattleUI()
{
	RemoveBattleUIInternal();
}

void UMelodiaUIBridgeSubsystem::ShowMelodiaBattleUI()
{
	if (MelodiaBattleWidget && !MelodiaBattleWidget->IsVisible())
	{
		MelodiaBattleWidget->SetVisibility(ESlateVisibility::Visible);
	}
}

void UMelodiaUIBridgeSubsystem::HideMelodiaBattleUI()
{
	if (MelodiaBattleWidget)
	{
		MelodiaBattleWidget->SetVisibility(ESlateVisibility::Hidden);
	}
}

bool UMelodiaUIBridgeSubsystem::ShowRhythmGradeOnBattleUI(const FString& GradeText, const int32 HitCount, const int32 MissCount)
{
	UUserWidget* Widget = MelodiaBattleWidget.Get();
	if (!Widget)
	{
		// Not an error: the Melodia battle overlay is only alive during a battle.
		return false;
	}

	UFunction* ShowGrade = Widget->FindFunction(TEXT("ShowRhythmGrade"));
	if (!ShowGrade)
	{
		UE_LOG(LogTemp, Warning,
			TEXT("MELODIA_UI %s has no ShowRhythmGrade event. Expected signature: "
				 "ShowRhythmGrade(GradeText:String, HitCount:Integer, MissCount:Integer)."),
			*GetNameSafe(Widget->GetClass()));
		return false;
	}

	// Layout must match the declared parameters exactly. Refuse rather than guess:
	// invoking with a mismatched frame would either corrupt the stack or silently
	// display nothing while every graph read says the call is wired.
	struct FShowRhythmGradeParams
	{
		FString GradeText;
		int32 HitCount = 0;
		int32 MissCount = 0;
	};

	if (ShowGrade->ParmsSize != sizeof(FShowRhythmGradeParams) || ShowGrade->NumParms != 3)
	{
		UE_LOG(LogTemp, Warning,
			TEXT("MELODIA_UI ShowRhythmGrade on %s has an unexpected signature (NumParms=%d). "
				 "Expected exactly: GradeText:String, HitCount:Integer, MissCount:Integer."),
			*GetNameSafe(Widget->GetClass()), ShowGrade->NumParms);
		return false;
	}

	FShowRhythmGradeParams Params;
	Params.GradeText = GradeText;
	Params.HitCount = HitCount;
	Params.MissCount = MissCount;
	Widget->ProcessEvent(ShowGrade, &Params);

	UE_LOG(LogTemp, Verbose, TEXT("MELODIA_UI ShowRhythmGrade grade=%s hits=%d misses=%d"),
		*GradeText, HitCount, MissCount);
	return true;
}

bool UMelodiaUIBridgeSubsystem::IsMelodiaUIVisible() const
{
	return MelodiaBattleWidget && MelodiaBattleWidget->GetVisibility() == ESlateVisibility::Visible;
}

void UMelodiaUIBridgeSubsystem::HandleBattleRequested(FName EncounterId)
{
	CreateBattleUIInternal();
}

void UMelodiaUIBridgeSubsystem::HandleBattleCompleted(FName EncounterId, EMelodiaBattleResult Result)
{
	RemoveBattleUIInternal();
}

void UMelodiaUIBridgeSubsystem::HandleBattleAborted(FName EncounterId, FString Reason)
{
	RemoveBattleUIInternal();
}

void UMelodiaUIBridgeSubsystem::HandleExternalBattleStarted(FName EncounterId)
{
	CreateBattleUIInternal();

	// The stock BP_BattleUI is created inside InitBattle, which runs after this
	// broadcast -- so the widget does not exist yet on this tick. Defer by one.
	if (UGameInstance* GameInstance = GetGameInstance())
	{
		if (UWorld* World = GameInstance->GetWorld())
		{
			World->GetTimerManager().SetTimerForNextTick(this, &ThisClass::EnsureStockBattleUIControllerReferenceDeferred);
		}
	}
}

void UMelodiaUIBridgeSubsystem::EnsureStockBattleUIControllerReferenceDeferred()
{
	EnsureStockBattleUIControllerReference();
}

bool UMelodiaUIBridgeSubsystem::EnsureStockBattleUIControllerReference()
{
	UGameInstance* GameInstance = GetGameInstance();
	UWorld* World = GameInstance ? GameInstance->GetWorld() : nullptr;
	if (!World)
	{
		return false;
	}

	AActor* BattleController = nullptr;
	for (TActorIterator<AActor> It(World); It; ++It)
	{
		if (It->GetClass()->GetName().StartsWith(TEXT("BP_BattleController")))
		{
			BattleController = *It;
			break;
		}
	}
	if (!BattleController)
	{
		UE_LOG(LogTemp, Warning, TEXT("MELODIA_BATTLEUI_LINK no BP_BattleController actor in the world; nothing to link."));
		return false;
	}

	const FObjectPropertyBase* BattleUIProperty = FindFProperty<FObjectPropertyBase>(BattleController->GetClass(), TEXT("battleUI"));
	if (!BattleUIProperty)
	{
		UE_LOG(LogTemp, Error, TEXT("MELODIA_BATTLEUI_LINK '%s' has no 'battleUI' object property; the stock contract changed."),
			*BattleController->GetClass()->GetName());
		return false;
	}

	UUserWidget* Widget = Cast<UUserWidget>(BattleUIProperty->GetObjectPropertyValue_InContainer(BattleController));
	if (!Widget)
	{
		// Ordinary and expected outside a battle -- not an error.
		UE_LOG(LogTemp, Verbose, TEXT("MELODIA_BATTLEUI_LINK battleUI is not yet constructed; nothing to link."));
		return false;
	}

	FObjectPropertyBase* ControllerProperty = FindFProperty<FObjectPropertyBase>(Widget->GetClass(), TEXT("battleController"));
	if (!ControllerProperty)
	{
		UE_LOG(LogTemp, Error, TEXT("MELODIA_BATTLEUI_LINK widget '%s' has no 'battleController' property; the stock contract changed."),
			*Widget->GetClass()->GetName());
		return false;
	}

	if (ControllerProperty->GetObjectPropertyValue_InContainer(Widget) == BattleController)
	{
		return true;
	}

	// Never write through a property whose declared class cannot hold this actor;
	// that is how a "successful" set produces a null read one frame later.
	if (ControllerProperty->PropertyClass && !BattleController->IsA(ControllerProperty->PropertyClass))
	{
		UE_LOG(LogTemp, Error, TEXT("MELODIA_BATTLEUI_LINK refusing to write '%s' into 'battleController' declared as '%s'."),
			*BattleController->GetClass()->GetName(), *ControllerProperty->PropertyClass->GetName());
		return false;
	}

	ControllerProperty->SetObjectPropertyValue_InContainer(Widget, BattleController);

	const bool bLinked = ControllerProperty->GetObjectPropertyValue_InContainer(Widget) == BattleController;
	if (bLinked)
	{
		UE_LOG(LogTemp, Log, TEXT("MELODIA_BATTLEUI_LINK linked '%s' -> %s.battleController"),
			*BattleController->GetName(), *Widget->GetClass()->GetName());
	}
	else
	{
		UE_LOG(LogTemp, Error, TEXT("MELODIA_BATTLEUI_LINK write to '%s.battleController' did not take."),
			*Widget->GetClass()->GetName());
	}
	return bLinked;
}

void UMelodiaUIBridgeSubsystem::HandleExternalBattleEnded(uint8 BattleResult)
{
	RemoveBattleUIInternal();

	// The stock controller creates BP_MelodiaDefeatDialogue after its terminal
	// delay. An authored Quill defeat branch is already the presentation owner,
	// so remove that legacy surface as soon as it appears. The timer is scoped to
	// a pending narrative encounter; ordinary stock battles retain their normal
	// defeat dialogue.
	if (NarrativeSubsystem && NarrativeSubsystem->IsBattlePending())
	{
		if (UWorld* World = GetWorld())
		{
			StockDefeatCleanupTicksRemaining = 24; // six seconds at 250 ms
			World->GetTimerManager().SetTimer(
				StockDefeatCleanupTimer,
				this,
				&ThisClass::RemoveStockDefeatDialogueWidgets,
				0.25f,
				true,
				0.0f);
		}
	}
}

void UMelodiaUIBridgeSubsystem::RemoveStockDefeatDialogueWidgets()
{
	UWorld* World = GetWorld();
	bool bRemoved = false;
	if (World)
	{
		for (TObjectIterator<UUserWidget> It; It; ++It)
		{
			UUserWidget* Widget = *It;
			if (!IsValid(Widget) || Widget->GetWorld() != World)
			{
				continue;
			}
			if (Widget->GetClass()->GetName().StartsWith(TEXT("BP_MelodiaDefeatDialogue")))
			{
				Widget->RemoveFromParent();
				bRemoved = true;
			}
		}
	}

	if (bRemoved || --StockDefeatCleanupTicksRemaining <= 0)
	{
		if (World)
		{
			World->GetTimerManager().ClearTimer(StockDefeatCleanupTimer);
		}
		StockDefeatCleanupTicksRemaining = 0;
	}
}

void UMelodiaUIBridgeSubsystem::CreateBattleUIInternal()
{
	if (IsValid(MelodiaBattleWidget))
	{
		ShowMelodiaBattleUI();
		CreateBattlePresentationOverlaysInternal();
		return;
	}

	UClass* WidgetClass = MelodiaBattleWidgetPath.TryLoadClass<UUserWidget>();
	if (!WidgetClass)
	{
		UE_LOG(LogTemp, Warning, TEXT("Melodia UI Bridge: cannot load widget class from %s"), *MelodiaBattleWidgetPath.ToString());
		// Keep the keyboard legend and collapsed rhythm prompt available even if
		// the optional authored battle surface is absent; this subsystem remains
		// the sole owner of both presentation paths.
		CreateBattlePresentationOverlaysInternal();
		return;
	}

	UWorld* World = GetWorld();
	if (!World)
	{
		return;
	}

	MelodiaBattleWidget = CreateWidget<UUserWidget>(World, WidgetClass);
	if (MelodiaBattleWidget)
	{
		MelodiaBattleWidget->AddToViewport(100);
		UE_LOG(LogTemp, Log, TEXT("Melodia UI Bridge: auto-created Melodia battle widget from path %s."), *MelodiaBattleWidgetPath.ToString());
	}
	CreateBattlePresentationOverlaysInternal();

	// Spawn the native rhythm highway HUD and bind it to the rhythm combat subsystem.
	// Without this, UMelodiaRhythmCombatSubsystem::BoundHUD stays null on the JRPG
	// GameMode path and the highway silently never renders.
	if (!GBridgeRhythmHUD.IsValid())
	{
		UClass* RhythmHUDClass = FSoftClassPath(DefaultMelodiaRhythmHUDPath).TryLoadClass<UMelodiaRhythmHUDWidget>();
		if (!RhythmHUDClass)
		{
			RhythmHUDClass = UMelodiaRhythmHUDWidget::StaticClass();
		}
		if (UMelodiaRhythmHUDWidget* HUD = CreateWidget<UMelodiaRhythmHUDWidget>(World, RhythmHUDClass))
		{
			HUD->AddToViewport(90);
			GBridgeRhythmHUD = HUD;
			UE_LOG(LogTemp, Log, TEXT("Melodia UI Bridge: spawned rhythm HUD %s."), *RhythmHUDClass->GetName());
		}
	}
	if (UMelodiaRhythmCombatSubsystem* Rhythm = World->GetSubsystem<UMelodiaRhythmCombatSubsystem>())
	{
		Rhythm->BindRhythmHUD(GBridgeRhythmHUD.Get());
	}

	// Link Melodia UI widgets to BP_BattleController so the owner systems can access them.
	LinkMelodiaWidgetsToBattleController();
}

void UMelodiaUIBridgeSubsystem::LinkMelodiaWidgetsToBattleController()
{
	UGameInstance* GameInstance = GetGameInstance();
	UWorld* World = GameInstance ? GameInstance->GetWorld() : nullptr;
	if (!World)
	{
		return;
	}

	AActor* BattleController = nullptr;
	for (TActorIterator<AActor> It(World); It; ++It)
	{
		if (It->GetClass()->GetName().StartsWith(TEXT("BP_BattleController")))
		{
			BattleController = *It;
			break;
		}
	}
	if (!BattleController)
	{
		UE_LOG(LogTemp, Verbose, TEXT("MELODIA_UI_LINK no BP_BattleController actor in the world; nothing to link."));
		return;
	}

	// Set melodiaBattleUI (BP_MelodiaBattleUI_C)
	const FObjectPropertyBase* MelodiaBattleUIProperty = FindFProperty<FObjectPropertyBase>(BattleController->GetClass(), TEXT("melodiaBattleUI"));
	if (MelodiaBattleUIProperty && IsValid(MelodiaBattleWidget.Get()))
	{
		if (!MelodiaBattleUIProperty->PropertyClass || MelodiaBattleWidget->IsA(MelodiaBattleUIProperty->PropertyClass))
		{
			MelodiaBattleUIProperty->SetObjectPropertyValue_InContainer(BattleController, MelodiaBattleWidget.Get());
			UE_LOG(LogTemp, Log, TEXT("MELODIA_UI_LINK set melodiaBattleUI on %s"), *BattleController->GetName());
		}
		else
		{
			UE_LOG(LogTemp, Warning, TEXT("MELODIA_UI_LINK refusing to write melodiaBattleUI: type mismatch (widget=%s, property=%s)"),
				*MelodiaBattleWidget->GetClass()->GetName(), *MelodiaBattleUIProperty->PropertyClass->GetName());
		}
	}
	else if (!MelodiaBattleUIProperty)
	{
		UE_LOG(LogTemp, Verbose, TEXT("MELODIA_UI_LINK BP_BattleController has no melodiaBattleUI property."));
	}

	// Set MelodiaUI (UserWidget) - use the rhythm HUD
	const FObjectPropertyBase* MelodiaUIProperty = FindFProperty<FObjectPropertyBase>(BattleController->GetClass(), TEXT("MelodiaUI"));
	if (MelodiaUIProperty && GBridgeRhythmHUD.IsValid())
	{
		if (!MelodiaUIProperty->PropertyClass || GBridgeRhythmHUD->IsA(MelodiaUIProperty->PropertyClass))
		{
			MelodiaUIProperty->SetObjectPropertyValue_InContainer(BattleController, GBridgeRhythmHUD.Get());
			UE_LOG(LogTemp, Log, TEXT("MELODIA_UI_LINK set MelodiaUI on %s"), *BattleController->GetName());
		}
		else
		{
			UE_LOG(LogTemp, Warning, TEXT("MELODIA_UI_LINK refusing to write MelodiaUI: type mismatch (hud=%s, property=%s)"),
				*GBridgeRhythmHUD->GetClass()->GetName(), *MelodiaUIProperty->PropertyClass->GetName());
		}
	}
	else if (!MelodiaUIProperty)
	{
		UE_LOG(LogTemp, Verbose, TEXT("MELODIA_UI_LINK BP_BattleController has no MelodiaUI property."));
	}
}

void UMelodiaUIBridgeSubsystem::CreateBattlePresentationOverlaysInternal()
{
	UWorld* World = GetWorld();
	APlayerController* PlayerController = World ? World->GetFirstPlayerController() : nullptr;
	if (!IsValid(PlayerController))
	{
		UE_LOG(LogTemp, Warning, TEXT("Melodia UI Bridge: battle presentation overlays not created; no player controller."));
		return;
	}

	if (!KeyboardLegend)
	{
		KeyboardLegend = CreateWidget<UMelodiaBattleKeyboardLegendWidget>(
			PlayerController, UMelodiaBattleKeyboardLegendWidget::StaticClass());
		if (KeyboardLegend)
		{
			KeyboardLegend->SetIsFocusable(false);
			KeyboardLegend->AddToViewport(KeyboardLegendZOrder);
		}
		else
		{
			UE_LOG(LogTemp, Warning, TEXT("Melodia UI Bridge: keyboard legend creation failed."));
		}
	}

	if (!RhythmPrompt)
	{
		const TSubclassOf<UUserWidget> PromptClass = LoadClass<UUserWidget>(nullptr, RhythmPromptClassPath);
		if (!PromptClass)
		{
			UE_LOG(LogTemp, Error, TEXT("Melodia UI Bridge: rhythm prompt class is missing: %s"), RhythmPromptClassPath);
			return;
		}

		RhythmPrompt = CreateWidget<UUserWidget>(PlayerController, PromptClass);
		if (!RhythmPrompt)
		{
			UE_LOG(LogTemp, Error, TEXT("Melodia UI Bridge: rhythm prompt creation failed."));
			return;
		}

		RhythmPrompt->SetIsFocusable(false);
		RhythmPrompt->SetVisibility(ESlateVisibility::Collapsed);
		RhythmPrompt->AddToViewport(RhythmPromptZOrder);
	}
}

void UMelodiaUIBridgeSubsystem::RemoveBattlePresentationOverlaysInternal()
{
	if (RhythmPrompt)
	{
		RhythmPrompt->RemoveFromParent();
		RhythmPrompt = nullptr;
	}
	if (KeyboardLegend)
	{
		KeyboardLegend->RemoveFromParent();
		KeyboardLegend = nullptr;
	}
}

void UMelodiaUIBridgeSubsystem::RemoveBattleUIInternal()
{
	RemoveBattlePresentationOverlaysInternal();

	if (IsValid(MelodiaBattleWidget))
	{
		MelodiaBattleWidget->RemoveFromParent();
		MelodiaBattleWidget = nullptr;
		UE_LOG(LogTemp, Log, TEXT("Melodia UI Bridge: removed Melodia battle widget."));
	}

	if (IsValid(LiveResultsWidget))
	{
		LiveResultsWidget->RemoveFromParent();
		LiveResultsWidget = nullptr;
		UE_LOG(LogTemp, Log, TEXT("Melodia UI Bridge: removed live-results widget."));
	}

	if (UWorld* World = GetWorld())
	{
		if (UMelodiaRhythmCombatSubsystem* Rhythm = World->GetSubsystem<UMelodiaRhythmCombatSubsystem>())
		{
			Rhythm->BindRhythmHUD(nullptr);
		}
	}
	if (GBridgeRhythmHUD.IsValid())
	{
		GBridgeRhythmHUD->RemoveFromParent();
	}
	GBridgeRhythmHUD = nullptr;

	PushLiveGameDataToActiveWidgets();
}

void UMelodiaUIBridgeSubsystem::HandleNarrativeFlagChanged(FName FlagId, bool bValue)
{
	PushLiveGameDataToActiveWidgets();
}

void UMelodiaUIBridgeSubsystem::HandleQuestStateCommitted(FName QuestId, bool bCompleted)
{
	PushLiveGameDataToActiveWidgets();
}

void UMelodiaUIBridgeSubsystem::HandleBattleSessionEnded(EMelodiaEncounterResult Result)
{
	// Results screen should only appear when a battle encounter finishes with a valid outcome.
	if (Result != EMelodiaEncounterResult::None)
	{
		CreateLiveResultsWidgetInternal();
	}
	PushLiveGameDataToActiveWidgets();
}

void UMelodiaUIBridgeSubsystem::HandleBattlePhaseChanged(EMelodiaBattlePhase NewPhase, EMelodiaBattlePhase PreviousPhase)
{
	PushLiveGameDataToActiveWidgets();
}

void UMelodiaUIBridgeSubsystem::CreateLiveResultsWidgetInternal()
{
	if (IsValid(LiveResultsWidget) || !GetWorld())
	{
		return;
	}

	UClass* ResultsClass = LiveResultsWidgetPath.TryLoadClass<UMelodiaBattleResultsWidget>();
	if (!ResultsClass)
	{
		UE_LOG(LogTemp, Warning, TEXT("Melodia UI Bridge: cannot load live-results widget class from %s"),
			*LiveResultsWidgetPath.ToString());
		return;
	}

	UWorld* World = GetWorld();
	LiveResultsWidget = CreateWidget<UMelodiaBattleResultsWidget>(World, ResultsClass);
	if (LiveResultsWidget)
	{
		LiveResultsWidget->SetIsFocusable(true);
		LiveResultsWidget->AddToViewport(LiveResultsWidgetZOrder);
		LiveResultsWidget->SetKeyboardFocus();
		LiveResultsWidget->RefreshFromBattleSession();
		UE_LOG(LogTemp, Log, TEXT("Melodia UI Bridge: spawned live-results widget %s."),
			*ResultsClass->GetName());
	}
}

void UMelodiaUIBridgeSubsystem::PushLiveGameDataToActiveWidgets()
{
	const FMelodiaNarrativeRecord Record = NarrativeSubsystem ? NarrativeSubsystem->GetNarrativeRecord() : FMelodiaNarrativeRecord();
	const UMelodiaBattleSession* Session = BattleSession.Get();

	// (a) Refresh results surface if currently active.
	if (IsValid(LiveResultsWidget))
	{
		LiveResultsWidget->RefreshFromBattleSession();
	}

	// (b) Optionally drive the battle widget's BlueprintImplementable event when
	// it implements it. Invoked reflectively with the exact same guarded idiom as
	// ShowRhythmGrade: refuse on any layout mismatch rather than guess.
	UUserWidget* Widget = MelodiaBattleWidget.Get();
	if (!Widget)
	{
		return;
	}
	UFunction* UpdateLive = Widget->FindFunction(TEXT("UpdateLiveGameData"));
	if (!UpdateLive)
	{
		return;
	}

	struct FLiveParams
	{
		FName LastEncounterId;
		EMelodiaBattleResult LastOutcome = EMelodiaBattleResult::Unavailable;
		int32 ActiveQuestCount = 0;
		int32 CompletedQuestCount = 0;
		float SessionScore = 0.0f;
		int32 SessionMaxCombo = 0;
	};

	if (UpdateLive->ParmsSize != sizeof(FLiveParams) || UpdateLive->NumParms != 6)
	{
		UE_LOG(LogTemp, Warning,
			TEXT("MELODIA_UI UpdateLiveGameData on %s has an unexpected signature (NumParms=%d). "
				 "Expected exactly: LastEncounterId:Name, LastOutcome:Enum, ActiveQuestCount:Int, "
				 "CompletedQuestCount:Int, SessionScore:Float, SessionMaxCombo:Int."),
			*GetNameSafe(Widget->GetClass()), UpdateLive->NumParms);
		return;
	}

	FLiveParams Params;
	Params.LastEncounterId = Record.LastEncounterId;
	Params.LastOutcome = Record.LastEncounterOutcome;
	Params.ActiveQuestCount = Record.ActiveQuestIds.Num();
	Params.CompletedQuestCount = Record.CompletedQuestIds.Num();
	Params.SessionScore = Session ? Session->SessionScore : 0.0f;
	Params.SessionMaxCombo = Session ? Session->SessionMaxCombo : 0;
	Widget->ProcessEvent(UpdateLive, &Params);

	UE_LOG(LogTemp, Verbose, TEXT("MELODIA_UI UpdateLiveGameData encounter=%s active=%d complete=%d score=%.1f maxcombo=%d"),
		*Record.LastEncounterId.ToString(), Params.ActiveQuestCount, Params.CompletedQuestCount,
		Params.SessionScore, Params.SessionMaxCombo);
}
