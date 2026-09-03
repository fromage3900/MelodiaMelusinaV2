// Copyright 2024 Tore Lervik. All Rights Reserved.


#include "PrimitiveDataHelper.h"

#include "MeshBlendShared.h"
#include "Components/InstancedStaticMeshComponent.h"
#include "Components/PrimitiveComponent.h"

void FPrimitiveDataHelper::EnsurePrimitiveDataSlot(UMeshComponent* StaticMeshComponent, const int32 CustomPrimitiveDataIndex)
{
	TRACE_CPUPROFILER_EVENT_SCOPE_STR(__FUNCTION__);

	if (UInstancedStaticMeshComponent* InstancedStaticMeshComponent = Cast<UInstancedStaticMeshComponent>(StaticMeshComponent))
	{
		const int32 DesiredNumCustomDataFloats = CustomPrimitiveDataIndex + 1;

		if (InstancedStaticMeshComponent->NumCustomDataFloats < DesiredNumCustomDataFloats)
		{
			TArray<float> CustomData;
			CustomData.Reserve(InstancedStaticMeshComponent->GetInstanceCount() * DesiredNumCustomDataFloats);

			for (int32 i = 0; i < InstancedStaticMeshComponent->GetInstanceCount(); ++i)
			{
				for (int32 j = 0; j < InstancedStaticMeshComponent->NumCustomDataFloats; ++j)
				{
					CustomData.Add(InstancedStaticMeshComponent->PerInstanceSMCustomData[i * InstancedStaticMeshComponent->NumCustomDataFloats + j]);
				}

				for (int32 y = 0; y < (DesiredNumCustomDataFloats - InstancedStaticMeshComponent->NumCustomDataFloats); ++y)
				{
					CustomData.Add(0.0f);
				}
			}

			InstancedStaticMeshComponent->NumCustomDataFloats = DesiredNumCustomDataFloats;
			InstancedStaticMeshComponent->PerInstanceSMCustomData = MoveTemp(CustomData);
		}
	}
}

// Helper function since InstancedStaticMeshComponent->SetCustomDataValue marks the component as modified.
void FPrimitiveDataHelper::SetCustomDataValue(UInstancedStaticMeshComponent* InstancedStaticMeshComponent,
                                              const int32 InstanceIndex,
                                              const int32 CustomPrimitiveDataIndex,
                                              const float Value)
{
	TArray<float> CustomData;
	CustomData.SetNum(InstancedStaticMeshComponent->NumCustomDataFloats);

	for (int32 j = 0; j < InstancedStaticMeshComponent->NumCustomDataFloats; j++)
	{
		CustomData[j] = InstancedStaticMeshComponent->PerInstanceSMCustomData[InstanceIndex * InstancedStaticMeshComponent->NumCustomDataFloats + j];
	}

	CustomData[CustomPrimitiveDataIndex] = Value;

	InstancedStaticMeshComponent->SetCustomData(InstanceIndex, MakeArrayView(CustomData), false);
}
