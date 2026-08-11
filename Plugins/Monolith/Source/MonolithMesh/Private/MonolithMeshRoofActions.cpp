#if WITH_GEOMETRYSCRIPT

#include "MonolithMeshRoofActions.h"
#include "MonolithMeshProceduralActions.h"
#include "MonolithMeshHandlePool.h"
#include "MonolithMeshUtils.h"
#include "MonolithToolRegistry.h"
#include "MonolithParamSchema.h"
#include "MonolithJsonUtils.h"
#include "MonolithAssetUtils.h"

#include "UDynamicMesh.h"
#include "DynamicMesh/DynamicMesh3.h"

#include "GeometryScript/MeshPrimitiveFunctions.h"
#include "GeometryScript/MeshBasicEditFunctions.h"
#include "GeometryScript/MeshNormalsFunctions.h"
#include "GeometryScript/MeshTransformFunctions.h"
#include "GeometryScript/MeshUVFunctions.h"

#include "Engine/StaticMesh.h"
#include "Engine/StaticMeshActor.h"
#include "Engine/World.h"
#include "Editor.h"

#include "Dom/JsonObject.h"
#include "Dom/JsonValue.h"

using namespace UE::Geometry;

static const FString GS_ERROR_ROOF = TEXT("Enable the GeometryScripting plugin in your .uproject to use roof generation.");

UMonolithMeshHandlePool* FMonolithMeshRoofActions::Pool = nullptr;

void FMonolithMeshRoofActions::SetHandlePool(UMonolithMeshHandlePool* InPool)
{
	Pool = InPool;
}

// ============================================================================
// Registration
// ============================================================================

void FMonolithMeshRoofActions::RegisterActions(FMonolithToolRegistry& Registry)
{
	Registry.RegisterAction(TEXT("mesh"), TEXT("generate_roof"),
		TEXT("Generate roof geometry from a building footprint polygon. "
			"Types: gable, hip, flat (parapet), shed, gambrel. "
			"Consumes footprint_polygon from the Building Descriptor (SP1). "
			"MaterialID 0 = roof surface, 1 = soffit, 2 = fascia/parapet."),
		FMonolithActionHandler::CreateStatic(&FMonolithMeshRoofActions::GenerateRoof),
		FParamSchemaBuilder()
			.Required(TEXT("footprint_polygon"), TEXT("array"), TEXT("Array of [x,y] points defining the building outline (CCW winding, cm)"))
			.RequiredAssetPath(TEXT("save_path"), TEXT("Asset path for the roof mesh (e.g. /Game/CityBlock/Mesh/SM_Roof_01)"))
			.Optional(TEXT("roof_type"), TEXT("string"), TEXT("Roof type: gable, hip, flat, shed, gambrel"), TEXT("gable"))
			.Optional(TEXT("pitch_degrees"), TEXT("number"), TEXT("Roof pitch angle in degrees"), TEXT("30"))
			.Optional(TEXT("overhang"), TEXT("number"), TEXT("Overhang distance in cm"), TEXT("30"))
			.Optional(TEXT("height_offset"), TEXT("number"), TEXT("Z offset where roof sits (top of building walls)"), TEXT("0"))
			.Optional(TEXT("parapet_height"), TEXT("number"), TEXT("For flat roofs, parapet wall height in cm"), TEXT("60"))
			.Optional(TEXT("parapet_thickness"), TEXT("number"), TEXT("For flat roofs, parapet wall thickness in cm"), TEXT("10"))
			.Optional(TEXT("ridge_offset"), TEXT("number"), TEXT("For shed roofs, ridge offset from center"), TEXT("0"))
			.Optional(TEXT("material_roof"), TEXT("string"), TEXT("Material asset path for roof surface (slot 0)"))
			.Optional(TEXT("material_soffit"), TEXT("string"), TEXT("Material asset path for soffit/underside (slot 1)"))
			.Optional(TEXT("material_fascia"), TEXT("string"), TEXT("Material asset path for fascia trim (slot 2)"))
			.Optional(TEXT("location"), TEXT("array"), TEXT("World location [x,y,z]"))
			.Optional(TEXT("label"), TEXT("string"), TEXT("Actor label"))
			.OptionalAssetPath(TEXT("folder"), TEXT("Outliner folder path"))
			.Optional(TEXT("overwrite"), TEXT("boolean"), TEXT("Allow overwriting existing asset"), TEXT("false"))
			.Optional(TEXT("building_id"), TEXT("string"), TEXT("Building ID for tagging the actor"))
			.Build());
}

// ============================================================================
// Helpers
// ============================================================================

