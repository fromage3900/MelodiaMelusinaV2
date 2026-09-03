#include "MelodiaUIFeedbackSubsystem.h"

#include "Engine/GameInstance.h"
#include "Engine/World.h"
#include "Kismet/GameplayStatics.h"
#include "Sound/SoundBase.h"

UMelodiaUIFeedbackSubsystem::UMelodiaUIFeedbackSubsystem()
{
	DefaultFeedbackSound = TSoftObjectPtr<USoundBase>(
		FSoftObjectPath(TEXT("/Game/Melodia/Audio/SFX/A_UI_Bubble.A_UI_Bubble")));
}

UMelodiaUIFeedbackSubsystem* UMelodiaUIFeedbackSubsystem::Get(const UObject* WorldContextObject)
{
	if (!IsValid(WorldContextObject))
	{
		return nullptr;
	}

	const UWorld* World = WorldContextObject->GetWorld();
	UGameInstance* GameInstance = World ? World->GetGameInstance() : nullptr;
	return GameInstance ? GameInstance->GetSubsystem<UMelodiaUIFeedbackSubsystem>() : nullptr;
}

bool UMelodiaUIFeedbackSubsystem::RequestFeedback(
	const UObject* WorldContextObject,
	const FName FeedbackId,
	const FVector2D ScreenPosition)
{
	if (FeedbackId.IsNone())
	{
		return false;
	}

	UMelodiaUIFeedbackSubsystem* Subsystem = Get(WorldContextObject);
	if (!Subsystem)
	{
		return false;
	}

	Subsystem->PlayDefaultFeedback();
	Subsystem->OnFeedbackRequested.Broadcast(FeedbackId, ScreenPosition);
	return true;
}

void UMelodiaUIFeedbackSubsystem::PlayDefaultFeedback()
{
	if (!LoadedDefaultFeedbackSound && !DefaultFeedbackSound.IsNull())
	{
		LoadedDefaultFeedbackSound = DefaultFeedbackSound.LoadSynchronous();
	}
	if (LoadedDefaultFeedbackSound)
	{
		UGameplayStatics::PlaySound2D(this, LoadedDefaultFeedbackSound);
	}
}
