#pragma once

#include "CoreMinimal.h"
#include "MonolithToolRegistry.h"

class UObject;
class UWorld;
class AActor;
class FProperty;
class FJsonValue;
class FJsonObject;

// Shared PIE-object resolution + property-read helpers for the live-PIE actions
// (pie_get_object_properties / pie_call_function) and reused by sample_pie_timeseries
// (Gap 9) for its dotted-variable read surface. All game-thread-only.
namespace MonolithPieObject
{
	// Outcome of resolving a target object inside the live PIE world. On failure
	// bSuccess is false and Error carries a clean user-facing message; on success
	// Object is the resolved target (actor, a named component on it, or the
	// component's skeletal-mesh anim instance).
	struct FResolvedObject
	{
		UObject* Object = nullptr;     // the resolved target object
		AActor* Actor = nullptr;       // the owning actor (always set on success)
		FString ResolvedName;          // label/name we matched on (for the report echo)
		bool bSuccess = false;
		FString Error;                 // populated only when bSuccess == false
	};

	// Resolve the active PIE world (first EWorldType::PIE context), or nullptr.
	UWorld* FindPieWorld();

	// Resolve a target object in the live PIE world from a params blob:
	//   actor_label | object_name | class_name (substring) — actor selector (one required);
	//   component_name (optional) — hop to a named component on the actor;
	//   anim_instance (optional bool) — hop to the skeletal mesh component's anim instance.
	// Returns a clean error when PIE is not running or nothing matches.
	FResolvedObject Resolve(const TSharedPtr<FJsonObject>& Params);

	// Read an already-resolved property leaf into a JSON value. Mirrors the
	// MonolithAnimation ReadResolvedValue conventions: common scalars directly,
	// ExportText fallback for enums/structs/vectors. OutTypeName receives the CPP type.
	TSharedPtr<FJsonValue> ReadLeafValue(const FProperty* Prop, const void* ValuePtr,
		const UObject* OwnerForExport, FString& OutTypeName);

	// Read a dotted (UDS-friendly) member path off an object into a JSON value,
	// resolving via the shared MonolithStructField resolver. Null when unresolved
	// (OutTypeName set to a diagnostic token).
	TSharedPtr<FJsonValue> ReadDottedValue(UObject* Obj, const FString& Path, FString& OutTypeName);
}

// pie_get_object_properties / pie_call_function — synchronous live-PIE actions.
class FMonolithPieObjectActions
{
public:
	static void RegisterActions(FMonolithToolRegistry& Registry);

	static FMonolithActionResult HandleGetObjectProperties(const TSharedPtr<FJsonObject>& Params);
	static FMonolithActionResult HandleCallFunction(const TSharedPtr<FJsonObject>& Params);
};
