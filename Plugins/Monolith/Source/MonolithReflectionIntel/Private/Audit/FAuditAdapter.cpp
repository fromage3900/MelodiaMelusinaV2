// SPDX-License-Identifier: MIT
// Plan: Plugins/Monolith/Docs/plans/2026-05-28-reflection-intelligence.md (Phase 4a — v0.17.0).
//
// FAuditAdapter — implementation. Four audit handlers registered against
// existing namespaces (material / niagara / blueprint / project). All run on
// the game thread, all read-only.
//
// Cursor codec mirrored from FCppReflectQueryAdapter / FNetworkQueryAdapter.
// Consolidation into MonolithCore is Phase 5+ work.

#include "Audit/FAuditAdapter.h"
#include "MonolithReflectionIntelModule.h"
#include "Shared/RICursorCodec.h"

#include "AssetRegistry/ARFilter.h"
#include "AssetRegistry/AssetData.h"
#include "AssetRegistry/AssetRegistryModule.h"
#include "AssetRegistry/IAssetRegistry.h"

#include "Dom/JsonObject.h"
#include "Dom/JsonValue.h"
#include "Engine/Blueprint.h"
#include "Misc/Base64.h"
#include "Modules/ModuleManager.h"
#include "MonolithJsonUtils.h"
#include "MonolithParamSchema.h"
#include "Serialization/JsonReader.h"
#include "Serialization/JsonSerializer.h"
#include "Serialization/JsonWriter.h"
#include "SQLiteDatabase.h"
#include "Templates/TypeHash.h"
#include "UObject/Class.h"
#include "UObject/Object.h"
#include "UObject/TopLevelAssetPath.h"
#include "UObject/UObjectGlobals.h"
#include "UObject/UnrealType.h"

namespace
{
	// Cursor codec + filter-hash hoisted to Private/Shared/RICursorCodec.{h,cpp}
	// to avoid unity-build collisions across the six query adapters. See that
	// header for rationale. Wire format / behaviour unchanged.

	/** Pop the AssetRegistry. LoadModuleChecked is the canonical idiom — same
	 *  as FAssetGraphJoiner uses. */
	IAssetRegistry& GetAssetRegistry()
	{
		FAssetRegistryModule& ARModule =
			FModuleManager::LoadModuleChecked<FAssetRegistryModule>(TEXT("AssetRegistry"));
		return ARModule.Get();
	}

	/** True iff the package name looks like a `/Game/...` content asset (not engine /
	 *  not script / not memory). */
	bool IsContentPackage(const FString& PackageNameStr)
	{
		if (PackageNameStr.IsEmpty()) { return false; }
		if (PackageNameStr.StartsWith(TEXT("/Script/"))) { return false; }
		if (PackageNameStr.StartsWith(TEXT("/Engine/"))) { return false; }
		if (PackageNameStr.StartsWith(TEXT("/Memory/"))) { return false; }
		return true;
	}

	/** Pull the bare native-class name (no /Script/ prefix) out of an
	 *  FTopLevelAssetPath. Returns FString() for non-script paths. */
	FString ExtractNativeClassNameFromTopLevel(const FTopLevelAssetPath& Path)
	{
		const FString PathStr = Path.ToString();
		if (PathStr.IsEmpty() || !PathStr.StartsWith(TEXT("/Script/")))
		{
			return FString();
		}
		const int32 DotIdx = PathStr.Find(TEXT("."), ESearchCase::CaseSensitive,
			ESearchDir::FromStart, 8);
		if (DotIdx == INDEX_NONE) { return FString(); }
		return PathStr.Mid(DotIdx + 1);
	}
}

// ============================================================================
// Registration — registers 4 actions ACROSS 4 existing namespaces.
// ============================================================================

