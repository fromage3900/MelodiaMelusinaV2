#include "MonolithMeshVolumeActions.h"
#include "MonolithMeshUtils.h"
#include "MonolithToolRegistry.h"
#include "MonolithParamSchema.h"
#include "MonolithJsonUtils.h"

#include "Engine/World.h"
#include "Engine/TriggerVolume.h"
#include "Engine/BlockingVolume.h"
#include "Engine/PostProcessVolume.h"
#include "GameFramework/KillZVolume.h"
#include "GameFramework/PainCausingVolume.h"
#include "NavAreas/NavArea_Obstacle.h"
#include "NavModifierVolume.h"
#include "Sound/AudioVolume.h"
#include "EngineUtils.h"
#include "GameFramework/Actor.h"
#include "GameFramework/Volume.h"
#include "Components/BrushComponent.h"
#include "Components/PrimitiveComponent.h"
#include "Dom/JsonObject.h"
#include "Dom/JsonValue.h"
#include "Editor.h"
#include "Selection.h"
#include "CollisionQueryParams.h"
#include "NavigationSystem.h"
#include "NavigationData.h"
#include "Builders/CubeBuilder.h"
#include "Builders/CylinderBuilder.h"
#include "Builders/TetrahedronBuilder.h"
#include "ActorFactories/ActorFactory.h"
#include "UObject/FieldIterator.h"
#include "Engine/CollisionProfile.h"
#include "Misc/DateTime.h"

// ============================================================================
// Helpers
// ============================================================================

namespace VolumeActionHelpers
{
	/** Make a JSON array from a FVector */
	TArray<TSharedPtr<FJsonValue>> VectorToJsonArray(const FVector& V)
	{
		TArray<TSharedPtr<FJsonValue>> Arr;
		Arr.Add(MakeShared<FJsonValueNumber>(V.X));
		Arr.Add(MakeShared<FJsonValueNumber>(V.Y));
		Arr.Add(MakeShared<FJsonValueNumber>(V.Z));
		return Arr;
	}

	/** Scoped undo transaction */
	struct FScopedMeshTransaction
	{
		bool bOwnsTransaction;

		FScopedMeshTransaction(const FText& Description)
			: bOwnsTransaction(true)
		{
			if (GEditor)
			{
				GEditor->BeginTransaction(Description);
			}
		}

		~FScopedMeshTransaction()
		{
			if (bOwnsTransaction && GEditor)
			{
				GEditor->EndTransaction();
			}
		}

		void Cancel()
		{
			if (bOwnsTransaction && GEditor)
			{
				GEditor->CancelTransaction(0);
				bOwnsTransaction = false;
			}
		}
	};

	/** Find a UActorComponent by class name on an actor */
	UActorComponent* FindComponentByClassName(AActor* Actor, const FString& ClassName)
	{
		TArray<UActorComponent*> Components;
		Actor->GetComponents(Components);

		for (UActorComponent* Comp : Components)
		{
			if (Comp->GetClass()->GetName().Equals(ClassName, ESearchCase::IgnoreCase) ||
				Comp->GetFName().ToString().Equals(ClassName, ESearchCase::IgnoreCase))
			{
				return Comp;
			}
		}
		return nullptr;
	}

	/** Find a UActorComponent by class type on an actor */
	UActorComponent* FindComponentByClassType(AActor* Actor, const FString& ClassFilter)
	{
		TArray<UActorComponent*> Components;
		Actor->GetComponents(Components);

		for (UActorComponent* Comp : Components)
		{
			// Walk up the class hierarchy to match
			for (UClass* C = Comp->GetClass(); C; C = C->GetSuperClass())
			{
				if (C->GetName().Equals(ClassFilter, ESearchCase::IgnoreCase))
				{
					return Comp;
				}
			}
		}
		return nullptr;
	}
}

// ============================================================================
// Volume class resolver
// ============================================================================

UClass* FMonolithMeshVolumeActions::ResolveVolumeClass(const FString& TypeStr, FString& OutError)
{
	if (TypeStr.Equals(TEXT("trigger"), ESearchCase::IgnoreCase))       return ATriggerVolume::StaticClass();
	if (TypeStr.Equals(TEXT("blocking"), ESearchCase::IgnoreCase))      return ABlockingVolume::StaticClass();
	if (TypeStr.Equals(TEXT("kill"), ESearchCase::IgnoreCase))          return AKillZVolume::StaticClass();
	if (TypeStr.Equals(TEXT("pain"), ESearchCase::IgnoreCase))          return APainCausingVolume::StaticClass();
	if (TypeStr.Equals(TEXT("nav_modifier"), ESearchCase::IgnoreCase))  return ANavModifierVolume::StaticClass();
	if (TypeStr.Equals(TEXT("audio"), ESearchCase::IgnoreCase))         return AAudioVolume::StaticClass();
	if (TypeStr.Equals(TEXT("post_process"), ESearchCase::IgnoreCase))  return APostProcessVolume::StaticClass();

	OutError = FString::Printf(
		TEXT("Unknown volume type: '%s'. Valid types: trigger, blocking, kill, pain, nav_modifier, audio, post_process"),
		*TypeStr);
	return nullptr;
}

// ============================================================================
// Property reflection helpers
// ============================================================================

bool FMonolithMeshVolumeActions::ExportPropertyValue(const FProperty* Prop, const void* ContainerPtr, FString& OutValue)
{
	if (!Prop || !ContainerPtr)
	{
		return false;
	}

	const void* ValuePtr = Prop->ContainerPtrToValuePtr<void>(ContainerPtr);
	Prop->ExportText_Direct(OutValue, ValuePtr, ValuePtr, nullptr, PPF_None);
	return true;
}

bool FMonolithMeshVolumeActions::ImportPropertyValue(FProperty* Prop, void* ContainerPtr, const FString& Value, UObject* OwnerObject)
{
	if (!Prop || !ContainerPtr)
	{
		return false;
	}

	void* ValuePtr = Prop->ContainerPtrToValuePtr<void>(ContainerPtr);
	const TCHAR* Result = Prop->ImportText_Direct(*Value, ValuePtr, OwnerObject, PPF_None);
	return Result != nullptr;
}

// ============================================================================
// Registration
// ============================================================================

