#include "MelodiaTravelSubsystem.h"

#include "Engine/Engine.h"
#include "Engine/GameInstance.h"
#include "Engine/World.h"
#include "GameFramework/Pawn.h"
#include "GameFramework/PlayerController.h"
#include "GameFramework/PlayerStart.h"
#include "Kismet/GameplayStatics.h"
#include "MelodiaAuthorityLocator.h"
#include "MelodiaInputContextSubsystem.h"
#include "MelodiaNarrativeSubsystem.h"
#include "MultiWorldManager.h"
#include "MultiWorldStatics.h"
#include "UObject/SoftObjectPath.h"
#include "UObject/UObjectGlobals.h"

namespace
{
	/** cpp-only transition guard; avoids changing the GameInstance subsystem layout. */
	TSet<UMelodiaTravelSubsystem*> GMultiWorldTransitions;
}

void UMelodiaTravelSubsystem::Initialize(FSubsystemCollectionBase& Collection)
{
	Super::Initialize(Collection);

	if (UMelodiaNarrativeSubsystem* Narrative = GetNarrative())
	{
		// Narrative validates against the allowlist and broadcasts. This subsystem is
		// the single consumer -- before it existed the broadcast went nowhere.
		Narrative->OnTravelRequested.AddUniqueDynamic(this, &ThisClass::HandleTravelRequested);
	}

	PostLoadMapHandle = FCoreUObjectDelegates::PostLoadMapWithWorld.AddUObject(this, &ThisClass::HandlePostLoadMap);

	if (UMelodiaAuthorityLocator* Locator = UMelodiaAuthorityLocator::Get(this))
	{
		Locator->RegisterTravelProvider(TScriptInterface<IMelodiaTravelProvider>(this));
		UE_LOG(LogTemp, Log, TEXT("MELODIA_AUTHORITY registered TravelProvider"));
	}
}

void UMelodiaTravelSubsystem::Deinitialize()
{
	if (PostLoadMapHandle.IsValid())
	{
		FCoreUObjectDelegates::PostLoadMapWithWorld.Remove(PostLoadMapHandle);
		PostLoadMapHandle.Reset();
	}

	if (UMelodiaNarrativeSubsystem* Narrative = GetNarrative())
	{
		Narrative->OnTravelRequested.RemoveDynamic(this, &ThisClass::HandleTravelRequested);
	}

	TravellingToLevelId = NAME_None;
	GMultiWorldTransitions.Remove(this);
	Super::Deinitialize();
}

UMelodiaTravelSubsystem* UMelodiaTravelSubsystem::Get(const UObject* WorldContextObject)
{
	const UWorld* World = GEngine ? GEngine->GetWorldFromContextObject(WorldContextObject, EGetWorldErrorMode::ReturnNull) : nullptr;
	const UGameInstance* GameInstance = World ? World->GetGameInstance() : nullptr;
	return GameInstance ? GameInstance->GetSubsystem<UMelodiaTravelSubsystem>() : nullptr;
}

UMelodiaNarrativeSubsystem* UMelodiaTravelSubsystem::GetNarrative() const
{
	const UGameInstance* GameInstance = GetGameInstance();
	return GameInstance ? GameInstance->GetSubsystem<UMelodiaNarrativeSubsystem>() : nullptr;
}

FName UMelodiaTravelSubsystem::GetPendingSpawnTag(const FName MapId) const
{
	const UMelodiaNarrativeSubsystem* Narrative = GetNarrative();
	return Narrative ? Narrative->GetSpawnContext(MapId) : NAME_None;
}

bool UMelodiaTravelSubsystem::TravelTo(const FName LevelId, const FName SpawnTag)
{
	UMelodiaNarrativeSubsystem* Narrative = GetNarrative();
	if (!Narrative)
	{
		UE_LOG(LogTemp, Warning, TEXT("MELODIA_TRAVEL rejected: narrative subsystem unavailable (level=%s)"), *LevelId.ToString());
		return false;
	}

	// Record the arrival point BEFORE requesting travel. RequestTravel broadcasts
	// synchronously, so HandleTravelRequested must already be able to see the tag.
	// It lives on the narrative record so it survives a save/load across the
	// transition rather than in a member here.
	if (!SpawnTag.IsNone())
	{
		Narrative->SetSpawnContext(LevelId, SpawnTag);
	}

	// Validation lives in RequestTravel: allowlist check against TravelLevelIds.
	// A false return means the ID was not approved and nothing should happen.
	if (!Narrative->RequestTravel(LevelId))
	{
		return false;
	}

	return true;
}