void FAuditAdapter::RegisterActions(FMonolithToolRegistry& Registry)
{
	// ---- material_query("audit_orphan_materials") ----
	Registry.RegisterAction(TEXT("material"), TEXT("audit_orphan_materials"),
		TEXT("Audit: list /Game/.../*.uasset materials with zero IAssetRegistry "
		     "referencers (no other asset references this material). Useful as a "
		     "pre-release cleanup audit. Excludes /Engine/* + /Memory/* packages "
		     "by default. Read-only. Cursor pagination."),
		FMonolithActionHandler::CreateStatic(&FAuditAdapter::HandleAuditOrphanMaterials),
		FParamSchemaBuilder()
			.Optional(TEXT("limit"), TEXT("integer"),
				TEXT("Max rows per page (default 50, hard cap 200)"), TEXT("50"))
			.Optional(TEXT("cursor"), TEXT("string"),
				TEXT("Opaque pagination cursor"))
			.Build());

	// ---- niagara_query("audit_cross_asset_refs") ----
	Registry.RegisterAction(TEXT("niagara"), TEXT("audit_cross_asset_refs"),
		TEXT("Audit: list Niagara systems whose native class instance_of edge in "
		     "cpp_asset_edges points at a class name NOT present in "
		     "reflect_uclasses. Surfaces post-rename / post-removal dangling "
		     "class references in Niagara assets. Composed on Phase 3a tables. "
		     "Read-only. Cursor pagination."),
		FMonolithActionHandler::CreateStatic(&FAuditAdapter::HandleAuditNiagaraCrossAssetRefs),
		FParamSchemaBuilder()
			.Optional(TEXT("limit"), TEXT("integer"),
				TEXT("Max rows per page (default 50, hard cap 200)"), TEXT("50"))
			.Optional(TEXT("cursor"), TEXT("string"),
				TEXT("Opaque pagination cursor"))
			.Build());

	// ---- blueprint_query("audit_cdo_drift") ----
	Registry.RegisterAction(TEXT("blueprint"), TEXT("audit_cdo_drift"),
		TEXT("Audit: surface Blueprint child CDOs whose property defaults differ "
		     "from the immediate native parent UCLASS's CDO defaults. Walks all "
		     "/Game/.../*.uasset Blueprints; for each, compares every CPF_BlueprintVisible "
		     "FProperty's ExportText form between BP CDO and native-parent CDO. "
		     "Read-only. Cursor pagination."),
		FMonolithActionHandler::CreateStatic(&FAuditAdapter::HandleAuditCdoDrift),
		FParamSchemaBuilder()
			.Optional(TEXT("class_filter"), TEXT("string"),
				TEXT("Optional native-parent class name to restrict the scan"))
			.Optional(TEXT("limit"), TEXT("integer"),
				TEXT("Max rows per page (default 50, hard cap 200)"), TEXT("50"))
			.Optional(TEXT("cursor"), TEXT("string"),
				TEXT("Opaque pagination cursor"))
			.Build());

	// ---- project_query("audit_orphan_assets") ----
	Registry.RegisterAction(TEXT("project"), TEXT("audit_orphan_assets"),
		TEXT("Audit: list /Game/.../*.uasset assets with ZERO IAssetRegistry "
		     "referencers AND zero entries in cpp_asset_edges. Strictest orphan "
		     "signal — useful for pre-release cleanup. Excludes /Engine/* + "
		     "/Memory/* packages. Read-only. Cursor pagination."),
		FMonolithActionHandler::CreateStatic(&FAuditAdapter::HandleAuditOrphanAssets),
		FParamSchemaBuilder()
			.Optional(TEXT("asset_class_filter"), TEXT("string"),
				TEXT("Optional bare class name filter (e.g. 'Material', 'Texture2D')"))
			.Optional(TEXT("limit"), TEXT("integer"),
				TEXT("Max rows per page (default 50, hard cap 200)"), TEXT("50"))
			.Optional(TEXT("cursor"), TEXT("string"),
				TEXT("Opaque pagination cursor"))
			.Build());

	// NO dispatcher annotation rewrites — those are owned by the namespaces'
	// primary host modules (MonolithMaterial / MonolithNiagara / MonolithBlueprint
	// / MonolithIndex). Adding an action preserves existing annotations because
	// SetDispatcherAnnotations is namespace-scoped, not action-scoped.
}

// ============================================================================
// DB accessor
// ============================================================================