void FMonolithMeshVolumeActions::RegisterActions(FMonolithToolRegistry& Registry)
{
	// 1. spawn_volume
	Registry.RegisterAction(TEXT("mesh"), TEXT("spawn_volume"),
		TEXT("Spawn a volume actor (trigger, blocking, kill, pain, nav_modifier, audio, post_process) with proper brush geometry."),
		FMonolithActionHandler::CreateStatic(&FMonolithMeshVolumeActions::SpawnVolume),
		FParamSchemaBuilder()
			.Required(TEXT("type"), TEXT("string"), TEXT("Volume type: trigger, blocking, kill, pain, nav_modifier, audio, post_process"))
			.Required(TEXT("location"), TEXT("array"), TEXT("World location [x, y, z]"))
			.Optional(TEXT("extent"), TEXT("array"), TEXT("Half-extents [x, y, z]"), TEXT("[500,500,300]"))
			.Optional(TEXT("rotation"), TEXT("array"), TEXT("Rotation [pitch, yaw, roll]"), TEXT("[0,0,0]"))
			.Optional(TEXT("name"), TEXT("string"), TEXT("Optional label for the volume actor"))
			.OptionalAssetPath(TEXT("folder"), TEXT("Actor folder path in the outliner"))
			.Optional(TEXT("properties"), TEXT("object"), TEXT("Type-specific properties (e.g. damage_per_sec for pain, reverb_effect for audio)"))
			.Build());

	// 2. get_actor_properties
	Registry.RegisterAction(TEXT("mesh"), TEXT("get_actor_properties"),
		TEXT("Read arbitrary UPROPERTY values from an actor or its components via FProperty reflection. Returns string-serialized values."),
		FMonolithActionHandler::CreateStatic(&FMonolithMeshVolumeActions::GetActorProperties),
		FParamSchemaBuilder()
			.Required(TEXT("actor_name"), TEXT("string"), TEXT("Actor name or label"))
			.Optional(TEXT("properties"), TEXT("array"), TEXT("Array of property names to read. If omitted, reads all non-transient UPROPERTYs."))
			.Optional(TEXT("component"), TEXT("string"), TEXT("Component name or class to target (e.g. 'PointLightComponent0')"))
			.Optional(TEXT("include_defaults"), TEXT("boolean"), TEXT("Include properties at default values"), TEXT("false"))
			.Build());

	// 3. copy_actor_properties
	Registry.RegisterAction(TEXT("mesh"), TEXT("copy_actor_properties"),
		TEXT("Copy UPROPERTY values from a source actor to one or more target actors. Optionally filter to specific properties."),
		FMonolithActionHandler::CreateStatic(&FMonolithMeshVolumeActions::CopyActorProperties),
		FParamSchemaBuilder()
			.Required(TEXT("source_actor"), TEXT("string"), TEXT("Source actor name or label"))
			.Required(TEXT("target_actors"), TEXT("array"), TEXT("Array of target actor names or labels"))
			.Optional(TEXT("properties"), TEXT("array"), TEXT("Property names to copy. If omitted, copies all non-transient EditAnywhere properties."))
			.Optional(TEXT("component_class"), TEXT("string"), TEXT("Component class to target on both source and targets (e.g. 'PointLightComponent')"))
			.Build());

	// 4. build_navmesh
	Registry.RegisterAction(TEXT("mesh"), TEXT("build_navmesh"),
		TEXT("Trigger navigation mesh rebuild. Synchronous — blocks the game thread. Can take seconds on large maps."),
		FMonolithActionHandler::CreateStatic(&FMonolithMeshVolumeActions::BuildNavmesh),
		FParamSchemaBuilder()
			.Optional(TEXT("mode"), TEXT("string"), TEXT("Build mode: full or dirty_only"), TEXT("full"))
			.Build());

	// 5. select_actors
	Registry.RegisterAction(TEXT("mesh"), TEXT("select_actors"),
		TEXT("Control editor actor selection. Select, deselect, clear selection, get current selection, or focus camera on actors."),
		FMonolithActionHandler::CreateStatic(&FMonolithMeshVolumeActions::SelectActors),
		FParamSchemaBuilder()
			.Required(TEXT("sub_action"), TEXT("string"), TEXT("Action: select, deselect, clear, get, focus"))
			.Optional(TEXT("actors"), TEXT("array"), TEXT("Actor names or labels to select/deselect/focus"))
			.Optional(TEXT("filter"), TEXT("object"), TEXT("Filter: { class, tag, sublevel, radius, center }"))
			.Optional(TEXT("add_to_selection"), TEXT("boolean"), TEXT("If true, add to existing selection instead of replacing"), TEXT("false"))
			.Optional(TEXT("focus_camera"), TEXT("boolean"), TEXT("Move viewport camera to selected actors"), TEXT("false"))
			.Build());

	// 6. snap_to_surface
	Registry.RegisterAction(TEXT("mesh"), TEXT("snap_to_surface"),
		TEXT("Drop actors onto geometry via directional trace. Unlike snap_to_floor, supports any direction and surface normal alignment."),
		FMonolithActionHandler::CreateStatic(&FMonolithMeshVolumeActions::SnapToSurface),
		FParamSchemaBuilder()
			.Required(TEXT("actors"), TEXT("array"), TEXT("Actor names or labels to snap"))
			.Optional(TEXT("direction"), TEXT("array"), TEXT("Trace direction [x, y, z] (normalized)"), TEXT("[0,0,-1]"))
			.Optional(TEXT("trace_length"), TEXT("number"), TEXT("Maximum trace distance"), TEXT("10000"))
			.Optional(TEXT("align_to_normal"), TEXT("boolean"), TEXT("Rotate actor to align with surface normal"), TEXT("true"))
			.Optional(TEXT("offset"), TEXT("number"), TEXT("Distance offset from surface along normal"), TEXT("0"))
			.Optional(TEXT("channel"), TEXT("string"), TEXT("Collision channel for trace"), TEXT("WorldStatic"))
			.Build());

	// 7. set_collision_preset
	Registry.RegisterAction(TEXT("mesh"), TEXT("set_collision_preset"),
		TEXT("Set the collision profile on an actor's root primitive component (or a named component)."),
		FMonolithActionHandler::CreateStatic(&FMonolithMeshVolumeActions::SetCollisionPreset),
		FParamSchemaBuilder()
			.Required(TEXT("actor_name"), TEXT("string"), TEXT("Actor name or label"))
			.Required(TEXT("preset"), TEXT("string"), TEXT("Collision profile name (e.g. BlockAll, OverlapAll, NoCollision, Pawn, Custom...)"))
			.Optional(TEXT("component"), TEXT("string"), TEXT("Specific component name (defaults to root primitive)"))
			.Build());
}

