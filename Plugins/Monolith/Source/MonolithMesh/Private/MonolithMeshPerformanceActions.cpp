#include "MonolithMeshPerformanceActions.h"
#include "MonolithMeshUtils.h"
#include "MonolithToolRegistry.h"
#include "MonolithParamSchema.h"
#include "MonolithAssetUtils.h"

#include "Engine/StaticMesh.h"
#include "Engine/SkeletalMesh.h"
#include "Engine/StaticMeshActor.h"
#include "Engine/Light.h"
#include "Engine/World.h"
#include "EngineUtils.h"
#include "GameFramework/Actor.h"
#include "Components/StaticMeshComponent.h"
#include "Components/InstancedStaticMeshComponent.h"
#include "Components/SkeletalMeshComponent.h"
#include "Components/PrimitiveComponent.h"
#include "Components/LightComponent.h"
#include "Materials/MaterialInterface.h"
#include "Dom/JsonObject.h"
#include "Dom/JsonValue.h"
#include "ConvexVolume.h"
#include "SceneView.h"
#include "StaticMeshResources.h"
#include "Rendering/SkeletalMeshRenderData.h"
#include "Editor.h"

// ============================================================================
// Helpers
// ============================================================================

TArray<TSharedPtr<FJsonValue>> FMonolithMeshPerformanceActions::VectorToJsonArray(const FVector& V)
{
	TArray<TSharedPtr<FJsonValue>> Arr;
	Arr.Add(MakeShared<FJsonValueNumber>(V.X));
	Arr.Add(MakeShared<FJsonValueNumber>(V.Y));
	Arr.Add(MakeShared<FJsonValueNumber>(V.Z));
	return Arr;
}

// ============================================================================
// Registration
// ============================================================================

void FMonolithMeshPerformanceActions::RegisterActions(FMonolithToolRegistry& Registry)
{
	// 1. get_region_performance
	Registry.RegisterAction(TEXT("mesh"), TEXT("get_region_performance"),
		TEXT("Analyze performance metrics for a world region: triangle count, draw call estimate, light count, shadow caster count. Conservative estimates (no occlusion culling)."),
		FMonolithActionHandler::CreateStatic(&FMonolithMeshPerformanceActions::GetRegionPerformance),
		FParamSchemaBuilder()
			.Required(TEXT("region_min"), TEXT("array"), TEXT("Min corner of region [x, y, z]"))
			.Required(TEXT("region_max"), TEXT("array"), TEXT("Max corner of region [x, y, z]"))
			.Build());

	// 2. estimate_placement_cost
	Registry.RegisterAction(TEXT("mesh"), TEXT("estimate_placement_cost"),
		TEXT("Pre-placement budgeting: estimate triangle and draw call cost for a set of meshes without spawning. Loads mesh assets to read render data."),
		FMonolithActionHandler::CreateStatic(&FMonolithMeshPerformanceActions::EstimatePlacementCost),
		FParamSchemaBuilder()
			.Required(TEXT("assets"), TEXT("array"), TEXT("Array of {asset_path, count} objects"))
			.Build());

	// 3. find_overdraw_hotspots
	Registry.RegisterAction(TEXT("mesh"), TEXT("find_overdraw_hotspots"),
		TEXT("Detect overdraw hotspots from translucent/additive material actors. Projects bounds to screen-space AABBs and counts overlap in a tile grid."),
		FMonolithActionHandler::CreateStatic(&FMonolithMeshPerformanceActions::FindOverdrawHotspots),
		FParamSchemaBuilder()
			.Required(TEXT("viewpoint"), TEXT("array"), TEXT("Camera position [x, y, z]"))
			.Optional(TEXT("view_direction"), TEXT("array"), TEXT("Camera forward direction [x, y, z] (default: +X)"))
			.Optional(TEXT("fov"), TEXT("number"), TEXT("Field of view in degrees"), TEXT("90"))
			.Build());

	// 4. analyze_shadow_cost
	Registry.RegisterAction(TEXT("mesh"), TEXT("analyze_shadow_cost"),
		TEXT("Audit shadow-casting actors and lights in a region. Flags small props casting shadows unnecessarily and lights with high shadow resolution on non-hero objects."),
		FMonolithActionHandler::CreateStatic(&FMonolithMeshPerformanceActions::AnalyzeShadowCost),
		FParamSchemaBuilder()
			.Required(TEXT("region_min"), TEXT("array"), TEXT("Min corner of region [x, y, z]"))
			.Required(TEXT("region_max"), TEXT("array"), TEXT("Max corner of region [x, y, z]"))
			.Build());

	// 5. get_triangle_budget
	Registry.RegisterAction(TEXT("mesh"), TEXT("get_triangle_budget"),
		TEXT("LOD-aware triangle budget check from a viewpoint. Builds a view frustum, tests actor visibility, selects LOD by screen size. Returns count vs budget. Conservative (no occlusion culling)."),
		FMonolithActionHandler::CreateStatic(&FMonolithMeshPerformanceActions::GetTriangleBudget),
		FParamSchemaBuilder()
			.Required(TEXT("viewpoint"), TEXT("array"), TEXT("Camera position [x, y, z]"))
			.Optional(TEXT("view_direction"), TEXT("array"), TEXT("Camera forward direction [x, y, z] (default: +X)"))
			.Optional(TEXT("fov"), TEXT("number"), TEXT("Field of view in degrees"), TEXT("90"))
			.Optional(TEXT("budget"), TEXT("integer"), TEXT("Triangle budget to compare against"), TEXT("500000"))
			.Build());
}

// ============================================================================
// 1. get_region_performance
// ============================================================================