void UMelodiaTravelSubsystem::HandleTravelRequested(const FName LevelId)
{
	UWorld* World = GetGameInstance() ? GetGameInstance()->GetWorld() : nullptr;
	if (!World)
	{
		UE_LOG(LogTemp, Warning, TEXT("MELODIA_TRAVEL rejected: no world (level=%s)"), *LevelId.ToString());
		return;
	}

	if (GMultiWorldTransitions.Contains(this))
	{
		UE_LOG(LogTemp, Warning, TEXT("MELODIA_TRAVEL rejected: a MultiWorld transition is already in flight"));
		return;
	}

	TravellingToLevelId = LevelId;
	const FName SpawnTag = GetPendingSpawnTag(LevelId);

	UE_LOG(LogTemp, Log, TEXT("MELODIA_TRAVEL_START level=%s spawn_tag=%s"),
		*LevelId.ToString(), *SpawnTag.ToString());

	OnTravelStarted.Broadcast(LevelId, SpawnTag);

	// This is the MultiWorld seam. Morning is deliberately the main world:
	// when we enter KaleidoNave the main-world package stays loaded and its
	// PlayerController/UI state remains available for the return switch.
	const FString MorningMapName(TEXT("/Game/Melodia/Levels/Opening/L_MelusinaMorning"));
	const FString KaleidoMapName(TEXT("/Game/EnvSandbox/Environments/L_KaleidoNave"));
	const FName KaleidoWorldName(TEXT("Melodia_KaleidoNave"));

	if (LevelId.ToString() == MorningMapName)
	{
		UMultiWorldManager* MultiWorld = GetGameInstance()
			? GetGameInstance()->GetSubsystem<UMultiWorldManager>()
			: nullptr;
		if (!MultiWorld)
		{
			UE_LOG(LogTemp, Warning, TEXT("MELODIA_TRAVEL rejected: MultiWorld manager unavailable (level=%s)"), *LevelId.ToString());
			return;
		}

		GMultiWorldTransitions.Add(this);
		UE_LOG(LogTemp, Log, TEXT("MELODIA_TRAVEL_MULTIWORLD_RETURN level=%s spawn_tag=%s"),
			*LevelId.ToString(), *SpawnTag.ToString());

		MultiWorld->RequestSwitchWorld(MultiWorld->GetMainWorldHandle(), [this, MultiWorld, ArrivedLevelId = LevelId](bool bSwitched)
		{
			if (!bSwitched)
			{
				UE_LOG(LogTemp, Warning, TEXT("MELODIA_TRAVEL_MULTIWORLD_RETURN failed: could not switch to Morning"));
				TravellingToLevelId = NAME_None;
				GMultiWorldTransitions.Remove(this);
				return;
			}

				TravellingToLevelId = ArrivedLevelId;
				HandlePostLoadMap(UMultiWorldStatics::GetWorldPtr(MultiWorld->GetActiveWorldHandle()));
		});
		return;
	}

	if (LevelId.ToString() == KaleidoMapName)
	{
		UMultiWorldManager* MultiWorld = GetGameInstance()
			? GetGameInstance()->GetSubsystem<UMultiWorldManager>()
			: nullptr;
		if (!MultiWorld)
		{
			UE_LOG(LogTemp, Warning, TEXT("MELODIA_TRAVEL rejected: MultiWorld manager unavailable (level=%s)"), *LevelId.ToString());
			return;
		}

		FMultiWorldLoadParameters LoadParams;
		LoadParams.WorldName = KaleidoWorldName;
		LoadParams.bAutoInitializeWorld = true;
		LoadParams.bStartWithTickEnabled = false;
		LoadParams.bAutoHandleWidgets = true;
		LoadParams.bAutoHandleInputMode = true;
		LoadParams.bCreateDedicatedAudioDevice = true;

		GMultiWorldTransitions.Add(this);
		UE_LOG(LogTemp, Log, TEXT("MELODIA_TRAVEL_MULTIWORLD_LOAD level=%s spawn_tag=%s world_name=%s"),
			*LevelId.ToString(), *SpawnTag.ToString(), *KaleidoWorldName.ToString());

		TSoftObjectPtr<UWorld> MapAsset{FSoftObjectPath(KaleidoMapName)};
		MultiWorld->LoadWorldAsync(MapAsset, LoadParams,
			[this, MultiWorld, ArrivedLevelId = LevelId](bool bLoaded, FMultiWorldHandle WorldHandle, FMultiWorldLoadParameters)
			{
				if (!bLoaded || !MultiWorld)
				{
					UE_LOG(LogTemp, Warning, TEXT("MELODIA_TRAVEL_MULTIWORLD_LOAD failed: KaleidoNave did not load"));
					TravellingToLevelId = NAME_None;
					GMultiWorldTransitions.Remove(this);
					return;
				}

				MultiWorld->RequestSwitchWorld(WorldHandle, [this, ArrivedLevelId, WorldHandle](bool bSwitched)
				{
					if (!bSwitched)
					{
						UE_LOG(LogTemp, Warning, TEXT("MELODIA_TRAVEL_MULTIWORLD_LOAD failed: could not switch to KaleidoNave"));
						TravellingToLevelId = NAME_None;
						GMultiWorldTransitions.Remove(this);
						return;
					}

					TravellingToLevelId = ArrivedLevelId;
					HandlePostLoadMap(UMultiWorldStatics::GetWorldPtr(WorldHandle));
				});
			});
		return;
	}

	// Ordinary destinations retain the engine's unload-and-load behavior.
	// Only the Morning/KaleidoNave pair above is a live secondary-world seam.
	UGameplayStatics::OpenLevel(World, LevelId);
}