// ============================================================================
// 1. spawn_volume
// ============================================================================

FMonolithActionResult FMonolithMeshVolumeActions::SpawnVolume(const TSharedPtr<FJsonObject>& Params)
{
	FString TypeStr;
	if (!Params->TryGetStringField(TEXT("type"), TypeStr))
	{
		return FMonolithActionResult::Error(TEXT("Missing required param: type"));
	}

	FVector Location;
	if (!MonolithMeshUtils::ParseVector(Params, TEXT("location"), Location))
	{
		return FMonolithActionResult::Error(TEXT("Missing or invalid required param: location (array of 3 numbers)"));
	}

	// Parse extent (half-extents) — defaults to 500x500x300
	FVector Extent(500.0, 500.0, 300.0);
	MonolithMeshUtils::ParseVector(Params, TEXT("extent"), Extent);

	if (Extent.X <= 0 || Extent.Y <= 0 || Extent.Z <= 0)
	{
		return FMonolithActionResult::Error(TEXT("All extent values must be positive"));
	}

	FRotator Rotation(0, 0, 0);
	MonolithMeshUtils::ParseRotator(Params, TEXT("rotation"), Rotation);

	FString OptionalName;
	Params->TryGetStringField(TEXT("name"), OptionalName);

	FString Folder;
	Params->TryGetStringField(TEXT("folder"), Folder);

	// Resolve volume class
	FString ClassError;
	UClass* VolumeClass = ResolveVolumeClass(TypeStr, ClassError);
	if (!VolumeClass)
	{
		return FMonolithActionResult::Error(ClassError);
	}

	UWorld* World = MonolithMeshUtils::GetEditorWorld();
	if (!World)
	{
		return FMonolithActionResult::Error(TEXT("No editor world available"));
	}

	VolumeActionHelpers::FScopedMeshTransaction Transaction(FText::FromString(TEXT("Monolith: Spawn Volume")));

	// Spawn the volume actor
	FActorSpawnParameters SpawnParams;
	SpawnParams.SpawnCollisionHandlingOverride = ESpawnActorCollisionHandlingMethod::AlwaysSpawn;

	AVolume* Volume = Cast<AVolume>(World->SpawnActor(VolumeClass, &Location, &Rotation, SpawnParams));
	if (!Volume)
	{
		Transaction.Cancel();
		return FMonolithActionResult::Error(FString::Printf(TEXT("Failed to spawn volume of type '%s'"), *TypeStr));
	}

	// Create brush geometry using UCubeBuilder
	// UCubeBuilder dimensions are FULL width, so extent * 2
	UCubeBuilder* CubeBuilder = NewObject<UCubeBuilder>();
	CubeBuilder->X = Extent.X * 2.0;
	CubeBuilder->Y = Extent.Y * 2.0;
	CubeBuilder->Z = Extent.Z * 2.0;

	UActorFactory::CreateBrushForVolumeActor(Volume, CubeBuilder);

	// Verify brush was created
	UBrushComponent* BrushComp = Volume->GetBrushComponent();
	bool bBrushValid = BrushComp && BrushComp->Brush != nullptr;

	// Set label
	if (!OptionalName.IsEmpty())
	{
		Volume->SetActorLabel(OptionalName);
	}

	// Set folder — default to /Volumes
	if (!Folder.IsEmpty())
	{
		Volume->SetFolderPath(FName(*Folder));
	}
	else
	{
		Volume->SetFolderPath(FName(TEXT("Volumes")));
	}

	// Apply type-specific properties
	const TSharedPtr<FJsonObject>* PropsObj;
	if (Params->TryGetObjectField(TEXT("properties"), PropsObj))
	{
		// Pain volume — damage_per_sec
		if (APainCausingVolume* PainVol = Cast<APainCausingVolume>(Volume))
		{
			double DamagePerSec;
			if ((*PropsObj)->TryGetNumberField(TEXT("damage_per_sec"), DamagePerSec))
			{
				PainVol->DamagePerSec = static_cast<float>(DamagePerSec);
			}
			bool bPainCausing;
			if ((*PropsObj)->TryGetBoolField(TEXT("pain_causing"), bPainCausing))
			{
				PainVol->bPainCausing = bPainCausing;
			}
			else
			{
				// Default to pain-causing if damage_per_sec is set
				PainVol->bPainCausing = true;
			}
		}

		// Audio volume — reverb, priority, etc
		if (AAudioVolume* AudioVol = Cast<AAudioVolume>(Volume))
		{
			double Priority;
			if ((*PropsObj)->TryGetNumberField(TEXT("priority"), Priority))
			{
				AudioVol->SetPriority(static_cast<float>(Priority));
			}
		}

		// Post process volume — settings
		if (APostProcessVolume* PPVol = Cast<APostProcessVolume>(Volume))
		{
			bool bUnbound;
			if ((*PropsObj)->TryGetBoolField(TEXT("unbound"), bUnbound))
			{
				PPVol->bUnbound = bUnbound;
			}
			double BlendRadius;
			if ((*PropsObj)->TryGetNumberField(TEXT("blend_radius"), BlendRadius))
			{
				PPVol->BlendRadius = static_cast<float>(BlendRadius);
			}
			double BlendWeight;
			if ((*PropsObj)->TryGetNumberField(TEXT("blend_weight"), BlendWeight))
			{
				PPVol->BlendWeight = static_cast<float>(BlendWeight);
			}
			double PPPriority;
			if ((*PropsObj)->TryGetNumberField(TEXT("priority"), PPPriority))
			{
				PPVol->Priority = static_cast<float>(PPPriority);
			}
		}
	}

	Volume->MarkPackageDirty();

	auto Result = MakeShared<FJsonObject>();
	Result->SetStringField(TEXT("actor_name"), Volume->GetActorNameOrLabel());
	Result->SetStringField(TEXT("class"), VolumeClass->GetName());
	Result->SetArrayField(TEXT("location"), VolumeActionHelpers::VectorToJsonArray(Volume->GetActorLocation()));
	Result->SetArrayField(TEXT("extent"), VolumeActionHelpers::VectorToJsonArray(Extent));
	Result->SetBoolField(TEXT("brush_valid"), bBrushValid);

	return FMonolithActionResult::Success(Result);
}

// ============================================================================
// 2. get_actor_properties
// ============================================================================