FMonolithActionResult FMonolithMeshPerformanceActions::GetRegionPerformance(const TSharedPtr<FJsonObject>& Params)
{
	FVector RegionMin, RegionMax;
	if (!MonolithMeshUtils::ParseVector(Params, TEXT("region_min"), RegionMin))
	{
		return FMonolithActionResult::Error(TEXT("Missing or invalid required param: region_min (array of 3 numbers)"));
	}
	if (!MonolithMeshUtils::ParseVector(Params, TEXT("region_max"), RegionMax))
	{
		return FMonolithActionResult::Error(TEXT("Missing or invalid required param: region_max (array of 3 numbers)"));
	}

	UWorld* World = MonolithMeshUtils::GetEditorWorld();
	if (!World)
	{
		return FMonolithActionResult::Error(TEXT("No editor world available"));
	}

	FBox RegionBox(
		FVector(FMath::Min(RegionMin.X, RegionMax.X), FMath::Min(RegionMin.Y, RegionMax.Y), FMath::Min(RegionMin.Z, RegionMax.Z)),
		FVector(FMath::Max(RegionMin.X, RegionMax.X), FMath::Max(RegionMin.Y, RegionMax.Y), FMath::Max(RegionMin.Z, RegionMax.Z))
	);

	int64 TotalTriangles = 0;
	int32 DrawCallEstimate = 0;
	int32 LightCount = 0;
	int32 ShadowCasterCount = 0;
	int32 ActorCount = 0;
	int32 StaticMeshComponentCount = 0;
	int32 SkeletalMeshComponentCount = 0;

	for (TActorIterator<AActor> It(World); It; ++It)
	{
		AActor* Actor = *It;

		FVector Origin, Extent;
		Actor->GetActorBounds(false, Origin, Extent);
		FBox ActorBox(Origin - Extent, Origin + Extent);

		if (!RegionBox.Intersect(ActorBox))
		{
			continue;
		}

		ActorCount++;

		// Static mesh components
		TArray<UStaticMeshComponent*> SMCs;
		Actor->GetComponents(SMCs);
		for (UStaticMeshComponent* SMC : SMCs)
		{
			if (!SMC || !SMC->IsVisible())
			{
				continue;
			}

			StaticMeshComponentCount++;

			UStaticMesh* Mesh = SMC->GetStaticMesh();
			if (Mesh && Mesh->GetRenderData() && Mesh->GetRenderData()->LODResources.Num() > 0)
			{
				const FStaticMeshLODResources& LOD0 = Mesh->GetRenderData()->LODResources[0];
				TotalTriangles += LOD0.GetNumTriangles();

				// Draw calls: sections per mesh per component
				// ISM batches into 1 draw call per section, not per instance
				if (SMC->IsA<UInstancedStaticMeshComponent>())
				{
					DrawCallEstimate += LOD0.Sections.Num();
				}
				else
				{
					DrawCallEstimate += LOD0.Sections.Num();
				}
			}
			else
			{
				// Fallback: 1 draw call for components with unknown mesh
				DrawCallEstimate += FMath::Max(1, SMC->GetNumMaterials());
			}

			// Shadow caster check
			if (SMC->CastShadow)
			{
				ShadowCasterCount++;
			}
		}

		// Skeletal mesh components
		TArray<USkeletalMeshComponent*> SkMCs;
		Actor->GetComponents(SkMCs);
		for (USkeletalMeshComponent* SkMC : SkMCs)
		{
			if (!SkMC || !SkMC->IsVisible())
			{
				continue;
			}

			SkeletalMeshComponentCount++;

			USkeletalMesh* SkMesh = SkMC->GetSkeletalMeshAsset();
			if (SkMesh)
			{
				FSkeletalMeshRenderData* RenderData = SkMesh->GetResourceForRendering();
				if (RenderData && RenderData->LODRenderData.Num() > 0)
				{
					const FSkeletalMeshLODRenderData& LOD0 = RenderData->LODRenderData[0];
					TotalTriangles += LOD0.GetTotalFaces();
					DrawCallEstimate += LOD0.RenderSections.Num();
				}
			}

			if (SkMC->CastShadow)
			{
				ShadowCasterCount++;
			}
		}

		// Lights
		ULightComponent* LightComp = Actor->FindComponentByClass<ULightComponent>();
		if (LightComp)
		{
			LightCount++;
			if (LightComp->CastShadows)
			{
				ShadowCasterCount++;
			}
		}
	}

	auto Result = MakeShared<FJsonObject>();
	Result->SetArrayField(TEXT("region_min"), VectorToJsonArray(RegionBox.Min));
	Result->SetArrayField(TEXT("region_max"), VectorToJsonArray(RegionBox.Max));
	Result->SetNumberField(TEXT("actor_count"), ActorCount);
	Result->SetNumberField(TEXT("total_triangles"), static_cast<double>(TotalTriangles));
	Result->SetNumberField(TEXT("draw_call_estimate"), DrawCallEstimate);
	Result->SetNumberField(TEXT("light_count"), LightCount);
	Result->SetNumberField(TEXT("shadow_caster_count"), ShadowCasterCount);
	Result->SetNumberField(TEXT("static_mesh_components"), StaticMeshComponentCount);
	Result->SetNumberField(TEXT("skeletal_mesh_components"), SkeletalMeshComponentCount);
	Result->SetStringField(TEXT("note"), TEXT("Conservative estimate: LOD0 triangles, no occlusion culling, no dynamic batching"));

	return FMonolithActionResult::Success(Result);
}

// ============================================================================
// 2. estimate_placement_cost
// ============================================================================

