#include "MelodiaBattleInputComponent.h"

#include "EnhancedInputComponent.h"
#include "EnhancedInputSubsystems.h"
#include "InputMappingContext.h"
#include "InputAction.h"
#include "GameFramework/PlayerController.h"
#include "Kismet/GameplayStatics.h"
#include "MelodiaBattleSession.h"
#include "MelodiaRhythmHUDWidget.h"
#include "MelodiaSongSkillLibrary.h"
#include "MelodiaRhythmExecutionComponent.h"

UMelodiaBattleInputComponent::UMelodiaBattleInputComponent()
{
	PrimaryComponentTick.bCanEverTick = false;
}

void UMelodiaBattleInputComponent::BeginPlay()
{
	Super::BeginPlay();

	ActiveSkillId = UMelodiaSongSkillLibrary::GetSkillIdForMechanicLevel(1);
	ActiveSkillIndex = 0;

	if (bAutoBindPlayerInput)
	{
		BindBattleInput();
	}
}

void UMelodiaBattleInputComponent::EndPlay(const EEndPlayReason::Type EndPlayReason)
{
	UnbindBattleInput();
	Super::EndPlay(EndPlayReason);
}

void UMelodiaBattleInputComponent::CreateInputMappingContext()
{
	if (BattleMappingContext)
	{
		return;
	}

	BattleMappingContext = NewObject<UInputMappingContext>(this, TEXT("IMC_MelodiaBattle"));

	auto MakeAction = [this](const FName& Name, EInputActionValueType ValueType) -> UInputAction*
	{
		UInputAction* Action = NewObject<UInputAction>(this, Name);
		Action->ValueType = ValueType;
		return Action;
	};

	BasicAction = MakeAction(TEXT("IA_Melodia_Basic"), EInputActionValueType::Boolean);
	SkillAction = MakeAction(TEXT("IA_Melodia_Skill"), EInputActionValueType::Boolean);
	UltimateAction = MakeAction(TEXT("IA_Melodia_Ultimate"), EInputActionValueType::Boolean);
	FleeAction = MakeAction(TEXT("IA_Melodia_Flee"), EInputActionValueType::Boolean);
	CycleSkillAction = MakeAction(TEXT("IA_Melodia_CycleSkill"), EInputActionValueType::Boolean);
	LaneTapAction0 = MakeAction(TEXT("IA_Melodia_Lane0"), EInputActionValueType::Boolean);
	LaneTapAction1 = MakeAction(TEXT("IA_Melodia_Lane1"), EInputActionValueType::Boolean);
	LaneTapAction2 = MakeAction(TEXT("IA_Melodia_Lane2"), EInputActionValueType::Boolean);
	LaneTapAction3 = MakeAction(TEXT("IA_Melodia_Lane3"), EInputActionValueType::Boolean);

	// Keyboard mappings
	BattleMappingContext->MapKey(BasicAction, EKeys::SpaceBar);
	BattleMappingContext->MapKey(BasicAction, EKeys::One);
	BattleMappingContext->MapKey(SkillAction, EKeys::Two);
	BattleMappingContext->MapKey(CycleSkillAction, EKeys::Tab);
	BattleMappingContext->MapKey(UltimateAction, EKeys::R);
	BattleMappingContext->MapKey(FleeAction, EKeys::Four);
	BattleMappingContext->MapKey(FleeAction, EKeys::Escape);

	// Gamepad mappings
	BattleMappingContext->MapKey(BasicAction, EKeys::Gamepad_FaceButton_Bottom);
	BattleMappingContext->MapKey(SkillAction, EKeys::Gamepad_FaceButton_Left);
	BattleMappingContext->MapKey(UltimateAction, EKeys::Gamepad_RightTrigger);
	BattleMappingContext->MapKey(FleeAction, EKeys::Gamepad_FaceButton_Right);

	// 4-lane rhythm highway (keyboard — Q/W/O/P avoids JRPG command keys J/K/F/D)
	BattleMappingContext->MapKey(LaneTapAction0, EKeys::Q);
	BattleMappingContext->MapKey(LaneTapAction1, EKeys::W);
	BattleMappingContext->MapKey(LaneTapAction2, EKeys::O);
	BattleMappingContext->MapKey(LaneTapAction3, EKeys::P);

	// 4-lane touch (mobile ΓÇö added during gameplay when mobile detected)
}