FMonolithActionResult FMonolithMeshVolumeActions::GetActorProperties(const TSharedPtr<FJsonObject>& Params)
{
	FString ActorName;
	if (!Params->TryGetStringField(TEXT("actor_name"), ActorName))
	{
		return FMonolithActionResult::Error(TEXT("Missing required param: actor_name"));
	}

	FString Error;
	AActor* Actor = MonolithMeshUtils::FindActorByName(ActorName, Error);
	if (!Actor)
	{
		return FMonolithActionResult::Error(Error);
	}

	bool bIncludeDefaults = false;
	Params->TryGetBoolField(TEXT("include_defaults"), bIncludeDefaults);

	// Determine target object — actor itself or a component
	UObject* TargetObject = Actor;
	FString ComponentName;
	if (Params->TryGetStringField(TEXT("component"), ComponentName))
	{
		UActorComponent* Comp = VolumeActionHelpers::FindComponentByClassName(Actor, ComponentName);
		if (!Comp)
		{
			return FMonolithActionResult::Error(FString::Printf(
				TEXT("Component '%s' not found on actor '%s'"), *ComponentName, *ActorName));
		}
		TargetObject = Comp;
	}

	// Determine which properties to read
	TSet<FString> RequestedProps;
	bool bFilterByName = false;
	const TArray<TSharedPtr<FJsonValue>>* PropsArr;
	if (Params->TryGetArrayField(TEXT("properties"), PropsArr) && PropsArr->Num() > 0)
	{
		bFilterByName = true;
		for (const auto& Val : *PropsArr)
		{
			RequestedProps.Add(Val->AsString());
		}
	}

	// Get the CDO for default comparison
	UObject* CDO = TargetObject->GetClass()->GetDefaultObject();

	auto PropertiesObj = MakeShared<FJsonObject>();
	int32 PropCount = 0;

	for (TFieldIterator<FProperty> PropIt(TargetObject->GetClass()); PropIt; ++PropIt)
	{
		FProperty* Prop = *PropIt;

		// Skip transient properties
		if (Prop->HasAnyPropertyFlags(CPF_Transient))
		{
			continue;
		}

		FString PropName = Prop->GetName();

		// If filtering by name, only include requested properties
		if (bFilterByName && !RequestedProps.Contains(PropName))
		{
			continue;
		}

		// Export the value
		FString Value;
		if (!ExportPropertyValue(Prop, TargetObject, Value))
		{
			continue;
		}

		// Skip defaults unless requested
		if (!bIncludeDefaults && !bFilterByName && CDO)
		{
			FString DefaultValue;
			if (ExportPropertyValue(Prop, CDO, DefaultValue) && Value == DefaultValue)
			{
				continue;
			}
		}

		PropertiesObj->SetStringField(PropName, Value);
		PropCount++;
	}

	// Warn about requested properties that weren't found
	TArray<TSharedPtr<FJsonValue>> NotFoundArr;
	if (bFilterByName)
	{
		for (const FString& Req : RequestedProps)
		{
			if (!PropertiesObj->HasField(Req))
			{
				NotFoundArr.Add(MakeShared<FJsonValueString>(Req));
			}
		}
	}

	auto Result = MakeShared<FJsonObject>();
	Result->SetStringField(TEXT("actor_name"), Actor->GetActorNameOrLabel());
	Result->SetStringField(TEXT("class"), TargetObject->GetClass()->GetName());
	Result->SetObjectField(TEXT("properties"), PropertiesObj);
	Result->SetNumberField(TEXT("property_count"), PropCount);

	if (NotFoundArr.Num() > 0)
	{
		Result->SetArrayField(TEXT("not_found"), NotFoundArr);
	}

	if (!ComponentName.IsEmpty())
	{
		Result->SetStringField(TEXT("component"), ComponentName);
	}

	return FMonolithActionResult::Success(Result);
}

// ============================================================================
// 3. copy_actor_properties
// ============================================================================