FMonolithActionResult FMonolithMeshPerformanceActions::EstimatePlacementCost(const TSharedPtr<FJsonObject>& Params)
{
	const TArray<TSharedPtr<FJsonValue>>* AssetsArr;
	if (!Params->TryGetArrayField(TEXT("assets"), AssetsArr) || AssetsArr->Num() == 0)
	{
		return FMonolithActionResult::Error(TEXT("Missing or empty required param: assets (array of {asset_path, count} objects)"));
	}

	if (AssetsArr->Num() > 100)
	{
		return FMonolithActionResult::Error(TEXT("Too many asset entries (max 100)"));
	}

	int64 TotalTriangles = 0;
	int32 TotalDrawCalls = 0;
	int64 TotalVertices = 0;
	TArray<TSharedPtr<FJsonValue>> PerAssetResults;

	for (const TSharedPtr<FJsonValue>& Val : *AssetsArr)
	{
		const TSharedPtr<FJsonObject>* EntryObj;
		if (!Val->TryGetObject(EntryObj))
		{
			return FMonolithActionResult::Error(TEXT("Each entry in assets must be an object with asset_path and count"));
		}

		FString AssetPath;
		if (!(*EntryObj)->TryGetStringField(TEXT("asset_path"), AssetPath) || AssetPath.IsEmpty())
		{
			return FMonolithActionResult::Error(TEXT("Each entry requires a non-empty asset_path"));
		}

		double CountD = 1.0;
		(*EntryObj)->TryGetNumberField(TEXT("count"), CountD);
		int32 Count = FMath::Clamp(static_cast<int32>(CountD), 1, 10000);

		// Try loading as StaticMesh first, then SkeletalMesh
		int64 MeshTris = 0;
		int64 MeshVerts = 0;
		int32 MeshSections = 0;
		FString MeshType;

		UStaticMesh* SM = FMonolithAssetUtils::LoadAssetByPath<UStaticMesh>(AssetPath);
		if (SM && SM->GetRenderData() && SM->GetRenderData()->LODResources.Num() > 0)
		{
			const FStaticMeshLODResources& LOD0 = SM->GetRenderData()->LODResources[0];
			MeshTris = LOD0.GetNumTriangles();
			MeshVerts = LOD0.GetNumVertices();
			MeshSections = LOD0.Sections.Num();
			MeshType = TEXT("StaticMesh");
		}
		else
		{
			USkeletalMesh* SkM = FMonolithAssetUtils::LoadAssetByPath<USkeletalMesh>(AssetPath);
			if (SkM)
			{
				FSkeletalMeshRenderData* RenderData = SkM->GetResourceForRendering();
				if (RenderData && RenderData->LODRenderData.Num() > 0)
				{
					const FSkeletalMeshLODRenderData& LOD0 = RenderData->LODRenderData[0];
					MeshTris = LOD0.GetTotalFaces();
					MeshVerts = LOD0.GetNumVertices();
					MeshSections = LOD0.RenderSections.Num();
					MeshType = TEXT("SkeletalMesh");
				}
			}
		}

		if (MeshType.IsEmpty())
		{
			return FMonolithActionResult::Error(FString::Printf(
				TEXT("Could not load mesh or has no render data: %s"), *AssetPath));
		}

		int64 EntryTris = MeshTris * Count;
		int32 EntryDrawCalls = MeshSections * Count;
		int64 EntryVerts = MeshVerts * Count;

		TotalTriangles += EntryTris;
		TotalDrawCalls += EntryDrawCalls;
		TotalVertices += EntryVerts;

		auto EntryResult = MakeShared<FJsonObject>();
		EntryResult->SetStringField(TEXT("asset_path"), AssetPath);
		EntryResult->SetStringField(TEXT("type"), MeshType);
		EntryResult->SetNumberField(TEXT("count"), Count);
		EntryResult->SetNumberField(TEXT("triangles_per_mesh"), static_cast<double>(MeshTris));
		EntryResult->SetNumberField(TEXT("sections_per_mesh"), MeshSections);
		EntryResult->SetNumberField(TEXT("total_triangles"), static_cast<double>(EntryTris));
		EntryResult->SetNumberField(TEXT("total_draw_calls"), EntryDrawCalls);

		PerAssetResults.Add(MakeShared<FJsonValueObject>(EntryResult));
	}

	auto Result = MakeShared<FJsonObject>();
	Result->SetArrayField(TEXT("assets"), PerAssetResults);
	Result->SetNumberField(TEXT("total_triangles"), static_cast<double>(TotalTriangles));
	Result->SetNumberField(TEXT("total_draw_calls"), TotalDrawCalls);
	Result->SetNumberField(TEXT("total_vertices"), static_cast<double>(TotalVertices));
	Result->SetStringField(TEXT("note"), TEXT("Conservative estimate: LOD0 counts, no ISM batching, no dynamic merging"));

	return FMonolithActionResult::Success(Result);
}

// ============================================================================
// 3. find_overdraw_hotspots
// ============================================================================

