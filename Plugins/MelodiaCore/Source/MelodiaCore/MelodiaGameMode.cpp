// Melodia game mode ΓÇö bootstraps all battle systems.

#include "MelodiaGameMode.h"
#include "MelodiaBattleSession.h"
#include "MelodiaBattleInputComponent.h"
#include "MelodiaBattleResultsWidget.h"
#include "MelodiaRhythmHUDWidget.h"
#include "MelodiaSmokeCharacter.h"
#include "Blueprint/UserWidget.h"
#include "GameFramework/PlayerController.h"
#include "Kismet/GameplayStatics.h"

AMelodiaGameMode::AMelodiaGameMode()
{
	PrimaryActorTick.bCanEverTick = false;
	DefaultPawnClass = AMelodiaSmokeCharacter::StaticClass();
}

void AMelodiaGameMode::InitGame(const FString& MapName, const FString& Options, FString& ErrorMessage)
{
	Super::InitGame(MapName, Options, ErrorMessage);
	UE_LOG(LogTemp, Log, TEXT("Melodia GameMode: InitGame for %s"), *MapName);
}

void AMelodiaGameMode::BeginPlay()
{
	Super::BeginPlay();

	// Slight delay to let player controller finish setup
	FTimerHandle BootstrapTimer;
	GetWorld()->GetTimerManager().SetTimer(BootstrapTimer, this, &AMelodiaGameMode::Bootstrap, 0.5f, false);
}

void AMelodiaGameMode::Bootstrap()
{
	UE_LOG(LogTemp, Log, TEXT("Melodia GameMode: Bootstrapping..."));

	// 1. Spawn HUD
	SpawnBattleHUD();

	// 2. Add input component to player pawn
	APlayerController* PC = UGameplayStatics::GetPlayerController(GetWorld(), 0);
	if (PC && PC->GetPawn())
	{
		APawn* PlayerPawn = PC->GetPawn();

		// Check if input component already exists
		InputComponentRef = PlayerPawn->FindComponentByClass<UMelodiaBattleInputComponent>();
		if (!InputComponentRef)
		{
			InputComponentRef = NewObject<UMelodiaBattleInputComponent>(PlayerPawn, TEXT("MelodiaBattleInput"));
			if (InputComponentRef)
			{
				InputComponentRef->bAutoBindPlayerInput = true;
				InputComponentRef->RegisterComponent();
				PlayerPawn->AddInstanceComponent(InputComponentRef);
				UE_LOG(LogTemp, Log, TEXT("Melodia GameMode: Battle input component added to player pawn."));
			}
		}
	}

	// 3. Bind to battle session delegates
	BindBattleSession();

	// 4. Transition to exploration
	SetLoopPhase(EMelodiaLoopPhase::Exploration);
	UE_LOG(LogTemp, Log, TEXT("Melodia GameMode: Bootstrap complete ΓÇö ready for exploration."));
}

void AMelodiaGameMode::BindBattleSession()
{
	UMelodiaBattleSession* Session = UMelodiaBattleSession::Get(this);
	if (!Session)
	{
		UE_LOG(LogTemp, Warning, TEXT("Melodia GameMode: No BattleSession subsystem found."));
		return;
	}

	Session->OnBattlePhaseChanged.AddDynamic(this, &AMelodiaGameMode::OnBattlePhaseChanged);
	Session->OnEncounterEnded.AddDynamic(this, &AMelodiaGameMode::OnEncounterEnded);
	UE_LOG(LogTemp, Log, TEXT("Melodia GameMode: Bound to BattleSession delegates."));
}

