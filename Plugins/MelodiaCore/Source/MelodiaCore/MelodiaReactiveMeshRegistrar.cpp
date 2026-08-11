#include "MelodiaReactiveMeshRegistrar.h"
#include "EngineUtils.h"
#include "MelodiaRhythmReactivitySubsystem.h"
#include "Engine/World.h"
#include "Engine/Engine.h"
#include "Components/PrimitiveComponent.h"
#include "Components/StaticMeshComponent.h"
#include "Components/SkeletalMeshComponent.h"

const FName UMelodiaReactiveMeshRegistrar::ReactiveTag = TEXT("ReactiveToMusic");

void UMelodiaReactiveMeshRegistrar::Initialize(FSubsystemCollectionBase& Collection)
{
	Super::Initialize(Collection);

	UWorld* World = GetWorld();
	if (!World)
	{
		return;
	}

	UMelodiaRhythmReactivitySubsystem* Reactivity = World->GetSubsystem<UMelodiaRhythmReactivitySubsystem>();
	if (!Reactivity)
	{
		return;
	}

	// Scan all actors tagged ReactiveToMusic and register their visible mesh components.
	for (TActorIterator<AActor> It(World); It; ++It)
	{
		AActor* Actor = *It;
		if (!Actor || !Actor->Tags.Contains(ReactiveTag))
		{
			continue;
		}

		TArray<UPrimitiveComponent*> MeshComponents;
		Actor->GetComponents<UPrimitiveComponent>(MeshComponents);

		for (UPrimitiveComponent* Comp : MeshComponents)
		{
			if (Comp && Comp->IsVisible())
			{
				Reactivity->RegisterReactiveMeshComponent(Comp);
			}
		}
	}
}
