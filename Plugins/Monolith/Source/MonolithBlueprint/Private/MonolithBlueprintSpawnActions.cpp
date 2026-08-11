// Copyright Monolith. All Rights Reserved.

#include "MonolithBlueprintSpawnActions.h"
#include "MonolithJsonUtils.h"
#include "MonolithToolRegistry.h"
#include "MonolithParamSchema.h"
#include "MonolithParamUtils.h"
#include "Engine/Blueprint.h"
#include "Engine/World.h"
#include "Engine/LevelStreaming.h"
#include "GameFramework/Actor.h"
#include "Components/SceneComponent.h"
#include "Editor.h"
#include "UObject/UnrealType.h"
#include "Dom/JsonObject.h"
#include "Dom/JsonValue.h"

// ============================================================================
// Local Helpers
// ============================================================================

namespace
{

/** Apply label, folder, tags, and mobility to a freshly spawned actor. */
void ApplyActorMetadata(
	AActor* Actor,
	const FString& Label,
	const FString& Folder,
	const TArray<FString>& Tags,
	const FString& MobilityStr)
{
	if (!Label.IsEmpty())
	{
		Actor->SetActorLabel(Label);
	}

	Actor->SetFolderPath(FName(*Folder));

	for (const FString& Tag : Tags)
	{
		Actor->Tags.Add(FName(*Tag));
	}

	if (!MobilityStr.IsEmpty())
	{
		EComponentMobility::Type Mobility;
		if (MonolithParamUtils::ParseMobility(MobilityStr, Mobility))
		{
			if (Actor->GetRootComponent())
			{
				Actor->GetRootComponent()->SetMobility(Mobility);
			}
		}
	}
}

/** Convert a JSON value to a string suitable for ImportText_Direct. */
FString JsonValueToImportString(const TSharedPtr<FJsonValue>& Value)
{
	if (Value->Type == EJson::Boolean)
	{
		return Value->AsBool() ? TEXT("True") : TEXT("False");
	}
	if (Value->Type == EJson::Number)
	{
		return FString::SanitizeFloat(Value->AsNumber());
	}
	return Value->AsString();
}

/**
 * Set properties on an actor via reflection.
 * Searches the actor first, then its components.
 * Reports successes and failures separately.
 */
void ApplyPropertiesToActor(
	AActor* Actor,
	const TSharedPtr<FJsonObject>& PropsObj,
	TArray<FString>& OutPropertiesSet,
	TArray<TSharedPtr<FJsonValue>>& OutPropertiesFailed)
{
	if (!PropsObj.IsValid() || PropsObj->Values.Num() == 0)
	{
		return;
	}

	for (const auto& Pair : PropsObj->Values)
	{
		const FString PropName = MonolithKeyToString(Pair.Key);
		const TSharedPtr<FJsonValue>& PropValue = Pair.Value;

		FProperty* Prop = Actor->GetClass()->FindPropertyByName(FName(*PropName));
		UObject* Container = Actor;

		if (!Prop)
		{
			// Search components
			bool bFoundOnComponent = false;
			TArray<UActorComponent*> Components;
			Actor->GetComponents(Components);
			for (UActorComponent* Comp : Components)
			{
				Prop = Comp->GetClass()->FindPropertyByName(FName(*PropName));
				if (Prop)
				{
					Container = Comp;
					bFoundOnComponent = true;
					break;
				}
			}

			if (!Prop)
			{
				auto FailObj = MakeShared<FJsonObject>();
				FailObj->SetStringField(TEXT("name"), PropName);
				FailObj->SetStringField(TEXT("reason"), TEXT("Property not found on actor or any component"));
				OutPropertiesFailed.Add(MakeShared<FJsonValueObject>(FailObj));
				continue;
			}
		}

		FString ValueStr = JsonValueToImportString(PropValue);
		void* ValuePtr = Prop->ContainerPtrToValuePtr<void>(Container);

		if (Prop->ImportText_Direct(*ValueStr, ValuePtr, Container, PPF_None))
		{
			FPropertyChangedEvent ChangedEvent(Prop);
			if (Container == Actor)
			{
				Actor->PostEditChangeProperty(ChangedEvent);
			}
			else
			{
				Cast<UActorComponent>(Container)->PostEditChangeProperty(ChangedEvent);
			}
			OutPropertiesSet.Add(PropName);
		}
		else
		{
			auto FailObj = MakeShared<FJsonObject>();
			FailObj->SetStringField(TEXT("name"), PropName);
			FailObj->SetStringField(TEXT("reason"), FString::Printf(TEXT("ImportText_Direct failed for value: %s"), *ValueStr));
			OutPropertiesFailed.Add(MakeShared<FJsonValueObject>(FailObj));
		}
	}
}

/** Parse string tags from a JSON array param. */
TArray<FString> ParseTagsParam(const TSharedPtr<FJsonObject>& Params)
{
	TArray<FString> Tags;
	const TArray<TSharedPtr<FJsonValue>>* TagsArr = nullptr;
	if (Params->TryGetArrayField(TEXT("tags"), TagsArr) && TagsArr)
	{
		for (const auto& TagVal : *TagsArr)
		{
			FString TagStr;
			if (TagVal->TryGetString(TagStr) && !TagStr.IsEmpty())
			{
				Tags.Add(TagStr);
			}
		}
	}
	return Tags;
}

/** Resolve a sublevel by name. Returns nullptr and sets OutError if not found. */
ULevel* ResolveSublevel(UWorld* World, const FString& SublevelName, FString& OutError)
{
	if (SublevelName.IsEmpty())
	{
		return World->PersistentLevel;
	}

	for (ULevelStreaming* StreamingLevel : World->GetStreamingLevels())
	{
		if (StreamingLevel && StreamingLevel->GetWorldAssetPackageFName().ToString().Contains(SublevelName))
		{
			ULevel* LoadedLevel = StreamingLevel->GetLoadedLevel();
			if (LoadedLevel)
			{
				return LoadedLevel;
			}
		}
	}

	OutError = FString::Printf(TEXT("Sublevel not found or not loaded: %s"), *SublevelName);
	return nullptr;
}

} // anonymous namespace

