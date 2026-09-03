// Copyright 2026 Timothé Lapetite and contributors
// Released under the MIT license https://opensource.org/license/MIT/

#pragma once

#include "CoreMinimal.h"
#include "Elements/PCGDataFromActor.h"
#include "Fitting/PCGExFitting.h"
#include "Filters/Points/PCGExPolyPathFilterFactory.h" // EPCGExSplineSamplingIncludeMode
#include "Details/PCGExFilterDetails.h"                 // EPCGExTagsToDataAction

#include "PCGExGetPathData.generated.h"

/**
 * Get Path Data
 *
 * Engine-style getter -- inherits UPCGDataFromActorSettings (NOT UPCGExSettings), so it runs on the
 * game thread and can read spline components directly off the selected actors, before they become PCG
 * data. Handles both USplineComponent and ULandscapeSplinesComponent via the shared UPCGPolyLineData
 * interface. Each spline is emitted as a PCGEx path (point data, closed-loop marked) and/or as the
 * source spline data, on separate pins. Convertible features are geometry-derived (transform, tangents,
 * length, alpha); point type is regular-spline-only (landscape splines have no CIM interp modes). In
 * exchange, every output is stamped with the source actor reference (@Data), which GetSplineData loses.
 *
 * Replaces the GetSplineData -> SplineToPath flow for the common "spline on an actor -> path/spline that
 * remembers its actor" case (e.g. feeding Get Properties Data).
 */
UCLASS(MinimalAPI, BlueprintType, ClassGroup = (Procedural), Category = "PCGEx|Path",
	meta = (Keywords = "pcgex spline path actor reference getter", PCGExNodeLibraryDoc = "paths/generate/get-path-data"))
class UPCGExGetPathDataSettings : public UPCGDataFromActorSettings
{
	GENERATED_BODY()

public:
	//~Begin UPCGSettings interface
#if WITH_EDITOR
	virtual FName GetDefaultNodeName() const override { return FName(TEXT("GetPathData")); }
	virtual FText GetDefaultNodeTitle() const override { return NSLOCTEXT("PCGExGetPathData", "NodeTitle", "PCGEx | Get Path Data"); }
	virtual FText GetNodeTooltipText() const override;
#endif

	// Fixed output pin types (Point + PolyLine), so opt out of the base's actor-data-driven dynamic typing.
	virtual bool HasDynamicPins() const override { return false; }

	// Output pins gray out (rather than vanish) when their toggle is off -- never drops downstream wires.
	virtual bool OutputPinsCanBeDeactivated() const override { return true; }
	virtual bool IsPinStaticallyActive(const FName& PinLabel) const override;
	virtual bool IsPinUsedByNodeExecution(const UPCGPin* InPin) const override;

protected:
	virtual TArray<FPCGPinProperties> OutputPinProperties() const override;
	virtual FPCGElementPtr CreateElement() const override;
	//~End UPCGSettings

	//~Begin UPCGDataFromActorSettings interface
public:
	virtual EPCGDataType GetDataFilter() const override { return EPCGDataType::PolyLine; }

protected:
#if WITH_EDITOR
	virtual bool DisplayModeSettings() const override { return false; }
#endif
	//~End UPCGDataFromActorSettings

public:
	/** Output a converted point path per spline (on the Paths pin). */
	UPROPERTY(BlueprintReadWrite, EditAnywhere, Category = "Settings|Output", meta = (PCG_NotOverridable))
	bool bOutputPaths = true;

	/** Output the source spline data per spline on the Splines pin -- "GetSplineData that remembers its
	 *  actor" when Write Actor Reference is enabled. Built from the same component, so nearly free. */
	UPROPERTY(BlueprintReadWrite, EditAnywhere, Category = "Settings|Output", meta = (PCG_NotOverridable))
	bool bOutputSplines = false;

	/** How point transforms inherit from the source spline. Location is always taken. */
	UPROPERTY(BlueprintReadWrite, EditAnywhere, Category = "Settings|Path", meta = (PCG_Overridable))
	FPCGExLeanTransformDetails TransformDetails;

	/** Which splines to include based on their open/closed state. */
	UPROPERTY(BlueprintReadWrite, EditAnywhere, Category = "Settings|Path", meta = (PCG_Overridable))
	EPCGExSplineSamplingIncludeMode SampleInputs = EPCGExSplineSamplingIncludeMode::All;

	/** Write the spline arrive tangent to an attribute. */
	UPROPERTY(BlueprintReadWrite, EditAnywhere, Category = "Settings|Path", meta = (PCG_Overridable, InlineEditConditionToggle))
	bool bWriteArriveTangent = true;