bool FMonolithMeshRoofActions::ParseFootprint(const TSharedPtr<FJsonObject>& Params, TArray<FVector2D>& OutPoly, FString& OutError)
{
	const TArray<TSharedPtr<FJsonValue>>* FootArr = nullptr;
	if (!Params->TryGetArrayField(TEXT("footprint_polygon"), FootArr) || !FootArr || FootArr->Num() < 3)
	{
		OutError = TEXT("footprint_polygon requires at least 3 [x,y] points");
		return false;
	}

	for (int32 i = 0; i < FootArr->Num(); ++i)
	{
		const TArray<TSharedPtr<FJsonValue>>* Pair = nullptr;
		if (!(*FootArr)[i]->TryGetArray(Pair) || !Pair || Pair->Num() < 2)
		{
			OutError = FString::Printf(TEXT("footprint_polygon[%d] is not a valid [x,y] pair"), i);
			return false;
		}
		OutPoly.Add(FVector2D((*Pair)[0]->AsNumber(), (*Pair)[1]->AsNumber()));
	}

	return true;
}

void FMonolithMeshRoofActions::ComputeFootprintOBB(const TArray<FVector2D>& Polygon,
	FVector2D& OutCenter, float& OutHalfW, float& OutHalfD,
	FVector2D& OutLongAxis, FVector2D& OutShortAxis)
{
	// Compute centroid
	OutCenter = FVector2D::ZeroVector;
	for (const FVector2D& V : Polygon)
	{
		OutCenter += V;
	}
	OutCenter /= static_cast<float>(Polygon.Num());

	// Compute AABB of the polygon to determine the long axis
	FVector2D Min(TNumericLimits<float>::Max(), TNumericLimits<float>::Max());
	FVector2D Max(TNumericLimits<float>::Lowest(), TNumericLimits<float>::Lowest());
	for (const FVector2D& V : Polygon)
	{
		Min.X = FMath::Min(Min.X, V.X);
		Min.Y = FMath::Min(Min.Y, V.Y);
		Max.X = FMath::Max(Max.X, V.X);
		Max.Y = FMath::Max(Max.Y, V.Y);
	}

	float ExtentX = (Max.X - Min.X) * 0.5f;
	float ExtentY = (Max.Y - Min.Y) * 0.5f;

	// Long axis is the axis with the larger extent
	if (ExtentX >= ExtentY)
	{
		OutLongAxis = FVector2D(1.0f, 0.0f);
		OutShortAxis = FVector2D(0.0f, 1.0f);
		OutHalfW = ExtentX; // half-width along long axis
		OutHalfD = ExtentY; // half-depth along short axis
	}
	else
	{
		OutLongAxis = FVector2D(0.0f, 1.0f);
		OutShortAxis = FVector2D(1.0f, 0.0f);
		OutHalfW = ExtentY;
		OutHalfD = ExtentX;
	}

	// Recenter to AABB center (more reliable than centroid for non-uniform shapes)
	OutCenter = (Min + Max) * 0.5f;
}

TArray<FVector2D> FMonolithMeshRoofActions::ExpandPolygon(const TArray<FVector2D>& Polygon, float Distance)
{
	// Negative inset = outward expansion
	const int32 N = Polygon.Num();
	if (N < 3) return Polygon;

	TArray<FVector2D> Result;
	Result.Reserve(N);

	for (int32 i = 0; i < N; ++i)
	{
		const FVector2D& Prev = Polygon[(i + N - 1) % N];
		const FVector2D& Curr = Polygon[i];
		const FVector2D& Next = Polygon[(i + 1) % N];

		FVector2D E0 = (Curr - Prev).GetSafeNormal();
		FVector2D E1 = (Next - Curr).GetSafeNormal();
		// Outward normals for CCW polygon (negate the inward ones)
		FVector2D N0(E0.Y, -E0.X);
		FVector2D N1(E1.Y, -E1.X);

		FVector2D AvgN = (N0 + N1);
		float Len = AvgN.Size();
		if (Len < KINDA_SMALL_NUMBER)
		{
			Result.Add(Curr + N0 * Distance);
		}
		else
		{
			AvgN /= Len;
			float Dot = FVector2D::DotProduct(N0, AvgN);
			float Scale = (FMath::Abs(Dot) > 0.01f) ? (Distance / Dot) : Distance;
			Scale = FMath::Clamp(Scale, Distance * 0.5f, Distance * 3.0f);
			Result.Add(Curr + AvgN * Scale);
		}
	}

	return Result;
}

// ============================================================================
// Roof Builders
// ============================================================================

