#include "MonolithAIAdvancedActions.h"
#include "MonolithParamSchema.h"
#include "MonolithAssetUtils.h"

#if WITH_MASSENTITY
#include "MassEntityConfigAsset.h"
#include "MassEntityTraitBase.h"
#include "MassProcessingPhaseManager.h"
#include "MassProcessor.h"
#include "MassEntitySubsystem.h"
#include "MassArchetypeTypes.h"

#include "AssetRegistry/AssetRegistryModule.h"
#include "UObject/UObjectIterator.h"
#include "UObject/Package.h"
#include "ScopedTransaction.h"
#include "Editor.h"
#include "Engine/World.h"

#if WITH_ZONEGRAPH
#include "ZoneGraphSubsystem.h"
#include "ZoneGraphTypes.h"
#include "ZoneGraphQuery.h"
#include "ZoneGraphData.h"
#include "EngineUtils.h"
#endif // WITH_ZONEGRAPH

// ============================================================
//  Helpers
// ============================================================

namespace
{
	UMassEntityConfigAsset* LoadMassConfigFromParams(const TSharedPtr<FJsonObject>& Params, FString& OutAssetPath, FString& OutError)
	{
		OutAssetPath = Params->GetStringField(TEXT("asset_path"));
		if (OutAssetPath.IsEmpty())
		{
			OutError = TEXT("Missing required param 'asset_path'");
			return nullptr;
		}
		OutAssetPath = FMonolithAssetUtils::ResolveAssetPath(OutAssetPath);

		UMassEntityConfigAsset* Config = FMonolithAssetUtils::LoadAssetByPath<UMassEntityConfigAsset>(OutAssetPath);
		if (!Config)
		{
			OutError = FString::Printf(TEXT("MassEntityConfigAsset not found at '%s'"), *OutAssetPath);
		}
		return Config;
	}

	/** Serialize a single trait to JSON via reflection. */
	TSharedPtr<FJsonObject> SerializeTrait(const UMassEntityTraitBase* Trait)
	{
		TSharedPtr<FJsonObject> Obj = MakeShared<FJsonObject>();
		Obj->SetStringField(TEXT("class_name"), Trait->GetClass()->GetName());
		Obj->SetStringField(TEXT("display_name"), Trait->GetClass()->GetDisplayNameText().ToString());

		// Collect UPROPERTY values
		TSharedPtr<FJsonObject> Props = MakeShared<FJsonObject>();
		for (TFieldIterator<FProperty> It(Trait->GetClass(), EFieldIteratorFlags::ExcludeSuper); It; ++It)
		{
			FString ValueStr;
			It->ExportTextItem_Direct(ValueStr, It->ContainerPtrToValuePtr<void>(Trait), nullptr, nullptr, PPF_None);
			Props->SetStringField(It->GetName(), ValueStr);
		}
		if (Props->Values.Num() > 0)
		{
			Obj->SetObjectField(TEXT("properties"), Props);
		}

		return Obj;
	}
}

#endif // WITH_MASSENTITY

// ============================================================
//  Registration
// ============================================================

