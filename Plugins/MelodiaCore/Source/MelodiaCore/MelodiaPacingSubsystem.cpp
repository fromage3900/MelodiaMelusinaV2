#include "MelodiaPacingSubsystem.h"

#include "Engine/Engine.h"
#include "Engine/GameInstance.h"
#include "Engine/World.h"
#include "MelodiaPacingProfile.h"

void UMelodiaPacingSubsystem::Initialize(FSubsystemCollectionBase& Collection)
{
	Super::Initialize(Collection);

	if (ActiveProfile)
	{
		return;
	}
	ActiveProfile = LoadObject<UMelodiaPacingProfile>(nullptr, TEXT("/Game/MelodiaIntegration/Config/DA_MelodiaPacingProfile.DA_MelodiaPacingProfile"));
	if (!ActiveProfile)
	{
		UE_LOG(LogTemp, Warning, TEXT("MelodiaPacingProfile is missing: /Game/MelodiaIntegration/Config/DA_MelodiaPacingProfile -- pacing tuning disabled, consumers use their EditAnywhere defaults."));
	}
}

UMelodiaPacingSubsystem* UMelodiaPacingSubsystem::Get(const UObject* WorldContextObject)
{
	const UWorld* World = GEngine ? GEngine->GetWorldFromContextObject(WorldContextObject, EGetWorldErrorMode::ReturnNull) : nullptr;
	const UGameInstance* GameInstance = World ? World->GetGameInstance() : nullptr;
	return GameInstance ? GameInstance->GetSubsystem<UMelodiaPacingSubsystem>() : nullptr;
}

void UMelodiaPacingSubsystem::SetActiveProfile(UMelodiaPacingProfile* InProfile)
{
	ActiveProfile = InProfile;
}

bool UMelodiaPacingSubsystem::ResolveDuration(const FName DurationId, float& OutValue) const
{
	if (!ActiveProfile || DurationId.IsNone())
	{
		return false;
	}

	if (const float* Found = ActiveProfile->Durations.Find(DurationId))
	{
		OutValue = *Found;
		return true;
	}

	return false;
}
