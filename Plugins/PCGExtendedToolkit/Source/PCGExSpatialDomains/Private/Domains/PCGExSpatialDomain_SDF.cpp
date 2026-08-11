// Copyright 2026 Timothé Lapetite and contributors
// Released under the MIT license https://opensource.org/license/MIT/

#include "Domains/PCGExSpatialDomain_SDF.h"

float FPCGExSpatialDomain_SDF::QueryPoint(const FVector& Point) const
{
	checkf(false, TEXT("FPCGExSpatialDomain_SDF is a stub; QueryPoint not implemented."));
	return TNumericLimits<float>::Max();
}

FBox FPCGExSpatialDomain_SDF::GetBounds() const
{
	checkf(false, TEXT("FPCGExSpatialDomain_SDF is a stub; GetBounds not implemented."));
	return FBox(ForceInit);
}

bool FPCGExSpatialDomain_SDF::IsValid() const
{
	// returns false (not check(false)) so IsValid-guarded call sites don't crash on stub instances
	return false;
}

int32 FPCGExSpatialDomain_SDF::Append(const FPCGExFootprintShape& Shape, int32 OwnerIndex, uint32 ChannelMask)
{
	checkf(false, TEXT("FPCGExSpatialDomain_SDF is immutable; Append() is not supported."));
	return INDEX_NONE;
}
