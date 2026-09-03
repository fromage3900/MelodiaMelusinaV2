// Copyright 2024 Tore Lervik. All Rights Reserved.

#include "MeshBlendLevelProcessor.h"

#include "AutoBlendUserData.h"
#include "MeshBlendActivatorSubsystem.h"
#include "PrimitiveDataHelper.h"
#include "Engine/Level.h"
#include "Misc/EngineVersionComparison.h"
#include "PackedLevelActor/PackedLevelActor.h"

const FName GName_AutoBlendHasPrimitiveDataPacked = TEXT("AutoBlend_HasPrimitiveDataPacked");

void FMeshBlendLevelProcessor::Transform(ULevel* Level, UMeshBlendProcessor* Processor, const bool bAddPackedTag)
{
	TRACE_CPUPROFILER_EVENT_SCOPE_STR(__FUNCTION__);

	for (AActor* Actor : Level->Actors)
	{
		if (Actor && !Actor->IsEditorOnly())
		{
			if (Actor->Tags.Contains(GName_AutoBlendHasPrimitiveDataPacked))
			{
				// Ensure we don't process Actors already processed by the WP Runtime Cell Transformer.
				Actor->Tags.RemoveSwap(GName_AutoBlendHasPrimitiveDataPacked);

				// PLAs seem to get re-generated so we reprocess them even if the WP Cell Transformer already did it.
				if (!Actor->IsA(APackedLevelActor::StaticClass()))
				{
					continue;
				}
			}

			if (FUAutoBlendHelper::DoesItBlend(Actor))
			{
				Actor->Tags.RemoveSwap(GName_AutoBlendHasPrimitiveData);
				TInlineComponentArray<UMeshComponent*> Meshes(Actor);

				for (UMeshComponent* MeshComponent : Meshes)
				{
					// Ensure we remove any existing tags before processing the component.
					MeshComponent->ComponentTags.RemoveSwap(GName_AutoBlendHasPrimitiveData);

#if UE_VERSION_OLDER_THAN(5, 4, 0)
#else
					// Ensure the ISMs PICDs are saved when serializing (packaging).
					// Reference: https://jira.it.epicgames.com/browse/UE-216035
					if (UInstancedStaticMeshComponent* ISMComponent = Cast<UInstancedStaticMeshComponent>(MeshComponent))
					{
						ISMComponent->bInheritPerInstanceData = false;
					}
					MeshComponent->bEditableWhenInherited = true;
#endif
				}

				Processor->ActivateActor(Actor, TNumericLimits<double>::Max(), true);
			}
			else
			{
				// Mark non blending actors as "already initialized" to avoid processing them again at runtime.
				Actor->Tags.Add(GName_AutoBlendHasPrimitiveData);
			}

			if (bAddPackedTag)
			{
				Actor->Tags.Add(GName_AutoBlendHasPrimitiveDataPacked);
			}
		}
	}
}