// ============================================================================
// Registration
// ============================================================================

void FMonolithBlueprintSpawnActions::RegisterActions(FMonolithToolRegistry& Registry)
{
	// 1. spawn_blueprint_actor
	Registry.RegisterAction(TEXT("blueprint"), TEXT("spawn_blueprint_actor"),
		TEXT("Spawn a Blueprint actor into the editor world with transform, properties, tags, sublevel, and mobility control."),
		FMonolithActionHandler::CreateStatic(&HandleSpawnBlueprintActor),
		FParamSchemaBuilder()
			.Required(TEXT("blueprint"), TEXT("string"), TEXT("Blueprint asset path (e.g. /Game/Blueprints/BP_Lamp)"))
			.Optional(TEXT("location"), TEXT("array|object"), TEXT("Spawn location [x,y,z] or {x,y,z}"), TEXT("[0,0,0]"))
			.Optional(TEXT("rotation"), TEXT("array|object"), TEXT("Spawn rotation [pitch,yaw,roll]"), TEXT("[0,0,0]"))
			.Optional(TEXT("scale"), TEXT("array|object"), TEXT("Spawn scale [x,y,z]"), TEXT("[1,1,1]"))
			.Optional(TEXT("label"), TEXT("string"), TEXT("Actor label (display name)"))
			.OptionalAssetPathWithDefault(TEXT("folder"), TEXT("Outliner folder path"), TEXT("Blueprints"))
			.Optional(TEXT("properties"), TEXT("object"), TEXT("Properties to set via reflection {name: value}"))
			.Optional(TEXT("tags"), TEXT("array"), TEXT("Array of string tags to add to actor"))
			.Optional(TEXT("sublevel"), TEXT("string"), TEXT("Target streaming sublevel name"))
			.Optional(TEXT("mobility"), TEXT("string"), TEXT("Root component mobility: static, stationary, movable"))
			.Optional(TEXT("select"), TEXT("boolean"), TEXT("Select actor after spawn"), TEXT("true"))
			.Build());

	// 2. batch_spawn_blueprint_actors
	Registry.RegisterAction(TEXT("blueprint"), TEXT("batch_spawn_blueprint_actors"),
		TEXT("Spawn multiple Blueprint actors in a grid or linear pattern. Continues on per-actor failure."),
		FMonolithActionHandler::CreateStatic(&HandleBatchSpawnBlueprintActors),
		FParamSchemaBuilder()
			.Required(TEXT("blueprint"), TEXT("string"), TEXT("Blueprint asset path"))
			.Required(TEXT("count"), TEXT("integer"), TEXT("Number of actors to spawn (1-1000)"))
			.Optional(TEXT("pattern"), TEXT("string"), TEXT("Layout: grid or linear"), TEXT("grid"))
			.Optional(TEXT("origin"), TEXT("array|object"), TEXT("Origin point [x,y,z]"), TEXT("[0,0,0]"))
			.Optional(TEXT("spacing"), TEXT("number"), TEXT("Center-to-center spacing in cm"), TEXT("200"))
			.Optional(TEXT("columns"), TEXT("integer"), TEXT("Columns per row (grid only)"), TEXT("10"))
			.Optional(TEXT("direction"), TEXT("array|object"), TEXT("Direction vector for linear pattern"), TEXT("[1,0,0]"))
			.Optional(TEXT("rotation"), TEXT("array|object"), TEXT("Rotation for all actors"), TEXT("[0,0,0]"))
			.Optional(TEXT("scale"), TEXT("array|object"), TEXT("Scale for all actors"), TEXT("[1,1,1]"))
			.Optional(TEXT("label_prefix"), TEXT("string"), TEXT("Label prefix; actors get prefix_0, prefix_1, etc."))
			.OptionalAssetPathWithDefault(TEXT("folder"), TEXT("Outliner folder"), TEXT("Blueprints"))
			.Optional(TEXT("properties"), TEXT("object"), TEXT("Properties set on every actor"))
			.Optional(TEXT("tags"), TEXT("array"), TEXT("Tags added to every actor"))
			.Optional(TEXT("sublevel"), TEXT("string"), TEXT("Target streaming sublevel name"))
			.Optional(TEXT("mobility"), TEXT("string"), TEXT("Root component mobility: static, stationary, movable"))
			.Optional(TEXT("select"), TEXT("boolean"), TEXT("Select spawned actors"), TEXT("false"))
			.Build());
}