void FMonolithAIAdvancedActions::RegisterActions(FMonolithToolRegistry& Registry)
{
#if WITH_MASSENTITY

	// 219. list_mass_entity_configs
	Registry.RegisterAction(TEXT("ai"), TEXT("list_mass_entity_configs"),
		TEXT("List all UMassEntityConfigAsset assets in the project"),
		FMonolithActionHandler::CreateStatic(&HandleListMassEntityConfigs),
		FParamSchemaBuilder()
			.OptionalAssetPath(TEXT("path_filter"), TEXT("Only include assets under this path prefix"))
			.Build());

	// 220. get_mass_entity_config
	Registry.RegisterAction(TEXT("ai"), TEXT("get_mass_entity_config"),
		TEXT("Inspect a MassEntityConfigAsset: traits, fragments, parent config"),
		FMonolithActionHandler::CreateStatic(&HandleGetMassEntityConfig),
		FParamSchemaBuilder()
			.RequiredAssetPath(TEXT("asset_path"), TEXT("MassEntityConfigAsset asset path"))
			.Build());

	// 221. create_mass_entity_config
	Registry.RegisterAction(TEXT("ai"), TEXT("create_mass_entity_config"),
		TEXT("Create a new MassEntityConfigAsset"),
		FMonolithActionHandler::CreateStatic(&HandleCreateMassEntityConfig),
		FParamSchemaBuilder()
			.RequiredAssetPath(TEXT("save_path"), TEXT("Asset save path (e.g. /Game/AI/Mass/MEC_Zombie)"))
			.Optional(TEXT("name"), TEXT("string"), TEXT("Asset name (derived from save_path if omitted)"))
			.Optional(TEXT("parent_config"), TEXT("string"), TEXT("Parent config asset path to inherit from"))
			.Build());

	// 222. add_mass_trait
	Registry.RegisterAction(TEXT("ai"), TEXT("add_mass_trait"),
		TEXT("Add a trait to a MassEntityConfigAsset"),
		FMonolithActionHandler::CreateStatic(&HandleAddMassTrait),
		FParamSchemaBuilder()
			.RequiredAssetPath(TEXT("asset_path"), TEXT("MassEntityConfigAsset asset path"))
			.Required(TEXT("trait_class"), TEXT("string"), TEXT("Trait class name (e.g. UMassMovementTrait)"))
			.Optional(TEXT("properties"), TEXT("object"), TEXT("JSON object of property_name->value pairs to set on the trait"))
			.Build());

	// 223. remove_mass_trait
	Registry.RegisterAction(TEXT("ai"), TEXT("remove_mass_trait"),
		TEXT("Remove a trait from a MassEntityConfigAsset"),
		FMonolithActionHandler::CreateStatic(&HandleRemoveMassTrait),
		FParamSchemaBuilder()
			.RequiredAssetPath(TEXT("asset_path"), TEXT("MassEntityConfigAsset asset path"))
			.Required(TEXT("trait_class"), TEXT("string"), TEXT("Trait class name to remove"))
			.Build());

	// 224. list_mass_traits
	Registry.RegisterAction(TEXT("ai"), TEXT("list_mass_traits"),
		TEXT("List all available UMassEntityTraitBase subclasses"),
		FMonolithActionHandler::CreateStatic(&HandleListMassTraits),
		FParamSchemaBuilder().Build());

	// 225. list_mass_processors
	Registry.RegisterAction(TEXT("ai"), TEXT("list_mass_processors"),
		TEXT("List all registered UMassProcessor subclasses"),
		FMonolithActionHandler::CreateStatic(&HandleListMassProcessors),
		FParamSchemaBuilder().Build());

	// 226. validate_mass_entity_config
	Registry.RegisterAction(TEXT("ai"), TEXT("validate_mass_entity_config"),
		TEXT("Validate a MassEntityConfigAsset: check trait compatibility, missing fragments, duplicates"),
		FMonolithActionHandler::CreateStatic(&HandleValidateMassEntityConfig),
		FParamSchemaBuilder()
			.RequiredAssetPath(TEXT("asset_path"), TEXT("MassEntityConfigAsset asset path"))
			.Build());

	// 230. get_mass_entity_stats
	Registry.RegisterAction(TEXT("ai"), TEXT("get_mass_entity_stats"),
		TEXT("Get runtime MassEntity statistics: archetype counts, entity totals (requires PIE)"),
		FMonolithActionHandler::CreateStatic(&HandleGetMassEntityStats),
		FParamSchemaBuilder().Build());

#if WITH_ZONEGRAPH
	// 227. list_zone_graphs
	Registry.RegisterAction(TEXT("ai"), TEXT("list_zone_graphs"),
		TEXT("Enumerate ZoneGraphData actors in loaded levels"),
		FMonolithActionHandler::CreateStatic(&HandleListZoneGraphs),
		FParamSchemaBuilder()
			.Optional(TEXT("level"), TEXT("string"), TEXT("Level name filter"))
			.Build());

	// 228. query_zone_lanes
	Registry.RegisterAction(TEXT("ai"), TEXT("query_zone_lanes"),
		TEXT("Spatial query for zone graph lanes near a world location"),
		FMonolithActionHandler::CreateStatic(&HandleQueryZoneLanes),
		FParamSchemaBuilder()
			.Required(TEXT("location"), TEXT("object"), TEXT("World location {x, y, z}"))
			.Optional(TEXT("radius"), TEXT("number"), TEXT("Search radius (default 1000)"))
			.Optional(TEXT("tag_filter"), TEXT("string"), TEXT("Gameplay tag filter for lane tags"))
			.Build());

	// 229. get_zone_lane_info
	Registry.RegisterAction(TEXT("ai"), TEXT("get_zone_lane_info"),
		TEXT("Get detailed info about a specific zone graph lane by handle index"),
		FMonolithActionHandler::CreateStatic(&HandleGetZoneLaneInfo),
		FParamSchemaBuilder()
			.Required(TEXT("lane_handle"), TEXT("number"), TEXT("Lane handle index"))
			.Build());
#endif // WITH_ZONEGRAPH

#endif // WITH_MASSENTITY
}

// ============================================================
//  Implementations (all inside WITH_MASSENTITY)
// ============================================================

#if WITH_MASSENTITY

