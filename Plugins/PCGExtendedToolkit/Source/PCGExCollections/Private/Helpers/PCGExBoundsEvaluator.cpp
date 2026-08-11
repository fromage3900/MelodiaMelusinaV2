// Copyright 2026 Timothé Lapetite and contributors
// Released under the MIT license https://opensource.org/license/MIT/

#include "Helpers/PCGExBoundsEvaluator.h"

#include "Components/LightComponent.h"
#include "Components/PrimitiveComponent.h"
#include "GameFramework/Actor.h"

#pragma region UPCGExBoundsEvaluator

FBox UPCGExBoundsEvaluator::EvaluateActorBounds_Implementation(AActor* Actor, UPCGExAssetCollection* OwningCollection, int32 EntryIndex) const
{
	if (!Actor)
	{
		return FBox(ForceInit);
	}

	FBox AccumulatedBounds(ForceInit);

	TInlineComponentArray<UPrimitiveComponent*> PrimitiveComponents;
	Actor->GetComponents<UPrimitiveComponent>(PrimitiveComponents);

	for (const UPrimitiveComponent* PrimComp : PrimitiveComponents)
	{
		if (!PrimComp->IsRegistered())
		{
			continue;
		}
		AccumulatedBounds += PrimComp->Bounds.GetBox();
	}

	return AccumulatedBounds;
}

#pragma endregion

#pragma region UPCGExDefaultBoundsEvaluator

FBox UPCGExDefaultBoundsEvaluator::EvaluateActorBounds_Implementation(AActor* Actor, UPCGExAssetCollection* OwningCollection, int32 EntryIndex) const
{
	if (!Actor)
	{
		return FBox(ForceInit);
	}

	FBox AccumulatedBounds(ForceInit);

	TInlineComponentArray<UPrimitiveComponent*> PrimitiveComponents;
	Actor->GetComponents<UPrimitiveComponent>(PrimitiveComponents, bIncludeFromChildActors);

	for (const UPrimitiveComponent* PrimComp : PrimitiveComponents)
	{
		if (!PrimComp->IsRegistered())
		{
			continue;
		}
		if (bIgnoreEditorOnlyComponents && PrimComp->IsEditorOnly())
		{
			continue;
		}
		if (bOnlyCollidingComponents && !PrimComp->IsCollisionEnabled())
		{
			continue;
		}
		if (bIgnoreLightComponents && PrimComp->IsA<ULightComponent>())
		{
			continue;
		}

		AccumulatedBounds += PrimComp->Bounds.GetBox();
	}

	return AccumulatedBounds;
}

#pragma endregion