FSQLiteDatabase* FAuditAdapter::GetRawDB()
{
	ensure(IsInGameThread());

	FMonolithReflectionIntelModule* Module =
		FModuleManager::GetModulePtr<FMonolithReflectionIntelModule>(
			TEXT("MonolithReflectionIntel"));
	if (!Module) { return nullptr; }
	return Module->GetOrOpenCachedQueryDb();
}

// ============================================================================
// Handler — material_query("audit_orphan_materials")
// ============================================================================

FMonolithActionResult FAuditAdapter::HandleAuditOrphanMaterials(const TSharedPtr<FJsonObject>& Params)
{
	const int32 ReqLimit = Params->HasField(TEXT("limit"))
		? static_cast<int32>(Params->GetNumberField(TEXT("limit"))) : 50;
	const FString CursorIn = Params->HasField(TEXT("cursor"))
		? Params->GetStringField(TEXT("cursor")) : FString();

	constexpr int32 HARD_CAP = 200;
	const int32 Limit = FMath::Clamp(ReqLimit, 1, HARD_CAP);
	const uint32 FilterHash = RIComputeFilterHash({});

	int32 Page = 0;
	const bool bHasCursor = !CursorIn.IsEmpty();
	if (bHasCursor)
	{
		FRICursorState State;
		if (!DecodeRICursor(CursorIn, State))
		{
			return RIInvalidCursorError(TEXT("Cursor decode failed; restart pagination without `cursor`."));
		}
		if (State.QueryHash != FilterHash)
		{
			return RIInvalidCursorError(TEXT("Cursor filter mismatch; restart pagination without `cursor`."));
		}
		Page = State.Page;
	}

	IAssetRegistry& AR = GetAssetRegistry();

	// Enumerate all material / material-instance assets. We accept the bare
	// class names "Material", "MaterialInstanceConstant", and
	// "MaterialFunction" — the three primary material-asset shapes the project
	// ships. Bare-name matching against AssetClassPath's tail-token avoids
	// hard-linking against /Script/Engine.Material in this audit module.
	TArray<FAssetData> AllAssets;
	if (!AR.GetAllAssets(AllAssets, /*bIncludeOnlyOnDiskAssets=*/false))
	{
		return FMonolithActionResult::Error(TEXT("IAssetRegistry::GetAllAssets failed"));
	}

	TArray<TSharedPtr<FJsonValue>> Orphans;
	int32 Considered = 0;
	int32 Visited = 0;
	const int32 SkipBefore = Page * Limit;

	for (const FAssetData& Asset : AllAssets)
	{
		const FString PackageNameStr = Asset.PackageName.ToString();
		if (!IsContentPackage(PackageNameStr)) { continue; }

		const FString BareClass = ExtractNativeClassNameFromTopLevel(Asset.AssetClassPath);
		const bool bIsMaterialAsset =
			BareClass.Equals(TEXT("Material"), ESearchCase::CaseSensitive) ||
			BareClass.Equals(TEXT("MaterialInstanceConstant"), ESearchCase::CaseSensitive) ||
			BareClass.Equals(TEXT("MaterialFunction"), ESearchCase::CaseSensitive) ||
			BareClass.Equals(TEXT("MaterialFunctionInstance"), ESearchCase::CaseSensitive);
		if (!bIsMaterialAsset) { continue; }

		++Considered;

		TArray<FName> Referencers;
		AR.GetReferencers(Asset.PackageName, Referencers);
		if (Referencers.Num() > 0) { continue; }

		// Orphan — page through.
		if (Visited++ < SkipBefore) { continue; }
		if (Orphans.Num() >= Limit) { break; }

		TSharedPtr<FJsonObject> R = MakeShared<FJsonObject>();
		R->SetStringField(TEXT("asset_path"), PackageNameStr);
		R->SetStringField(TEXT("asset_class"), BareClass);
		R->SetStringField(TEXT("violation"),
			TEXT("Material has zero referencers in the asset graph — candidate for removal."));
		Orphans.Add(MakeShared<FJsonValueObject>(R));
	}

	TSharedPtr<FJsonObject> Out = MakeShared<FJsonObject>();
	Out->SetArrayField(TEXT("orphans"), Orphans);
	if (!bHasCursor)
	{
		Out->SetNumberField(TEXT("considered"), Considered);
	}

	if (Orphans.Num() == Limit)
	{
		FRICursorState OutCursor;
		OutCursor.QueryHash = FilterHash;
		OutCursor.Page = Page + 1;
		OutCursor.CachedTotalEstimate = -1;
		Out->SetStringField(TEXT("next_cursor"), EncodeRICursor(OutCursor));
	}
	return FMonolithActionResult::Success(Out);
}

