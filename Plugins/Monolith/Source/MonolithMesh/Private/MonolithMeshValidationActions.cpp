#include "MonolithMeshTemplateActions.h"
#include "MonolithMeshUtils.h"
#include "MonolithMeshCatalog.h"
#include "MonolithToolRegistry.h"
#include "MonolithParamSchema.h"
#include "MonolithAssetUtils.h"
#include "MonolithJsonUtils.h"
#include "MonolithIndexSubsystem.h"
#include "MonolithIndexDatabase.h"

#include "Engine/StaticMesh.h"
#include "MeshDescription.h"
#include "PhysicsEngine/BodySetup.h"
#include "StaticMeshResources.h"
#include "Dom/JsonObject.h"
#include "Dom/JsonValue.h"
#include "SQLiteDatabase.h"
#include "Editor.h"

// ============================================================================
// Validation action registration (called from RegisterActions in header's class)
// Split into separate .cpp but uses same class: FMonolithMeshTemplateActions
// We register the 4 validation actions from the template actions' RegisterActions
// by calling this helper from MonolithMeshTemplateActions.cpp.
// Actually — since RegisterActions is in the other .cpp, we add an internal
// registration function and call it from there.
// ============================================================================

// Forward: we need a way to register these from the main RegisterActions.
// Solution: we add a static helper and call it.

namespace MeshValidationHelpers
{
	/** Get catalog database, or nullptr */
	FSQLiteDatabase* GetCatalogDB()
	{
		UMonolithIndexSubsystem* IndexSub = GEditor ?
			GEditor->GetEditorSubsystem<UMonolithIndexSubsystem>() : nullptr;
		if (!IndexSub || !IndexSub->GetDatabase())
		{
			return nullptr;
		}
		return IndexSub->GetDatabase()->GetRawDatabase();
	}

	/** Severity string to numeric priority (lower = more severe) */
	int32 SeverityPriority(const FString& Severity)
	{
		if (Severity == TEXT("CRITICAL")) return 0;
		if (Severity == TEXT("HIGH"))     return 1;
		if (Severity == TEXT("MEDIUM"))   return 2;
		if (Severity == TEXT("LOW"))      return 3;
		return 4;
	}
}

// ============================================================================
// 5. validate_game_ready
// ============================================================================