FMonolithActionResult FMonolithMeshPerformanceActions::FindOverdrawHotspots(const TSharedPtr<FJsonObject>& Params)
{
	FVector Viewpoint;
	if (!MonolithMeshUtils::ParseVector(Params, TEXT("viewpoint"), Viewpoint))
	{
		return FMonolithActionResult::Error(TEXT("Missing or invalid required param: viewpoint (array of 3 numbers)"));
	}

	FVector ViewDirection(1.0, 0.0, 0.0); // Default: +X forward
	MonolithMeshUtils::ParseVector(Params, TEXT("view_direction"), ViewDirection);
	ViewDirection.Normalize();
	if (ViewDirection.IsNearlyZero())
	{
		ViewDirection = FVector(1.0, 0.0, 0.0);
	}

	double FOV = 90.0;
	Params->TryGetNumberField(TEXT("fov"), FOV);
	FOV = FMath::Clamp(FOV, 10.0, 170.0);

	UWorld* World = MonolithMeshUtils::GetEditorWorld();
	if (!World)
	{
		return FMonolithActionResult::Error(TEXT("No editor world available"));
	}

	// Build a view projection matrix for screen-space projection
	const float AspectRatio = 16.0f / 9.0f;
	const float HalfFOVRad = FMath::DegreesToRadians(static_cast<float>(FOV) * 0.5f);

	// Build view matrix from viewpoint + direction
	FVector UpVector(0.0f, 0.0f, 1.0f);
	if (FMath::Abs(FVector::DotProduct(ViewDirection, UpVector)) > 0.99f)
	{
		UpVector = FVector(0.0f, 1.0f, 0.0f);
	}
	FVector RightVector = FVector::CrossProduct(UpVector, ViewDirection).GetSafeNormal();
	UpVector = FVector::CrossProduct(ViewDirection, RightVector);

	FMatrix ViewMatrix = FLookAtMatrix(Viewpoint, Viewpoint + ViewDirection * 100.0f, UpVector);
	FMatrix ProjectionMatrix = FPerspectiveMatrix(HalfFOVRad, AspectRatio, 1.0f, 1.0f, 50000.0f);
	FMatrix ViewProjectionMatrix = ViewMatrix * ProjectionMatrix;

	// Tile grid for overlap counting (16x16)
	static const int32 TileCountX = 16;
	static const int32 TileCountY = 16;
	int32 TileOverlapCount[TileCountX][TileCountY];
	FMemory::Memzero(TileOverlapCount, sizeof(TileOverlapCount));

	struct FTranslucentActorInfo
	{
		FString Name;
		FString MaterialName;
		FString BlendMode;
		FVector2D ScreenMin;
		FVector2D ScreenMax;
		int32 TilesCovered;
	};

	TArray<FTranslucentActorInfo> TranslucentActors;

	for (TActorIterator<AActor> It(World); It; ++It)
	{
		AActor* Actor = *It;

		TArray<UPrimitiveComponent*> PrimComps;
		Actor->GetComponents(PrimComps);

		for (UPrimitiveComponent* PrimComp : PrimComps)
		{
			if (!PrimComp || !PrimComp->IsVisible())
			{
				continue;
			}

			// Check all materials on this component for translucency
			bool bHasTranslucent = false;
			FString TranslucentMatName;
			FString BlendModeStr;

			for (int32 MatIdx = 0; MatIdx < PrimComp->GetNumMaterials(); ++MatIdx)
			{
				UMaterialInterface* Mat = PrimComp->GetMaterial(MatIdx);
				if (!Mat)
				{
					continue;
				}

				EBlendMode BlendMode = Mat->GetBlendMode();
				if (BlendMode >= BLEND_Translucent)
				{
					bHasTranslucent = true;
					TranslucentMatName = Mat->GetName();

					switch (BlendMode)
					{
					case BLEND_Translucent:    BlendModeStr = TEXT("Translucent"); break;
					case BLEND_Additive:       BlendModeStr = TEXT("Additive"); break;
					case BLEND_Modulate:       BlendModeStr = TEXT("Modulate"); break;
					case BLEND_AlphaComposite: BlendModeStr = TEXT("AlphaComposite"); break;
					case BLEND_AlphaHoldout:   BlendModeStr = TEXT("AlphaHoldout"); break;
					default:                   BlendModeStr = TEXT("Other"); break;
					}
					break; // Found at least one translucent material
				}
			}

			if (!bHasTranslucent)
			{
				continue;
			}

			// Project bounds to screen-space AABB
			FBoxSphereBounds CompBounds = PrimComp->Bounds;
			FVector BoundsOrigin = CompBounds.Origin;
			FVector BoundsExtent = CompBounds.BoxExtent;

			// 8 corners of the bounding box
			FVector Corners[8];
			Corners[0] = BoundsOrigin + FVector(-BoundsExtent.X, -BoundsExtent.Y, -BoundsExtent.Z);
			Corners[1] = BoundsOrigin + FVector( BoundsExtent.X, -BoundsExtent.Y, -BoundsExtent.Z);
			Corners[2] = BoundsOrigin + FVector(-BoundsExtent.X,  BoundsExtent.Y, -BoundsExtent.Z);
			Corners[3] = BoundsOrigin + FVector( BoundsExtent.X,  BoundsExtent.Y, -BoundsExtent.Z);
			Corners[4] = BoundsOrigin + FVector(-BoundsExtent.X, -BoundsExtent.Y,  BoundsExtent.Z);
			Corners[5] = BoundsOrigin + FVector( BoundsExtent.X, -BoundsExtent.Y,  BoundsExtent.Z);
			Corners[6] = BoundsOrigin + FVector(-BoundsExtent.X,  BoundsExtent.Y,  BoundsExtent.Z);
			Corners[7] = BoundsOrigin + FVector( BoundsExtent.X,  BoundsExtent.Y,  BoundsExtent.Z);

			FVector2D ScreenMin(TNumericLimits<float>::Max(), TNumericLimits<float>::Max());
			FVector2D ScreenMax(TNumericLimits<float>::Lowest(), TNumericLimits<float>::Lowest());
			bool bAnyVisible = false;

			for (int32 c = 0; c < 8; ++c)
			{
				FVector4 Projected = ViewProjectionMatrix.TransformFVector4(FVector4(Corners[c], 1.0f));
				if (Projected.W > 0.0f)
				{
					float InvW = 1.0f / Projected.W;
					float ScreenX = (Projected.X * InvW * 0.5f + 0.5f);
					float ScreenY = (Projected.Y * InvW * 0.5f + 0.5f);

					ScreenMin.X = FMath::Min(ScreenMin.X, ScreenX);
					ScreenMin.Y = FMath::Min(ScreenMin.Y, ScreenY);
					ScreenMax.X = FMath::Max(ScreenMax.X, ScreenX);
					ScreenMax.Y = FMath::Max(ScreenMax.Y, ScreenY);
					bAnyVisible = true;
				}
			}

			if (!bAnyVisible)
			{
				continue;
			}

			// Clamp to [0,1] screen space
			ScreenMin.X = FMath::Clamp(ScreenMin.X, 0.0f, 1.0f);
			ScreenMin.Y = FMath::Clamp(ScreenMin.Y, 0.0f, 1.0f);
			ScreenMax.X = FMath::Clamp(ScreenMax.X, 0.0f, 1.0f);
			ScreenMax.Y = FMath::Clamp(ScreenMax.Y, 0.0f, 1.0f);

			if (ScreenMax.X <= ScreenMin.X || ScreenMax.Y <= ScreenMin.Y)
			{
				continue;
			}

			// Rasterize into tiles
			int32 TileMinX = FMath::Clamp(static_cast<int32>(ScreenMin.X * TileCountX), 0, TileCountX - 1);
			int32 TileMinY = FMath::Clamp(static_cast<int32>(ScreenMin.Y * TileCountY), 0, TileCountY - 1);
			int32 TileMaxX = FMath::Clamp(static_cast<int32>(ScreenMax.X * TileCountX), 0, TileCountX - 1);
			int32 TileMaxY = FMath::Clamp(static_cast<int32>(ScreenMax.Y * TileCountY), 0, TileCountY - 1);

			int32 TilesCovered = 0;
			for (int32 tx = TileMinX; tx <= TileMaxX; ++tx)
			{
				for (int32 ty = TileMinY; ty <= TileMaxY; ++ty)
				{
					TileOverlapCount[tx][ty]++;
					TilesCovered++;
				}
			}

			FTranslucentActorInfo Info;
			Info.Name = Actor->GetActorNameOrLabel();
			Info.MaterialName = TranslucentMatName;
			Info.BlendMode = BlendModeStr;
			Info.ScreenMin = ScreenMin;
			Info.ScreenMax = ScreenMax;
			Info.TilesCovered = TilesCovered;
			TranslucentActors.Add(MoveTemp(Info));
		}
	}

	// Find hotspot tiles (overlap >= 2)
	TArray<TSharedPtr<FJsonValue>> HotspotArr;
	int32 MaxOverlap = 0;

	for (int32 tx = 0; tx < TileCountX; ++tx)
	{
		for (int32 ty = 0; ty < TileCountY; ++ty)
		{
			MaxOverlap = FMath::Max(MaxOverlap, TileOverlapCount[tx][ty]);

			if (TileOverlapCount[tx][ty] >= 2)
			{
				auto TileObj = MakeShared<FJsonObject>();
				TileObj->SetNumberField(TEXT("tile_x"), tx);
				TileObj->SetNumberField(TEXT("tile_y"), ty);
				TileObj->SetNumberField(TEXT("overlap_count"), TileOverlapCount[tx][ty]);

				// Screen-space position of tile center
				TileObj->SetNumberField(TEXT("screen_x"), (static_cast<float>(tx) + 0.5f) / static_cast<float>(TileCountX));
				TileObj->SetNumberField(TEXT("screen_y"), (static_cast<float>(ty) + 0.5f) / static_cast<float>(TileCountY));

				HotspotArr.Add(MakeShared<FJsonValueObject>(TileObj));
			}
		}
	}

	// Sort hotspots by overlap count descending
	HotspotArr.Sort([](const TSharedPtr<FJsonValue>& A, const TSharedPtr<FJsonValue>& B)
	{
		return A->AsObject()->GetNumberField(TEXT("overlap_count")) > B->AsObject()->GetNumberField(TEXT("overlap_count"));
	});

	// Cap output to top 50 hotspot tiles
	if (HotspotArr.Num() > 50)
	{
		HotspotArr.SetNum(50);
	}

	// Build translucent actor list
	TArray<TSharedPtr<FJsonValue>> ActorArr;
	for (const FTranslucentActorInfo& Info : TranslucentActors)
	{
		auto ActorObj = MakeShared<FJsonObject>();
		ActorObj->SetStringField(TEXT("actor"), Info.Name);
		ActorObj->SetStringField(TEXT("material"), Info.MaterialName);
		ActorObj->SetStringField(TEXT("blend_mode"), Info.BlendMode);

		TArray<TSharedPtr<FJsonValue>> MinArr;
		MinArr.Add(MakeShared<FJsonValueNumber>(Info.ScreenMin.X));
		MinArr.Add(MakeShared<FJsonValueNumber>(Info.ScreenMin.Y));
		ActorObj->SetArrayField(TEXT("screen_min"), MinArr);

		TArray<TSharedPtr<FJsonValue>> MaxArr;
		MaxArr.Add(MakeShared<FJsonValueNumber>(Info.ScreenMax.X));
		MaxArr.Add(MakeShared<FJsonValueNumber>(Info.ScreenMax.Y));
		ActorObj->SetArrayField(TEXT("screen_max"), MaxArr);

		ActorObj->SetNumberField(TEXT("tiles_covered"), Info.TilesCovered);

		ActorArr.Add(MakeShared<FJsonValueObject>(ActorObj));
	}

	auto Result = MakeShared<FJsonObject>();
	Result->SetNumberField(TEXT("translucent_actor_count"), TranslucentActors.Num());
	Result->SetNumberField(TEXT("max_tile_overlap"), MaxOverlap);
	Result->SetNumberField(TEXT("hotspot_tile_count"), HotspotArr.Num());
	Result->SetArrayField(TEXT("hotspot_tiles"), HotspotArr);
	Result->SetArrayField(TEXT("translucent_actors"), ActorArr);
	Result->SetStringField(TEXT("tile_grid"), FString::Printf(TEXT("%dx%d"), TileCountX, TileCountY));

	return FMonolithActionResult::Success(Result);
}