bool FMonolithMeshRoofActions::BuildGableRoof(UDynamicMesh* Mesh, const TArray<FVector2D>& FootprintPoly,
	const TArray<FVector2D>& OverhangPoly, float PitchDeg, float HeightOffset,
	float Overhang, FString& OutError)
{
	// Compute footprint OBB for ridge orientation
	FVector2D Center, LongAxis, ShortAxis;
	float HalfW, HalfD;
	ComputeFootprintOBB(FootprintPoly, Center, HalfW, HalfD, LongAxis, ShortAxis);

	// Ridge height from pitch angle and short-axis half-extent (+ overhang)
	float PitchRad = FMath::DegreesToRadians(PitchDeg);
	float RidgeH = (HalfD + Overhang) * FMath::Tan(PitchRad);

	// Triangular cross-section (looking along the ridge / long axis)
	// Profile is in the plane perpendicular to the sweep direction.
	// For AppendSimpleSweptPolygon: Y = right, Z = up relative to sweep direction.
	float HalfBase = HalfD + Overhang;
	TArray<FVector2D> Profile;
	Profile.Add(FVector2D(-HalfBase, 0.0f));  // Left eave
	Profile.Add(FVector2D(0.0f, RidgeH));     // Ridge peak
	Profile.Add(FVector2D(HalfBase, 0.0f));   // Right eave

	// Sweep path along the long axis (with overhang extension at both ends)
	float SweepHalf = HalfW + Overhang;
	FVector PathStart = FVector(
		Center.X + LongAxis.X * (-SweepHalf),
		Center.Y + LongAxis.Y * (-SweepHalf),
		HeightOffset);
	FVector PathEnd = FVector(
		Center.X + LongAxis.X * SweepHalf,
		Center.Y + LongAxis.Y * SweepHalf,
		HeightOffset);

	TArray<FVector> SweepPath;
	SweepPath.Add(PathStart);
	SweepPath.Add(PathEnd);

	// Build the transform to orient the profile perpendicular to the long axis
	// The sweep direction is along LongAxis. Profile Y maps to ShortAxis, Profile Z maps to Up.
	// AppendSimpleSweptPolygon auto-computes the frame from the path direction, so if the long axis
	// is along X, profile Y = right = Y world, Z = up. If long axis is along Y, we need a rotation.
	FTransform SweepXf = FTransform::Identity;

	// Determine rotation: the sweep auto-frames based on the path direction.
	// Path direction = LongAxis(3D). The profile Y axis will be perpendicular to the path in the XY plane.
	// For axis-aligned cases this works out automatically. For arbitrary orientations, the
	// InitialFrame in the GeneralizedCylinderGenerator handles it.

	FGeometryScriptPrimitiveOptions RoofOpts;
	RoofOpts.PolygroupMode = EGeometryScriptPrimitivePolygroupMode::PerFace;
	RoofOpts.MaterialID = 0; // Roof surface

	UGeometryScriptLibrary_MeshPrimitiveFunctions::AppendSimpleSweptPolygon(
		Mesh, RoofOpts, SweepXf,
		Profile, SweepPath,
		/*bLoop=*/false, /*bCapped=*/true,
		/*StartScale=*/1.0f, /*EndScale=*/1.0f,
		/*RotationAngleDeg=*/0.0f, /*MiterLimit=*/1.0f);

	return true;
}