void AMelodiaGameMode::OnBattlePhaseChanged(const EMelodiaBattlePhase NewPhase, const EMelodiaBattlePhase PreviousPhase)
{
	switch (NewPhase)
	{
	case EMelodiaBattlePhase::AwaitingPlayerCommand:
		if (PreviousPhase == EMelodiaBattlePhase::None)
		{
			SetLoopPhase(EMelodiaLoopPhase::Battle);
		}

		if (ActiveHUDWidget)
		{
			const FString SkillPrompt = InputComponentRef
				? InputComponentRef->GetActiveSkillPrompt()
				: TEXT("Skill");
			ActiveHUDWidget->ShowActionPrompt(FString::Printf(
				TEXT("Space/1=Basic | 2=%s | R=Ultimate | Tab=Cycle | 4/Esc=Flee"),
				*SkillPrompt));
		}
		break;

	case EMelodiaBattlePhase::RhythmExecution:
		if (ActiveHUDWidget)
		{
			ActiveHUDWidget->SetBattlePhaseBanner(TEXT("ΓÖ½ RHYTHM EXECUTION ΓÖ½"));
		}
		break;

	case EMelodiaBattlePhase::EnemyTurn:
		if (ActiveHUDWidget)
		{
			ActiveHUDWidget->SetBattlePhaseBanner(TEXT("Enemy Turn"));
		}
		break;

	case EMelodiaBattlePhase::Victory:
		SetLoopPhase(EMelodiaLoopPhase::VictoryReward);
		if (ActiveHUDWidget)
		{
			ActiveHUDWidget->SetBattlePhaseBanner(TEXT("Γ£º VICTORY Γ£º"));
			ActiveHUDWidget->ShowActionPrompt(TEXT("Press any key to continue..."));
		}
		break;

	case EMelodiaBattlePhase::Defeat:
		if (ActiveHUDWidget)
		{
			ActiveHUDWidget->SetBattlePhaseBanner(TEXT("Defeat..."));
			ActiveHUDWidget->ShowActionPrompt(TEXT("Press Escape to return."));
		}
		break;

	default:
		break;
	}
}

void AMelodiaGameMode::OnEncounterEnded(const EMelodiaEncounterResult Result)
{
	const FString ResultName = Result == EMelodiaEncounterResult::Victory ? TEXT("Victory")
		: Result == EMelodiaEncounterResult::Defeat ? TEXT("Defeat")
		: Result == EMelodiaEncounterResult::Fled ? TEXT("Fled")
		: TEXT("None");

	UE_LOG(LogTemp, Log, TEXT("Melodia GameMode: Encounter ended ΓÇö %s"), *ResultName);

	if (Result == EMelodiaEncounterResult::Victory || Result == EMelodiaEncounterResult::Defeat)
	{
		if (APlayerController* PC = UGameplayStatics::GetPlayerController(GetWorld(), 0))
		{
			TSubclassOf<UMelodiaBattleResultsWidget> WidgetClass = BattleResultsWidgetClass;
			if (!WidgetClass)
			{
				WidgetClass = UMelodiaBattleResultsWidget::StaticClass();
			}
			ActiveBattleResultsWidget = CreateWidget<UMelodiaBattleResultsWidget>(PC, WidgetClass);
			if (ActiveBattleResultsWidget)
			{
				ActiveBattleResultsWidget->AddToViewport(110);
				ActiveBattleResultsWidget->RefreshFromBattleSession();
				UE_LOG(LogTemp, Log, TEXT("Melodia GameMode: Battle results widget spawned."));
			}
		}
	}
	SetLoopPhase(EMelodiaLoopPhase::Exploration);

	if (ActiveHUDWidget)
	{
		ActiveHUDWidget->SetHUDMode(EMelodiaHUDMode::Exploration);
		ActiveHUDWidget->ShowActionPrompt(TEXT(""));
	}
}

void AMelodiaGameMode::SetLoopPhase(const EMelodiaLoopPhase NewPhase)
{
	if (CurrentLoopPhase == NewPhase)
	{
		return;
	}

	UE_LOG(LogTemp, Log, TEXT("Melodia GameMode: Loop phase %d ΓåÆ %d"),
		static_cast<int32>(CurrentLoopPhase), static_cast<int32>(NewPhase));

	CurrentLoopPhase = NewPhase;
}

void AMelodiaGameMode::SpawnBattleHUD()
{
	if (ActiveHUDWidget)
	{
		return; // Already spawned
	}

	APlayerController* PC = UGameplayStatics::GetPlayerController(GetWorld(), 0);
	if (!PC)
	{
		return;
	}

	// Use configured class or fall back to base UMelodiaRhythmHUDWidget
	TSubclassOf<UMelodiaRhythmHUDWidget> WidgetClass = HUDWidgetClass;
	if (!WidgetClass)
	{
		WidgetClass = UMelodiaRhythmHUDWidget::StaticClass();
	}

	ActiveHUDWidget = CreateWidget<UMelodiaRhythmHUDWidget>(PC, WidgetClass);
	if (ActiveHUDWidget)
	{
		ActiveHUDWidget->AddToViewport(10); // High Z-order to render on top
		UE_LOG(LogTemp, Log, TEXT("Melodia GameMode: HUD widget spawned."));
	}
}

void AMelodiaGameMode::RemoveBattleHUD()
{
	if (ActiveHUDWidget)
	{
		ActiveHUDWidget->RemoveFromParent();
		ActiveHUDWidget = nullptr;
		UE_LOG(LogTemp, Log, TEXT("Melodia GameMode: HUD widget removed."));
	}
}