bool UMelodiaBattleInputComponent::BindBattleInput()
{
	UWorld* World = GetWorld();
	if (!World)
	{
		return false;
	}

	APlayerController* PlayerController = UGameplayStatics::GetPlayerController(World, 0);
	if (!PlayerController)
	{
		UE_LOG(LogTemp, Warning, TEXT("Melodia battle input: no player controller."));
		return false;
	}

	if (bInputBound)
	{
		return true;
	}

	UEnhancedInputComponent* EIC = Cast<UEnhancedInputComponent>(PlayerController->InputComponent);
	if (!EIC)
	{
		UE_LOG(LogTemp, Warning, TEXT("Melodia battle input: InputComponent is not EnhancedInputComponent."));
		return false;
	}

	CreateInputMappingContext();

	auto SafeBind = [&](UInputAction* Action, ETriggerEvent TriggerEvent, auto Handler)
	{
		if (Action)
		{
			EIC->BindAction(Action, TriggerEvent, this, Handler);
		}
	};

	SafeBind(BasicAction, ETriggerEvent::Started, &UMelodiaBattleInputComponent::OnBasicInputPressed);
	SafeBind(SkillAction, ETriggerEvent::Started, &UMelodiaBattleInputComponent::OnSkillInputPressed);
	SafeBind(UltimateAction, ETriggerEvent::Started, &UMelodiaBattleInputComponent::OnUltimateInputPressed);
	SafeBind(FleeAction, ETriggerEvent::Started, &UMelodiaBattleInputComponent::OnFleeInputPressed);
	SafeBind(CycleSkillAction, ETriggerEvent::Started, &UMelodiaBattleInputComponent::OnCycleSkillInputPressed);

	// Lane tap bindings forward their LaneIndex
	if (LaneTapAction0) EIC->BindAction(LaneTapAction0, ETriggerEvent::Started, this, &UMelodiaBattleInputComponent::OnLaneTapPressed, 0);
	if (LaneTapAction1) EIC->BindAction(LaneTapAction1, ETriggerEvent::Started, this, &UMelodiaBattleInputComponent::OnLaneTapPressed, 1);
	if (LaneTapAction2) EIC->BindAction(LaneTapAction2, ETriggerEvent::Started, this, &UMelodiaBattleInputComponent::OnLaneTapPressed, 2);
	if (LaneTapAction3) EIC->BindAction(LaneTapAction3, ETriggerEvent::Started, this, &UMelodiaBattleInputComponent::OnLaneTapPressed, 3);

	// Add mapping context to subsystem
	if (ULocalPlayer* LocalPlayer = PlayerController->GetLocalPlayer())
	{
		if (UEnhancedInputLocalPlayerSubsystem* Subsystem = LocalPlayer->GetSubsystem<UEnhancedInputLocalPlayerSubsystem>())
		{
			Subsystem->AddMappingContext(BattleMappingContext, 0);
			bContextAdded = true;
		}
	}

	bInputBound = true;
	UE_LOG(LogTemp, Log, TEXT("Melodia: Battle input bound via Enhanced Input (Space/1=Basic, 2=Skill, R=Ult, 4/Esc=Flee, Tab=Cycle, Q/W/O/P=Lanes)."));
	return true;
}

bool UMelodiaBattleInputComponent::UnbindBattleInput()
{
	if (!bInputBound)
	{
		return false;
	}

	UWorld* World = GetWorld();
	if (World)
	{
		APlayerController* PlayerController = UGameplayStatics::GetPlayerController(World, 0);
		if (PlayerController && PlayerController->GetLocalPlayer())
		{
			if (UEnhancedInputLocalPlayerSubsystem* Subsystem = PlayerController->GetLocalPlayer()->GetSubsystem<UEnhancedInputLocalPlayerSubsystem>())
			{
				if (bContextAdded && BattleMappingContext)
				{
					Subsystem->RemoveMappingContext(BattleMappingContext);
				}
			}
		}
	}

	bInputBound = false;
	bContextAdded = false;
	return true;
}

bool UMelodiaBattleInputComponent::HandleBasicInput()
{
	++BasicInputCount;
	LastInputCommandName = TEXT("Basic");

	UMelodiaBattleSession* Session = UMelodiaBattleSession::Get(this);
	if (!Session)
	{
		return false;
	}

	AActor* Controller = Session->GetBattleController();
	if (Controller)
	{
		if (UMelodiaRhythmExecutionComponent* Exec = Controller->FindComponentByClass<UMelodiaRhythmExecutionComponent>())
		{
			if (Exec->IsExecutionActive())
			{
				return Exec->TryHitCurrentNote();
			}
		}
	}

	return Session->SubmitBasicCommand();
}

bool UMelodiaBattleInputComponent::HandleSkillInput()
{
	// Shift+2 = cycle skill (checked via key state for backward compat)
	APlayerController* PC = GetWorld() ? UGameplayStatics::GetPlayerController(GetWorld(), 0) : nullptr;
	if (PC && (PC->IsInputKeyDown(EKeys::LeftShift) || PC->IsInputKeyDown(EKeys::RightShift)))
	{
		return HandleCycleSkillInput();
	}

	++SkillInputCount;
	LastInputCommandName = TEXT("Skill");

	UMelodiaBattleSession* Session = UMelodiaBattleSession::Get(this);
	if (!Session)
	{
		return false;
	}

	AActor* Controller = Session->GetBattleController();
	if (Controller)
	{
		if (UMelodiaRhythmExecutionComponent* Exec = Controller->FindComponentByClass<UMelodiaRhythmExecutionComponent>())
		{
			if (Exec->IsExecutionActive())
			{
				return Exec->TryHitCurrentNote();
			}
		}
	}

	if (ActiveSkillId.IsNone())
	{
		ActiveSkillId = UMelodiaSongSkillLibrary::GetSkillIdForMechanicLevel(1);
	}

	const bool bResult = Session->SubmitSkillCommand(ActiveSkillId);
	if (!bResult)
	{
		UE_LOG(LogTemp, Warning, TEXT("Melodia: Skill command failed for %s (insufficient SP or not unlocked)."), *ActiveSkillId.ToString());
	}
	return bResult;
}