bool FMonolithMeshRoofActions::BuildHipRoof(UDynamicMesh* Mesh, const TArray<FVector2D>& FootprintPoly,
	const TArray<FVector2D>& OverhangPoly, float PitchDeg, float HeightOffset,
	float Overhang, FString& OutError)
{
	FVector2D Center, LongAxis, ShortAxis;
	float HalfW, HalfD;
	ComputeFootprintOBB(FootprintPoly, Center, HalfW, HalfD, LongAxis, ShortAxis);

	float PitchRad = FMath::DegreesToRadians(PitchDeg);
	float RidgeH = (HalfD + Overhang) * FMath::Tan(PitchRad);

	// Ridge length: for a hip roof, the ridge is shortened by the amount the hip slopes eat
	// Ridge shrinks by HalfD on each end (the triangular hip face eats into the ridge)
	float RidgeHalfLen = HalfW - HalfD; // If building is square, ridge collapses to a point (pyramid)
	if (RidgeHalfLen < 0.0f) RidgeHalfLen = 0.0f;

	// Eave corners (with overhang)
	float EaveHW = HalfW + Overhang;
	float EaveHD = HalfD + Overhang;

	// All positions relative to Center, at HeightOffset Z
	auto ToWorld = [&](float AlongLong, float AlongShort, float Z) -> FVector
	{
		return FVector(
			Center.X + LongAxis.X * AlongLong + ShortAxis.X * AlongShort,
			Center.Y + LongAxis.Y * AlongLong + ShortAxis.Y * AlongShort,
			Z);
	};

	// 4 eave corners
	FVector EaveNE = ToWorld( EaveHW,  EaveHD, HeightOffset);
	FVector EaveSE = ToWorld( EaveHW, -EaveHD, HeightOffset);
	FVector EaveSW = ToWorld(-EaveHW, -EaveHD, HeightOffset);
	FVector EaveNW = ToWorld(-EaveHW,  EaveHD, HeightOffset);

	// 2 ridge endpoints (or single apex if square)
	FVector RidgeE = ToWorld( RidgeHalfLen, 0.0f, HeightOffset + RidgeH);
	FVector RidgeW = ToWorld(-RidgeHalfLen, 0.0f, HeightOffset + RidgeH);

	FGeometryScriptPrimitiveOptions RoofOpts;
	RoofOpts.PolygroupMode = EGeometryScriptPrimitivePolygroupMode::PerFace;
	RoofOpts.MaterialID = 0; // Roof surface

	if (RidgeHalfLen > KINDA_SMALL_NUMBER)
	{
		// Rectangular building: 2 trapezoidal side faces + 2 triangular hip faces

		// North face (trapezoidal): EaveNW -> EaveNE -> RidgeE -> RidgeW (CCW from outside/above-north)
		{
			TArray<FVector> Verts;
			Verts.Add(EaveNW);
			Verts.Add(EaveNE);
			Verts.Add(RidgeE);
			Verts.Add(RidgeW);
			UGeometryScriptLibrary_MeshPrimitiveFunctions::AppendTriangulatedPolygon3D(
				Mesh, RoofOpts, FTransform::Identity, Verts);
		}

		// South face (trapezoidal): EaveSE -> EaveSW -> RidgeW -> RidgeE (CCW from outside/below-south)
		{
			TArray<FVector> Verts;
			Verts.Add(EaveSE);
			Verts.Add(EaveSW);
			Verts.Add(RidgeW);
			Verts.Add(RidgeE);
			UGeometryScriptLibrary_MeshPrimitiveFunctions::AppendTriangulatedPolygon3D(
				Mesh, RoofOpts, FTransform::Identity, Verts);
		}

		// East hip face (triangle): EaveNE -> EaveSE -> RidgeE (CCW from outside/east)
		{
			TArray<FVector> Verts;
			Verts.Add(EaveNE);
			Verts.Add(EaveSE);
			Verts.Add(RidgeE);
			UGeometryScriptLibrary_MeshPrimitiveFunctions::AppendTriangulatedPolygon3D(
				Mesh, RoofOpts, FTransform::Identity, Verts);
		}

		// West hip face (triangle): EaveSW -> EaveNW -> RidgeW (CCW from outside/west)
		{
			TArray<FVector> Verts;
			Verts.Add(EaveSW);
			Verts.Add(EaveNW);
			Verts.Add(RidgeW);
			UGeometryScriptLibrary_MeshPrimitiveFunctions::AppendTriangulatedPolygon3D(
				Mesh, RoofOpts, FTransform::Identity, Verts);
		}
	}
	else
	{
		// Square building: pyramid (4 triangular faces meeting at apex)
		FVector Apex = ToWorld(0.0f, 0.0f, HeightOffset + RidgeH);

		// North
		{
			TArray<FVector> Verts;
			Verts.Add(EaveNW); Verts.Add(EaveNE); Verts.Add(Apex);
			UGeometryScriptLibrary_MeshPrimitiveFunctions::AppendTriangulatedPolygon3D(
				Mesh, RoofOpts, FTransform::Identity, Verts);
		}
		// East
		{
			TArray<FVector> Verts;
			Verts.Add(EaveNE); Verts.Add(EaveSE); Verts.Add(Apex);
			UGeometryScriptLibrary_MeshPrimitiveFunctions::AppendTriangulatedPolygon3D(
				Mesh, RoofOpts, FTransform::Identity, Verts);
		}
		// South
		{
			TArray<FVector> Verts;
			Verts.Add(EaveSE); Verts.Add(EaveSW); Verts.Add(Apex);
			UGeometryScriptLibrary_MeshPrimitiveFunctions::AppendTriangulatedPolygon3D(
				Mesh, RoofOpts, FTransform::Identity, Verts);
		}
		// West
		{
			TArray<FVector> Verts;
			Verts.Add(EaveSW); Verts.Add(EaveNW); Verts.Add(Apex);
			UGeometryScriptLibrary_MeshPrimitiveFunctions::AppendTriangulatedPolygon3D(
				Mesh, RoofOpts, FTransform::Identity, Verts);
		}
	}

	// Soffit underside — flat polygon connecting eave corners at HeightOffset
	// Winding reversed (CW from above = CCW from below) so normal faces down
	{
		FGeometryScriptPrimitiveOptions SoffitOpts;
		SoffitOpts.PolygroupMode = EGeometryScriptPrimitivePolygroupMode::PerFace;
		SoffitOpts.MaterialID = 1; // Soffit

		TArray<FVector> Verts;
		Verts.Add(EaveSW);
		Verts.Add(EaveSE);
		Verts.Add(EaveNE);
		Verts.Add(EaveNW);
		UGeometryScriptLibrary_MeshPrimitiveFunctions::AppendTriangulatedPolygon3D(
			Mesh, SoffitOpts, FTransform::Identity, Verts);
	}

	return true;
}