// 219. list_mass_entity_configs
FMonolithActionResult FMonolithAIAdvancedActions::HandleListMassEntityConfigs(const TSharedPtr<FJsonObject>& Params)
{
	FString PathFilter = Params->GetStringField(TEXT("path_filter"));

	IAssetRegistry& AR = FModuleManager::LoadModuleChecked<FAssetRegistryModule>(TEXT("AssetRegistry")).Get();

	TArray<FAssetData> Assets;
	AR.GetAssetsByClass(UMassEntityConfigAsset::StaticClass()->GetClassPathName(), Assets);

	TArray<TSharedPtr<FJsonValue>> ResultArr;
	for (const FAssetData& Asset : Assets)
	{
		FString AssetPathStr = Asset.GetObjectPathString();
		if (!PathFilter.IsEmpty() && !AssetPathStr.StartsWith(PathFilter))
		{
			continue;
		}

		TSharedPtr<FJsonObject> Entry = MakeShared<FJsonObject>();
		Entry->SetStringField(TEXT("asset_path"), Asset.PackageName.ToString());
		Entry->SetStringField(TEXT("name"), Asset.AssetName.ToString());
		ResultArr.Add(MakeShared<FJsonValueObject>(Entry));
	}

	TSharedPtr<FJsonObject> Result = MakeShared<FJsonObject>();
	Result->SetArrayField(TEXT("configs"), ResultArr);
	Result->SetNumberField(TEXT("count"), ResultArr.Num());
	return FMonolithActionResult::Success(Result);
}

// 220. get_mass_entity_config
FMonolithActionResult FMonolithAIAdvancedActions::HandleGetMassEntityConfig(const TSharedPtr<FJsonObject>& Params)
{
	FString AssetPath, Error;
	UMassEntityConfigAsset* Config = LoadMassConfigFromParams(Params, AssetPath, Error);
	if (!Config) return FMonolithActionResult::Error(Error);

	TSharedPtr<FJsonObject> Result = MakeShared<FJsonObject>();
	Result->SetStringField(TEXT("asset_path"), AssetPath);

	const FMassEntityConfig& EntityConfig = Config->GetConfig();

	// Parent config
	if (const UMassEntityConfigAsset* ParentConfig = EntityConfig.GetParent())
	{
		Result->SetStringField(TEXT("parent_config"), ParentConfig->GetPathName());
	}

	// Traits
	TArray<TSharedPtr<FJsonValue>> TraitArr;
	for (const UMassEntityTraitBase* Trait : EntityConfig.GetTraits())
	{
		if (Trait)
		{
			TraitArr.Add(MakeShared<FJsonValueObject>(SerializeTrait(Trait)));
		}
	}
	Result->SetArrayField(TEXT("traits"), TraitArr);
	Result->SetNumberField(TEXT("trait_count"), TraitArr.Num());

	return FMonolithActionResult::Success(Result);
}

// 221. create_mass_entity_config
FMonolithActionResult FMonolithAIAdvancedActions::HandleCreateMassEntityConfig(const TSharedPtr<FJsonObject>& Params)
{
	FString SavePath = Params->GetStringField(TEXT("save_path"));
	if (SavePath.IsEmpty())
	{
		return FMonolithActionResult::Error(TEXT("Missing required param 'save_path'"));
	}
	SavePath = FMonolithAssetUtils::ResolveAssetPath(SavePath);

	FString AssetName = Params->GetStringField(TEXT("name"));
	if (AssetName.IsEmpty())
	{
		AssetName = FPackageName::GetShortName(SavePath);
	}

	FString PackagePath = SavePath;
	if (FPackageName::GetShortName(PackagePath) != AssetName)
	{
		PackagePath = SavePath / AssetName;
	}

	FString PathErr;
	if (!MonolithAI::EnsureAssetPathFree(PackagePath, AssetName, PathErr))
	{
		return FMonolithActionResult::Error(PathErr);
	}

	FScopedTransaction Transaction(FText::FromString(TEXT("Monolith: Create MassEntityConfig")));

	UPackage* Package = CreatePackage(*PackagePath);
	if (!Package)
	{
		return FMonolithActionResult::Error(FString::Printf(TEXT("Failed to create package at '%s'"), *PackagePath));
	}

	UMassEntityConfigAsset* NewConfig = NewObject<UMassEntityConfigAsset>(Package, *AssetName, RF_Public | RF_Standalone);
	if (!NewConfig)
	{
		return FMonolithActionResult::Error(TEXT("Failed to create UMassEntityConfigAsset"));
	}

	// Set parent config if provided
	FString ParentConfigPath = Params->GetStringField(TEXT("parent_config"));
	if (!ParentConfigPath.IsEmpty())
	{
		ParentConfigPath = FMonolithAssetUtils::ResolveAssetPath(ParentConfigPath);
		UMassEntityConfigAsset* ParentConfig = FMonolithAssetUtils::LoadAssetByPath<UMassEntityConfigAsset>(ParentConfigPath);
		if (ParentConfig)
		{
			NewConfig->GetMutableConfig().SetParentAsset(*ParentConfig);
		}
		else
		{
			return FMonolithActionResult::Error(FString::Printf(TEXT("Parent config not found at '%s'"), *ParentConfigPath));
		}
	}

	NewConfig->MarkPackageDirty();
	FAssetRegistryModule::AssetCreated(NewConfig);

	TSharedPtr<FJsonObject> Result = MakeShared<FJsonObject>();
	Result->SetStringField(TEXT("asset_path"), PackagePath);
	Result->SetStringField(TEXT("message"), FString::Printf(TEXT("Created MassEntityConfigAsset '%s'"), *AssetName));
	return FMonolithActionResult::Success(Result);
}

