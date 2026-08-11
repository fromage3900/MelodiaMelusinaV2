// Copyright 2026 Timothé Lapetite and contributors
// Released under the MIT license https://opensource.org/license/MIT/

#pragma once

#include "CoreMinimal.h"
#include "Domains/PCGExSpatialDomain.h"

/**
 * Static spatial domain backed by a voxelized signed-distance field.
 *
 * STATUS: STUB. All virtuals fail-loud (check(false)) until a concrete
 * authoring/storage path is committed. The class exists so other code
 * (future bake pipelines, type registry) can reference the type by name
 * without waiting on the implementation.
 *
 * Activation criteria (any of):
 *   - PCG-graph plumbing lands a node that produces voxel SDF data
 *     (e.g. baked from UStaticMesh collision).
 *   - A direct authoring path emits SDF chunks for level-import use cases
 *     that the Polygon2D / OBB types don't cover (carved holes, organic
 *     shapes, mesh-derived volumes).
 *
 * Sketch of intended representation:
 *   - Dense voxel grid: TArray<float> Voxels indexed (x + y*W + z*W*H).
 *     Cell size + grid origin/extents define world placement.
 *   - QueryPoint: trilinear sample between 8 nearest cells.
 *   - QueryOBB: base default (center + 8 corners) is fine; the SDF nature
 *     means corners give a usable lower bound on signed distance.
 *   - GetBounds: grid origin + (cell_size * dimensions).
 *
 * Memory budget warning: dense storage scales cubically. 1m^3 at 5cm =
 * ~32 KB; 10m^3 at 5cm = ~32 MB. Either (a) document a "use sparingly"
 * guideline OR (b) introduce a sparse octree-backed variant later.
 *
 * Mutability: false. Append() must check(false) per the static-subclass
 * policy in FPCGExSpatialDomain::Append docs.
 */
class PCGEXSPATIALDOMAINS_API FPCGExSpatialDomain_SDF : public FPCGExSpatialDomain
{
public:
	FPCGExSpatialDomain_SDF() = default;
	virtual ~FPCGExSpatialDomain_SDF() override = default;

	// ========== FPCGExSpatialDomain (query) ==========

	virtual float QueryPoint(const FVector& Point) const override;
	virtual FBox GetBounds() const override;
	virtual bool IsValid() const override;

	// ========== FPCGExSpatialDomain (mutation) ==========

	virtual int32 Append(const FPCGExFootprintShape& Shape, int32 OwnerIndex, uint32 ChannelMask = 0) override;
};
