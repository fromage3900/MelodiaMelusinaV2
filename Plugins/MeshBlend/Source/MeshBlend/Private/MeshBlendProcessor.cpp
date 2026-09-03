// Copyright 2024 Tore Lervik. All Rights Reserved.


#include "MeshBlendProcessor.h"

#include "MeshBlendActivator.h"
#include "PrimitiveDataHelper.h"
#include "Components/InstancedStaticMeshComponent.h"
#include "Materials/MaterialInterface.h"

void UMeshBlendProcessor::Reset()
{
	BlendValueBucket.Reset();
	PrimitiveDataIndexHelper.Empty();
	ActorActivationComponentInstanceIndex = 0;
	ActorActivationComponentIndex = 0;
}

uint8 UMeshBlendProcessor::GetAutoBlendID(const EAutoBlendOption MeshAutoBlendState)
{
	uint8 StencilValue = 0;

	if (MeshAutoBlendState == Small)
	{
		StencilValue = SmallBlendCounter;
		SmallBlendCounter += 2;
		SmallBlendCounter = (SmallBlendCounter - StencilStartSmall) % ClampedStencilRange + StencilStartSmall;
	}
	else if (MeshAutoBlendState == Medium)
	{
		StencilValue = MediumBlendCounter;
		MediumBlendCounter += 2;
		MediumBlendCounter = (MediumBlendCounter - StencilStartMedium) % ClampedStencilRange + StencilStartMedium;
	}
	else if (MeshAutoBlendState == Large)
	{
		StencilValue = LargeBlendCounter;
		LargeBlendCounter += 2;
		LargeBlendCounter = (LargeBlendCounter - StencilStartLarge) % ClampedStencilRange + StencilStartLarge;
	}
	else if (MeshAutoBlendState == Extra_Large)
	{
		StencilValue = ExtraLargeBlendCounter;
		ExtraLargeBlendCounter += 2;
		ExtraLargeBlendCounter = (ExtraLargeBlendCounter - StencilStartExtraLarge) % ClampedStencilRange + StencilStartExtraLarge;
	}

	return StencilValue;
}

uint8 UMeshBlendProcessor::GetReservedAutoBlendID(const EAutoBlendOption MeshAutoBlendState, const uint8 Offset)
{
	if (MeshAutoBlendState == Small)
	{
		return StencilStartSmall + ClampedStencilRange + 1 + Offset;
	}
	else if (MeshAutoBlendState == Medium)
	{
		return StencilStartMedium + ClampedStencilRange + 1 + Offset;
	}
	else if (MeshAutoBlendState == Large)
	{
		return StencilStartLarge + ClampedStencilRange + 1 + Offset;
	}
	else if (MeshAutoBlendState == Extra_Large)
	{
		return StencilStartExtraLarge + ClampedStencilRange + 1 + Offset;
	}

	return 0;
}

uint8 UMeshBlendProcessor::AssignAutoBlendId(const FBox& Box, const EAutoBlendOption MeshAutoBlendState)
{
	TRACE_CPUPROFILER_EVENT_SCOPE_STR(__FUNCTION__);

	// We try N times to find an available AutoBlendID that doesn't overlap with any other bounds
	constexpr int32 MaxAttempts = 20;

	for (int32 AttemptIndex = 0; AttemptIndex <= MaxAttempts; AttemptIndex++)
	{
		const uint8 AutoBlendID = GetAutoBlendID(MeshAutoBlendState);

		if (!BlendValueBucket.Contains(AutoBlendID))
		{
			BlendValueBucket.Add(AutoBlendID, FBlendValueBucket());
		}

		FBlendValueBucket& Bucket = BlendValueBucket[AutoBlendID];

		if (Bucket.Intersect(Box))
		{
			continue;
		}

		Bucket.Add(Box);
		return AutoBlendID;
	}

	// If we have exhausted all attempts we try to find a AutoBlendID in the reserved range.
	for (int32 ReservedRangeOffset = 0; ReservedRangeOffset < ReservedStencilRange; ReservedRangeOffset++)
	{
		const uint8 AutoBlendID = GetReservedAutoBlendID(MeshAutoBlendState, ReservedRangeOffset);

		if (!BlendValueBucket.Contains(AutoBlendID))
		{
			BlendValueBucket.Add(AutoBlendID, FBlendValueBucket());
		}

		FBlendValueBucket& Bucket = BlendValueBucket[AutoBlendID];

		if (Bucket.Intersect(Box))
		{
			continue;
		}

		Bucket.Add(Box);
		return AutoBlendID;
	}

	return GetAutoBlendID(MeshAutoBlendState);
}