// 222. add_mass_trait
FMonolithActionResult FMonolithAIAdvancedActions::HandleAddMassTrait(const TSharedPtr<FJsonObject>& Params)
{
	FString AssetPath, Error;
	UMassEntityConfigAsset* Config = LoadMassConfigFromParams(Params, AssetPath, Error);
	if (!Config) return FMonolithActionResult::Error(Error);

	FString TraitClassName;
	FMonolithActionResult ErrResult;
	if (!MonolithAI::RequireStringParam(Params, TEXT("trait_class"), TraitClassName, ErrResult))
	{
		return ErrResult;
	}

	// Find the trait class via reflection
	UClass* TraitClass = FindFirstObject<UClass>(*TraitClassName, EFindFirstObjectOptions::EnsureIfAmbiguous);
	if (!TraitClass)
	{
		TraitClass = FindFirstObject<UClass>(*(TEXT("U") + TraitClassName), EFindFirstObjectOptions::EnsureIfAmbiguous);
	}
	if (!TraitClass || !TraitClass->IsChildOf(UMassEntityTraitBase::StaticClass()))
	{
		return FMonolithActionResult::Error(FString::Printf(
			TEXT("Trait class '%s' not found or not a UMassEntityTraitBase subclass"), *TraitClassName));
	}

	FScopedTransaction Transaction(FText::FromString(TEXT("Monolith: Add Mass Trait")));

	UMassEntityTraitBase* NewTrait = NewObject<UMassEntityTraitBase>(Config, TraitClass);
	if (!NewTrait)
	{
		return FMonolithActionResult::Error(TEXT("Failed to instantiate trait"));
	}

	// Set properties if provided
	const TSharedPtr<FJsonObject>* PropertiesPtr = nullptr;
	if (Params->TryGetObjectField(TEXT("properties"), PropertiesPtr) && PropertiesPtr && PropertiesPtr->IsValid())
	{
		TArray<FString> PropWarnings;
		for (const auto& Pair : (*PropertiesPtr)->Values)
		{
			FProperty* Prop = TraitClass->FindPropertyByName(*Pair.Key);
			if (!Prop)
			{
				PropWarnings.Add(FString::Printf(TEXT("Property '%s' not found on %s"), *Pair.Key, *TraitClass->GetName()));
				continue;
			}
			void* PropAddr = Prop->ContainerPtrToValuePtr<void>(NewTrait);
			FString ValueStr;
			if (Pair.Value->Type == EJson::String) ValueStr = Pair.Value->AsString();
			else if (Pair.Value->Type == EJson::Number) ValueStr = FString::SanitizeFloat(Pair.Value->AsNumber());
			else if (Pair.Value->Type == EJson::Boolean) ValueStr = Pair.Value->AsBool() ? TEXT("true") : TEXT("false");

			Prop->ImportText_Direct(*ValueStr, PropAddr, NewTrait, PPF_None);
		}
	}

	Config->GetMutableConfig().AddTrait(*NewTrait);
	Config->MarkPackageDirty();

	TSharedPtr<FJsonObject> Result = MakeShared<FJsonObject>();
	Result->SetStringField(TEXT("asset_path"), AssetPath);
	Result->SetStringField(TEXT("trait_class"), TraitClass->GetName());
	Result->SetStringField(TEXT("message"), FString::Printf(TEXT("Added trait '%s'"), *TraitClass->GetName()));
	return FMonolithActionResult::Success(Result);
}

