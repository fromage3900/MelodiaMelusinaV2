// Copyright 2026 Timothé Lapetite and contributors
// Released under the MIT license https://opensource.org/license/MIT/

#include "Elements/Utils/PCGExDestroyActor.h"

#include "GameFramework/Actor.h"
#include "PCGComponent.h"
#include "PCGManagedResource.h"
#include "PCGModule.h"
#include "PCGPin.h"

#include "Data/PCGExData.h"
#include "Helpers/PCGExBulkAttributeHelpers.h"

#define LOCTEXT_NAMESPACE "PCGExDestroyActorElement"
#define PCGEX_NAMESPACE DestroyActor

TArray<FPCGPinProperties> UPCGExDestroyActorSettings::InputPinProperties() const
{
	TArray<FPCGPinProperties> PinProperties;
	PCGEX_PIN_ANY(PCGExCommon::Labels::SourceTargetsLabel, "Data carrying the actor references to destroy.", Required)
	return PinProperties;
}

TArray<FPCGPinProperties> UPCGExDestroyActorSettings::OutputPinProperties() const
{
	TArray<FPCGPinProperties> PinProperties;
	PCGEX_PIN_ANY(PCGPinConstants::DefaultOutputLabel, "Input data, forwarded untouched.", Required)
	return PinProperties;
}

PCGEX_INITIALIZE_ELEMENT(DestroyActor)

bool FPCGExDestroyActorElement::AdvanceWork(FPCGExContext* InContext, const UPCGExSettings* InSettings) const
{
	TRACE_CPUPROFILER_EVENT_SCOPE(FPCGExDestroyActorElement::Execute);

	PCGEX_CONTEXT_AND_SETTINGS(DestroyActor)
	PCGEX_EXECUTION_CHECK

	const TArray<FPCGTaggedData> Inputs = Context->InputData.GetInputsByPin(PCGExCommon::Labels::SourceTargetsLabel);
	Context->IncreaseStagedOutputReserve(Inputs.Num());

	// Forward every input untouched, harvesting actor references from any input that carries the attribute.
	TSet<FSoftObjectPath> UniqueActorReferences;
	for (const FPCGTaggedData& Input : Inputs)
	{
		if (!Input.Data)
		{
			continue;
		}

		TArray<FSoftObjectPath> Paths;
		PCGExData::Helpers::BulkReadSoftPaths(Input.Data, Settings->ActorReferenceAttribute, Paths);
		for (const FSoftObjectPath& Path : Paths)
		{
			if (Path.IsValid())
			{
				UniqueActorReferences.Add(Path);
			}
		}

		Context->StageOutput(const_cast<UPCGData*>(Input.Data.Get()), PCGPinConstants::DefaultOutputLabel, PCGExData::EStaging::None, Input.Tags);
	}

	// Runs on the game thread (CanExecuteOnlyOnMainThread), so matched actors are destroyed inline.
	if (!UniqueActorReferences.IsEmpty())
	{
		// Null when the execution source isn't a UPCGComponent -- then there's nothing this node spawned.
		if (UPCGComponent* Component = Context->GetMutableComponent())
		{
			TArray<AActor*> ActorsToDestroy;

			Component->ForEachManagedResource([&](UPCGManagedResource* InResource)
			{
				UPCGManagedActors* ManagedActors = Cast<UPCGManagedActors>(InResource);
				if (!ManagedActors)
				{
					return;
				}

				// Pull out ONLY the referenced actors -- never the whole spawn batch. Match on the stored
				// soft path (no deref, so unloaded actors don't crash) and walk backwards so RemoveAtSwap
				// stays valid (mirrors UPCGManagedActors::MoveResourceToNewActor).
				TArray<TSoftObjectPtr<AActor>>& GeneratedActors = ManagedActors->GetMutableGeneratedActors();
				for (int32 i = GeneratedActors.Num() - 1; i >= 0; --i)
				{
					if (!UniqueActorReferences.Contains(GeneratedActors[i].ToSoftObjectPath()))
					{
						continue;
					}

					// Unresolved (e.g. streamed-out) matches stay tracked -- can't destroy what isn't loaded.
					if (AActor* Actor = GeneratedActors[i].Get())
					{
						ActorsToDestroy.Add(Actor);
						GeneratedActors.RemoveAtSwap(i);
					}
				}
			});

			// Destroy outside the iteration -- ForEachManagedResource holds the component's resource lock.
			for (AActor* Actor : ActorsToDestroy)
			{
				Actor->Destroy();
			}
		}
	}
	else
	{
		// Warn-but-continue: data still forwards; an empty set usually means a mis-wired attribute name.
		PCGE_LOG_C(Warning, GraphAndLog, Context, FTEXT("No actor references found under the specified attribute; nothing to destroy."));
	}

	Context->Done();
	return Context->TryComplete();
}

#undef LOCTEXT_NAMESPACE
#undef PCGEX_NAMESPACE
