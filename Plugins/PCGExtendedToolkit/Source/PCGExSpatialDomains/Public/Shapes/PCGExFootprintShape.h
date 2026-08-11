// Copyright 2026 Timothé Lapetite and contributors
// Released under the MIT license https://opensource.org/license/MIT/

#pragma once

#include "CoreMinimal.h"
#include "Math/OBB/PCGExOBB.h"

#include "PCGExFootprintShape.generated.h"

/**
 * Extruded-prism polygon entry. Outline lives in projection-frame XY; the
 * Z band is along the frame's normal. World placement = WorldOrigin
 * (translation) + ProjectionQuat (world->frame). To test a world point P:
 *   LocalP = ProjectionQuat.UnrotateVector(P - WorldOrigin); 2D test on Outline; Z vs band.
 *
 * Pure data -- UPROPERTY-less inner fields keep the struct trivially copyable
 * at the CPU level. Stored inside FPCGExFootprintShape_Polygon at runtime;
 * never serialized through reflection (the placed-modules tracker is rebuilt
 * per growth run).
 */
USTRUCT()
struct PCGEXSPATIALDOMAINS_API FPCGExSpatialPolygonEntry
{
	GENERATED_BODY()

	/** 2D outline in projection-frame XY. Concave allowed; winding-agnostic. */
	TArray<FVector2D> Outline;

	FVector WorldOrigin = FVector::ZeroVector;
	FQuat ProjectionQuat = FQuat::Identity;

	float ZMin = 0.0f;
	float ZMax = 0.0f;

	/** Placement-instance identity. Reserved INDEX_NONE = skip-by-owner sentinel. */
	int32 OwnerIndex = INDEX_NONE;

	/** Cached at append time for the cheap-reject pre-filter tier. */
	FBox WorldAABB = FBox(ForceInit);

	FORCEINLINE bool IsValid() const
	{
		return Outline.Num() >= 3 && ZMax > ZMin;
	}
};

/**
 * Polymorphic world-space shape descriptor. Carried by reference at the
 * Domain.Append / Domain.Overlaps boundary; copied into TInstancedStruct
 * storage when the broadphase domain accepts it.
 *
 * The base is abstract: subclasses MUST override GetScriptStruct() (returns
 * their StaticStruct, used as the type-keyed registry lookup key) and
 * GetWorldAABB() (broadphase pre-cull AABB, always implementable for any shape).
 *
 * Adding a new shape kind is a pure addition: declare a USTRUCT subclass,
 * implement the two virtuals, register pair tests via
 * PCGExSpatial::NarrowPhase::Register from the shape's owning module's
 * StartupModule. Existing shapes / domains / placement code never change.
 */
USTRUCT()
struct PCGEXSPATIALDOMAINS_API FPCGExFootprintShape
{
	GENERATED_BODY()

	// Out-of-line virtual destructor anchors the vtable in the cpp. UE pattern
	// for _API-marked polymorphic USTRUCTs -- inline `= default` risks no-emit
	// when consuming modules need to reference the destructor symbol (LNK2019).
	virtual ~FPCGExFootprintShape();

	/**
	 * Return this instance's reflection identity. Subclasses override with
	 * `return StaticStruct();`. Used by the narrow-phase registry to resolve
	 * pair tests.
	 */
	virtual UScriptStruct* GetScriptStruct() const
	{
		return nullptr;
	}

	/**
	 * World-space AABB. Must be implementable for any shape -- the broadphase
	 * indexes entries by AABB and never inspects shape-specific fields.
	 */
	virtual FBox GetWorldAABB() const
	{
		return FBox(ForceInit);
	}
};

/** Oriented-box shape -- the default contribution kind for cage modules. */
USTRUCT()
struct PCGEXSPATIALDOMAINS_API FPCGExFootprintShape_OBB : public FPCGExFootprintShape
{
	GENERATED_BODY()

	PCGExMath::OBB::FOBB Bounds;

	// Out-of-line ctors/dtor: see base-class comment for rationale.
	FPCGExFootprintShape_OBB();
	explicit FPCGExFootprintShape_OBB(const PCGExMath::OBB::FOBB& InBounds);
	virtual ~FPCGExFootprintShape_OBB() override;

	virtual UScriptStruct* GetScriptStruct() const override
	{
		return StaticStruct();
	}

	virtual FBox GetWorldAABB() const override;
};

/** Extruded-prism polygon shape -- concave allowed, projection-frame aware. */
USTRUCT()
struct PCGEXSPATIALDOMAINS_API FPCGExFootprintShape_Polygon : public FPCGExFootprintShape
{
	GENERATED_BODY()

	FPCGExSpatialPolygonEntry Entry;

	FPCGExFootprintShape_Polygon();
	explicit FPCGExFootprintShape_Polygon(FPCGExSpatialPolygonEntry InEntry);
	virtual ~FPCGExFootprintShape_Polygon() override;

	virtual UScriptStruct* GetScriptStruct() const override
	{
		return StaticStruct();
	}

	virtual FBox GetWorldAABB() const override
	{
		return Entry.WorldAABB;
	}
};