// 223. remove_mass_trait
FMonolithActionResult FMonolithAIAdvancedActions::HandleRemoveMassTrait(const TSharedPtr<FJsonObject>& Params)
{
	FString AssetPath, Error;
	UMassEntityConfigAsset* Config = LoadMassConfigFromParams(Params, AssetPath, Error);
	if (!Config) return FMonolithActionResult::Error(Error);

	FString TraitClassName;
	FMonolithActionResult ErrResult;
	if (!MonolithAI::RequireStringParam(Params, TEXT("trait_class"), TraitClassName, ErrResult))
	{
		return ErrResult;
	}

	FScopedTransaction Transaction(FText::FromString(TEXT("Monolith: Remove Mass Trait")));

	FMassEntityConfig& EntityConfig = Config->GetMutableConfig();
	TConstArrayView<UMassEntityTraitBase*> Traits = EntityConfig.GetTraits();

	int32 RemovedIndex = INDEX_NONE;
	for (int32 i = 0; i < Traits.Num(); ++i)
	{
		if (Traits[i] && (Traits[i]->GetClass()->GetName() == TraitClassName ||
			Traits[i]->GetClass()->GetName() == TEXT("U") + TraitClassName ||
			TEXT("U") + TraitClassName == Traits[i]->GetClass()->GetName()))
		{
			RemovedIndex = i;
			break;
		}
	}

	// FMassEntityConfig has no RemoveTrait API — access the Traits UPROPERTY directly via reflection
	if (RemovedIndex != INDEX_NONE)
	{
		FArrayProperty* TraitsProp = CastField<FArrayProperty>(FMassEntityConfig::StaticStruct()->FindPropertyByName(TEXT("Traits")));
		if (TraitsProp)
		{
			FScriptArrayHelper ArrayHelper(TraitsProp, TraitsProp->ContainerPtrToValuePtr<void>(&EntityConfig));
			ArrayHelper.RemoveValues(RemovedIndex, 1);
		}
	}

	if (RemovedIndex == INDEX_NONE)
	{
		return FMonolithActionResult::Error(FString::Printf(TEXT("Trait '%s' not found on config"), *TraitClassName));
	}

	Config->MarkPackageDirty();

	TSharedPtr<FJsonObject> Result = MakeShared<FJsonObject>();
	Result->SetStringField(TEXT("asset_path"), AssetPath);
	Result->SetStringField(TEXT("message"), FString::Printf(TEXT("Removed trait '%s'"), *TraitClassName));
	return FMonolithActionResult::Success(Result);
}

// 224. list_mass_traits
FMonolithActionResult FMonolithAIAdvancedActions::HandleListMassTraits(const TSharedPtr<FJsonObject>& Params)
{
	TArray<TSharedPtr<FJsonValue>> TraitArr;

	TArray<UClass*> DerivedClasses;
	GetDerivedClasses(UMassEntityTraitBase::StaticClass(), DerivedClasses, /*bRecursive=*/true);

	for (UClass* Cls : DerivedClasses)
	{
		if (Cls->HasAnyClassFlags(CLASS_Abstract | CLASS_Deprecated | CLASS_NewerVersionExists))
		{
			continue;
		}

		TSharedPtr<FJsonObject> Entry = MakeShared<FJsonObject>();
		Entry->SetStringField(TEXT("class_name"), Cls->GetName());
		Entry->SetStringField(TEXT("display_name"), Cls->GetDisplayNameText().ToString());

		// List configurable properties (non-super)
		TArray<TSharedPtr<FJsonValue>> PropArr;
		for (TFieldIterator<FProperty> It(Cls, EFieldIteratorFlags::ExcludeSuper); It; ++It)
		{
			if (It->HasAnyPropertyFlags(CPF_Edit))
			{
				TSharedPtr<FJsonObject> PropObj = MakeShared<FJsonObject>();
				PropObj->SetStringField(TEXT("name"), It->GetName());
				PropObj->SetStringField(TEXT("type"), It->GetCPPType());
				PropArr.Add(MakeShared<FJsonValueObject>(PropObj));
			}
		}
		if (PropArr.Num() > 0)
		{
			Entry->SetArrayField(TEXT("editable_properties"), PropArr);
		}

		TraitArr.Add(MakeShared<FJsonValueObject>(Entry));
	}

	TSharedPtr<FJsonObject> Result = MakeShared<FJsonObject>();
	Result->SetArrayField(TEXT("traits"), TraitArr);
	Result->SetNumberField(TEXT("count"), TraitArr.Num());
	return FMonolithActionResult::Success(Result);
}

// 225. list_mass_processors
FMonolithActionResult FMonolithAIAdvancedActions::HandleListMassProcessors(const TSharedPtr<FJsonObject>& Params)
{
	TArray<TSharedPtr<FJsonValue>> ProcessorArr;

	TArray<UClass*> DerivedClasses;
	GetDerivedClasses(UMassProcessor::StaticClass(), DerivedClasses, /*bRecursive=*/true);

	for (UClass* Cls : DerivedClasses)
	{
		if (Cls->HasAnyClassFlags(CLASS_Abstract | CLASS_Deprecated | CLASS_NewerVersionExists))
		{
			continue;
		}

		TSharedPtr<FJsonObject> Entry = MakeShared<FJsonObject>();
		Entry->SetStringField(TEXT("class_name"), Cls->GetName());
		Entry->SetStringField(TEXT("display_name"), Cls->GetDisplayNameText().ToString());

		// Get processing phase from CDO if available
		if (UMassProcessor* CDO = Cast<UMassProcessor>(Cls->GetDefaultObject()))
		{
			Entry->SetStringField(TEXT("processing_phase"), UEnum::GetValueAsString(CDO->GetProcessingPhase()));
			Entry->SetBoolField(TEXT("auto_register"), !CDO->ShouldAllowQueryBasedPruning(/*bRuntimeMode=*/false));
		}

		ProcessorArr.Add(MakeShared<FJsonValueObject>(Entry));
	}

	TSharedPtr<FJsonObject> Result = MakeShared<FJsonObject>();
	Result->SetArrayField(TEXT("processors"), ProcessorArr);
	Result->SetNumberField(TEXT("count"), ProcessorArr.Num());
	return FMonolithActionResult::Success(Result);
}