bool FMonolithMeshRoofActions::BuildFlatRoof(UDynamicMesh* Mesh, const TArray<FVector2D>& FootprintPoly,
	float HeightOffset, float ParapetHeight, float ParapetThickness, FString& OutError)
{
	// Flat slab at roof height
	FGeometryScriptPrimitiveOptions SlabOpts;
	SlabOpts.PolygroupMode = EGeometryScriptPrimitivePolygroupMode::PerFace;
	SlabOpts.MaterialID = 0; // Roof surface

	float SlabThickness = 5.0f; // Thin slab
	FTransform SlabXf(FRotator::ZeroRotator, FVector(0, 0, HeightOffset), FVector::OneVector);
	UGeometryScriptLibrary_MeshPrimitiveFunctions::AppendSimpleExtrudePolygon(
		Mesh, SlabOpts, SlabXf, FootprintPoly, SlabThickness,
		0, true, EGeometryScriptPrimitiveOriginMode::Base);

	// Parapet walls: sweep a rectangular profile around the footprint perimeter
	if (ParapetHeight > 0.0f && ParapetThickness > 0.0f)
	{
		FGeometryScriptPrimitiveOptions ParapetOpts;
		ParapetOpts.PolygroupMode = EGeometryScriptPrimitivePolygroupMode::PerFace;
		ParapetOpts.MaterialID = 2; // Fascia/parapet material slot

		// Rectangular profile for parapet wall (thickness x height)
		float HalfT = ParapetThickness * 0.5f;
		TArray<FVector2D> ParapetProfile;
		ParapetProfile.Add(FVector2D(-HalfT, 0.0f));
		ParapetProfile.Add(FVector2D(-HalfT, ParapetHeight));
		ParapetProfile.Add(FVector2D( HalfT, ParapetHeight));
		ParapetProfile.Add(FVector2D( HalfT, 0.0f));

		// Sweep path follows the footprint polygon at the top of the slab
		float ParapetZ = HeightOffset + SlabThickness;
		TArray<FVector> SweepPath;
		SweepPath.Reserve(FootprintPoly.Num());
		for (const FVector2D& V : FootprintPoly)
		{
			SweepPath.Add(FVector(V.X, V.Y, ParapetZ));
		}

		UGeometryScriptLibrary_MeshPrimitiveFunctions::AppendSimpleSweptPolygon(
			Mesh, ParapetOpts, FTransform::Identity,
			ParapetProfile, SweepPath,
			/*bLoop=*/true, /*bCapped=*/false,
			/*StartScale=*/1.0f, /*EndScale=*/1.0f,
			/*RotationAngleDeg=*/0.0f, /*MiterLimit=*/1.5f);
	}

	return true;
}

bool FMonolithMeshRoofActions::BuildShedRoof(UDynamicMesh* Mesh, const TArray<FVector2D>& FootprintPoly,
	const TArray<FVector2D>& OverhangPoly, float PitchDeg, float HeightOffset,
	float Overhang, float RidgeOffset, FString& OutError)
{
	FVector2D Center, LongAxis, ShortAxis;
	float HalfW, HalfD;
	ComputeFootprintOBB(FootprintPoly, Center, HalfW, HalfD, LongAxis, ShortAxis);

	float PitchRad = FMath::DegreesToRadians(PitchDeg);
	// Shed roof: slope runs along the short axis. High side at +ShortAxis, low side at -ShortAxis.
	float TotalRise = (HalfD * 2.0f + Overhang * 2.0f) * FMath::Tan(PitchRad);

	float EaveHW = HalfW + Overhang;
	float EaveHD = HalfD + Overhang;

	auto ToWorld = [&](float AlongLong, float AlongShort, float Z) -> FVector
	{
		return FVector(
			Center.X + LongAxis.X * AlongLong + ShortAxis.X * AlongShort,
			Center.Y + LongAxis.Y * AlongLong + ShortAxis.Y * AlongShort,
			Z);
	};

	// 4 corners: high side (+short) and low side (-short)
	float HighZ = HeightOffset + TotalRise;
	float LowZ = HeightOffset;

	FVector HighNE = ToWorld( EaveHW,  EaveHD, HighZ);
	FVector HighNW = ToWorld(-EaveHW,  EaveHD, HighZ);
	FVector LowSE  = ToWorld( EaveHW, -EaveHD, LowZ);
	FVector LowSW  = ToWorld(-EaveHW, -EaveHD, LowZ);

	// Top slope face (CCW from above/outside)
	FGeometryScriptPrimitiveOptions RoofOpts;
	RoofOpts.PolygroupMode = EGeometryScriptPrimitivePolygroupMode::PerFace;
	RoofOpts.MaterialID = 0;

	{
		TArray<FVector> Verts;
		Verts.Add(LowSW);
		Verts.Add(LowSE);
		Verts.Add(HighNE);
		Verts.Add(HighNW);
		UGeometryScriptLibrary_MeshPrimitiveFunctions::AppendTriangulatedPolygon3D(
			Mesh, RoofOpts, FTransform::Identity, Verts);
	}

	// Soffit (underside of the slope)
	{
		FGeometryScriptPrimitiveOptions SoffitOpts;
		SoffitOpts.PolygroupMode = EGeometryScriptPrimitivePolygroupMode::PerFace;
		SoffitOpts.MaterialID = 1;

		TArray<FVector> Verts;
		Verts.Add(HighNW);
		Verts.Add(HighNE);
		Verts.Add(LowSE);
		Verts.Add(LowSW);
		UGeometryScriptLibrary_MeshPrimitiveFunctions::AppendTriangulatedPolygon3D(
			Mesh, SoffitOpts, FTransform::Identity, Verts);
	}

	return true;
}