	/** Name of the 'FVector' attribute to write the arrive tangent to. */
	UPROPERTY(BlueprintReadWrite, EditAnywhere, Category = "Settings|Path", meta = (DisplayName = "Arrive Tangent", PCG_Overridable, EditCondition = "bWriteArriveTangent"))
	FName ArriveTangentAttributeName = FName("ArriveTangent");

	/** Write the spline leave tangent to an attribute. */
	UPROPERTY(BlueprintReadWrite, EditAnywhere, Category = "Settings|Path", meta = (PCG_Overridable, InlineEditConditionToggle))
	bool bWriteLeaveTangent = true;

	/** Name of the 'FVector' attribute to write the leave tangent to. */
	UPROPERTY(BlueprintReadWrite, EditAnywhere, Category = "Settings|Path", meta = (DisplayName = "Leave Tangent", PCG_Overridable, EditCondition = "bWriteLeaveTangent"))
	FName LeaveTangentAttributeName = FName("LeaveTangent");

	/** Write the cumulative spline length at each point to an attribute. */
	UPROPERTY(BlueprintReadWrite, EditAnywhere, Category = "Settings|Path", meta = (PCG_Overridable, InlineEditConditionToggle))
	bool bWriteLengthAtPoint = false;

	/** Name of the 'double' attribute to write the length at point to. */
	UPROPERTY(BlueprintReadWrite, EditAnywhere, Category = "Settings|Path", meta = (DisplayName = "Length at Point", PCG_Overridable, EditCondition = "bWriteLengthAtPoint"))
	FName LengthAtPointAttributeName = FName("LengthAtPoint");

	/** Write the normalized position along the spline (0-1) to an attribute. */
	UPROPERTY(BlueprintReadWrite, EditAnywhere, Category = "Settings|Path", meta = (PCG_Overridable, InlineEditConditionToggle))
	bool bWriteAlpha = false;

	/** Name of the 'double' attribute to write the alpha to. */
	UPROPERTY(BlueprintReadWrite, EditAnywhere, Category = "Settings|Path", meta = (DisplayName = "Alpha", PCG_Overridable, EditCondition = "bWriteAlpha"))
	FName AlphaAttributeName = FName("Alpha");

	/** Write the original spline point type (Linear, Curve, etc.) to an attribute. */
	UPROPERTY(BlueprintReadWrite, EditAnywhere, Category = "Settings|Path", meta = (PCG_Overridable, InlineEditConditionToggle))
	bool bWritePointType = false;

	/** Name of the 'int32' attribute to write the point type to. */
	UPROPERTY(BlueprintReadWrite, EditAnywhere, Category = "Settings|Path", meta = (DisplayName = "Point Type", PCG_Overridable, EditCondition = "bWritePointType"))
	FName PointTypeAttributeName = FName("PointType");

	/** Stamp each output path with the source actor reference, written to the @Data domain. */
	UPROPERTY(BlueprintReadWrite, EditAnywhere, Category = "Settings|Output", meta = (PCG_Overridable, InlineEditConditionToggle))
	bool bWriteActorReference = true;

	/** Name of the 'FSoftObjectPath' @Data attribute to write the actor reference to. */
	UPROPERTY(BlueprintReadWrite, EditAnywhere, Category = "Settings|Output", meta = (DisplayName = "Actor Reference", PCG_Overridable, EditCondition = "bWriteActorReference"))
	FName ActorReferenceAttributeName = FName("ActorReference");

	/** Forward the source actor & spline-component tags onto the output data. */
	UPROPERTY(BlueprintReadWrite, EditAnywhere, Category = "Settings|Tagging")
	bool bForwardSourceTags = true;

	/** How key:value tags (from the forwarded actor/component tags) are converted to attributes. */
	UPROPERTY(BlueprintReadWrite, EditAnywhere, Category = "Settings|Tagging", meta = (PCG_NotOverridable))
	EPCGExTagsToDataAction TagsToData = EPCGExTagsToDataAction::ToData;
};

class FPCGExGetPathDataElement : public FPCGDataFromActorElement
{
protected:
	// Drives both phases. NewObject_AnyThread + metadata setup happen single-threaded here; only the
	// per-point value fill is parallelized (NewObject_AnyThread is not safe across concurrent threads).
	virtual void ProcessActors(FPCGContext* Context, const UPCGDataFromActorSettings* Settings, const TArray<AActor*>& FoundActors) const override;
};