bool UMelodiaBattleInputComponent::HandleUltimateInput()
{
	++UltimateInputCount;
	LastInputCommandName = TEXT("Ultimate");

	UMelodiaBattleSession* Session = UMelodiaBattleSession::Get(this);
	if (!Session)
	{
		return false;
	}

	if (AActor* Controller = Session->GetBattleController())
	{
		if (UMelodiaRhythmExecutionComponent* Exec = Controller->FindComponentByClass<UMelodiaRhythmExecutionComponent>())
		{
			if (Exec->IsExecutionActive())
			{
				Exec->CancelExecution();
			}
		}
	}

	return Session->SubmitUltimateCommand();
}

bool UMelodiaBattleInputComponent::HandleFleeInput()
{
	LastInputCommandName = TEXT("Flee");

	UMelodiaBattleSession* Session = UMelodiaBattleSession::Get(this);
	if (!Session)
	{
		return false;
	}

	return Session->SubmitFleeCommand();
}

bool UMelodiaBattleInputComponent::HandleCycleSkillInput()
{
	const TArray<FName> UnlockedSkills = UMelodiaSongSkillLibrary::GetSkillIdsUnlockedAtOrBelowLevel(10);
	if (UnlockedSkills.Num() == 0)
	{
		return false;
	}

	ActiveSkillIndex = (ActiveSkillIndex + 1) % UnlockedSkills.Num();
	ActiveSkillId = UnlockedSkills[ActiveSkillIndex];

	FMelodiaSongSkillRecipe Recipe;
	if (UMelodiaSongSkillLibrary::FindSongSkill(ActiveSkillId, Recipe))
	{
		UE_LOG(LogTemp, Log, TEXT("Melodia: Active skill cycled -> %s (%s)"),
			*Recipe.DisplayName.ToString(), *ActiveSkillId.ToString());
		if (UMelodiaRhythmHUDWidget* HUD = UMelodiaRhythmHUDWidget::FindFirst(this))
		{
			HUD->ShowActionPrompt(FString::Printf(TEXT("Selected: %s | Press 2 to perform"), *GetActiveSkillPrompt()));
		}
	}

	return true;
}

FString UMelodiaBattleInputComponent::GetActiveSkillPrompt() const
{
	const FName SkillId = ActiveSkillId.IsNone()
		? UMelodiaSongSkillLibrary::GetSkillIdForMechanicLevel(1)
		: ActiveSkillId;

	FMelodiaSongSkillRecipe Recipe;
	if (!UMelodiaSongSkillLibrary::FindSongSkill(SkillId, Recipe))
	{
		return TEXT("Skill");
	}

	const int32 Cost = Recipe.SPCostOverride > 0 ? Recipe.SPCostOverride : 1;
	return FString::Printf(TEXT("%s (%d SP)"), *Recipe.DisplayName.ToString(), Cost);
}

bool UMelodiaBattleInputComponent::HandleLaneTap(int32 LaneIndex)
{
	UMelodiaBattleSession* Session = UMelodiaBattleSession::Get(this);
	if (!Session)
	{
		return false;
	}

	AActor* Controller = Session->GetBattleController();
	if (Controller)
	{
		if (UMelodiaRhythmExecutionComponent* Exec = Controller->FindComponentByClass<UMelodiaRhythmExecutionComponent>())
		{
			if (Exec->IsExecutionActive())
			{
				return Exec->TryHitNoteInLane(LaneIndex);
			}
		}
	}

	return false;
}

// --- Enhanced Input Handlers ---

void UMelodiaBattleInputComponent::OnBasicInputPressed(const FInputActionValue& Value)
{
	HandleBasicInput();
}

void UMelodiaBattleInputComponent::OnSkillInputPressed(const FInputActionValue& Value)
{
	HandleSkillInput();
}

void UMelodiaBattleInputComponent::OnUltimateInputPressed(const FInputActionValue& Value)
{
	HandleUltimateInput();
}

void UMelodiaBattleInputComponent::OnFleeInputPressed(const FInputActionValue& Value)
{
	HandleFleeInput();
}

void UMelodiaBattleInputComponent::OnCycleSkillInputPressed(const FInputActionValue& Value)
{
	HandleCycleSkillInput();
}

void UMelodiaBattleInputComponent::OnLaneTapPressed(const FInputActionValue& Value, int32 LaneIndex)
{
	HandleLaneTap(LaneIndex);
}