// ============================================================================
// 1. spawn_blueprint_actor
// ============================================================================

FMonolithActionResult FMonolithBlueprintSpawnActions::HandleSpawnBlueprintActor(const TSharedPtr<FJsonObject>& Params)
{
	// PIE guard
	if (GEditor && GEditor->IsPlayingSessionInEditor())
	{
		return FMonolithActionResult::Error(TEXT("Cannot spawn Blueprint actors during Play-In-Editor session"));
	}

	// Required: blueprint
	FString BlueprintPath;
	if (!Params->TryGetStringField(TEXT("blueprint"), BlueprintPath))
	{
		return FMonolithActionResult::Error(TEXT("Missing required param: blueprint"));
	}

	// Normalize and load class
	FString ClassPath = MonolithParamUtils::NormalizeBlueprintClassPath(BlueprintPath);
	UClass* BPClass = StaticLoadClass(AActor::StaticClass(), nullptr, *ClassPath);
	if (!BPClass)
	{
		return FMonolithActionResult::Error(FString::Printf(
			TEXT("Failed to load Blueprint class: %s (tried %s)"), *BlueprintPath, *ClassPath));
	}

	// Abstract check
	if (BPClass->HasAnyClassFlags(CLASS_Abstract))
	{
		return FMonolithActionResult::Error(FString::Printf(
			TEXT("Cannot spawn abstract Blueprint class: %s"), *BlueprintPath));
	}

	// Editor world
	UWorld* World = MonolithParamUtils::GetEditorWorld();
	if (!World)
	{
		return FMonolithActionResult::Error(TEXT("No editor world available. Is a level open?"));
	}

	// Parse optional transform
	FVector Location(0, 0, 0);
	MonolithParamUtils::ParseVector(Params, TEXT("location"), Location);

	FRotator Rotation(0, 0, 0);
	MonolithParamUtils::ParseRotator(Params, TEXT("rotation"), Rotation);

	FVector Scale(1, 1, 1);
	MonolithParamUtils::ParseVector(Params, TEXT("scale"), Scale);

	// Parse metadata
	FString Label;
	Params->TryGetStringField(TEXT("label"), Label);

	FString Folder = TEXT("Blueprints");
	Params->TryGetStringField(TEXT("folder"), Folder);

	FString MobilityStr;
	Params->TryGetStringField(TEXT("mobility"), MobilityStr);

	FString SublevelName;
	Params->TryGetStringField(TEXT("sublevel"), SublevelName);

	bool bSelect = true;
	Params->TryGetBoolField(TEXT("select"), bSelect);

	TArray<FString> Tags = ParseTagsParam(Params);

	// Resolve sublevel
	FString SublevelError;
	ULevel* TargetLevel = ResolveSublevel(World, SublevelName, SublevelError);
	if (!TargetLevel)
	{
		return FMonolithActionResult::Error(SublevelError);
	}

	// Begin transaction
	GEditor->BeginTransaction(NSLOCTEXT("Monolith", "SpawnBPActor", "Monolith: Spawn Blueprint Actor"));

	// Spawn via AddActor (NOTE: AddActor ignores scale from FTransform — it only extracts location + rotation)
	FTransform SpawnTransform(Rotation.Quaternion(), Location);
	AActor* NewActor = GEditor->AddActor(TargetLevel, BPClass, SpawnTransform, /*bSilent=*/false, RF_Transactional, bSelect);

	if (!NewActor)
	{
		GEditor->CancelTransaction(0);
		return FMonolithActionResult::Error(FString::Printf(
			TEXT("GEditor->AddActor failed for class: %s"), *BPClass->GetName()));
	}

	// Apply scale manually (AddActor doesn't propagate it)
	if (!Scale.Equals(FVector::OneVector))
	{
		NewActor->SetActorScale3D(Scale);
	}

	// Apply metadata
	ApplyActorMetadata(NewActor, Label, Folder, Tags, MobilityStr);

	// Set properties via reflection (guard against FJsonValueString::AsObject() gotcha)
	TArray<FString> PropertiesSet;
	TArray<TSharedPtr<FJsonValue>> PropertiesFailed;
	const TSharedPtr<FJsonObject>* PropsObj = nullptr;
	if (Params->TryGetObjectField(TEXT("properties"), PropsObj) && PropsObj && (*PropsObj).IsValid() && (*PropsObj)->Values.Num() > 0)
	{
		ApplyPropertiesToActor(NewActor, *PropsObj, PropertiesSet, PropertiesFailed);
	}

	// End transaction
	GEditor->EndTransaction();

	// Build response
	auto Result = MakeShared<FJsonObject>();
	Result->SetStringField(TEXT("actor_name"), NewActor->GetFName().ToString());
	Result->SetStringField(TEXT("actor_label"), NewActor->GetActorLabel());
	Result->SetStringField(TEXT("class"), NewActor->GetClass()->GetName());
	Result->SetArrayField(TEXT("location"), MonolithParamUtils::VectorToJsonArray(NewActor->GetActorLocation()));
	{
		FRotator ActorRot = NewActor->GetActorRotation();
		TArray<TSharedPtr<FJsonValue>> RotArr;
		RotArr.Add(MakeShared<FJsonValueNumber>(ActorRot.Pitch));
		RotArr.Add(MakeShared<FJsonValueNumber>(ActorRot.Yaw));
		RotArr.Add(MakeShared<FJsonValueNumber>(ActorRot.Roll));
		Result->SetArrayField(TEXT("rotation"), RotArr);
	}
	Result->SetArrayField(TEXT("scale"), MonolithParamUtils::VectorToJsonArray(NewActor->GetActorScale3D()));

	TArray<TSharedPtr<FJsonValue>> PropsSetArr;
	for (const FString& P : PropertiesSet)
	{
		PropsSetArr.Add(MakeShared<FJsonValueString>(P));
	}
	Result->SetArrayField(TEXT("properties_set"), PropsSetArr);

	if (PropertiesFailed.Num() > 0)
	{
		Result->SetArrayField(TEXT("properties_failed"), PropertiesFailed);
	}

	if (!SublevelName.IsEmpty())
	{
		Result->SetStringField(TEXT("sublevel"), SublevelName);
	}

	return FMonolithActionResult::Success(Result);
}

