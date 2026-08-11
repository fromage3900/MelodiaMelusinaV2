#include "MelodiaJRPGBattleOverlaySubsystem.h"

#include "Blueprint/UserWidget.h"
#include "Engine/GameInstance.h"
#include "GameFramework/PlayerController.h"
#include "MelodiaBattleKeyboardLegendWidget.h"
#include "MelodiaNarrativeSubsystem.h"

namespace
{
	constexpr TCHAR RhythmPromptClassPath[] =
		TEXT("/Game/MelodiaIntegration/UI/BP_MelodiaRhythmPrompt.BP_MelodiaRhythmPrompt_C");
	constexpr int32 RhythmPromptZOrder = 100;
	constexpr int32 KeyboardLegendZOrder = 110;
}

void UMelodiaJRPGBattleOverlaySubsystem::Initialize(FSubsystemCollectionBase& Collection)
{
	Super::Initialize(Collection);
	Collection.InitializeDependency<UMelodiaNarrativeSubsystem>();

	if (UMelodiaNarrativeSubsystem* Narrative =
		GetGameInstance()->GetSubsystem<UMelodiaNarrativeSubsystem>())
	{
		Narrative->OnBattleRequested.AddUniqueDynamic(this, &ThisClass::HandleBattleRequested);
		Narrative->OnBattleCompleted.AddUniqueDynamic(this, &ThisClass::HandleBattleCompleted);
		Narrative->OnBattleAborted.AddUniqueDynamic(this, &ThisClass::HandleBattleAborted);
	}
}

void UMelodiaJRPGBattleOverlaySubsystem::Deinitialize()
{
	if (const UGameInstance* GameInstance = GetGameInstance())
	{
		if (UMelodiaNarrativeSubsystem* Narrative =
			GameInstance->GetSubsystem<UMelodiaNarrativeSubsystem>())
		{
			Narrative->OnBattleRequested.RemoveDynamic(this, &ThisClass::HandleBattleRequested);
			Narrative->OnBattleCompleted.RemoveDynamic(this, &ThisClass::HandleBattleCompleted);
			Narrative->OnBattleAborted.RemoveDynamic(this, &ThisClass::HandleBattleAborted);
		}
	}

	RemoveRhythmPrompt();
	RemoveKeyboardLegend();
	Super::Deinitialize();
}

void UMelodiaJRPGBattleOverlaySubsystem::HandleBattleRequested(const FName EncounterId)
{
	RemoveRhythmPrompt();
	RemoveKeyboardLegend();

	UWorld* World = GetWorld();
	APlayerController* PlayerController = World ? World->GetFirstPlayerController() : nullptr;
	if (!IsValid(PlayerController))
	{
		UE_LOG(LogTemp, Warning,
			TEXT("Melodia rhythm prompt not created for encounter %s: no player controller."),
			*EncounterId.ToString());
		return;
	}

	KeyboardLegend = CreateWidget<UMelodiaBattleKeyboardLegendWidget>(
		PlayerController, UMelodiaBattleKeyboardLegendWidget::StaticClass());
	if (KeyboardLegend)
	{
		KeyboardLegend->SetIsFocusable(false);
		KeyboardLegend->AddToViewport(KeyboardLegendZOrder);
	}
	else
	{
		UE_LOG(LogTemp, Warning, TEXT("Melodia keyboard legend creation failed for encounter %s."), *EncounterId.ToString());
	}

	const TSubclassOf<UUserWidget> PromptClass = LoadClass<UUserWidget>(nullptr, RhythmPromptClassPath);
	if (!PromptClass)
	{
		UE_LOG(LogTemp, Error, TEXT("Melodia rhythm prompt class is missing: %s"), RhythmPromptClassPath);
		return;
	}

	RhythmPrompt = CreateWidget<UUserWidget>(PlayerController, PromptClass);
	if (!RhythmPrompt)
	{
		UE_LOG(LogTemp, Error,
			TEXT("Melodia rhythm prompt creation failed for encounter %s."),
			*EncounterId.ToString());
		return;
	}

	RhythmPrompt->SetIsFocusable(false);
	RhythmPrompt->SetVisibility(ESlateVisibility::Collapsed);
	RhythmPrompt->AddToViewport(RhythmPromptZOrder);
}

void UMelodiaJRPGBattleOverlaySubsystem::HandleBattleCompleted(
	const FName EncounterId,
	const EMelodiaBattleResult Result)
{
	RemoveRhythmPrompt();
	RemoveKeyboardLegend();
}

void UMelodiaJRPGBattleOverlaySubsystem::HandleBattleAborted(
	const FName EncounterId,
	const FString Reason)
{
	RemoveRhythmPrompt();
	RemoveKeyboardLegend();
}

void UMelodiaJRPGBattleOverlaySubsystem::RemoveRhythmPrompt()
{
	if (RhythmPrompt)
	{
		RhythmPrompt->RemoveFromParent();
		RhythmPrompt = nullptr;
	}
}

void UMelodiaJRPGBattleOverlaySubsystem::RemoveKeyboardLegend()
{
	if (KeyboardLegend)
	{
		KeyboardLegend->RemoveFromParent();
		KeyboardLegend = nullptr;
	}
}