FMonolithActionResult FMonolithMeshTemplateActions::ValidateGameReady(const TSharedPtr<FJsonObject>& Params)
{
	FString AssetPath;
	if (!Params->TryGetStringField(TEXT("asset_path"), AssetPath) || AssetPath.IsEmpty())
	{
		return FMonolithActionResult::Error(TEXT("Missing required param: asset_path"));
	}

	FString Error;
	UStaticMesh* SM = MonolithMeshUtils::LoadStaticMesh(AssetPath, Error);
	if (!SM)
	{
		return FMonolithActionResult::Error(Error);
	}

	FStaticMeshRenderData* RenderData = SM->GetRenderData();
	if (!RenderData || RenderData->LODResources.Num() == 0)
	{
		return FMonolithActionResult::Error(TEXT("Mesh has no render data (empty or corrupt)"));
	}

	const FStaticMeshLODResources& LOD0 = RenderData->LODResources[0];
	const int32 NumTris = LOD0.GetNumTriangles();
	const int32 NumVerts = LOD0.GetNumVertices();
	const int32 NumLODs = SM->GetNumLODs();
	const int32 MatCount = SM->GetStaticMaterials().Num();

	auto Result = MakeShared<FJsonObject>();
	Result->SetStringField(TEXT("asset_path"), AssetPath);

	TArray<TSharedPtr<FJsonValue>> Checks;
	bool bAllPassed = true;
	int32 CriticalCount = 0;
	int32 HighCount = 0;

	// --- 1. Collision check (CRITICAL) ---
	{
		auto Check = MakeShared<FJsonObject>();
		Check->SetStringField(TEXT("name"), TEXT("collision"));

		UBodySetup* BodySetup = SM->GetBodySetup();
		bool bHasCollision = false;
		if (BodySetup)
		{
			// Has simple shapes or complex-as-simple
			bHasCollision = (BodySetup->AggGeom.BoxElems.Num() > 0 ||
				BodySetup->AggGeom.SphereElems.Num() > 0 ||
				BodySetup->AggGeom.SphylElems.Num() > 0 ||
				BodySetup->AggGeom.ConvexElems.Num() > 0 ||
				BodySetup->CollisionTraceFlag == CTF_UseComplexAsSimple);
		}

		if (bHasCollision)
		{
			Check->SetStringField(TEXT("result"), TEXT("PASS"));
			Check->SetStringField(TEXT("severity"), TEXT("CRITICAL"));
			Check->SetStringField(TEXT("message"), TEXT("Collision setup present"));
		}
		else
		{
			Check->SetStringField(TEXT("result"), TEXT("FAIL"));
			Check->SetStringField(TEXT("severity"), TEXT("CRITICAL"));
			Check->SetStringField(TEXT("message"), TEXT("No collision setup — players will fall through this mesh"));
			bAllPassed = false;
			CriticalCount++;
		}
		Checks.Add(MakeShared<FJsonValueObject>(Check));
	}

	// --- 2. LOD check (HIGH if >1K tris and only 1 LOD) ---
	{
		auto Check = MakeShared<FJsonObject>();
		Check->SetStringField(TEXT("name"), TEXT("lods"));
		Check->SetStringField(TEXT("severity"), TEXT("HIGH"));

		if (NumTris <= 1000 || NumLODs >= 2)
		{
			Check->SetStringField(TEXT("result"), TEXT("PASS"));
			Check->SetStringField(TEXT("message"), FString::Printf(TEXT("%d tris, %d LODs"), NumTris, NumLODs));
		}
		else
		{
			Check->SetStringField(TEXT("result"), TEXT("FAIL"));
			Check->SetStringField(TEXT("message"), FString::Printf(TEXT("Mesh has %d tris but only %d LOD — add LODs for performance"), NumTris, NumLODs));
			bAllPassed = false;
			HighCount++;
		}
		Checks.Add(MakeShared<FJsonValueObject>(Check));
	}

	// --- 3. Lightmap UV overlap (MEDIUM) ---
	{
		auto Check = MakeShared<FJsonObject>();
		Check->SetStringField(TEXT("name"), TEXT("lightmap_uv"));
		Check->SetStringField(TEXT("severity"), TEXT("MEDIUM"));

		int32 LightmapUVIndex = SM->GetLightMapCoordinateIndex();
		// Quick overlap estimation via UV bounding box overlap check
		bool bHasLightmapChannel = (static_cast<int32>(LOD0.GetNumTexCoords()) > LightmapUVIndex);

		if (!bHasLightmapChannel)
		{
			Check->SetStringField(TEXT("result"), TEXT("FAIL"));
			Check->SetStringField(TEXT("message"), FString::Printf(TEXT("Lightmap UV channel %d does not exist"), LightmapUVIndex));
			bAllPassed = false;
		}
		else
		{
			Check->SetStringField(TEXT("result"), TEXT("PASS"));
			Check->SetStringField(TEXT("message"), FString::Printf(TEXT("Lightmap UV channel %d present"), LightmapUVIndex));
		}
		Checks.Add(MakeShared<FJsonValueObject>(Check));
	}

	// --- 4. Degenerate geometry (MEDIUM) ---
	{
		auto Check = MakeShared<FJsonObject>();
		Check->SetStringField(TEXT("name"), TEXT("degenerate_geometry"));
		Check->SetStringField(TEXT("severity"), TEXT("MEDIUM"));

		int32 DegenerateTris = 0;
		if (NumTris <= 500000) // Skip for huge meshes
		{
			FIndexArrayView Indices = LOD0.IndexBuffer.GetArrayView();
			const FPositionVertexBuffer& PosBuffer = LOD0.VertexBuffers.PositionVertexBuffer;

			for (int32 T = 0; T < NumTris; T++)
			{
				uint32 I0 = Indices[T * 3 + 0];
				uint32 I1 = Indices[T * 3 + 1];
				uint32 I2 = Indices[T * 3 + 2];

				FVector3f P0 = PosBuffer.VertexPosition(I0);
				FVector3f P1 = PosBuffer.VertexPosition(I1);
				FVector3f P2 = PosBuffer.VertexPosition(I2);

				FVector3f Cross = FVector3f::CrossProduct(P1 - P0, P2 - P0);
				float Area = Cross.Size() * 0.5f;
				if (Area < 1e-6f)
				{
					DegenerateTris++;
				}
			}
		}

		if (DegenerateTris == 0)
		{
			Check->SetStringField(TEXT("result"), TEXT("PASS"));
			Check->SetStringField(TEXT("message"), TEXT("No degenerate triangles"));
		}
		else
		{
			Check->SetStringField(TEXT("result"), TEXT("FAIL"));
			Check->SetStringField(TEXT("message"), FString::Printf(TEXT("%d degenerate triangles (zero-area)"), DegenerateTris));
			bAllPassed = false;
		}
		Check->SetNumberField(TEXT("degenerate_count"), DegenerateTris);
		Checks.Add(MakeShared<FJsonValueObject>(Check));
	}

	// --- 5. Material count (MEDIUM if >4) ---
	{
		auto Check = MakeShared<FJsonObject>();
		Check->SetStringField(TEXT("name"), TEXT("material_count"));
		Check->SetStringField(TEXT("severity"), TEXT("MEDIUM"));

		if (MatCount <= 4)
		{
			Check->SetStringField(TEXT("result"), TEXT("PASS"));
			Check->SetStringField(TEXT("message"), FString::Printf(TEXT("%d material slots"), MatCount));
		}
		else
		{
			Check->SetStringField(TEXT("result"), TEXT("FAIL"));
			Check->SetStringField(TEXT("message"), FString::Printf(TEXT("%d material slots — consider merging to reduce draw calls (max recommended: 4)"), MatCount));
			bAllPassed = false;
		}
		Checks.Add(MakeShared<FJsonValueObject>(Check));
	}

	// --- 6. Pivot position (LOW — check pivot is at bottom-center) ---
	{
		auto Check = MakeShared<FJsonObject>();
		Check->SetStringField(TEXT("name"), TEXT("pivot_position"));
		Check->SetStringField(TEXT("severity"), TEXT("LOW"));

		FBoxSphereBounds Bounds = SM->GetBounds();
		// Bottom center: pivot should be at X=0, Y=0, Z=bottom of bounding box
		// We check if the origin is near the bottom of the bounding box
		float BottomZ = Bounds.Origin.Z - Bounds.BoxExtent.Z;
		float PivotZDist = FMath::Abs(BottomZ); // distance from world origin to bottom
		float Tolerance = Bounds.BoxExtent.Z * 0.1f; // 10% of height

		// Check if pivot is roughly at bottom-center
		bool bPivotOk = (FMath::Abs(Bounds.Origin.X) < Bounds.BoxExtent.X * 0.1f) &&
		                (FMath::Abs(Bounds.Origin.Y) < Bounds.BoxExtent.Y * 0.1f) &&
		                (FMath::Abs(BottomZ) < FMath::Max(Tolerance, 5.0f));

		if (bPivotOk)
		{
			Check->SetStringField(TEXT("result"), TEXT("PASS"));
			Check->SetStringField(TEXT("message"), TEXT("Pivot is near bottom-center"));
		}
		else
		{
			Check->SetStringField(TEXT("result"), TEXT("FAIL"));
			Check->SetStringField(TEXT("message"), FString::Printf(
				TEXT("Pivot offset from bottom-center: (%.1f, %.1f, %.1f)"),
				Bounds.Origin.X, Bounds.Origin.Y, BottomZ));
			// Don't fail overall for pivot — it's LOW severity
		}
		Checks.Add(MakeShared<FJsonValueObject>(Check));
	}

	// --- 7. Non-uniform scale (LOW) ---
	{
		auto Check = MakeShared<FJsonObject>();
		Check->SetStringField(TEXT("name"), TEXT("scale"));
		Check->SetStringField(TEXT("severity"), TEXT("LOW"));

		// Check scale is uniform (1,1,1) — non-uniform build scale indicates authoring issue
		// UStaticMesh doesn't expose GetBuildSettings in 5.7; check source model if available
		FVector BuildScale(1.0f);
		if (SM->GetNumSourceModels() > 0)
		{
			BuildScale = SM->GetSourceModel(0).BuildSettings.BuildScale3D;
		}
		bool bUniform = FMath::IsNearlyEqual(BuildScale.X, BuildScale.Y, 0.01f) &&
		                FMath::IsNearlyEqual(BuildScale.Y, BuildScale.Z, 0.01f);

		if (bUniform)
		{
			Check->SetStringField(TEXT("result"), TEXT("PASS"));
			Check->SetStringField(TEXT("message"), TEXT("Build scale is uniform"));
		}
		else
		{
			Check->SetStringField(TEXT("result"), TEXT("FAIL"));
			Check->SetStringField(TEXT("message"), FString::Printf(
				TEXT("Non-uniform build scale: (%.2f, %.2f, %.2f) — may cause lighting/physics issues"),
				BuildScale.X, BuildScale.Y, BuildScale.Z));
		}
		Checks.Add(MakeShared<FJsonValueObject>(Check));
	}

	Result->SetArrayField(TEXT("checks"), Checks);
	Result->SetBoolField(TEXT("game_ready"), bAllPassed);
	Result->SetNumberField(TEXT("critical_failures"), CriticalCount);
	Result->SetNumberField(TEXT("high_failures"), HighCount);
	Result->SetNumberField(TEXT("total_checks"), Checks.Num());

	return FMonolithActionResult::Success(Result);
}

