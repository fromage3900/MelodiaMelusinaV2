// Copyright 2024 Tore Lervik. All Rights Reserved.

#pragma once

#include "CoreMinimal.h"
#include "MeshBlendProcessor.h"
#include "MeshBlendLevelProcessor.generated.h"

USTRUCT()
struct MESHBLEND_API FMeshBlendLevelProcessor
{
	GENERATED_BODY()

	static void Transform(ULevel* Level, UMeshBlendProcessor* Processor, bool bAddPackedTag);
};