// ============================================================================
// Handler — niagara_query("audit_cross_asset_refs")
// ============================================================================

FMonolithActionResult FAuditAdapter::HandleAuditNiagaraCrossAssetRefs(const TSharedPtr<FJsonObject>& Params)
{
	FSQLiteDatabase* DB = GetRawDB();
	if (!DB)
	{
		return FMonolithActionResult::Error(
			TEXT("EngineSource.db not available. Run source.trigger_reindex to bootstrap, "
			     "or build the project at least once so UHT artefacts exist."));
	}

	const int32 ReqLimit = Params->HasField(TEXT("limit"))
		? static_cast<int32>(Params->GetNumberField(TEXT("limit"))) : 50;
	const FString CursorIn = Params->HasField(TEXT("cursor"))
		? Params->GetStringField(TEXT("cursor")) : FString();

	constexpr int32 HARD_CAP = 200;
	const int32 Limit = FMath::Clamp(ReqLimit, 1, HARD_CAP);
	const uint32 FilterHash = RIComputeFilterHash({});

	int32 Page = 0;
	const bool bHasCursor = !CursorIn.IsEmpty();
	if (bHasCursor)
	{
		FRICursorState State;
		if (!DecodeRICursor(CursorIn, State))
		{
			return RIInvalidCursorError(TEXT("Cursor decode failed; restart pagination without `cursor`."));
		}
		if (State.QueryHash != FilterHash)
		{
			return RIInvalidCursorError(TEXT("Cursor filter mismatch; restart pagination without `cursor`."));
		}
		Page = State.Page;
	}

	// Anti-join: assets whose cpp_class edge in cpp_asset_edges does NOT have a
	// matching row in reflect_uclasses. Restricted to Niagara-shape class names
	// (NiagaraSystem, NiagaraEmitter, NiagaraScript). Phase 3a's cpp_asset_edges
	// only emits `instance_of` edges right now (Phase 3b will add references_class).
	// Phase 4a uses only instance_of for the cross-ref audit.
	const TCHAR* Sql = TEXT(
		"SELECT e.cpp_class, e.asset_path, e.edge_kind "
		"FROM cpp_asset_edges e "
		"LEFT JOIN reflect_uclasses c "
		"  ON c.class_name = e.cpp_class "
		"WHERE c.class_name IS NULL "
		"  AND (e.cpp_class LIKE 'Niagara%' "
		"    OR e.cpp_class LIKE 'UNiagara%' "
		"    OR e.cpp_class LIKE 'ANiagara%') "
		"ORDER BY e.cpp_class, e.asset_path "
		"LIMIT ? OFFSET ?;");

	FSQLitePreparedStatement Stmt;
	if (!Stmt.Create(*DB, Sql))
	{
		return FMonolithActionResult::Error(TEXT("SELECT prepare failed (cpp_asset_edges absent?)."));
	}
	Stmt.SetBindingValueByIndex(1, Limit);
	Stmt.SetBindingValueByIndex(2, Page * Limit);

	TArray<TSharedPtr<FJsonValue>> Rows;
	while (Stmt.Step() == ESQLitePreparedStatementStepResult::Row)
	{
		FString CppClass, AssetPath, EdgeKind;
		Stmt.GetColumnValueByIndex(0, CppClass);
		Stmt.GetColumnValueByIndex(1, AssetPath);
		Stmt.GetColumnValueByIndex(2, EdgeKind);

		TSharedPtr<FJsonObject> R = MakeShared<FJsonObject>();
		R->SetStringField(TEXT("asset_path"), AssetPath);
		R->SetStringField(TEXT("missing_cpp_class"), CppClass);
		R->SetStringField(TEXT("edge_kind"), EdgeKind);
		R->SetStringField(TEXT("violation"),
			TEXT("Niagara asset references a C++ class not present in the reflection index — class likely renamed/removed."));
		Rows.Add(MakeShared<FJsonValueObject>(R));
	}

	TSharedPtr<FJsonObject> Out = MakeShared<FJsonObject>();
	Out->SetArrayField(TEXT("violations"), Rows);

	if (Rows.Num() == Limit)
	{
		FRICursorState OutCursor;
		OutCursor.QueryHash = FilterHash;
		OutCursor.Page = Page + 1;
		OutCursor.CachedTotalEstimate = -1;
		Out->SetStringField(TEXT("next_cursor"), EncodeRICursor(OutCursor));
	}
	return FMonolithActionResult::Success(Out);
}