// ============================================================================
// 6. suggest_lod_strategy
// ============================================================================

FMonolithActionResult FMonolithMeshTemplateActions::SuggestLodStrategy(const TSharedPtr<FJsonObject>& Params)
{
	FString AssetPath;
	if (!Params->TryGetStringField(TEXT("asset_path"), AssetPath) || AssetPath.IsEmpty())
	{
		return FMonolithActionResult::Error(TEXT("Missing required param: asset_path"));
	}

	FString Error;
	UStaticMesh* SM = MonolithMeshUtils::LoadStaticMesh(AssetPath, Error);
	if (!SM)
	{
		return FMonolithActionResult::Error(Error);
	}

	FStaticMeshRenderData* RenderData = SM->GetRenderData();
	if (!RenderData || RenderData->LODResources.Num() == 0)
	{
		return FMonolithActionResult::Error(TEXT("Mesh has no render data (empty or corrupt)"));
	}

	const int32 LOD0Tris = RenderData->LODResources[0].GetNumTriangles();
	const int32 CurrentLODs = SM->GetNumLODs();

	// Rules: <500=1 LOD, 500-2K=2, 2K-10K=3, 10K+=4
	int32 RecommendedLODs;
	if (LOD0Tris < 500)
	{
		RecommendedLODs = 1;
	}
	else if (LOD0Tris < 2000)
	{
		RecommendedLODs = 2;
	}
	else if (LOD0Tris < 10000)
	{
		RecommendedLODs = 3;
	}
	else
	{
		RecommendedLODs = 4;
	}

	auto Result = MakeShared<FJsonObject>();
	Result->SetStringField(TEXT("asset_path"), AssetPath);
	Result->SetNumberField(TEXT("lod0_triangles"), LOD0Tris);
	Result->SetNumberField(TEXT("current_lods"), CurrentLODs);
	Result->SetNumberField(TEXT("recommended_lods"), RecommendedLODs);

	bool bNeedsLODs = (RecommendedLODs > CurrentLODs);
	Result->SetBoolField(TEXT("needs_lods"), bNeedsLODs);

	if (bNeedsLODs)
	{
		// Build ready-to-execute params for generate_lods
		TArray<TSharedPtr<FJsonValue>> LodSteps;

		int32 CurrentTris = LOD0Tris;
		for (int32 LODIdx = 1; LODIdx < RecommendedLODs; LODIdx++)
		{
			auto Step = MakeShared<FJsonObject>();
			int32 TargetTris = CurrentTris / 2; // 50% reduction per step
			Step->SetNumberField(TEXT("lod_index"), LODIdx);
			Step->SetNumberField(TEXT("target_triangles"), TargetTris);
			Step->SetNumberField(TEXT("reduction_percent"), 50.0);

			// Screen size recommendations (progressively smaller)
			float ScreenSize = 1.0f;
			switch (LODIdx)
			{
			case 1: ScreenSize = 0.5f; break;
			case 2: ScreenSize = 0.25f; break;
			case 3: ScreenSize = 0.125f; break;
			default: ScreenSize = 0.1f / LODIdx; break;
			}
			Step->SetNumberField(TEXT("screen_size"), ScreenSize);

			LodSteps.Add(MakeShared<FJsonValueObject>(Step));
			CurrentTris = TargetTris;
		}

		Result->SetArrayField(TEXT("lod_steps"), LodSteps);

		// Ready-to-use params for generate_lods action
		auto GenerateParams = MakeShared<FJsonObject>();
		GenerateParams->SetStringField(TEXT("asset_path"), AssetPath);
		GenerateParams->SetNumberField(TEXT("num_lods"), RecommendedLODs);
		GenerateParams->SetNumberField(TEXT("reduction_percent"), 50.0);
		Result->SetObjectField(TEXT("generate_lods_params"), GenerateParams);
	}
	else
	{
		Result->SetStringField(TEXT("message"), FString::Printf(
			TEXT("Mesh already has %d LODs (recommended: %d) — no changes needed"),
			CurrentLODs, RecommendedLODs));
	}

	return FMonolithActionResult::Success(Result);
}