void UMelodiaTravelSubsystem::HandlePostLoadMap(UWorld* LoadedWorld)
{
	if (!LoadedWorld || TravellingToLevelId.IsNone())
	{
		// Not a transition we started -- editor PIE start, save load, etc.
		return;
	}

	// A MultiWorld package load can fire the engine's post-load delegate before
	// the plugin switches the active world. Only the explicit active-handle world
	// may complete the transition; ordinary OpenLevel uses the same callback.
	UWorld* ActiveWorld = nullptr;
	if (UMultiWorldManager* MultiWorld = GetGameInstance()
		? GetGameInstance()->GetSubsystem<UMultiWorldManager>()
		: nullptr)
	{
		ActiveWorld = UMultiWorldStatics::GetWorldPtr(MultiWorld->GetActiveWorldHandle());
	}
	if (GMultiWorldTransitions.Contains(this) && LoadedWorld != ActiveWorld)
	{
		return;
	}

	const FName ArrivedLevelId = TravellingToLevelId;
	TravellingToLevelId = NAME_None;
	GMultiWorldTransitions.Remove(this);

	// Force-clear input contexts on arrival. Widgets do not survive a level change,
	// so anything still stacked is orphaned and would otherwise strand the player in
	// dialogue or menu input with no owner left to release it. Any leak is logged
	// with the name of whatever pushed it.
	if (UMelodiaInputContextSubsystem* Input = GetGameInstance()
		? GetGameInstance()->GetSubsystem<UMelodiaInputContextSubsystem>()
		: nullptr)
	{
		Input->ClearAllContexts(FString::Printf(TEXT("travel arrival: %s"), *ArrivedLevelId.ToString()));
	}

	const FName SpawnTag = GetPendingSpawnTag(ArrivedLevelId);
	const bool bPlaced = PlacePawnAtSpawn(LoadedWorld, SpawnTag);

	UE_LOG(LogTemp, Log, TEXT("MELODIA_TRAVEL_ARRIVED level=%s spawn_tag=%s placed=%d"),
		*ArrivedLevelId.ToString(), *SpawnTag.ToString(), bPlaced ? 1 : 0);

	OnTravelArrived.Broadcast(ArrivedLevelId, bPlaced);
}

bool UMelodiaTravelSubsystem::PlacePawnAtSpawn(UWorld* World, const FName SpawnTag) const
{
	if (!World || SpawnTag.IsNone())
	{
		// No tag authored: leave placement to the engine. This is the pre-existing
		// behaviour, so an unconfigured transition is no worse than before.
		return false;
	}

	APlayerController* PC = UGameplayStatics::GetPlayerController(World, 0);
	APawn* Pawn = PC ? PC->GetPawn() : nullptr;
	if (!Pawn)
	{
		UE_LOG(LogTemp, Warning, TEXT("MELODIA_TRAVEL placement skipped: no player pawn yet (tag=%s)"), *SpawnTag.ToString());
		return false;
	}

	TArray<AActor*> Starts;
	UGameplayStatics::GetAllActorsOfClass(World, APlayerStart::StaticClass(), Starts);

	for (AActor* Actor : Starts)
	{
		const APlayerStart* Start = Cast<APlayerStart>(Actor);
		if (!Start)
		{
			continue;
		}

		// PlayerStartTag is the intended field; the Tags array is accepted too because
		// level designers reach for it first and both read identically in the editor.
		const bool bMatches = (Start->PlayerStartTag == SpawnTag) || Start->Tags.Contains(SpawnTag);
		if (!bMatches)
		{
			continue;
		}

		Pawn->TeleportTo(Start->GetActorLocation(), Start->GetActorRotation());
		if (PC)
		{
			PC->SetControlRotation(Start->GetActorRotation());
		}
		return true;
	}

	UE_LOG(LogTemp, Warning, TEXT("MELODIA_TRAVEL no PlayerStart tagged '%s' in %s (%d starts present); engine default used"),
		*SpawnTag.ToString(), *World->GetMapName(), Starts.Num());
	return false;
}