FMonolithActionResult FMonolithMeshVolumeActions::CopyActorProperties(const TSharedPtr<FJsonObject>& Params)
{
	FString SourceName;
	if (!Params->TryGetStringField(TEXT("source_actor"), SourceName))
	{
		return FMonolithActionResult::Error(TEXT("Missing required param: source_actor"));
	}

	const TArray<TSharedPtr<FJsonValue>>* TargetsArr;
	if (!Params->TryGetArrayField(TEXT("target_actors"), TargetsArr) || TargetsArr->Num() == 0)
	{
		return FMonolithActionResult::Error(TEXT("Missing or empty required param: target_actors"));
	}

	FString Error;
	AActor* SourceActor = MonolithMeshUtils::FindActorByName(SourceName, Error);
	if (!SourceActor)
	{
		return FMonolithActionResult::Error(Error);
	}

	// Resolve all target actors first
	TArray<AActor*> TargetActors;
	TargetActors.Reserve(TargetsArr->Num());
	for (const auto& Val : *TargetsArr)
	{
		FString TargetName = Val->AsString();
		FString TargetError;
		AActor* Target = MonolithMeshUtils::FindActorByName(TargetName, TargetError);
		if (!Target)
		{
			return FMonolithActionResult::Error(TargetError);
		}
		TargetActors.Add(Target);
	}

	// Determine component class filter
	FString ComponentClass;
	Params->TryGetStringField(TEXT("component_class"), ComponentClass);

	// Determine which properties to copy
	TSet<FString> RequestedProps;
	bool bFilterByName = false;
	const TArray<TSharedPtr<FJsonValue>>* PropsArr;
	if (Params->TryGetArrayField(TEXT("properties"), PropsArr) && PropsArr->Num() > 0)
	{
		bFilterByName = true;
		for (const auto& Val : *PropsArr)
		{
			RequestedProps.Add(Val->AsString());
		}
	}

	// Get source object (actor or component)
	UObject* SourceObj = SourceActor;
	if (!ComponentClass.IsEmpty())
	{
		UActorComponent* SourceComp = VolumeActionHelpers::FindComponentByClassType(SourceActor, ComponentClass);
		if (!SourceComp)
		{
			return FMonolithActionResult::Error(FString::Printf(
				TEXT("Component of class '%s' not found on source actor '%s'"), *ComponentClass, *SourceName));
		}
		SourceObj = SourceComp;
	}

	VolumeActionHelpers::FScopedMeshTransaction Transaction(FText::FromString(TEXT("Monolith: Copy Actor Properties")));

	// Collect source property values
	TMap<FString, FString> PropValues;
	for (TFieldIterator<FProperty> PropIt(SourceObj->GetClass()); PropIt; ++PropIt)
	{
		FProperty* Prop = *PropIt;

		if (Prop->HasAnyPropertyFlags(CPF_Transient))
		{
			continue;
		}

		// If not filtering, only copy EditAnywhere properties
		if (!bFilterByName && !Prop->HasAnyPropertyFlags(CPF_Edit))
		{
			continue;
		}

		FString PropName = Prop->GetName();
		if (bFilterByName && !RequestedProps.Contains(PropName))
		{
			continue;
		}

		FString Value;
		if (ExportPropertyValue(Prop, SourceObj, Value))
		{
			PropValues.Add(PropName, Value);
		}
	}

	if (PropValues.Num() == 0)
	{
		Transaction.Cancel();
		return FMonolithActionResult::Error(TEXT("No copyable properties found on source"));
	}

	// Apply to each target
	TArray<TSharedPtr<FJsonValue>> ResultsArr;
	int32 TotalCopied = 0;

	for (AActor* TargetActor : TargetActors)
	{
		UObject* TargetObj = TargetActor;
		if (!ComponentClass.IsEmpty())
		{
			UActorComponent* TargetComp = VolumeActionHelpers::FindComponentByClassType(TargetActor, ComponentClass);
			if (!TargetComp)
			{
				auto Entry = MakeShared<FJsonObject>();
				Entry->SetStringField(TEXT("actor"), TargetActor->GetActorNameOrLabel());
				Entry->SetNumberField(TEXT("copied"), 0);
				Entry->SetStringField(TEXT("error"), FString::Printf(TEXT("No %s component found"), *ComponentClass));
				ResultsArr.Add(MakeShared<FJsonValueObject>(Entry));
				continue;
			}
			TargetObj = TargetComp;
		}

		TargetObj->Modify();

		int32 Copied = 0;
		TArray<TSharedPtr<FJsonValue>> CopiedNames;

		for (const auto& Pair : PropValues)
		{
			FProperty* TargetProp = FindFProperty<FProperty>(TargetObj->GetClass(), *Pair.Key);
			if (!TargetProp)
			{
				continue;
			}

			if (ImportPropertyValue(TargetProp, TargetObj, Pair.Value, TargetObj))
			{
				Copied++;
				CopiedNames.Add(MakeShared<FJsonValueString>(Pair.Key));
			}
		}

		if (Copied > 0)
		{
			// Notify the engine about property changes
			FPropertyChangedEvent Event(nullptr);
			TargetObj->PostEditChangeProperty(Event);
			if (AActor* TargetAsActor = Cast<AActor>(TargetObj))
			{
				TargetAsActor->MarkPackageDirty();
			}
			else if (UActorComponent* Comp = Cast<UActorComponent>(TargetObj))
			{
				Comp->GetOwner()->MarkPackageDirty();
			}
		}

		TotalCopied += Copied;

		auto Entry = MakeShared<FJsonObject>();
		Entry->SetStringField(TEXT("actor"), TargetActor->GetActorNameOrLabel());
		Entry->SetNumberField(TEXT("copied"), Copied);
		Entry->SetArrayField(TEXT("properties"), CopiedNames);
		ResultsArr.Add(MakeShared<FJsonValueObject>(Entry));
	}

	auto Result = MakeShared<FJsonObject>();
	Result->SetStringField(TEXT("source"), SourceActor->GetActorNameOrLabel());
	Result->SetNumberField(TEXT("total_copied"), TotalCopied);
	Result->SetArrayField(TEXT("targets"), ResultsArr);

	return FMonolithActionResult::Success(Result);
}

// ============================================================================
// 4. build_navmesh
// ============================================================================

FMonolithActionResult FMonolithMeshVolumeActions::BuildNavmesh(const TSharedPtr<FJsonObject>& Params)
{
	UWorld* World = MonolithMeshUtils::GetEditorWorld();
	if (!World)
	{
		return FMonolithActionResult::Error(TEXT("No editor world available"));
	}

	UNavigationSystemV1* NavSys = FNavigationSystem::GetCurrent<UNavigationSystemV1>(World);
	if (!NavSys)
	{
		return FMonolithActionResult::Error(TEXT("NavigationSystem not found. Ensure a NavMeshBoundsVolume exists in the level."));
	}

	FString Mode = TEXT("full");
	Params->TryGetStringField(TEXT("mode"), Mode);

	if (!Mode.Equals(TEXT("full"), ESearchCase::IgnoreCase) &&
		!Mode.Equals(TEXT("dirty_only"), ESearchCase::IgnoreCase))
	{
		return FMonolithActionResult::Error(TEXT("Invalid mode. Use 'full' or 'dirty_only'."));
	}

	// Time the build
	FDateTime StartTime = FDateTime::Now();

	if (Mode.Equals(TEXT("full"), ESearchCase::IgnoreCase))
	{
		// Full synchronous rebuild — WARNING: blocks game thread
		NavSys->Build();
	}
	// For dirty_only, we don't explicitly build — the nav system handles incremental updates.
	// But we can force a dirty-area rebuild:
	// NavSys->OnNavigationBoundsUpdated() would trigger dirty rebuild, but Build() is more reliable.

	FDateTime EndTime = FDateTime::Now();
	double BuildTimeSeconds = (EndTime - StartTime).GetTotalSeconds();

	// Check nav data after build
	int32 NavDataCount = 0;
	TArray<FString> Warnings;

	ANavigationData* NavData = NavSys->GetDefaultNavDataInstance(FNavigationSystem::DontCreate);
	if (NavData)
	{
		NavDataCount = 1;
		// Count additional nav data instances
		for (TActorIterator<ANavigationData> It(World); It; ++It)
		{
			if (*It != NavData)
			{
				NavDataCount++;
			}
		}
	}
	else
	{
		Warnings.Add(TEXT("No navigation data generated. Ensure a NavMeshBoundsVolume exists and overlaps walkable geometry."));
	}

	if (BuildTimeSeconds > 5.0)
	{
		Warnings.Add(FString::Printf(TEXT("Build took %.1fs — consider reducing NavMeshBoundsVolume coverage for faster iteration."), BuildTimeSeconds));
	}

	auto Result = MakeShared<FJsonObject>();
	Result->SetBoolField(TEXT("success"), NavDataCount > 0);
	Result->SetNumberField(TEXT("build_time_seconds"), BuildTimeSeconds);
	Result->SetNumberField(TEXT("nav_data_count"), NavDataCount);
	Result->SetStringField(TEXT("mode"), Mode);

	if (Warnings.Num() > 0)
	{
		TArray<TSharedPtr<FJsonValue>> WarningsArr;
		for (const FString& W : Warnings)
		{
			WarningsArr.Add(MakeShared<FJsonValueString>(W));
		}
		Result->SetArrayField(TEXT("warnings"), WarningsArr);
	}

	return FMonolithActionResult::Success(Result);
}