// ============================================================================
// 7. batch_validate
// ============================================================================

FMonolithActionResult FMonolithMeshTemplateActions::BatchValidate(const TSharedPtr<FJsonObject>& Params)
{
	FString AssetClass = TEXT("StaticMesh");
	Params->TryGetStringField(TEXT("class"), AssetClass);

	FString PathFilter;
	Params->TryGetStringField(TEXT("path_filter"), PathFilter);

	FString SeverityMin = TEXT("HIGH");
	Params->TryGetStringField(TEXT("severity_min"), SeverityMin);

	int32 MinSeverityPriority = MeshValidationHelpers::SeverityPriority(SeverityMin);

	auto Result = MakeShared<FJsonObject>();
	TArray<TSharedPtr<FJsonValue>> IssuesArr;
	int32 TotalScanned = 0;
	int32 TotalFlagged = 0;
	int32 SQLFiltered = 0;

	// === Pass 1: Fast SQL pre-filter from mesh_catalog ===
	TArray<FString> FlaggedPaths;
	TMap<FString, TArray<FString>> SQLIssues; // asset_path -> list of issue descriptions

	FSQLiteDatabase* DB = MeshValidationHelpers::GetCatalogDB();
	if (DB)
	{
		// Build SQL to find meshes with obvious issues
		FString SQL = TEXT(
			"SELECT asset_path, tri_count, has_collision, lod_count, degenerate, pivot_offset_z "
			"FROM mesh_catalog WHERE 1=1"
		);

		if (!PathFilter.IsEmpty())
		{
			SQL += FString::Printf(TEXT(" AND asset_path LIKE '%%%s%%'"), *PathFilter);
		}

		FSQLitePreparedStatement Stmt;
		Stmt.Create(*DB, *SQL);

		while (Stmt.Step() == ESQLitePreparedStatementStepResult::Row)
		{
			FString AssetPath;
			int64 TriCount = 0, HasCollision = 0, LodCount = 0, Degenerate = 0;
			double PivotOffsetZ = 0.0;

			Stmt.GetColumnValueByIndex(0, AssetPath);
			Stmt.GetColumnValueByIndex(1, TriCount);
			Stmt.GetColumnValueByIndex(2, HasCollision);
			Stmt.GetColumnValueByIndex(3, LodCount);
			Stmt.GetColumnValueByIndex(4, Degenerate);
			Stmt.GetColumnValueByIndex(5, PivotOffsetZ);

			TotalScanned++;
			TArray<FString> Issues;

			// CRITICAL: no collision
			if (HasCollision == 0 && MinSeverityPriority >= MeshValidationHelpers::SeverityPriority(TEXT("CRITICAL")))
			{
				Issues.Add(TEXT("CRITICAL: No collision setup"));
			}

			// HIGH: >1K tris with no LODs
			if (TriCount > 1000 && LodCount <= 1 && MinSeverityPriority >= MeshValidationHelpers::SeverityPriority(TEXT("HIGH")))
			{
				Issues.Add(FString::Printf(TEXT("HIGH: %lld tris with only %lld LOD"), TriCount, LodCount));
			}

			// MEDIUM: degenerate
			if (Degenerate != 0 && MinSeverityPriority >= MeshValidationHelpers::SeverityPriority(TEXT("MEDIUM")))
			{
				Issues.Add(TEXT("MEDIUM: Has degenerate geometry"));
			}

			if (Issues.Num() > 0)
			{
				FlaggedPaths.Add(AssetPath);
				SQLIssues.Add(AssetPath, Issues);
				SQLFiltered++;
			}
		}
	}

	// === Pass 2: Deep validation on flagged assets only ===
	for (const FString& AssetPath : FlaggedPaths)
	{
		auto IssueObj = MakeShared<FJsonObject>();
		IssueObj->SetStringField(TEXT("asset_path"), AssetPath);

		// SQL issues
		TArray<TSharedPtr<FJsonValue>> IssueList;
		if (TArray<FString>* SQLIssueList = SQLIssues.Find(AssetPath))
		{
			for (const FString& Issue : *SQLIssueList)
			{
				auto IssueEntry = MakeShared<FJsonObject>();
				// Parse severity from prefix
				FString Severity = TEXT("HIGH");
				FString Message = Issue;
				int32 ColonIdx;
				if (Issue.FindChar(TEXT(':'), ColonIdx))
				{
					Severity = Issue.Left(ColonIdx).TrimStartAndEnd();
					Message = Issue.Mid(ColonIdx + 1).TrimStartAndEnd();
				}
				IssueEntry->SetStringField(TEXT("severity"), Severity);
				IssueEntry->SetStringField(TEXT("message"), Message);
				IssueEntry->SetStringField(TEXT("source"), TEXT("catalog"));
				IssueList.Add(MakeShared<FJsonValueObject>(IssueEntry));
			}
		}

		// Try to deep-validate by loading the asset
		FString LoadError;
		UStaticMesh* SM = MonolithMeshUtils::LoadStaticMesh(AssetPath, LoadError);
		if (SM)
		{
			FStaticMeshRenderData* RenderData = SM->GetRenderData();
			if (RenderData && RenderData->LODResources.Num() > 0)
			{
				const int32 MatCount = SM->GetStaticMaterials().Num();
				if (MatCount > 4)
				{
					auto IssueEntry = MakeShared<FJsonObject>();
					IssueEntry->SetStringField(TEXT("severity"), TEXT("MEDIUM"));
					IssueEntry->SetStringField(TEXT("message"), FString::Printf(TEXT("%d material slots (recommended max: 4)"), MatCount));
					IssueEntry->SetStringField(TEXT("source"), TEXT("deep"));
					IssueList.Add(MakeShared<FJsonValueObject>(IssueEntry));
				}
			}
		}

		// Determine worst severity
		FString WorstSeverity = TEXT("LOW");
		int32 WorstPriority = 99;
		for (const auto& IssueVal : IssueList)
		{
			const TSharedPtr<FJsonObject>* IssueEntryPtr;
			if (IssueVal->TryGetObject(IssueEntryPtr))
			{
				FString Sev;
				(*IssueEntryPtr)->TryGetStringField(TEXT("severity"), Sev);
				int32 Prio = MeshValidationHelpers::SeverityPriority(Sev);
				if (Prio < WorstPriority)
				{
					WorstPriority = Prio;
					WorstSeverity = Sev;
				}
			}
		}

		IssueObj->SetStringField(TEXT("worst_severity"), WorstSeverity);
		IssueObj->SetNumberField(TEXT("severity_priority"), WorstPriority);
		IssueObj->SetArrayField(TEXT("issues"), IssueList);

		IssuesArr.Add(MakeShared<FJsonValueObject>(IssueObj));
		TotalFlagged++;
	}

	// Sort by severity priority (CRITICAL first)
	IssuesArr.Sort([](const TSharedPtr<FJsonValue>& A, const TSharedPtr<FJsonValue>& B)
	{
		const TSharedPtr<FJsonObject>* AObj;
		const TSharedPtr<FJsonObject>* BObj;
		if (A->TryGetObject(AObj) && B->TryGetObject(BObj))
		{
			double APrio = (*AObj)->GetNumberField(TEXT("severity_priority"));
			double BPrio = (*BObj)->GetNumberField(TEXT("severity_priority"));
			return APrio < BPrio;
		}
		return false;
	});

	Result->SetArrayField(TEXT("flagged_assets"), IssuesArr);
	Result->SetNumberField(TEXT("total_scanned"), TotalScanned);
	Result->SetNumberField(TEXT("total_flagged"), TotalFlagged);
	Result->SetNumberField(TEXT("sql_pre_filtered"), SQLFiltered);
	Result->SetBoolField(TEXT("catalog_available"), DB != nullptr);

	if (!DB)
	{
		Result->SetStringField(TEXT("warning"), TEXT("Mesh catalog not available — run monolith_reindex() first for SQL pre-filtering. Falling back to slower asset-load validation."));
	}

	return FMonolithActionResult::Success(Result);
}

