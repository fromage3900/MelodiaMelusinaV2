// Copyright 2024 Tore Lervik. All Rights Reserved.

#include "MeshBlendActivator.h"

AMeshBlendActivator::AMeshBlendActivator(const FObjectInitializer& ObjectInitializer) : Super(ObjectInitializer)
{
#if WITH_EDITOR
	bIsSpatiallyLoaded = false;
#endif
}