// 226. validate_mass_entity_config
FMonolithActionResult FMonolithAIAdvancedActions::HandleValidateMassEntityConfig(const TSharedPtr<FJsonObject>& Params)
{
	FString AssetPath, Error;
	UMassEntityConfigAsset* Config = LoadMassConfigFromParams(Params, AssetPath, Error);
	if (!Config) return FMonolithActionResult::Error(Error);

	const FMassEntityConfig& EntityConfig = Config->GetConfig();
	TConstArrayView<UMassEntityTraitBase*> Traits = EntityConfig.GetTraits();

	TArray<TSharedPtr<FJsonValue>> Issues;
	int32 Score = 100;

	// Check for duplicate trait types
	TMap<FName, int32> TraitTypeCounts;
	for (const UMassEntityTraitBase* Trait : Traits)
	{
		if (!Trait)
		{
			TSharedPtr<FJsonObject> Issue = MakeShared<FJsonObject>();
			Issue->SetStringField(TEXT("severity"), TEXT("error"));
			Issue->SetStringField(TEXT("message"), TEXT("Null trait reference found"));
			Issues.Add(MakeShared<FJsonValueObject>(Issue));
			Score -= 20;
			continue;
		}

		FName ClassName = Trait->GetClass()->GetFName();
		int32& Count = TraitTypeCounts.FindOrAdd(ClassName);
		Count++;
		if (Count > 1)
		{
			TSharedPtr<FJsonObject> Issue = MakeShared<FJsonObject>();
			Issue->SetStringField(TEXT("severity"), TEXT("warning"));
			Issue->SetStringField(TEXT("message"), FString::Printf(
				TEXT("Duplicate trait type '%s' (count: %d)"), *ClassName.ToString(), Count));
			Issues.Add(MakeShared<FJsonValueObject>(Issue));
			Score -= 10;
		}
	}

	// Check if config has any traits
	if (Traits.Num() == 0)
	{
		TSharedPtr<FJsonObject> Issue = MakeShared<FJsonObject>();
		Issue->SetStringField(TEXT("severity"), TEXT("warning"));
		Issue->SetStringField(TEXT("message"), TEXT("Config has no traits — entity will have no behavior"));
		Issues.Add(MakeShared<FJsonValueObject>(Issue));
		Score -= 15;
	}

	// Validate via the config's template validation (requires a world)
	UWorld* World = GEditor ? GEditor->GetEditorWorldContext().World() : nullptr;
	if (World)
	{
		// ValidateEntityTemplate returns false if the template has issues
		FMassEntityConfig& MutableConfig = Config->GetMutableConfig();
		if (!MutableConfig.ValidateEntityTemplate(*World))
		{
			TSharedPtr<FJsonObject> Issue = MakeShared<FJsonObject>();
			Issue->SetStringField(TEXT("severity"), TEXT("error"));
			Issue->SetStringField(TEXT("message"), TEXT("Entity template validation failed — check trait compatibility and fragment requirements"));
			Issues.Add(MakeShared<FJsonValueObject>(Issue));
			Score -= 15;
		}
	}

	Score = FMath::Max(0, Score);

	TSharedPtr<FJsonObject> Result = MakeShared<FJsonObject>();
	Result->SetStringField(TEXT("asset_path"), AssetPath);
	Result->SetArrayField(TEXT("issues"), Issues);
	Result->SetNumberField(TEXT("issue_count"), Issues.Num());
	Result->SetNumberField(TEXT("score"), Score);
	Result->SetBoolField(TEXT("valid"), Issues.Num() == 0);
	return FMonolithActionResult::Success(Result);
}

// 230. get_mass_entity_stats
FMonolithActionResult FMonolithAIAdvancedActions::HandleGetMassEntityStats(const TSharedPtr<FJsonObject>& Params)
{
	UWorld* PIEWorld = MonolithAI::GetPIEWorld();
	if (!PIEWorld)
	{
		return FMonolithActionResult::Error(TEXT("No PIE world found — stats require Play In Editor to be running"));
	}

	UMassEntitySubsystem* MassSubsystem = PIEWorld->GetSubsystem<UMassEntitySubsystem>();
	if (!MassSubsystem)
	{
		return FMonolithActionResult::Error(TEXT("UMassEntitySubsystem not found — MassEntity may not be active in this world"));
	}

	const FMassEntityManager& EntityManager = MassSubsystem->GetEntityManager();

	// FMassEntityManager doesn't expose entity/archetype counts directly.
	// Use GetMatchingArchetypes with empty requirements to count archetypes.
	TArray<FMassArchetypeHandle> AllArchetypes;
	FMassFragmentRequirements EmptyReqs;
	EntityManager.GetMatchingArchetypes(EmptyReqs, AllArchetypes);

	TSharedPtr<FJsonObject> Result = MakeShared<FJsonObject>();
	Result->SetNumberField(TEXT("num_archetypes"), AllArchetypes.Num());
	Result->SetStringField(TEXT("message"), FString::Printf(
		TEXT("MassEntity runtime: %d archetypes found. Per-entity counts require FMassDebugger (editor only)."),
		AllArchetypes.Num()));

	return FMonolithActionResult::Success(Result);
}

