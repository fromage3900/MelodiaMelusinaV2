// Copyright 2024 Tore Lervik. All Rights Reserved.

#pragma once

#include "CoreMinimal.h"
#include "MeshBlendShared.h"
#include "Components/StaticMeshComponent.h"
#include "Materials/MaterialInterface.h"
#include "MeshBlendPrimitiveDataIndexHelper.generated.h"

USTRUCT()
struct MESHBLEND_API FMeshBlendPrimitiveDataIndexHelperData
{
	GENERATED_BODY()

	UPROPERTY()
	int32 PrimitiveDataIndex = INDEX_NONE;

#if WITH_EDITORONLY_DATA
	UPROPERTY()
	bool bIsOnlyStaticBlends = true;
#endif
};

USTRUCT()
struct MESHBLEND_API FMeshBlendPrimitiveDataIndexHelper
{
	GENERATED_BODY()

	UPROPERTY()
	TMap<TWeakObjectPtr<UStaticMesh>, FMeshBlendPrimitiveDataIndexHelperData> CachedMeshIndexes;

	UPROPERTY()
	TMap<TWeakObjectPtr<UMaterialInterface>, int32> CachedMaterialIndexes;

	void Empty()
	{
		CachedMeshIndexes.Empty();
		CachedMaterialIndexes.Empty();
	}

	int32 GetPrimitiveDataIndex(UMaterialInterface* MaterialInterface)
	{
		TRACE_CPUPROFILER_EVENT_SCOPE_STR(__FUNCTION__);
		check(MaterialInterface);

		if (const int32* FoundIndex = CachedMaterialIndexes.Find(MaterialInterface))
		{
			return *FoundIndex;
		}

		FMaterialParameterMetadata ParameterMetadata;

		if (MaterialInterface->GetParameterValue(EMaterialParameterType::Scalar,
		                                         FMemoryImageMaterialParameterInfo(GName_AutoBlendID),
		                                         ParameterMetadata,
		                                         EMaterialGetParameterValueFlags::CheckAll))
		{
			CachedMaterialIndexes.Add(MaterialInterface, ParameterMetadata.PrimitiveDataIndex);
			return ParameterMetadata.PrimitiveDataIndex;
		}

		return INDEX_NONE;
	}

	FMeshBlendPrimitiveDataIndexHelperData GetPrimitiveDataForMesh(UStaticMeshComponent* StaticMeshComponent)
	{
		TRACE_CPUPROFILER_EVENT_SCOPE_STR(__FUNCTION__);
		check(StaticMeshComponent);

		FMeshBlendPrimitiveDataIndexHelperData NewData;

		if (UStaticMesh* StaticMesh = StaticMeshComponent->GetStaticMesh())
		{
			if (const FMeshBlendPrimitiveDataIndexHelperData* FoundIndex = CachedMeshIndexes.Find(StaticMesh))
			{
				return *FoundIndex;
			}

			FMaterialParameterMetadata ParameterMetadata;

			for (FStaticMaterial& StaticMaterial : StaticMesh->GetStaticMaterials())
			{
				if (StaticMaterial.MaterialInterface)
				{
					if (NewData.PrimitiveDataIndex == INDEX_NONE)
					{
						NewData.PrimitiveDataIndex = GetPrimitiveDataIndex(StaticMaterial.MaterialInterface);
					}

#if WITH_EDITORONLY_DATA
					bool bIsChecked = false;
					FGuid ExpressionGuid;

					if (!NewData.bIsOnlyStaticBlends || !StaticMaterial.MaterialInterface->GetStaticSwitchParameterValue(TEXT("Use Static Value"), bIsChecked, ExpressionGuid) || !
						bIsChecked)
					{
						NewData.bIsOnlyStaticBlends = false;
					}
#endif
				}
			}

			CachedMeshIndexes.Add(StaticMesh, NewData);
		}

		return NewData;
	}
};