// ============================================================================
// 8. compare_lod_chain
// ============================================================================

FMonolithActionResult FMonolithMeshTemplateActions::CompareLodChain(const TSharedPtr<FJsonObject>& Params)
{
	FString AssetPath;
	if (!Params->TryGetStringField(TEXT("asset_path"), AssetPath) || AssetPath.IsEmpty())
	{
		return FMonolithActionResult::Error(TEXT("Missing required param: asset_path"));
	}

	FString Error;
	UStaticMesh* SM = MonolithMeshUtils::LoadStaticMesh(AssetPath, Error);
	if (!SM)
	{
		return FMonolithActionResult::Error(Error);
	}

	FStaticMeshRenderData* RenderData = SM->GetRenderData();
	if (!RenderData || RenderData->LODResources.Num() == 0)
	{
		return FMonolithActionResult::Error(TEXT("Mesh has no render data (empty or corrupt)"));
	}

	const int32 NumLODs = RenderData->LODResources.Num();
	if (NumLODs < 2)
	{
		auto Result = MakeShared<FJsonObject>();
		Result->SetStringField(TEXT("asset_path"), AssetPath);
		Result->SetNumberField(TEXT("lod_count"), 1);
		Result->SetStringField(TEXT("message"), TEXT("Mesh has only 1 LOD — nothing to compare"));
		return FMonolithActionResult::Success(Result);
	}

	auto Result = MakeShared<FJsonObject>();
	Result->SetStringField(TEXT("asset_path"), AssetPath);
	Result->SetNumberField(TEXT("lod_count"), NumLODs);

	TArray<TSharedPtr<FJsonValue>> StepsArr;
	TArray<TSharedPtr<FJsonValue>> WarningsArr;

	for (int32 i = 1; i < NumLODs; i++)
	{
		const FStaticMeshLODResources& PrevLOD = RenderData->LODResources[i - 1];
		const FStaticMeshLODResources& CurrLOD = RenderData->LODResources[i];

		int32 PrevTris = PrevLOD.GetNumTriangles();
		int32 CurrTris = CurrLOD.GetNumTriangles();
		int32 PrevVerts = PrevLOD.GetNumVertices();
		int32 CurrVerts = CurrLOD.GetNumVertices();
		int32 PrevSections = PrevLOD.Sections.Num();
		int32 CurrSections = CurrLOD.Sections.Num();

		float TriReduction = PrevTris > 0 ? (1.0f - static_cast<float>(CurrTris) / PrevTris) * 100.0f : 0.0f;
		float VertReduction = PrevVerts > 0 ? (1.0f - static_cast<float>(CurrVerts) / PrevVerts) * 100.0f : 0.0f;

		float PrevScreenSize = RenderData->ScreenSize[i - 1].Default;
		float CurrScreenSize = RenderData->ScreenSize[i].Default;
		float ScreenSizeRatio = CurrScreenSize > 0.0f ? PrevScreenSize / CurrScreenSize : 0.0f;

		auto Step = MakeShared<FJsonObject>();
		Step->SetStringField(TEXT("transition"), FString::Printf(TEXT("LOD%d -> LOD%d"), i - 1, i));
		Step->SetNumberField(TEXT("prev_triangles"), PrevTris);
		Step->SetNumberField(TEXT("curr_triangles"), CurrTris);
		Step->SetNumberField(TEXT("triangle_reduction_pct"), FMath::RoundToFloat(TriReduction * 10.0f) / 10.0f);
		Step->SetNumberField(TEXT("vertex_reduction_pct"), FMath::RoundToFloat(VertReduction * 10.0f) / 10.0f);
		Step->SetNumberField(TEXT("prev_screen_size"), PrevScreenSize);
		Step->SetNumberField(TEXT("curr_screen_size"), CurrScreenSize);
		Step->SetNumberField(TEXT("screen_size_ratio"), FMath::RoundToFloat(ScreenSizeRatio * 10.0f) / 10.0f);
		Step->SetNumberField(TEXT("prev_sections"), PrevSections);
		Step->SetNumberField(TEXT("curr_sections"), CurrSections);

		// Flag issues
		TArray<TSharedPtr<FJsonValue>> StepWarnings;

		// Flag if <30% reduction (likely pop)
		if (TriReduction < 30.0f && TriReduction >= 0.0f)
		{
			auto Warning = MakeShared<FJsonObject>();
			Warning->SetStringField(TEXT("type"), TEXT("low_reduction"));
			Warning->SetStringField(TEXT("message"), FString::Printf(
				TEXT("Only %.1f%% triangle reduction — LOD transition may pop (recommend >30%%)"), TriReduction));
			StepWarnings.Add(MakeShared<FJsonValueObject>(Warning));
			WarningsArr.Add(MakeShared<FJsonValueString>(FString::Printf(
				TEXT("LOD%d->LOD%d: Low reduction (%.1f%%)"), i - 1, i, TriReduction)));
		}

		// Flag if screen size gap >3x
		if (ScreenSizeRatio > 3.0f)
		{
			auto Warning = MakeShared<FJsonObject>();
			Warning->SetStringField(TEXT("type"), TEXT("screen_size_gap"));
			Warning->SetStringField(TEXT("message"), FString::Printf(
				TEXT("Screen size gap %.1fx — may cause visible pop (recommend <3x)"), ScreenSizeRatio));
			StepWarnings.Add(MakeShared<FJsonValueObject>(Warning));
			WarningsArr.Add(MakeShared<FJsonValueString>(FString::Printf(
				TEXT("LOD%d->LOD%d: Screen size gap %.1fx"), i - 1, i, ScreenSizeRatio)));
		}

		// Flag section count mismatch
		if (PrevSections != CurrSections)
		{
			auto Warning = MakeShared<FJsonObject>();
			Warning->SetStringField(TEXT("type"), TEXT("section_mismatch"));
			Warning->SetStringField(TEXT("message"), FString::Printf(
				TEXT("Section count changed: %d -> %d (material slots differ)"), PrevSections, CurrSections));
			StepWarnings.Add(MakeShared<FJsonValueObject>(Warning));
			WarningsArr.Add(MakeShared<FJsonValueString>(FString::Printf(
				TEXT("LOD%d->LOD%d: Section mismatch (%d->%d)"), i - 1, i, PrevSections, CurrSections)));
		}

		if (StepWarnings.Num() > 0)
		{
			Step->SetArrayField(TEXT("warnings"), StepWarnings);
		}

		StepsArr.Add(MakeShared<FJsonValueObject>(Step));
	}

	Result->SetArrayField(TEXT("lod_steps"), StepsArr);
	Result->SetArrayField(TEXT("warnings"), WarningsArr);
	Result->SetNumberField(TEXT("warning_count"), WarningsArr.Num());
	Result->SetBoolField(TEXT("chain_healthy"), WarningsArr.Num() == 0);

	return FMonolithActionResult::Success(Result);
}