// ============================================================================
// 5. select_actors
// ============================================================================

FMonolithActionResult FMonolithMeshVolumeActions::SelectActors(const TSharedPtr<FJsonObject>& Params)
{
	FString SubAction;
	if (!Params->TryGetStringField(TEXT("sub_action"), SubAction))
	{
		return FMonolithActionResult::Error(TEXT("Missing required param: sub_action"));
	}

	if (!GEditor)
	{
		return FMonolithActionResult::Error(TEXT("GEditor not available"));
	}

	UWorld* World = MonolithMeshUtils::GetEditorWorld();
	if (!World)
	{
		return FMonolithActionResult::Error(TEXT("No editor world available"));
	}

	bool bAddToSelection = false;
	Params->TryGetBoolField(TEXT("add_to_selection"), bAddToSelection);

	bool bFocusCamera = false;
	Params->TryGetBoolField(TEXT("focus_camera"), bFocusCamera);

	// ---- GET: return current selection ----
	if (SubAction.Equals(TEXT("get"), ESearchCase::IgnoreCase))
	{
		USelection* SelectedActors = GEditor->GetSelectedActors();
		TArray<TSharedPtr<FJsonValue>> SelectedArr;

		for (FSelectionIterator It(*SelectedActors); It; ++It)
		{
			AActor* Actor = Cast<AActor>(*It);
			if (!Actor) continue;

			auto Entry = MakeShared<FJsonObject>();
			Entry->SetStringField(TEXT("name"), Actor->GetActorNameOrLabel());
			Entry->SetStringField(TEXT("label"), Actor->GetActorLabel());
			Entry->SetStringField(TEXT("class"), Actor->GetClass()->GetName());
			Entry->SetArrayField(TEXT("location"), VolumeActionHelpers::VectorToJsonArray(Actor->GetActorLocation()));
			SelectedArr.Add(MakeShared<FJsonValueObject>(Entry));
		}

		auto Result = MakeShared<FJsonObject>();
		Result->SetNumberField(TEXT("selected_count"), SelectedArr.Num());
		Result->SetArrayField(TEXT("selected_actors"), SelectedArr);
		return FMonolithActionResult::Success(Result);
	}

	// ---- CLEAR: deselect everything ----
	if (SubAction.Equals(TEXT("clear"), ESearchCase::IgnoreCase))
	{
		GEditor->SelectNone(/*bNoteSelectionChange=*/true, /*bDeselectBSPSurfs=*/true, /*WarnAboutManyActors=*/false);

		auto Result = MakeShared<FJsonObject>();
		Result->SetNumberField(TEXT("selected_count"), 0);
		Result->SetArrayField(TEXT("selected_actors"), TArray<TSharedPtr<FJsonValue>>());
		return FMonolithActionResult::Success(Result);
	}

	// ---- SELECT / DESELECT / FOCUS: resolve actor list ----
	TArray<AActor*> ResolvedActors;

	// Resolve from explicit actor list
	const TArray<TSharedPtr<FJsonValue>>* ActorsArr;
	if (Params->TryGetArrayField(TEXT("actors"), ActorsArr))
	{
		for (const auto& Val : *ActorsArr)
		{
			FString Error;
			AActor* Actor = MonolithMeshUtils::FindActorByName(Val->AsString(), Error);
			if (Actor)
			{
				ResolvedActors.AddUnique(Actor);
			}
		}
	}

	// Resolve from filter
	const TSharedPtr<FJsonObject>* FilterObj;
	if (Params->TryGetObjectField(TEXT("filter"), FilterObj))
	{
		FString ClassFilter;
		(*FilterObj)->TryGetStringField(TEXT("class"), ClassFilter);

		FString TagFilter;
		(*FilterObj)->TryGetStringField(TEXT("tag"), TagFilter);

		FString SublevelFilter;
		(*FilterObj)->TryGetStringField(TEXT("sublevel"), SublevelFilter);

		double Radius = 0;
		FVector Center(0);
		bool bHasRadial = (*FilterObj)->TryGetNumberField(TEXT("radius"), Radius);
		if (bHasRadial)
		{
			MonolithMeshUtils::ParseVector(*FilterObj, TEXT("center"), Center);
		}

		for (TActorIterator<AActor> It(World); It; ++It)
		{
			AActor* Actor = *It;

			// Class filter
			if (!ClassFilter.IsEmpty())
			{
				bool bClassMatch = false;
				for (UClass* C = Actor->GetClass(); C; C = C->GetSuperClass())
				{
					if (C->GetName().Equals(ClassFilter, ESearchCase::IgnoreCase))
					{
						bClassMatch = true;
						break;
					}
				}
				if (!bClassMatch) continue;
			}

			// Tag filter
			if (!TagFilter.IsEmpty())
			{
				bool bTagMatch = false;
				for (const FName& Tag : Actor->Tags)
				{
					if (Tag.ToString().Equals(TagFilter, ESearchCase::IgnoreCase))
					{
						bTagMatch = true;
						break;
					}
				}
				if (!bTagMatch) continue;
			}

			// Sublevel filter
			if (!SublevelFilter.IsEmpty())
			{
				ULevel* Level = Actor->GetLevel();
				if (Level)
				{
					FString LevelName = Level->GetOuter()->GetName();
					if (!LevelName.Contains(SublevelFilter))
					{
						continue;
					}
				}
			}

			// Radius filter
			if (bHasRadial && Radius > 0)
			{
				if (FVector::Dist(Actor->GetActorLocation(), Center) > Radius)
				{
					continue;
				}
			}

			ResolvedActors.AddUnique(Actor);
		}
	}

	// ---- FOCUS ----
	if (SubAction.Equals(TEXT("focus"), ESearchCase::IgnoreCase))
	{
		if (ResolvedActors.Num() == 0)
		{
			return FMonolithActionResult::Error(TEXT("No actors to focus on"));
		}

		GEditor->MoveViewportCamerasToActor(ResolvedActors, /*bActiveViewportOnly=*/true);

		auto Result = MakeShared<FJsonObject>();
		Result->SetNumberField(TEXT("focused_count"), ResolvedActors.Num());
		TArray<TSharedPtr<FJsonValue>> FocusedArr;
		for (AActor* A : ResolvedActors)
		{
			FocusedArr.Add(MakeShared<FJsonValueString>(A->GetActorNameOrLabel()));
		}
		Result->SetArrayField(TEXT("focused_actors"), FocusedArr);
		return FMonolithActionResult::Success(Result);
	}

	// ---- SELECT / DESELECT ----
	bool bIsSelect = SubAction.Equals(TEXT("select"), ESearchCase::IgnoreCase);
	bool bIsDeselect = SubAction.Equals(TEXT("deselect"), ESearchCase::IgnoreCase);

	if (!bIsSelect && !bIsDeselect)
	{
		return FMonolithActionResult::Error(FString::Printf(
			TEXT("Invalid sub_action: '%s'. Valid: select, deselect, clear, get, focus"), *SubAction));
	}

	if (ResolvedActors.Num() == 0)
	{
		return FMonolithActionResult::Error(TEXT("No actors matched for selection"));
	}

	// Clear existing selection if selecting and not adding
	if (bIsSelect && !bAddToSelection)
	{
		GEditor->SelectNone(/*bNoteSelectionChange=*/false, /*bDeselectBSPSurfs=*/true, /*WarnAboutManyActors=*/false);
	}

	// Apply selection changes — bNotify=false for batch, then one NoteSelectionChange
	for (AActor* Actor : ResolvedActors)
	{
		GEditor->SelectActor(Actor, /*InSelected=*/bIsSelect, /*bNotify=*/false);
	}
	GEditor->NoteSelectionChange();

	// Optional camera focus
	if (bFocusCamera && bIsSelect && ResolvedActors.Num() > 0)
	{
		GEditor->MoveViewportCamerasToActor(ResolvedActors, /*bActiveViewportOnly=*/true);
	}

	// Build result with current selection
	USelection* SelectedActors = GEditor->GetSelectedActors();
	TArray<TSharedPtr<FJsonValue>> SelectedArr;
	for (FSelectionIterator It(*SelectedActors); It; ++It)
	{
		AActor* Actor = Cast<AActor>(*It);
		if (!Actor) continue;

		auto Entry = MakeShared<FJsonObject>();
		Entry->SetStringField(TEXT("name"), Actor->GetActorNameOrLabel());
		Entry->SetStringField(TEXT("label"), Actor->GetActorLabel());
		Entry->SetStringField(TEXT("class"), Actor->GetClass()->GetName());
		Entry->SetArrayField(TEXT("location"), VolumeActionHelpers::VectorToJsonArray(Actor->GetActorLocation()));
		SelectedArr.Add(MakeShared<FJsonValueObject>(Entry));
	}

	auto Result = MakeShared<FJsonObject>();
	Result->SetNumberField(TEXT("selected_count"), SelectedArr.Num());
	Result->SetArrayField(TEXT("selected_actors"), SelectedArr);
	return FMonolithActionResult::Success(Result);
}