bool FMonolithMeshRoofActions::BuildGambrelRoof(UDynamicMesh* Mesh, const TArray<FVector2D>& FootprintPoly,
	const TArray<FVector2D>& OverhangPoly, float PitchDeg, float HeightOffset,
	float Overhang, FString& OutError)
{
	FVector2D Center, LongAxis, ShortAxis;
	float HalfW, HalfD;
	ComputeFootprintOBB(FootprintPoly, Center, HalfW, HalfD, LongAxis, ShortAxis);

	// Gambrel: two slopes per side.
	// Lower slope is steep (60 degrees by default), upper slope uses the user's pitch.
	// The break point is at ~1/3 of the way up from the eave to where a full gable ridge would be.
	float LowerPitchDeg = 60.0f;
	float UpperPitchDeg = PitchDeg; // User's pitch for the upper (shallower) slope

	float LowerPitchRad = FMath::DegreesToRadians(LowerPitchDeg);
	float UpperPitchRad = FMath::DegreesToRadians(UpperPitchDeg);

	float HalfBase = HalfD + Overhang;

	// Break point: the lower slope covers ~40% of the horizontal span from eave to center
	float BreakFraction = 0.4f;
	float BreakHorizDist = HalfBase * BreakFraction; // Horizontal distance from eave to break
	float BreakH = BreakHorizDist * FMath::Tan(LowerPitchRad);

	// Upper slope: from break point inward to the ridge
	float UpperHorizDist = HalfBase - BreakHorizDist; // Horizontal distance from break to center
	float UpperH = UpperHorizDist * FMath::Tan(UpperPitchRad);
	float RidgeH = BreakH + UpperH;

	// Hexagonal cross-section profile (CCW, looking along ridge/long axis)
	// Profile Y = across building (short axis), Profile Z = up
	float BreakY = HalfBase - BreakHorizDist; // Distance from center to break point
	TArray<FVector2D> Profile;
	Profile.Add(FVector2D(-HalfBase, 0.0f));       // Left eave
	Profile.Add(FVector2D(-BreakY, BreakH));        // Left break
	Profile.Add(FVector2D(0.0f, RidgeH));           // Ridge peak
	Profile.Add(FVector2D(BreakY, BreakH));         // Right break
	Profile.Add(FVector2D(HalfBase, 0.0f));         // Right eave

	// Sweep along long axis with overhang
	float SweepHalf = HalfW + Overhang;
	FVector PathStart = FVector(
		Center.X + LongAxis.X * (-SweepHalf),
		Center.Y + LongAxis.Y * (-SweepHalf),
		HeightOffset);
	FVector PathEnd = FVector(
		Center.X + LongAxis.X * SweepHalf,
		Center.Y + LongAxis.Y * SweepHalf,
		HeightOffset);

	TArray<FVector> SweepPath;
	SweepPath.Add(PathStart);
	SweepPath.Add(PathEnd);

	FGeometryScriptPrimitiveOptions RoofOpts;
	RoofOpts.PolygroupMode = EGeometryScriptPrimitivePolygroupMode::PerFace;
	RoofOpts.MaterialID = 0;

	UGeometryScriptLibrary_MeshPrimitiveFunctions::AppendSimpleSweptPolygon(
		Mesh, RoofOpts, FTransform::Identity,
		Profile, SweepPath,
		/*bLoop=*/false, /*bCapped=*/true,
		/*StartScale=*/1.0f, /*EndScale=*/1.0f,
		/*RotationAngleDeg=*/0.0f, /*MiterLimit=*/1.0f);

	return true;
}

// ============================================================================
// Main Action Handler
// ============================================================================

