// Copyright 2026 Timothé Lapetite and contributors
// Released under the MIT license https://opensource.org/license/MIT/

#include "Shapes/PCGExFootprintShape.h"

// =============================================================================
// FPCGExFootprintShape (base)
// =============================================================================

// Out-of-line destructor: forces a single export of the vtable + dtor symbol
// from this module. Without this, consuming modules that construct/destroy
// subclasses inline get LNK2019 unresolved __imp_ symbols.
FPCGExFootprintShape::~FPCGExFootprintShape() = default;

// =============================================================================
// FPCGExFootprintShape_OBB
// =============================================================================

FPCGExFootprintShape_OBB::FPCGExFootprintShape_OBB() = default;

FPCGExFootprintShape_OBB::FPCGExFootprintShape_OBB(const PCGExMath::OBB::FOBB& InBounds)
	: Bounds(InBounds)
{
}

FPCGExFootprintShape_OBB::~FPCGExFootprintShape_OBB() = default;

FBox FPCGExFootprintShape_OBB::GetWorldAABB() const
{
	// Walk the eight corners and accumulate -- accounts for the orientation
	// component cleanly without a separate fast path. Single-element OBBs
	// hit this once per Append, not in the hot query loop.
	FBox AABB(ForceInit);
	Bounds.ForEachCorner([&AABB](const FVector& World)
	{
		AABB += World;
	});
	return AABB;
}

// =============================================================================
// FPCGExFootprintShape_Polygon
// =============================================================================

FPCGExFootprintShape_Polygon::FPCGExFootprintShape_Polygon() = default;

FPCGExFootprintShape_Polygon::FPCGExFootprintShape_Polygon(FPCGExSpatialPolygonEntry InEntry)
	: Entry(MoveTemp(InEntry))
{
}

FPCGExFootprintShape_Polygon::~FPCGExFootprintShape_Polygon() = default;