// ============================================================================
// 6. snap_to_surface
// ============================================================================

FMonolithActionResult FMonolithMeshVolumeActions::SnapToSurface(const TSharedPtr<FJsonObject>& Params)
{
	const TArray<TSharedPtr<FJsonValue>>* ActorsArr;
	if (!Params->TryGetArrayField(TEXT("actors"), ActorsArr) || ActorsArr->Num() == 0)
	{
		return FMonolithActionResult::Error(TEXT("Missing or empty required param: actors"));
	}

	// Parse direction (default: down)
	FVector Direction(0, 0, -1);
	MonolithMeshUtils::ParseVector(Params, TEXT("direction"), Direction);
	if (Direction.IsNearlyZero())
	{
		return FMonolithActionResult::Error(TEXT("direction must not be zero"));
	}
	Direction.Normalize();

	double TraceLength = 10000.0;
	Params->TryGetNumberField(TEXT("trace_length"), TraceLength);
	if (TraceLength <= 0)
	{
		return FMonolithActionResult::Error(TEXT("trace_length must be positive"));
	}

	bool bAlignToNormal = true;
	Params->TryGetBoolField(TEXT("align_to_normal"), bAlignToNormal);

	double Offset = 0.0;
	Params->TryGetNumberField(TEXT("offset"), Offset);

	// Parse collision channel
	FString ChannelName = TEXT("WorldStatic");
	Params->TryGetStringField(TEXT("channel"), ChannelName);

	// Resolve channel — reuse the spatial actions' approach inline
	ECollisionChannel Channel = ECC_WorldStatic;
	if (ChannelName.Equals(TEXT("Visibility"), ESearchCase::IgnoreCase))      Channel = ECC_Visibility;
	else if (ChannelName.Equals(TEXT("Camera"), ESearchCase::IgnoreCase))     Channel = ECC_Camera;
	else if (ChannelName.Equals(TEXT("WorldStatic"), ESearchCase::IgnoreCase))  Channel = ECC_WorldStatic;
	else if (ChannelName.Equals(TEXT("WorldDynamic"), ESearchCase::IgnoreCase)) Channel = ECC_WorldDynamic;
	else if (ChannelName.Equals(TEXT("Pawn"), ESearchCase::IgnoreCase))       Channel = ECC_Pawn;
	else if (ChannelName.Equals(TEXT("PhysicsBody"), ESearchCase::IgnoreCase)) Channel = ECC_PhysicsBody;

	// Resolve all actors first
	TArray<AActor*> Actors;
	Actors.Reserve(ActorsArr->Num());
	for (const auto& Val : *ActorsArr)
	{
		FString Name = Val->AsString();
		FString Error;
		AActor* Actor = MonolithMeshUtils::FindActorByName(Name, Error);
		if (!Actor)
		{
			return FMonolithActionResult::Error(FString::Printf(TEXT("Actor not found: %s"), *Name));
		}
		Actors.Add(Actor);
	}

	UWorld* World = MonolithMeshUtils::GetEditorWorld();
	if (!World)
	{
		return FMonolithActionResult::Error(TEXT("No editor world available"));
	}

	VolumeActionHelpers::FScopedMeshTransaction Transaction(FText::FromString(TEXT("Monolith: Snap to Surface")));

	TArray<TSharedPtr<FJsonValue>> ResultArr;
	int32 Snapped = 0;
	int32 Missed = 0;

	for (AActor* Actor : Actors)
	{
		FVector ActorLoc = Actor->GetActorLocation();

		// Trace from actor location in the specified direction
		FVector TraceStart = ActorLoc;
		FVector TraceEnd = TraceStart + Direction * TraceLength;

		FCollisionQueryParams QueryParams(SCENE_QUERY_STAT(MonolithSnapToSurface), true);
		QueryParams.AddIgnoredActor(Actor);

		FHitResult Hit;
		bool bHit = World->LineTraceSingleByChannel(Hit, TraceStart, TraceEnd, Channel, QueryParams);

		auto Entry = MakeShared<FJsonObject>();
		Entry->SetStringField(TEXT("actor"), Actor->GetActorNameOrLabel());

		if (bHit)
		{
			// Get actor bounds for half-extent along trace direction
			FVector BoundsOrigin, BoundsExtent;
			Actor->GetActorBounds(false, BoundsOrigin, BoundsExtent);

			// Compute the half-extent projected onto the trace direction
			// This determines how far to offset the actor center from the surface
			double HalfExtentAlongDir = FMath::Abs(FVector::DotProduct(BoundsExtent, Direction));

			// New location: surface point, offset back along direction by half-extent, plus user offset along normal
			FVector NewLoc = Hit.ImpactPoint - Direction * HalfExtentAlongDir;

			// Apply offset along surface normal
			if (!FMath::IsNearlyZero(Offset))
			{
				NewLoc += Hit.ImpactNormal * Offset;
			}

			Actor->SetActorLocation(NewLoc);

			// Align rotation to surface normal
			if (bAlignToNormal)
			{
				FVector ActorForward = Actor->GetActorForwardVector();
				// Build rotation that maps Z to surface normal, keeping forward as close to original as possible
				FMatrix RotMatrix = FRotationMatrix::MakeFromZX(Hit.ImpactNormal, ActorForward);
				FRotator NewRotation = RotMatrix.Rotator();
				Actor->SetActorRotation(NewRotation);
			}

			// Notify editor
			Actor->PostEditMove(true);

			Entry->SetBoolField(TEXT("snapped"), true);
			Entry->SetArrayField(TEXT("new_location"), VolumeActionHelpers::VectorToJsonArray(NewLoc));
			Entry->SetArrayField(TEXT("surface_normal"), VolumeActionHelpers::VectorToJsonArray(Hit.ImpactNormal));

			AActor* HitActor = Hit.GetActor();
			Entry->SetStringField(TEXT("hit_actor"), HitActor ? HitActor->GetActorNameOrLabel() : TEXT("None"));
			Snapped++;
		}
		else
		{
			Entry->SetBoolField(TEXT("snapped"), false);
			Entry->SetStringField(TEXT("reason"), TEXT("No surface found within trace length"));
			Missed++;
		}

		ResultArr.Add(MakeShared<FJsonValueObject>(Entry));
	}

	auto Result = MakeShared<FJsonObject>();
	Result->SetNumberField(TEXT("snapped"), Snapped);
	Result->SetNumberField(TEXT("missed"), Missed);
	Result->SetArrayField(TEXT("results"), ResultArr);

	return FMonolithActionResult::Success(Result);
}