FMonolithActionResult FMonolithMeshRoofActions::GenerateRoof(const TSharedPtr<FJsonObject>& Params)
{
	if (!Pool)
	{
		return FMonolithActionResult::Error(GS_ERROR_ROOF);
	}

	// ---- Parse parameters ----
	TArray<FVector2D> FootprintPoly;
	FString ParseErr;
	if (!ParseFootprint(Params, FootprintPoly, ParseErr))
	{
		return FMonolithActionResult::Error(ParseErr);
	}

	FString SavePath;
	if (!Params->TryGetStringField(TEXT("save_path"), SavePath) || SavePath.IsEmpty())
	{
		return FMonolithActionResult::Error(TEXT("save_path is required"));
	}

	FString RoofType = TEXT("gable");
	Params->TryGetStringField(TEXT("roof_type"), RoofType);
	RoofType = RoofType.ToLower();

	float PitchDeg = Params->HasField(TEXT("pitch_degrees"))
		? static_cast<float>(Params->GetNumberField(TEXT("pitch_degrees"))) : 30.0f;
	float OverhangDist = Params->HasField(TEXT("overhang"))
		? static_cast<float>(Params->GetNumberField(TEXT("overhang"))) : 30.0f;
	float HeightOffset = Params->HasField(TEXT("height_offset"))
		? static_cast<float>(Params->GetNumberField(TEXT("height_offset"))) : 0.0f;
	float ParapetHeight = Params->HasField(TEXT("parapet_height"))
		? static_cast<float>(Params->GetNumberField(TEXT("parapet_height"))) : 60.0f;
	float ParapetThickness = Params->HasField(TEXT("parapet_thickness"))
		? static_cast<float>(Params->GetNumberField(TEXT("parapet_thickness"))) : 10.0f;
	float RidgeOffset = Params->HasField(TEXT("ridge_offset"))
		? static_cast<float>(Params->GetNumberField(TEXT("ridge_offset"))) : 0.0f;
	bool bOverwrite = Params->HasField(TEXT("overwrite")) ? Params->GetBoolField(TEXT("overwrite")) : false;

	// Clamp pitch to sane range
	PitchDeg = FMath::Clamp(PitchDeg, 5.0f, 75.0f);

	// ---- Expand footprint for overhang ----
	TArray<FVector2D> OverhangPoly = (OverhangDist > 0.0f)
		? ExpandPolygon(FootprintPoly, OverhangDist)
		: FootprintPoly;

	// ---- Create dynamic mesh ----
	UDynamicMesh* Mesh = NewObject<UDynamicMesh>(Pool);
	if (!Mesh)
	{
		return FMonolithActionResult::Error(TEXT("Failed to allocate UDynamicMesh"));
	}

	// ---- Build roof geometry based on type ----
	FString BuildErr;
	bool bOK = false;

	if (RoofType == TEXT("gable"))
	{
		bOK = BuildGableRoof(Mesh, FootprintPoly, OverhangPoly, PitchDeg, HeightOffset, OverhangDist, BuildErr);
	}
	else if (RoofType == TEXT("hip"))
	{
		bOK = BuildHipRoof(Mesh, FootprintPoly, OverhangPoly, PitchDeg, HeightOffset, OverhangDist, BuildErr);
	}
	else if (RoofType == TEXT("flat"))
	{
		bOK = BuildFlatRoof(Mesh, FootprintPoly, HeightOffset, ParapetHeight, ParapetThickness, BuildErr);
	}
	else if (RoofType == TEXT("shed"))
	{
		bOK = BuildShedRoof(Mesh, FootprintPoly, OverhangPoly, PitchDeg, HeightOffset, OverhangDist, RidgeOffset, BuildErr);
	}
	else if (RoofType == TEXT("gambrel"))
	{
		bOK = BuildGambrelRoof(Mesh, FootprintPoly, OverhangPoly, PitchDeg, HeightOffset, OverhangDist, BuildErr);
	}
	else
	{
		return FMonolithActionResult::Error(FString::Printf(
			TEXT("Unknown roof_type '%s'. Valid: gable, hip, flat, shed, gambrel"), *RoofType));
	}

	if (!bOK)
	{
		return FMonolithActionResult::Error(FString::Printf(TEXT("Roof build failed: %s"), *BuildErr));
	}

	// ---- UV box projection ----
	{
		FGeometryScriptMeshSelection EmptySelection;
		FTransform UVBox = FTransform::Identity;
		UVBox.SetScale3D(FVector(100.0f));
		UGeometryScriptLibrary_MeshUVFunctions::SetMeshUVsFromBoxProjection(
			Mesh, 0, UVBox, EmptySelection, 2);
	}

	// ---- Normals cleanup (additive-only, no booleans) ----
	FMonolithMeshProceduralActions::CleanupMesh(Mesh, /*bHadBooleans=*/false);

	// ---- Compute stats for return JSON ----
	FVector2D Center, LongAxis, ShortAxis;
	float HalfW, HalfD;
	ComputeFootprintOBB(FootprintPoly, Center, HalfW, HalfD, LongAxis, ShortAxis);

	float PitchRad = FMath::DegreesToRadians(PitchDeg);
	float RidgeH = (RoofType == TEXT("flat")) ? 0.0f : (HalfD + OverhangDist) * FMath::Tan(PitchRad);
	float RidgeLen = (RoofType == TEXT("hip"))
		? FMath::Max(0.0f, (HalfW - HalfD) * 2.0f)
		: (HalfW + OverhangDist) * 2.0f;

	// Footprint area (shoelace formula)
	float FootprintArea = 0.0f;
	{
		int32 N = FootprintPoly.Num();
		for (int32 i = 0; i < N; ++i)
		{
			const FVector2D& A = FootprintPoly[i];
			const FVector2D& B = FootprintPoly[(i + 1) % N];
			FootprintArea += A.X * B.Y - B.X * A.Y;
		}
		FootprintArea = FMath::Abs(FootprintArea) * 0.5f;
	}

	// ---- Save to asset ----
	FString SaveErr;
	if (!FMonolithMeshProceduralActions::SaveMeshToAsset(Mesh, SavePath, bOverwrite, SaveErr))
	{
		return FMonolithActionResult::Error(FString::Printf(TEXT("Roof geometry built but save failed: %s"), *SaveErr));
	}

	// ---- Place in scene ----
	FVector Location = FVector::ZeroVector;
	MonolithMeshUtils::ParseVector(Params, TEXT("location"), Location);
	FString Label;
	Params->TryGetStringField(TEXT("label"), Label);
	FString Folder;
	Params->TryGetStringField(TEXT("folder"), Folder);
	if (Folder.IsEmpty())
	{
		Folder = TEXT("Procedural/Roofs");
	}

	AActor* Actor = FMonolithMeshProceduralActions::PlaceMeshInScene(
		SavePath, Location, FRotator::ZeroRotator, Label, /*bSnapToFloor=*/false, Folder);

	// ---- Tag actor ----
	FString BuildingId;
	Params->TryGetStringField(TEXT("building_id"), BuildingId);

	if (Actor)
	{
		Actor->Tags.Add(FName(TEXT("BuildingRoof")));
		if (!BuildingId.IsEmpty())
		{
			Actor->Tags.Add(FName(*FString::Printf(TEXT("BuildingId:%s"), *BuildingId)));
		}

		// Apply materials if specified
		AStaticMeshActor* SMActor = Cast<AStaticMeshActor>(Actor);
		if (SMActor && SMActor->GetStaticMeshComponent())
		{
			UStaticMeshComponent* SMC = SMActor->GetStaticMeshComponent();

			auto TrySetMaterial = [&](const FString& ParamKey, int32 SlotIndex)
			{
				FString MatPath;
				if (Params->TryGetStringField(ParamKey, MatPath) && !MatPath.IsEmpty())
				{
					UMaterialInterface* Mat = LoadObject<UMaterialInterface>(nullptr, *MatPath);
					if (Mat)
					{
						SMC->SetMaterial(SlotIndex, Mat);
					}
				}
			};

			TrySetMaterial(TEXT("material_roof"), 0);
			TrySetMaterial(TEXT("material_soffit"), 1);
			TrySetMaterial(TEXT("material_fascia"), 2);
		}
	}

	// ---- Build result JSON ----
	auto Result = MakeShared<FJsonObject>();
	Result->SetStringField(TEXT("asset_path"), SavePath);
	Result->SetStringField(TEXT("roof_type"), RoofType);
	Result->SetNumberField(TEXT("ridge_length"), RidgeLen);
	Result->SetNumberField(TEXT("ridge_height"), RidgeH);
	Result->SetNumberField(TEXT("overhang"), OverhangDist);
	Result->SetNumberField(TEXT("footprint_area"), FootprintArea);
	Result->SetNumberField(TEXT("height_offset"), HeightOffset);
	Result->SetNumberField(TEXT("pitch_degrees"), PitchDeg);

	// Material slots
	auto MatSlots = MakeShared<FJsonObject>();
	MatSlots->SetStringField(TEXT("0"), TEXT("roof_surface"));
	MatSlots->SetStringField(TEXT("1"), TEXT("soffit"));
	MatSlots->SetStringField(TEXT("2"), TEXT("fascia"));
	Result->SetObjectField(TEXT("material_slots"), MatSlots);

	if (Actor)
	{
		Result->SetStringField(TEXT("actor_name"), Actor->GetActorNameOrLabel());
	}

	if (!BuildingId.IsEmpty())
	{
		Result->SetStringField(TEXT("building_id"), BuildingId);
	}

	return FMonolithActionResult::Success(Result);
}

#endif // WITH_GEOMETRYSCRIPT