// ============================================================================
// Handler — blueprint_query("audit_cdo_drift")
// ============================================================================

FMonolithActionResult FAuditAdapter::HandleAuditCdoDrift(const TSharedPtr<FJsonObject>& Params)
{
	const FString ClassFilter = Params->HasField(TEXT("class_filter"))
		? Params->GetStringField(TEXT("class_filter")) : FString();
	const int32 ReqLimit = Params->HasField(TEXT("limit"))
		? static_cast<int32>(Params->GetNumberField(TEXT("limit"))) : 50;
	const FString CursorIn = Params->HasField(TEXT("cursor"))
		? Params->GetStringField(TEXT("cursor")) : FString();

	constexpr int32 HARD_CAP = 200;
	const int32 Limit = FMath::Clamp(ReqLimit, 1, HARD_CAP);
	const uint32 FilterHash = RIComputeFilterHash({ ClassFilter });

	int32 Page = 0;
	const bool bHasCursor = !CursorIn.IsEmpty();
	if (bHasCursor)
	{
		FRICursorState State;
		if (!DecodeRICursor(CursorIn, State))
		{
			return RIInvalidCursorError(TEXT("Cursor decode failed; restart pagination without `cursor`."));
		}
		if (State.QueryHash != FilterHash)
		{
			return RIInvalidCursorError(TEXT("Cursor filter mismatch; restart pagination without `cursor`."));
		}
		Page = State.Page;
	}

	IAssetRegistry& AR = GetAssetRegistry();

	// Enumerate all Blueprint assets in /Game/. Then per asset:
	//   1. Resolve generated UClass.
	//   2. Find its native (C++) super by walking GetSuperClass() chain until we
	//      hit one that is NOT in UBlueprintGeneratedClass family.
	//   3. Compare CDO property values via FProperty::ExportText_InContainer
	//      between BP CDO and native CDO. Any mismatch is a drift row.
	// Phase 4a flags ANY CPF_Edit-eligible (EditAnywhere/EditDefaultsOnly) drift;
	// callers can downscope via class_filter.
	TArray<FAssetData> AllAssets;
	{
		FARFilter Filter;
		Filter.ClassPaths.Add(UBlueprint::StaticClass()->GetClassPathName());
		Filter.bRecursiveClasses = true;
		Filter.PackagePaths.Add(TEXT("/Game"));
		Filter.bRecursivePaths = true;
		AR.GetAssets(Filter, AllAssets);
	}

	TArray<TSharedPtr<FJsonValue>> DriftRows;
	int32 Visited = 0;
	const int32 SkipBefore = Page * Limit;
	int32 Scanned = 0;

	for (const FAssetData& Asset : AllAssets)
	{
		if (DriftRows.Num() >= Limit) { break; }

		UBlueprint* BP = Cast<UBlueprint>(Asset.GetAsset());
		if (!BP || !BP->GeneratedClass) { continue; }

		UClass* GenClass = BP->GeneratedClass;
		// Walk up the chain until we hit a NATIVE class — the first super whose
		// IsNative() is true. This is the native parent we'll diff against.
		UClass* NativeSuper = GenClass->GetSuperClass();
		while (NativeSuper && !NativeSuper->IsNative())
		{
			NativeSuper = NativeSuper->GetSuperClass();
		}
		if (!NativeSuper) { continue; }

		if (!ClassFilter.IsEmpty() && !NativeSuper->GetName().Equals(ClassFilter, ESearchCase::IgnoreCase))
		{
			continue;
		}

		UObject* BpCdo     = GenClass->GetDefaultObject(/*bCreateIfNeeded=*/false);
		UObject* NativeCdo = NativeSuper->GetDefaultObject(/*bCreateIfNeeded=*/false);
		if (!BpCdo || !NativeCdo) { continue; }

		++Scanned;

		// Iterate native parent's properties so we only compare props that
		// exist on both sides (Blueprint-added vars are not in the parent
		// chain). Restrict to Edit-visible properties to avoid false positives
		// on internal state / transient defaults.
		for (TFieldIterator<FProperty> It(NativeSuper); It; ++It)
		{
			FProperty* Prop = *It;
			if (!Prop) { continue; }
			// Skip transient + native-only state.
			const bool bIsEditVisible =
				(Prop->PropertyFlags & (CPF_Edit | CPF_BlueprintVisible | CPF_BlueprintAssignable)) != 0;
			if (!bIsEditVisible) { continue; }
			if (Prop->HasAnyPropertyFlags(CPF_Transient)) { continue; }

			FString NativeStr;
			FString BpStr;
			Prop->ExportText_InContainer(/*ArrayIdx=*/0, NativeStr, NativeCdo, NativeCdo, nullptr, PPF_None);
			Prop->ExportText_InContainer(/*ArrayIdx=*/0, BpStr,     BpCdo,     BpCdo,     nullptr, PPF_None);
			if (NativeStr.Equals(BpStr, ESearchCase::CaseSensitive)) { continue; }

			if (Visited++ < SkipBefore) { continue; }
			if (DriftRows.Num() >= Limit) { break; }

			TSharedPtr<FJsonObject> R = MakeShared<FJsonObject>();
			R->SetStringField(TEXT("blueprint_path"), Asset.PackageName.ToString());
			R->SetStringField(TEXT("native_parent"), NativeSuper->GetName());
			R->SetStringField(TEXT("property_name"), Prop->GetName());
			R->SetStringField(TEXT("native_default"), NativeStr);
			R->SetStringField(TEXT("blueprint_default"), BpStr);
			DriftRows.Add(MakeShared<FJsonValueObject>(R));
		}
	}

	TSharedPtr<FJsonObject> Out = MakeShared<FJsonObject>();
	Out->SetArrayField(TEXT("drift"), DriftRows);
	if (!bHasCursor)
	{
		Out->SetNumberField(TEXT("blueprints_scanned"), Scanned);
	}

	if (DriftRows.Num() == Limit)
	{
		FRICursorState OutCursor;
		OutCursor.QueryHash = FilterHash;
		OutCursor.Page = Page + 1;
		OutCursor.CachedTotalEstimate = -1;
		Out->SetStringField(TEXT("next_cursor"), EncodeRICursor(OutCursor));
	}
	return FMonolithActionResult::Success(Out);
}