// ============================================================================
// 7. set_collision_preset
// ============================================================================

FMonolithActionResult FMonolithMeshVolumeActions::SetCollisionPreset(const TSharedPtr<FJsonObject>& Params)
{
	FString ActorName;
	if (!Params->TryGetStringField(TEXT("actor_name"), ActorName))
	{
		return FMonolithActionResult::Error(TEXT("Missing required param: actor_name"));
	}

	FString Preset;
	if (!Params->TryGetStringField(TEXT("preset"), Preset))
	{
		return FMonolithActionResult::Error(TEXT("Missing required param: preset"));
	}

	FString Error;
	AActor* Actor = MonolithMeshUtils::FindActorByName(ActorName, Error);
	if (!Actor)
	{
		return FMonolithActionResult::Error(Error);
	}

	// Find target component
	UPrimitiveComponent* PrimitiveComp = nullptr;

	FString ComponentName;
	if (Params->TryGetStringField(TEXT("component"), ComponentName))
	{
		UActorComponent* Comp = VolumeActionHelpers::FindComponentByClassName(Actor, ComponentName);
		if (!Comp)
		{
			return FMonolithActionResult::Error(FString::Printf(
				TEXT("Component '%s' not found on actor '%s'"), *ComponentName, *ActorName));
		}
		PrimitiveComp = Cast<UPrimitiveComponent>(Comp);
		if (!PrimitiveComp)
		{
			return FMonolithActionResult::Error(FString::Printf(
				TEXT("Component '%s' is not a PrimitiveComponent — cannot set collision"), *ComponentName));
		}
	}
	else
	{
		// Default to root primitive
		PrimitiveComp = Cast<UPrimitiveComponent>(Actor->GetRootComponent());
		if (!PrimitiveComp)
		{
			return FMonolithActionResult::Error(TEXT("Actor's root component is not a PrimitiveComponent — cannot set collision. Specify a component name."));
		}
	}

	// Validate the collision profile exists
	FCollisionResponseTemplate Template;
	if (!UCollisionProfile::Get()->GetProfileTemplate(FName(*Preset), Template))
	{
		// Profile not found — warn but still apply (it may be a custom name defined elsewhere)
		// UE will log a warning internally
	}

	VolumeActionHelpers::FScopedMeshTransaction Transaction(FText::FromString(TEXT("Monolith: Set Collision Preset")));

	PrimitiveComp->Modify();

	FString PreviousProfile = PrimitiveComp->GetCollisionProfileName().ToString();
	PrimitiveComp->SetCollisionProfileName(FName(*Preset));

	Actor->MarkPackageDirty();

	auto Result = MakeShared<FJsonObject>();
	Result->SetStringField(TEXT("actor_name"), Actor->GetActorNameOrLabel());
	Result->SetStringField(TEXT("component"), PrimitiveComp->GetFName().ToString());
	Result->SetStringField(TEXT("previous_preset"), PreviousProfile);
	Result->SetStringField(TEXT("new_preset"), Preset);

	return FMonolithActionResult::Success(Result);
}