// ============================================================
//  ZoneGraph actions (227-229)
// ============================================================

#if WITH_ZONEGRAPH

// 227. list_zone_graphs
FMonolithActionResult FMonolithAIAdvancedActions::HandleListZoneGraphs(const TSharedPtr<FJsonObject>& Params)
{
	FString LevelFilter = Params->GetStringField(TEXT("level"));

	UWorld* World = GEditor ? GEditor->GetEditorWorldContext().World() : nullptr;
	if (!World)
	{
		return FMonolithActionResult::Error(TEXT("No editor world available"));
	}

	TArray<TSharedPtr<FJsonValue>> GraphArr;

	for (TActorIterator<AActor> It(World); It; ++It)
	{
		AActor* Actor = *It;
		// ZoneGraphData actors — use class name check for reflection safety
		if (!Actor || !Actor->GetClass()->GetName().Contains(TEXT("ZoneGraphData")))
		{
			continue;
		}

		FString LevelName = Actor->GetLevel() ? Actor->GetLevel()->GetOuter()->GetName() : TEXT("Unknown");
		if (!LevelFilter.IsEmpty() && !LevelName.Contains(LevelFilter))
		{
			continue;
		}

		TSharedPtr<FJsonObject> Entry = MakeShared<FJsonObject>();
		Entry->SetStringField(TEXT("actor_name"), Actor->GetActorNameOrLabel());
		Entry->SetStringField(TEXT("actor_path"), Actor->GetPathName());
		Entry->SetStringField(TEXT("level"), LevelName);

		FVector Loc = Actor->GetActorLocation();
		Entry->SetStringField(TEXT("location"), FString::Printf(TEXT("(%.1f, %.1f, %.1f)"), Loc.X, Loc.Y, Loc.Z));

		GraphArr.Add(MakeShared<FJsonValueObject>(Entry));
	}

	TSharedPtr<FJsonObject> Result = MakeShared<FJsonObject>();
	Result->SetArrayField(TEXT("zone_graphs"), GraphArr);
	Result->SetNumberField(TEXT("count"), GraphArr.Num());
	return FMonolithActionResult::Success(Result);
}

// 228. query_zone_lanes
FMonolithActionResult FMonolithAIAdvancedActions::HandleQueryZoneLanes(const TSharedPtr<FJsonObject>& Params)
{
	const TSharedPtr<FJsonObject>* LocationPtr = nullptr;
	if (!Params->TryGetObjectField(TEXT("location"), LocationPtr) || !LocationPtr || !LocationPtr->IsValid())
	{
		return FMonolithActionResult::Error(TEXT("Missing required param 'location' (object with x, y, z)"));
	}

	FVector Location;
	Location.X = (*LocationPtr)->GetNumberField(TEXT("x"));
	Location.Y = (*LocationPtr)->GetNumberField(TEXT("y"));
	Location.Z = (*LocationPtr)->GetNumberField(TEXT("z"));

	double Radius = 1000.0;
	if (Params->HasField(TEXT("radius")))
	{
		Radius = Params->GetNumberField(TEXT("radius"));
	}

	UWorld* World = MonolithAI::GetPIEWorld();
	if (!World)
	{
		World = GEditor ? GEditor->GetEditorWorldContext().World() : nullptr;
	}
	if (!World)
	{
		return FMonolithActionResult::Error(TEXT("No world available for zone graph query"));
	}

	UZoneGraphSubsystem* ZGSubsystem = World->GetSubsystem<UZoneGraphSubsystem>();
	if (!ZGSubsystem)
	{
		return FMonolithActionResult::Error(TEXT("UZoneGraphSubsystem not found"));
	}

	FZoneGraphTagFilter TagFilter;
	FString TagFilterStr = Params->GetStringField(TEXT("tag_filter"));
	// Tag parsing is left as no-op for now — ZoneGraph tags are bitmask-based

	FBox QueryBounds = FBox::BuildAABB(Location, FVector(Radius));
	TArray<FZoneGraphLaneHandle> FoundLanes;
	ZGSubsystem->FindOverlappingLanes(QueryBounds, TagFilter, FoundLanes);

	TArray<TSharedPtr<FJsonValue>> LaneArr;
	for (const FZoneGraphLaneHandle& Handle : FoundLanes)
	{
		TSharedPtr<FJsonObject> LaneObj = MakeShared<FJsonObject>();
		LaneObj->SetNumberField(TEXT("lane_index"), Handle.Index);
		LaneObj->SetNumberField(TEXT("data_handle"), Handle.DataHandle.Index);
		LaneArr.Add(MakeShared<FJsonValueObject>(LaneObj));
	}

	TSharedPtr<FJsonObject> Result = MakeShared<FJsonObject>();
	Result->SetStringField(TEXT("query_location"), FString::Printf(TEXT("(%.1f, %.1f, %.1f)"), Location.X, Location.Y, Location.Z));
	Result->SetNumberField(TEXT("query_radius"), Radius);
	Result->SetArrayField(TEXT("lanes"), LaneArr);
	Result->SetNumberField(TEXT("count"), LaneArr.Num());
	return FMonolithActionResult::Success(Result);
}

