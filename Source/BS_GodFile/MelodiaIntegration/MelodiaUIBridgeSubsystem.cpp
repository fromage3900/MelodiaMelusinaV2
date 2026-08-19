#include "MelodiaUIBridgeSubsystem.h"

#include "Engine/GameInstance.h"
#include "Engine/World.h"
#include "EngineUtils.h"
#include "GameFramework/Actor.h"
#include "TimerManager.h"
#include "UObject/UnrealType.h"
#include "Blueprint/UserWidget.h"
#include "MelodiaNarrativeSubsystem.h"
#include "MelodiaExternalJRPGBridgeSubsystem.h"
#include "MelodiaRhythmCombatSubsystem.h"
#include "MelodiaRhythmHUDWidget.h"

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

void UMelodiaUIBridgeSubsystem::Initialize(FSubsystemCollectionBase& Collection)
{
	Super::Initialize(Collection);

	if (UGameInstance* GI = GetGameInstance())
	{
		NarrativeSubsystem = GI->GetSubsystem<UMelodiaNarrativeSubsystem>();
		ExternalBridge = GI->GetSubsystem<UMelodiaExternalJRPGBridgeSubsystem>();

		if (NarrativeSubsystem)
		{
			NarrativeSubsystem->OnBattleRequested.AddUniqueDynamic(this, &ThisClass::HandleBattleRequested);
			NarrativeSubsystem->OnBattleCompleted.AddUniqueDynamic(this, &ThisClass::HandleBattleCompleted);
			NarrativeSubsystem->OnBattleAborted.AddUniqueDynamic(this, &ThisClass::HandleBattleAborted);
		}

		if (ExternalBridge)
		{
			ExternalBridge->OnJRPGBattleStarted.AddUniqueDynamic(this, &ThisClass::HandleExternalBattleStarted);
			ExternalBridge->OnJRPGBattleEnded.AddUniqueDynamic(this, &ThisClass::HandleExternalBattleEnded);
		}
	}

	if (MelodiaBattleWidgetPath.IsNull())
	{
		MelodiaBattleWidgetPath = FSoftClassPath(DefaultMelodiaBattleWidgetPath);
	}
}

void UMelodiaUIBridgeSubsystem::Deinitialize()
{
	RemoveBattleUIInternal();

	if (NarrativeSubsystem)
	{
		NarrativeSubsystem->OnBattleRequested.RemoveDynamic(this, &ThisClass::HandleBattleRequested);
		NarrativeSubsystem->OnBattleCompleted.RemoveDynamic(this, &ThisClass::HandleBattleCompleted);
		NarrativeSubsystem->OnBattleAborted.RemoveDynamic(this, &ThisClass::HandleBattleAborted);
	}

	if (ExternalBridge)
	{
		ExternalBridge->OnJRPGBattleStarted.RemoveDynamic(this, &ThisClass::HandleExternalBattleStarted);
		ExternalBridge->OnJRPGBattleEnded.RemoveDynamic(this, &ThisClass::HandleExternalBattleEnded);
	}

	NarrativeSubsystem = nullptr;
	ExternalBridge = nullptr;

	Super::Deinitialize();
}

UUserWidget* UMelodiaUIBridgeSubsystem::CreateMelodiaBattleUI(TSubclassOf<UUserWidget> MelodiaWidgetClass)
{
	if (!MelodiaWidgetClass || IsValid(MelodiaBattleWidget))
	{
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
}

void UMelodiaUIBridgeSubsystem::CreateBattleUIInternal()
{
	if (IsValid(MelodiaBattleWidget))
	{
		ShowMelodiaBattleUI();
		return;
	}

	UClass* WidgetClass = MelodiaBattleWidgetPath.TryLoadClass<UUserWidget>();
	if (!WidgetClass)
	{
		UE_LOG(LogTemp, Warning, TEXT("Melodia UI Bridge: cannot load widget class from %s"), *MelodiaBattleWidgetPath.ToString());
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
}

void UMelodiaUIBridgeSubsystem::RemoveBattleUIInternal()
{
	if (IsValid(MelodiaBattleWidget))
	{
		MelodiaBattleWidget->RemoveFromParent();
		MelodiaBattleWidget = nullptr;
		UE_LOG(LogTemp, Log, TEXT("Melodia UI Bridge: removed Melodia battle widget."));
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
}