// ============================================================================
// 4. analyze_shadow_cost
// ============================================================================

FMonolithActionResult FMonolithMeshPerformanceActions::AnalyzeShadowCost(const TSharedPtr<FJsonObject>& Params)
{
	FVector RegionMin, RegionMax;
	if (!MonolithMeshUtils::ParseVector(Params, TEXT("region_min"), RegionMin))
	{
		return FMonolithActionResult::Error(TEXT("Missing or invalid required param: region_min (array of 3 numbers)"));
	}
	if (!MonolithMeshUtils::ParseVector(Params, TEXT("region_max"), RegionMax))
	{
		return FMonolithActionResult::Error(TEXT("Missing or invalid required param: region_max (array of 3 numbers)"));
	}

	UWorld* World = MonolithMeshUtils::GetEditorWorld();
	if (!World)
	{
		return FMonolithActionResult::Error(TEXT("No editor world available"));
	}

	FBox RegionBox(
		FVector(FMath::Min(RegionMin.X, RegionMax.X), FMath::Min(RegionMin.Y, RegionMax.Y), FMath::Min(RegionMin.Z, RegionMax.Z)),
		FVector(FMath::Max(RegionMin.X, RegionMax.X), FMath::Max(RegionMin.Y, RegionMax.Y), FMath::Max(RegionMin.Z, RegionMax.Z))
	);

	// Collect shadow casters and issues
	struct FShadowIssue
	{
		FString ActorName;
		FString ComponentName;
		FString Issue;
		FString Severity; // HIGH, MEDIUM, LOW
		int32 TriCount;
	};

	TArray<FShadowIssue> Issues;
	int32 TotalShadowCasters = 0;
	int32 ShadowCastingLights = 0;
	int32 SmallPropShadowCasters = 0;

	// Shadow-casting light info
	TArray<TSharedPtr<FJsonValue>> LightArr;

	for (TActorIterator<AActor> It(World); It; ++It)
	{
		AActor* Actor = *It;

		FVector Origin, Extent;
		Actor->GetActorBounds(false, Origin, Extent);
		FBox ActorBox(Origin - Extent, Origin + Extent);

		if (!RegionBox.Intersect(ActorBox))
		{
			continue;
		}

		// Check lights
		TArray<ULightComponent*> LightComps;
		Actor->GetComponents(LightComps);
		for (ULightComponent* LightComp : LightComps)
		{
			if (!LightComp)
			{
				continue;
			}

			if (LightComp->CastShadows)
			{
				ShadowCastingLights++;

				auto LightObj = MakeShared<FJsonObject>();
				LightObj->SetStringField(TEXT("actor"), Actor->GetActorNameOrLabel());
				LightObj->SetStringField(TEXT("light_type"), LightComp->GetClass()->GetName());
				LightObj->SetNumberField(TEXT("shadow_resolution_scale"), LightComp->ShadowResolutionScale);
				LightObj->SetBoolField(TEXT("cast_shadows"), true);
				LightObj->SetNumberField(TEXT("intensity"), LightComp->Intensity);

				if (LightComp->ShadowResolutionScale > 1.0f)
				{
					FShadowIssue Issue;
					Issue.ActorName = Actor->GetActorNameOrLabel();
					Issue.ComponentName = LightComp->GetName();
					Issue.Issue = FString::Printf(TEXT("High ShadowResolutionScale (%.1f) — costly for VSM. Consider lowering to 1.0 or below for non-hero lights."), LightComp->ShadowResolutionScale);
					Issue.Severity = TEXT("MEDIUM");
					Issue.TriCount = 0;
					Issues.Add(MoveTemp(Issue));
				}

				LightArr.Add(MakeShared<FJsonValueObject>(LightObj));
			}
		}

		// Check mesh components for unnecessary shadow casting
		TArray<UStaticMeshComponent*> SMCs;
		Actor->GetComponents(SMCs);
		for (UStaticMeshComponent* SMC : SMCs)
		{
			if (!SMC || !SMC->IsVisible() || !SMC->CastShadow)
			{
				continue;
			}

			TotalShadowCasters++;

			UStaticMesh* Mesh = SMC->GetStaticMesh();
			if (!Mesh || !Mesh->GetRenderData() || Mesh->GetRenderData()->LODResources.Num() == 0)
			{
				continue;
			}

			int32 TriCount = Mesh->GetRenderData()->LODResources[0].GetNumTriangles();

			// Flag small props casting shadows
			if (TriCount < 500)
			{
				SmallPropShadowCasters++;

				FShadowIssue Issue;
				Issue.ActorName = Actor->GetActorNameOrLabel();
				Issue.ComponentName = SMC->GetName();
				Issue.Issue = FString::Printf(TEXT("Small prop (%d tris) casting shadows — consider disabling CastShadow for performance."), TriCount);
				Issue.Severity = TEXT("LOW");
				Issue.TriCount = TriCount;
				Issues.Add(MoveTemp(Issue));
			}
		}

		// Check skeletal mesh shadow casters
		TArray<USkeletalMeshComponent*> SkMCs;
		Actor->GetComponents(SkMCs);
		for (USkeletalMeshComponent* SkMC : SkMCs)
		{
			if (!SkMC || !SkMC->IsVisible() || !SkMC->CastShadow)
			{
				continue;
			}

			TotalShadowCasters++;
		}
	}

	// Sort issues by severity
	Issues.Sort([](const FShadowIssue& A, const FShadowIssue& B)
	{
		auto SeverityRank = [](const FString& S) -> int32
		{
			if (S == TEXT("HIGH")) return 0;
			if (S == TEXT("MEDIUM")) return 1;
			return 2;
		};
		return SeverityRank(A.Severity) < SeverityRank(B.Severity);
	});

	// Build issues JSON
	TArray<TSharedPtr<FJsonValue>> IssuesArr;
	for (const FShadowIssue& Issue : Issues)
	{
		auto IssueObj = MakeShared<FJsonObject>();
		IssueObj->SetStringField(TEXT("actor"), Issue.ActorName);
		IssueObj->SetStringField(TEXT("component"), Issue.ComponentName);
		IssueObj->SetStringField(TEXT("issue"), Issue.Issue);
		IssueObj->SetStringField(TEXT("severity"), Issue.Severity);
		if (Issue.TriCount > 0)
		{
			IssueObj->SetNumberField(TEXT("tri_count"), Issue.TriCount);
		}
		IssuesArr.Add(MakeShared<FJsonValueObject>(IssueObj));
	}

	// Cap issues output
	if (IssuesArr.Num() > 100)
	{
		IssuesArr.SetNum(100);
	}

	auto Result = MakeShared<FJsonObject>();
	Result->SetArrayField(TEXT("region_min"), VectorToJsonArray(RegionBox.Min));
	Result->SetArrayField(TEXT("region_max"), VectorToJsonArray(RegionBox.Max));
	Result->SetNumberField(TEXT("total_shadow_casters"), TotalShadowCasters);
	Result->SetNumberField(TEXT("shadow_casting_lights"), ShadowCastingLights);
	Result->SetNumberField(TEXT("small_prop_shadow_casters"), SmallPropShadowCasters);
	Result->SetNumberField(TEXT("issue_count"), Issues.Num());
	Result->SetArrayField(TEXT("issues"), IssuesArr);
	Result->SetArrayField(TEXT("shadow_casting_lights_detail"), LightArr);

	return FMonolithActionResult::Success(Result);
}