// ============================================================================
// 2. batch_spawn_blueprint_actors
// ============================================================================

FMonolithActionResult FMonolithBlueprintSpawnActions::HandleBatchSpawnBlueprintActors(const TSharedPtr<FJsonObject>& Params)
{
	// PIE guard
	if (GEditor && GEditor->IsPlayingSessionInEditor())
	{
		return FMonolithActionResult::Error(TEXT("Cannot spawn Blueprint actors during Play-In-Editor session"));
	}

	// Required: blueprint
	FString BlueprintPath;
	if (!Params->TryGetStringField(TEXT("blueprint"), BlueprintPath))
	{
		return FMonolithActionResult::Error(TEXT("Missing required param: blueprint"));
	}

	// Required: count
	double CountD = 0;
	if (!Params->TryGetNumberField(TEXT("count"), CountD) || CountD < 1)
	{
		return FMonolithActionResult::Error(TEXT("Missing or invalid required param: count (must be >= 1)"));
	}
	int32 Count = FMath::RoundToInt32(CountD);
	if (Count > 1000)
	{
		return FMonolithActionResult::Error(TEXT("count exceeds maximum of 1000"));
	}

	// Normalize and load class
	FString ClassPath = MonolithParamUtils::NormalizeBlueprintClassPath(BlueprintPath);
	UClass* BPClass = StaticLoadClass(AActor::StaticClass(), nullptr, *ClassPath);
	if (!BPClass)
	{
		return FMonolithActionResult::Error(FString::Printf(
			TEXT("Failed to load Blueprint class: %s (tried %s)"), *BlueprintPath, *ClassPath));
	}

	if (BPClass->HasAnyClassFlags(CLASS_Abstract))
	{
		return FMonolithActionResult::Error(FString::Printf(
			TEXT("Cannot spawn abstract Blueprint class: %s"), *BlueprintPath));
	}

	// Editor world
	UWorld* World = MonolithParamUtils::GetEditorWorld();
	if (!World)
	{
		return FMonolithActionResult::Error(TEXT("No editor world available. Is a level open?"));
	}

	// Parse optional params
	FString Pattern = TEXT("grid");
	Params->TryGetStringField(TEXT("pattern"), Pattern);
	Pattern = Pattern.ToLower();
	if (Pattern != TEXT("grid") && Pattern != TEXT("linear"))
	{
		return FMonolithActionResult::Error(FString::Printf(
			TEXT("Invalid pattern: %s. Must be 'grid' or 'linear'"), *Pattern));
	}

	FVector Origin(0, 0, 0);
	MonolithParamUtils::ParseVector(Params, TEXT("origin"), Origin);

	double Spacing = 200.0;
	Params->TryGetNumberField(TEXT("spacing"), Spacing);
	if (Spacing <= 0)
	{
		return FMonolithActionResult::Error(TEXT("spacing must be positive"));
	}

	double ColumnsD = 10;
	Params->TryGetNumberField(TEXT("columns"), ColumnsD);
	int32 Columns = FMath::Max(1, FMath::RoundToInt32(ColumnsD));

	FVector Direction(1, 0, 0);
	MonolithParamUtils::ParseVector(Params, TEXT("direction"), Direction);
	if (Direction.IsNearlyZero())
	{
		Direction = FVector(1, 0, 0);
	}
	else
	{
		Direction.Normalize();
	}

	FRotator Rotation(0, 0, 0);
	MonolithParamUtils::ParseRotator(Params, TEXT("rotation"), Rotation);

	FVector Scale(1, 1, 1);
	MonolithParamUtils::ParseVector(Params, TEXT("scale"), Scale);

	FString LabelPrefix;
	Params->TryGetStringField(TEXT("label_prefix"), LabelPrefix);

	FString Folder = TEXT("Blueprints");
	Params->TryGetStringField(TEXT("folder"), Folder);

	FString MobilityStr;
	Params->TryGetStringField(TEXT("mobility"), MobilityStr);

	FString SublevelName;
	Params->TryGetStringField(TEXT("sublevel"), SublevelName);

	bool bSelect = false;
	Params->TryGetBoolField(TEXT("select"), bSelect);

	TArray<FString> Tags = ParseTagsParam(Params);

	// Resolve sublevel
	FString SublevelError;
	ULevel* TargetLevel = ResolveSublevel(World, SublevelName, SublevelError);
	if (!TargetLevel)
	{
		return FMonolithActionResult::Error(SublevelError);
	}

	// Parse properties (guard against FJsonValueString::AsObject() gotcha)
	const TSharedPtr<FJsonObject>* PropsObj = nullptr;
	bool bHasProperties = Params->TryGetObjectField(TEXT("properties"), PropsObj)
		&& PropsObj && (*PropsObj).IsValid() && (*PropsObj)->Values.Num() > 0;

	// Compute spawn positions
	TArray<FVector> Positions;
	Positions.Reserve(Count);

	if (Pattern == TEXT("grid"))
	{
		for (int32 i = 0; i < Count; i++)
		{
			int32 Col = i % Columns;
			int32 Row = i / Columns;
			FVector Pos = Origin + FVector(Col * Spacing, Row * Spacing, 0);
			Positions.Add(Pos);
		}
	}
	else // linear
	{
		for (int32 i = 0; i < Count; i++)
		{
			FVector Pos = Origin + Direction * (i * Spacing);
			Positions.Add(Pos);
		}
	}

	// Begin single transaction for entire batch (one undo step)
	GEditor->BeginTransaction(NSLOCTEXT("Monolith", "BatchSpawnBP", "Monolith: Batch Spawn Blueprint Actors"));

	TArray<TSharedPtr<FJsonValue>> SuccessArr;
	TArray<TSharedPtr<FJsonValue>> FailureArr;

	for (int32 i = 0; i < Count; i++)
	{
		FTransform SpawnTransform(Rotation.Quaternion(), Positions[i]);
		AActor* NewActor = GEditor->AddActor(TargetLevel, BPClass, SpawnTransform, /*bSilent=*/false, RF_Transactional, bSelect);

		if (!NewActor)
		{
			auto FailObj = MakeShared<FJsonObject>();
			FailObj->SetNumberField(TEXT("index"), i);
			FailObj->SetStringField(TEXT("error"), TEXT("GEditor->AddActor returned null"));
			FailureArr.Add(MakeShared<FJsonValueObject>(FailObj));
			continue;
		}

		// Apply scale manually (AddActor ignores scale from FTransform)
		if (!Scale.Equals(FVector::OneVector))
		{
			NewActor->SetActorScale3D(Scale);
		}

		// Label
		FString ActorLabel;
		if (!LabelPrefix.IsEmpty())
		{
			ActorLabel = FString::Printf(TEXT("%s_%d"), *LabelPrefix, i);
		}

		// Apply metadata
		ApplyActorMetadata(NewActor, ActorLabel, Folder, Tags, MobilityStr);

		// Apply properties
		TArray<FString> ActorPropsSet;
		TArray<TSharedPtr<FJsonValue>> ActorPropsFailed;
		if (bHasProperties)
		{
			ApplyPropertiesToActor(NewActor, *PropsObj, ActorPropsSet, ActorPropsFailed);
		}

		// Record success
		auto EntryObj = MakeShared<FJsonObject>();
		EntryObj->SetNumberField(TEXT("index"), i);
		EntryObj->SetStringField(TEXT("actor_name"), NewActor->GetFName().ToString());
		EntryObj->SetStringField(TEXT("actor_label"), NewActor->GetActorLabel());
		EntryObj->SetArrayField(TEXT("location"), MonolithParamUtils::VectorToJsonArray(NewActor->GetActorLocation()));
		if (ActorPropsFailed.Num() > 0)
		{
			EntryObj->SetArrayField(TEXT("properties_failed"), ActorPropsFailed);
		}
		SuccessArr.Add(MakeShared<FJsonValueObject>(EntryObj));
	}

	// End transaction
	GEditor->EndTransaction();

	// Build response
	auto Result = MakeShared<FJsonObject>();
	Result->SetStringField(TEXT("class"), BPClass->GetName());
	Result->SetStringField(TEXT("pattern"), Pattern);
	Result->SetNumberField(TEXT("requested"), Count);
	Result->SetNumberField(TEXT("spawned"), SuccessArr.Num());
	Result->SetNumberField(TEXT("failed"), FailureArr.Num());
	Result->SetArrayField(TEXT("actors"), SuccessArr);
	if (FailureArr.Num() > 0)
	{
		Result->SetArrayField(TEXT("failures"), FailureArr);
	}

	return FMonolithActionResult::Success(Result);
}