bool UMeshBlendProcessor::ActivateActor(AActor* Actor, const double MaxProcessDuration, bool bIsCooking)
{
	TRACE_CPUPROFILER_EVENT_SCOPE_STR(__FUNCTION__);
	SCOPE_CYCLE_UOBJECT(Actor, Actor);

	EAutoBlendOption ActorAutoBlendState = Disabled;
	FUAutoBlendHelper::TryGetBlendOptionFromActorTag(Actor, ActorAutoBlendState);
	int32 CurrentComponentIndex = 0;

	for (UActorComponent* Component : Actor->GetComponents())
	{
		if (CurrentComponentIndex < ActorActivationComponentIndex)
		{
			CurrentComponentIndex++;
			continue;
		}

		TRACE_CPUPROFILER_EVENT_SCOPE_STR("UMeshBlendProcessor::ActivateActor::StaticMeshComponent");

		if (FMeshBlendShared::IsOverProcessBudget(MaxProcessDuration))
		{
			ActorActivationComponentIndex = CurrentComponentIndex;
			return false;
		}

		CurrentComponentIndex++;

		if (!Component->IsA<UMeshComponent>())
		{
			continue;
		}

		UMeshComponent* MeshComponent = static_cast<UMeshComponent*>(Component);

		SCOPE_CYCLE_UOBJECT(Component, Component);

		if (MeshComponent->ComponentHasTag(GName_AutoBlendHasPrimitiveData))
		{
			continue;
		}

		EAutoBlendOption ComponentAutoBlendState = Disabled;

		if (!FUAutoBlendHelper::TryGetBlendOptionFromComponentTag(MeshComponent, ComponentAutoBlendState))
		{
			ComponentAutoBlendState = ActorAutoBlendState;
		}

		if (ComponentAutoBlendState == Disabled)
		{
			if (const UAutoBlendUserData* AutoBlendUserData = FMeshBlendShared::GetAutoBlendUserData(MeshComponent))
			{
				ComponentAutoBlendState = AutoBlendUserData->AutoBlendOption;
			}
		}

		if (ComponentAutoBlendState == Disabled)
		{
			continue;
		}

		int32 CustomPrimitiveDataIndex = INDEX_NONE;

#if WITH_EDITORONLY_DATA
		bool bIsOnlyStaticBlends = true;
#endif

		// Fast path for static mesh components without overridden materials
		if (MeshComponent->IsA<UStaticMeshComponent>() && !MeshComponent->HasOverrideMaterials())
		{
			UStaticMeshComponent* StaticMeshComponent = static_cast<UStaticMeshComponent*>(MeshComponent);
			FMeshBlendPrimitiveDataIndexHelperData PrimitiveDataResult = PrimitiveDataIndexHelper.GetPrimitiveDataForMesh(StaticMeshComponent);
			CustomPrimitiveDataIndex = PrimitiveDataResult.PrimitiveDataIndex;

#if WITH_EDITORONLY_DATA
			bIsOnlyStaticBlends = PrimitiveDataResult.bIsOnlyStaticBlends;
#endif
		}
		else
		{
			const int32 NumMaterials = MeshComponent->GetNumMaterials();
			for (int32 MaterialIndex = 0; MaterialIndex < NumMaterials; ++MaterialIndex)
			{
				TRACE_CPUPROFILER_EVENT_SCOPE_STR("UMeshBlendProcessor::ActivateActor::GetMaterial");
				if (UMaterialInterface* Material = MeshComponent->GetMaterial(MaterialIndex))
				{
					if (CustomPrimitiveDataIndex == INDEX_NONE)
					{
						CustomPrimitiveDataIndex = PrimitiveDataIndexHelper.GetPrimitiveDataIndex(Material);
					}

#if WITH_EDITORONLY_DATA
					bool bIsChecked = false;
					FGuid ExpressionGuid;

					if (!bIsOnlyStaticBlends || !Material->GetStaticSwitchParameterValue(TEXT("Use Static Value"), bIsChecked, ExpressionGuid) || !bIsChecked)
					{
						bIsOnlyStaticBlends = false;
					}
#endif
				}
			}
		}

		if (CustomPrimitiveDataIndex == INDEX_NONE)
		{
			continue;
		}

#if WITH_EDITORONLY_DATA
		// If all materials are using static values, we skip processing this component
		if (bIsOnlyStaticBlends)
		{
			continue;
		}
#endif

		FPrimitiveDataHelper::EnsurePrimitiveDataSlot(MeshComponent, CustomPrimitiveDataIndex);
		const FBoxSphereBounds MeshAssetBounds = FMeshBlendShared::GetMeshBounds(MeshComponent);

		if (MeshComponent->IsA<UInstancedStaticMeshComponent>())
		{
			UInstancedStaticMeshComponent* InstancedStaticMeshComponent = static_cast<UInstancedStaticMeshComponent*>(MeshComponent);

			for (int32 InstanceIndex = ActorActivationComponentInstanceIndex; InstanceIndex < InstancedStaticMeshComponent->GetInstanceCount(); InstanceIndex++)
			{
				if (FMeshBlendShared::IsOverProcessBudget(MaxProcessDuration))
				{
					ActorActivationComponentIndex = CurrentComponentIndex - 1;
					ActorActivationComponentInstanceIndex = InstanceIndex;
					return false;
				}

				FTransform InstanceTransform;
				InstancedStaticMeshComponent->GetInstanceTransform(InstanceIndex, InstanceTransform, true);
				const FBox Bounds = MeshAssetBounds.TransformBy(InstanceTransform).GetBox();
				const float Value = static_cast<float>(AssignAutoBlendId(Bounds, ComponentAutoBlendState)) / 255.0;
				FPrimitiveDataHelper::SetCustomDataValue(InstancedStaticMeshComponent, InstanceIndex, CustomPrimitiveDataIndex, Value);
			}

			{
				TRACE_CPUPROFILER_EVENT_SCOPE_STR("UMeshBlendProcessor::ActivateActor::InstancedStaticMeshComponent->MarkRenderStateDirty");
				InstancedStaticMeshComponent->MarkRenderStateDirty();
			}
		}
		else
		{
			const FBox Bounds = MeshAssetBounds.TransformBy(MeshComponent->GetComponentTransform()).GetBox();
			uint8 AutoBlendID = AssignAutoBlendId(Bounds, ComponentAutoBlendState);

			if (bIsCooking)
			{
				MeshComponent->SetDefaultCustomPrimitiveDataFloat(CustomPrimitiveDataIndex, static_cast<float>(AutoBlendID) / 255.0);
			}
			else
			{
				TRACE_CPUPROFILER_EVENT_SCOPE_STR("UMeshBlendProcessor::ActivateActor::MeshComponent->SetCustomPrimitiveDataFloat");
				MeshComponent->SetCustomPrimitiveDataFloat(CustomPrimitiveDataIndex, static_cast<float>(AutoBlendID) / 255.0);
			}
		}

		ActorActivationComponentInstanceIndex = 0;
		MeshComponent->ComponentTags.Add(GName_AutoBlendHasPrimitiveData);
	}

	ActorActivationComponentInstanceIndex = 0;
	ActorActivationComponentIndex = 0;
	Actor->Tags.Add(GName_AutoBlendHasPrimitiveData);
	return true;
}