// ============================================================================
// 5. get_triangle_budget
// ============================================================================

FMonolithActionResult FMonolithMeshPerformanceActions::GetTriangleBudget(const TSharedPtr<FJsonObject>& Params)
{
	FVector Viewpoint;
	if (!MonolithMeshUtils::ParseVector(Params, TEXT("viewpoint"), Viewpoint))
	{
		return FMonolithActionResult::Error(TEXT("Missing or invalid required param: viewpoint (array of 3 numbers)"));
	}

	FVector ViewDirection(1.0, 0.0, 0.0);
	MonolithMeshUtils::ParseVector(Params, TEXT("view_direction"), ViewDirection);
	ViewDirection.Normalize();
	if (ViewDirection.IsNearlyZero())
	{
		ViewDirection = FVector(1.0, 0.0, 0.0);
	}

	double FOV = 90.0;
	Params->TryGetNumberField(TEXT("fov"), FOV);
	FOV = FMath::Clamp(FOV, 10.0, 170.0);

	double BudgetD = 500000.0;
	Params->TryGetNumberField(TEXT("budget"), BudgetD);
	int64 Budget = FMath::Clamp(static_cast<int64>(BudgetD), 1000LL, 100000000LL);

	UWorld* World = MonolithMeshUtils::GetEditorWorld();
	if (!World)
	{
		return FMonolithActionResult::Error(TEXT("No editor world available"));
	}

	// Build view + projection matrices
	const float AspectRatio = 16.0f / 9.0f;
	const float HalfFOVRad = FMath::DegreesToRadians(static_cast<float>(FOV) * 0.5f);

	FVector UpVector(0.0f, 0.0f, 1.0f);
	if (FMath::Abs(FVector::DotProduct(ViewDirection, UpVector)) > 0.99f)
	{
		UpVector = FVector(0.0f, 1.0f, 0.0f);
	}
	FVector RightVector = FVector::CrossProduct(UpVector, ViewDirection).GetSafeNormal();
	UpVector = FVector::CrossProduct(ViewDirection, RightVector);

	FMatrix ViewMatrix = FLookAtMatrix(Viewpoint, Viewpoint + ViewDirection * 100.0f, UpVector);
	FMatrix ProjectionMatrix = FPerspectiveMatrix(HalfFOVRad, AspectRatio, 1.0f, 1.0f, 50000.0f);
	FMatrix ViewProjectionMatrix = ViewMatrix * ProjectionMatrix;

	// Build frustum using the free function GetViewFrustumBounds (ConvexVolume.h)
	FConvexVolume Frustum;
	GetViewFrustumBounds(Frustum, ViewProjectionMatrix, true);

	int64 TotalVisibleTriangles = 0;
	int32 VisibleActorCount = 0;
	int32 VisibleDrawCalls = 0;

	// Top contributors for reporting
	struct FTriContributor
	{
		FString Name;
		int64 Triangles;
		int32 LODUsed;
		float Distance;
	};
	TArray<FTriContributor> Contributors;

	for (TActorIterator<AActor> It(World); It; ++It)
	{
		AActor* Actor = *It;

		FVector Origin, Extent;
		Actor->GetActorBounds(false, Origin, Extent);

		// Frustum test using the convex volume
		if (!Frustum.IntersectBox(Origin, Extent))
		{
			continue;
		}

		int64 ActorTriangles = 0;
		int32 ActorDrawCalls = 0;
		int32 BestLOD = 0;

		// Static mesh components
		TArray<UStaticMeshComponent*> SMCs;
		Actor->GetComponents(SMCs);
		for (UStaticMeshComponent* SMC : SMCs)
		{
			if (!SMC || !SMC->IsVisible())
			{
				continue;
			}

			UStaticMesh* Mesh = SMC->GetStaticMesh();
			if (!Mesh || !Mesh->GetRenderData() || Mesh->GetRenderData()->LODResources.Num() == 0)
			{
				continue;
			}

			const FStaticMeshRenderData* RenderData = Mesh->GetRenderData();
			int32 NumLODs = RenderData->LODResources.Num();

			// LOD selection: approximate screen size from distance
			float Distance = FVector::Dist(Viewpoint, Origin);
			if (Distance < 1.0f)
			{
				Distance = 1.0f;
			}

			// Approximate screen size: bounds sphere radius / distance * FOV factor
			float BoundsRadius = Mesh->GetBounds().SphereRadius;
			float ScreenSize = BoundsRadius / (Distance * FMath::Tan(HalfFOVRad));

			// Select LOD based on screen size thresholds from the mesh
			int32 SelectedLOD = 0;
			for (int32 LODIdx = 1; LODIdx < NumLODs; ++LODIdx)
			{
				float LODScreenSize = RenderData->ScreenSize[LODIdx].Default;
				if (LODScreenSize > 0.0f && ScreenSize < LODScreenSize)
				{
					SelectedLOD = LODIdx;
				}
				else
				{
					break;
				}
			}

			const FStaticMeshLODResources& LODRes = RenderData->LODResources[SelectedLOD];
			int64 TriCount = LODRes.GetNumTriangles();

			// For ISM, multiply by instance count
			UInstancedStaticMeshComponent* ISM = Cast<UInstancedStaticMeshComponent>(SMC);
			if (ISM)
			{
				int32 InstanceCount = FMath::Max(1, ISM->GetInstanceCount());
				TriCount *= InstanceCount;
				// ISM: 1 draw call per section (not per instance)
				ActorDrawCalls += LODRes.Sections.Num();
			}
			else
			{
				ActorDrawCalls += LODRes.Sections.Num();
			}

			ActorTriangles += TriCount;
			BestLOD = SelectedLOD;
		}

		// Skeletal mesh components
		TArray<USkeletalMeshComponent*> SkMCs;
		Actor->GetComponents(SkMCs);
		for (USkeletalMeshComponent* SkMC : SkMCs)
		{
			if (!SkMC || !SkMC->IsVisible())
			{
				continue;
			}

			USkeletalMesh* SkMesh = SkMC->GetSkeletalMeshAsset();
			if (!SkMesh)
			{
				continue;
			}

			FSkeletalMeshRenderData* RenderData = SkMesh->GetResourceForRendering();
			if (!RenderData || RenderData->LODRenderData.Num() == 0)
			{
				continue;
			}

			// Simplified LOD selection for skeletal meshes
			float Distance = FVector::Dist(Viewpoint, Origin);
			int32 SelectedLOD = 0;
			// Use LOD0 for conservative estimate (skeletal LOD selection is animation-dependent)

			const FSkeletalMeshLODRenderData& LODRes = RenderData->LODRenderData[SelectedLOD];
			ActorTriangles += LODRes.GetTotalFaces();
			ActorDrawCalls += LODRes.RenderSections.Num();
		}

		if (ActorTriangles > 0)
		{
			VisibleActorCount++;
			TotalVisibleTriangles += ActorTriangles;
			VisibleDrawCalls += ActorDrawCalls;

			FTriContributor Contributor;
			Contributor.Name = Actor->GetActorNameOrLabel();
			Contributor.Triangles = ActorTriangles;
			Contributor.LODUsed = BestLOD;
			Contributor.Distance = FVector::Dist(Viewpoint, Origin);
			Contributors.Add(MoveTemp(Contributor));
		}
	}

	// Sort contributors by triangle count descending
	Contributors.Sort([](const FTriContributor& A, const FTriContributor& B)
	{
		return A.Triangles > B.Triangles;
	});

	// Top 20 contributors
	TArray<TSharedPtr<FJsonValue>> TopArr;
	int32 TopCount = FMath::Min(Contributors.Num(), 20);
	for (int32 i = 0; i < TopCount; ++i)
	{
		auto ContribObj = MakeShared<FJsonObject>();
		ContribObj->SetStringField(TEXT("actor"), Contributors[i].Name);
		ContribObj->SetNumberField(TEXT("triangles"), static_cast<double>(Contributors[i].Triangles));
		ContribObj->SetNumberField(TEXT("lod_used"), Contributors[i].LODUsed);
		ContribObj->SetNumberField(TEXT("distance"), Contributors[i].Distance);
		TopArr.Add(MakeShared<FJsonValueObject>(ContribObj));
	}

	bool bOverBudget = TotalVisibleTriangles > Budget;
	double UsagePct = (Budget > 0) ? (static_cast<double>(TotalVisibleTriangles) / static_cast<double>(Budget) * 100.0) : 0.0;

	auto Result = MakeShared<FJsonObject>();
	Result->SetArrayField(TEXT("viewpoint"), VectorToJsonArray(Viewpoint));
	Result->SetNumberField(TEXT("fov"), FOV);
	Result->SetNumberField(TEXT("budget"), static_cast<double>(Budget));
	Result->SetNumberField(TEXT("visible_triangles"), static_cast<double>(TotalVisibleTriangles));
	Result->SetNumberField(TEXT("visible_actors"), VisibleActorCount);
	Result->SetNumberField(TEXT("visible_draw_calls"), VisibleDrawCalls);
	Result->SetBoolField(TEXT("over_budget"), bOverBudget);
	Result->SetNumberField(TEXT("budget_usage_pct"), UsagePct);
	Result->SetArrayField(TEXT("top_contributors"), TopArr);
	Result->SetStringField(TEXT("note"), TEXT("Conservative: no occlusion culling, no dynamic batching, LOD-aware. ISM instances multiply triangles but not draw calls."));

	return FMonolithActionResult::Success(Result);
}