// ============================================================================
// Handler — project_query("audit_orphan_assets")
// ============================================================================

FMonolithActionResult FAuditAdapter::HandleAuditOrphanAssets(const TSharedPtr<FJsonObject>& Params)
{
	FSQLiteDatabase* DB = GetRawDB();
	// DB is OPTIONAL for this audit — if cpp_asset_edges is absent, we still
	// run the asset-registry-only side of the orphan check.

	const FString AssetClassFilter = Params->HasField(TEXT("asset_class_filter"))
		? Params->GetStringField(TEXT("asset_class_filter")) : FString();
	const int32 ReqLimit = Params->HasField(TEXT("limit"))
		? static_cast<int32>(Params->GetNumberField(TEXT("limit"))) : 50;
	const FString CursorIn = Params->HasField(TEXT("cursor"))
		? Params->GetStringField(TEXT("cursor")) : FString();

	constexpr int32 HARD_CAP = 200;
	const int32 Limit = FMath::Clamp(ReqLimit, 1, HARD_CAP);
	const uint32 FilterHash = RIComputeFilterHash({ AssetClassFilter });

	int32 Page = 0;
	const bool bHasCursor = !CursorIn.IsEmpty();
	if (bHasCursor)
	{
		FRICursorState State;
		if (!DecodeRICursor(CursorIn, State))
		{
			return RIInvalidCursorError(TEXT("Cursor decode failed; restart pagination without `cursor`."));
		}
		if (State.QueryHash != FilterHash)
		{
			return RIInvalidCursorError(TEXT("Cursor filter mismatch; restart pagination without `cursor`."));
		}
		Page = State.Page;
	}

	IAssetRegistry& AR = GetAssetRegistry();

	TArray<FAssetData> AllAssets;
	if (!AR.GetAllAssets(AllAssets, /*bIncludeOnlyOnDiskAssets=*/false))
	{
		return FMonolithActionResult::Error(TEXT("IAssetRegistry::GetAllAssets failed"));
	}

	// Pre-build a set of asset paths that appear on the LEFT side of
	// cpp_asset_edges. If the DB isn't available the set is empty and we
	// fall back to AR-only orphan detection.
	TSet<FString> CppEdgePaths;
	if (DB)
	{
		FSQLitePreparedStatement EdgeStmt;
		if (EdgeStmt.Create(*DB, TEXT("SELECT DISTINCT asset_path FROM cpp_asset_edges;")))
		{
			while (EdgeStmt.Step() == ESQLitePreparedStatementStepResult::Row)
			{
				FString P;
				EdgeStmt.GetColumnValueByIndex(0, P);
				if (!P.IsEmpty()) { CppEdgePaths.Add(P); }
			}
		}
	}

	TArray<TSharedPtr<FJsonValue>> Orphans;
	int32 Visited = 0;
	int32 Scanned = 0;
	const int32 SkipBefore = Page * Limit;

	for (const FAssetData& Asset : AllAssets)
	{
		const FString PackageNameStr = Asset.PackageName.ToString();
		if (!IsContentPackage(PackageNameStr)) { continue; }

		const FString BareClass = ExtractNativeClassNameFromTopLevel(Asset.AssetClassPath);
		if (!AssetClassFilter.IsEmpty()
		    && !BareClass.Equals(AssetClassFilter, ESearchCase::IgnoreCase))
		{
			continue;
		}

		++Scanned;

		TArray<FName> Referencers;
		AR.GetReferencers(Asset.PackageName, Referencers);
		if (Referencers.Num() > 0) { continue; }

		// Strict orphan = no AR referrer AND no cpp_asset_edges entry referring
		// to this asset path.
		if (CppEdgePaths.Contains(PackageNameStr)) { continue; }

		if (Visited++ < SkipBefore) { continue; }
		if (Orphans.Num() >= Limit) { break; }

		TSharedPtr<FJsonObject> R = MakeShared<FJsonObject>();
		R->SetStringField(TEXT("asset_path"), PackageNameStr);
		R->SetStringField(TEXT("asset_class"), BareClass);
		R->SetStringField(TEXT("violation"),
			TEXT("Asset has zero AR referrers AND no cpp_asset_edges entry — candidate for removal."));
		Orphans.Add(MakeShared<FJsonValueObject>(R));
	}

	TSharedPtr<FJsonObject> Out = MakeShared<FJsonObject>();
	Out->SetArrayField(TEXT("orphans"), Orphans);
	if (!bHasCursor)
	{
		Out->SetNumberField(TEXT("assets_scanned"), Scanned);
	}

	if (Orphans.Num() == Limit)
	{
		FRICursorState OutCursor;
		OutCursor.QueryHash = FilterHash;
		OutCursor.Page = Page + 1;
		OutCursor.CachedTotalEstimate = -1;
		Out->SetStringField(TEXT("next_cursor"), EncodeRICursor(OutCursor));
	}
	return FMonolithActionResult::Success(Out);
}