// 229. get_zone_lane_info
FMonolithActionResult FMonolithAIAdvancedActions::HandleGetZoneLaneInfo(const TSharedPtr<FJsonObject>& Params)
{
	if (!Params->HasField(TEXT("lane_handle")))
	{
		return FMonolithActionResult::Error(TEXT("Missing required param 'lane_handle'"));
	}

	int32 LaneIndex = static_cast<int32>(Params->GetNumberField(TEXT("lane_handle")));

	UWorld* World = MonolithAI::GetPIEWorld();
	if (!World)
	{
		World = GEditor ? GEditor->GetEditorWorldContext().World() : nullptr;
	}
	if (!World)
	{
		return FMonolithActionResult::Error(TEXT("No world available for zone graph query"));
	}

	UZoneGraphSubsystem* ZGSubsystem = World->GetSubsystem<UZoneGraphSubsystem>();
	if (!ZGSubsystem)
	{
		return FMonolithActionResult::Error(TEXT("UZoneGraphSubsystem not found"));
	}

	// Get lane location data from the first registered zone graph data
	const FZoneGraphStorage* Storage = nullptr;
	{
		TConstArrayView<FRegisteredZoneGraphData> AllData = ZGSubsystem->GetRegisteredZoneGraphData();
		for (int32 Idx = 0; Idx < AllData.Num(); ++Idx)
		{
			if (AllData[Idx].bInUse)
			{
				FZoneGraphDataHandle Handle(static_cast<uint16>(Idx), static_cast<uint16>(AllData[Idx].Generation));
				Storage = ZGSubsystem->GetZoneGraphStorage(Handle);
				if (Storage) break;
			}
		}
	}
	if (!Storage)
	{
		return FMonolithActionResult::Error(TEXT("No ZoneGraph storage available"));
	}

	if (LaneIndex < 0 || LaneIndex >= Storage->Lanes.Num())
	{
		return FMonolithActionResult::Error(FString::Printf(TEXT("Lane index %d out of range (0-%d)"), LaneIndex, Storage->Lanes.Num() - 1));
	}

	const FZoneLaneData& Lane = Storage->Lanes[LaneIndex];

	TSharedPtr<FJsonObject> Result = MakeShared<FJsonObject>();
	Result->SetNumberField(TEXT("lane_index"), LaneIndex);
	Result->SetNumberField(TEXT("width"), Lane.Width);
	Result->SetNumberField(TEXT("num_points"), Lane.PointsEnd - Lane.PointsBegin);
	Result->SetNumberField(TEXT("tags"), static_cast<int32>(Lane.Tags.GetValue())); // raw bitmask value

	// Lane start/end points
	if (Lane.PointsBegin < Storage->LanePoints.Num() && Lane.PointsEnd <= Storage->LanePoints.Num())
	{
		const FVector& StartPt = Storage->LanePoints[Lane.PointsBegin];
		const FVector& EndPt = Storage->LanePoints[Lane.PointsEnd - 1];
		Result->SetStringField(TEXT("start_point"), FString::Printf(TEXT("(%.1f, %.1f, %.1f)"), StartPt.X, StartPt.Y, StartPt.Z));
		Result->SetStringField(TEXT("end_point"), FString::Printf(TEXT("(%.1f, %.1f, %.1f)"), EndPt.X, EndPt.Y, EndPt.Z));

		// Calculate lane length
		float TotalLength = 0.f;
		for (int32 i = Lane.PointsBegin; i < Lane.PointsEnd - 1; ++i)
		{
			TotalLength += FVector::Dist(Storage->LanePoints[i], Storage->LanePoints[i + 1]);
		}
		Result->SetNumberField(TEXT("length"), TotalLength);
	}

	return FMonolithActionResult::Success(Result);
}

#endif // WITH_ZONEGRAPH

#endif // WITH_MASSENTITY
