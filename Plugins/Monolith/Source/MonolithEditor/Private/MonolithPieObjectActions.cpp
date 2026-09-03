#include "MonolithPieObjectActions.h"
#include "MonolithParamSchema.h"
#include "MonolithStructFieldResolver.h"

#include "Editor.h"
#include "Engine/Engine.h"
#include "Engine/World.h"
#include "EngineUtils.h"
#include "GameFramework/Actor.h"
#include "Components/ActorComponent.h"
#include "Components/SkeletalMeshComponent.h"
#include "Animation/AnimInstance.h"
#include "Dom/JsonObject.h"
#include "Dom/JsonValue.h"
#include "UObject/UnrealType.h"
#include "UObject/Class.h"
#include "UObject/Field.h"
#include "UObject/UObjectGlobals.h"
#include "StructUtils/UserDefinedStruct.h"

DEFINE_LOG_CATEGORY_STATIC(LogMonolithPieObject, Log, All);

namespace MonolithPieObject
{
	UWorld* FindPieWorld()
	{
		if (!GEditor)
		{
			return nullptr;
		}
		for (const FWorldContext& Context : GEditor->GetWorldContexts())
		{
			if (Context.WorldType == EWorldType::PIE && Context.World())
			{
				return Context.World();
			}
		}
		return nullptr;
	}

	namespace
	{
		// Resolve the actor selector. actor_label / object_name match exactly on the
		// editor label or object name; class_name matches a substring of the class name.
		// First match wins (deterministic actor iteration order). Returns nullptr + a
		// reason when nothing matches.
		AActor* ResolveActor(UWorld* PieWorld, const FString& ActorLabel,
			const FString& ObjectName, const FString& ClassName, FString& OutMatched, FString& OutError)
		{
			for (TActorIterator<AActor> It(PieWorld); It; ++It)
			{
				AActor* Candidate = *It;
				if (!Candidate) { continue; }

#if WITH_EDITOR
				const FString Label = Candidate->GetActorLabel();
#else
				const FString Label;
#endif
				const FString Name = Candidate->GetName();
				const FString Cls = Candidate->GetClass() ? Candidate->GetClass()->GetName() : FString();

				if (!ActorLabel.IsEmpty() && Label == ActorLabel)
				{
					OutMatched = Label;
					return Candidate;
				}
				if (!ObjectName.IsEmpty() && Name == ObjectName)
				{
					OutMatched = Name;
					return Candidate;
				}
				if (!ClassName.IsEmpty() && Cls.Contains(ClassName))
				{
					OutMatched = FString::Printf(TEXT("%s (%s)"), *Label, *Cls);
					return Candidate;
				}
			}
			OutError = TEXT("No PIE actor matched the actor_label / object_name / class_name selector");
			return nullptr;
		}

		// Find a named component on the actor, or the first component when Name is empty.
		UActorComponent* ResolveComponent(AActor* Actor, const FString& ComponentName, FString& OutError)
		{
			for (UActorComponent* C : Actor->GetComponents())
			{
				if (!C) { continue; }
				if (ComponentName.IsEmpty() || C->GetName() == ComponentName)
				{
					return C;
				}
			}
			OutError = FString::Printf(TEXT("No component named '%s' on actor '%s'"),
				*ComponentName, *Actor->GetName());
			return nullptr;
		}
	}

	FResolvedObject Resolve(const TSharedPtr<FJsonObject>& Params)
	{
		FResolvedObject Out;

		UWorld* PieWorld = FindPieWorld();
		if (!PieWorld)
		{
			Out.Error = TEXT("PIE not running — start Play-In-Editor first");
			return Out;
		}

		FString ActorLabel, ObjectName, ClassName;
		Params->TryGetStringField(TEXT("actor_label"), ActorLabel);
		Params->TryGetStringField(TEXT("object_name"), ObjectName);
		Params->TryGetStringField(TEXT("class_name"), ClassName);
		if (ActorLabel.IsEmpty() && ObjectName.IsEmpty() && ClassName.IsEmpty())
		{
			Out.Error = TEXT("Require one of: actor_label, object_name, class_name");
			return Out;
		}

		FString MatchError;
		AActor* Actor = ResolveActor(PieWorld, ActorLabel, ObjectName, ClassName, Out.ResolvedName, MatchError);
		if (!Actor)
		{
			Out.Error = MatchError;
			return Out;
		}
		Out.Actor = Actor;
		Out.Object = Actor;

		// Optional component hop.
		FString ComponentName;
		const bool bHasComponent = Params->TryGetStringField(TEXT("component_name"), ComponentName) && !ComponentName.IsEmpty();

		bool bWantAnimInstance = false;
		Params->TryGetBoolField(TEXT("anim_instance"), bWantAnimInstance);

		if (bWantAnimInstance)
		{
			// Hop to the (named or first) skeletal mesh component's anim instance.
			USkeletalMeshComponent* SkelComp = nullptr;
			for (UActorComponent* C : Actor->GetComponents())
			{
				USkeletalMeshComponent* MC = Cast<USkeletalMeshComponent>(C);
				if (!MC) { continue; }
				if (!bHasComponent || MC->GetName() == ComponentName)
				{
					SkelComp = MC;
					break;
				}
			}
			if (!SkelComp)
			{
				Out.Error = bHasComponent
					? FString::Printf(TEXT("No skeletal mesh component named '%s' on actor '%s'"), *ComponentName, *Actor->GetName())
					: FString::Printf(TEXT("No skeletal mesh component on actor '%s' (needed for anim_instance)"), *Actor->GetName());
				Out.Object = nullptr;
				return Out;
			}
			UAnimInstance* Anim = SkelComp->GetAnimInstance();
			if (!Anim)
			{
				Out.Error = FString::Printf(TEXT("Skeletal mesh component '%s' has no active anim instance"), *SkelComp->GetName());
				Out.Object = nullptr;
				return Out;
			}
			Out.Object = Anim;
			Out.bSuccess = true;
			return Out;
		}

		if (bHasComponent)
		{
			FString CompError;
			UActorComponent* Comp = ResolveComponent(Actor, ComponentName, CompError);
			if (!Comp)
			{
				Out.Error = CompError;
				Out.Object = nullptr;
				return Out;
			}
			Out.Object = Comp;
		}

		Out.bSuccess = true;
		return Out;
	}

	TSharedPtr<FJsonValue> ReadLeafValue(const FProperty* Prop, const void* ValuePtr,
		const UObject* OwnerForExport, FString& OutTypeName)
	{
		if (!Prop || !ValuePtr)
		{
			OutTypeName = TEXT("<not found>");
			return nullptr;
		}
		OutTypeName = Prop->GetCPPType(nullptr, 0u);

		if (const FBoolProperty* BoolProp = CastField<FBoolProperty>(Prop))
		{
			return MakeShared<FJsonValueBoolean>(BoolProp->GetPropertyValue(ValuePtr));
		}
		if (const FFloatProperty* FloatProp = CastField<FFloatProperty>(Prop))
		{
			return MakeShared<FJsonValueNumber>(FloatProp->GetPropertyValue(ValuePtr));
		}
		if (const FDoubleProperty* DoubleProp = CastField<FDoubleProperty>(Prop))
		{
			return MakeShared<FJsonValueNumber>(DoubleProp->GetPropertyValue(ValuePtr));
		}
		if (const FIntProperty* IntProp = CastField<FIntProperty>(Prop))
		{
			return MakeShared<FJsonValueNumber>(IntProp->GetPropertyValue(ValuePtr));
		}
		if (const FStrProperty* StrProp = CastField<FStrProperty>(Prop))
		{
			return MakeShared<FJsonValueString>(StrProp->GetPropertyValue(ValuePtr));
		}
		if (const FNameProperty* NameProp = CastField<FNameProperty>(Prop))
		{
			return MakeShared<FJsonValueString>(NameProp->GetPropertyValue(ValuePtr).ToString());
		}
		if (const FObjectPropertyBase* ObjProp = CastField<FObjectPropertyBase>(Prop))
		{
			UObject* Val = ObjProp->GetObjectPropertyValue(ValuePtr);
			return MakeShared<FJsonValueString>(Val ? Val->GetPathName() : TEXT("None"));
		}

		// Generic fallback (enums, structs, vectors, etc.) — same convention as the
		// MonolithAnimation runtime ReadResolvedValue.
		FString Exported;
		Prop->ExportTextItem_Direct(Exported, ValuePtr, nullptr, const_cast<UObject*>(OwnerForExport), PPF_None);
		return MakeShared<FJsonValueString>(Exported);
	}

	TSharedPtr<FJsonValue> ReadDottedValue(UObject* Obj, const FString& Path, FString& OutTypeName)
	{
		if (!Obj)
		{
			OutTypeName = TEXT("<not found>");
			return nullptr;
		}
		const MonolithStructField::FResolved Resolved = MonolithStructField::Resolve(Obj, Path);
		if (!Resolved.Leaf)
		{
			OutTypeName = FString::Printf(TEXT("<unresolved: %s>"), *Resolved.FailedSegment);
			return nullptr;
		}
		return ReadLeafValue(Resolved.Leaf, Resolved.ValuePtr, Obj, OutTypeName);
	}
}

// ── pie_call_function arg-marshalling support ──────────────────────────

namespace
{
	using namespace MonolithPieObject;

	// RAII parameter frame for a UFunction: allocates ParmsSize bytes, InitializeValue's
	// each property in the function's property chain, and DestroyValue's them on scope
	// exit. Holding live object refs in an uninitialised / un-destroyed frame is a GC /
	// crash risk, so construction + destruction are paired exactly once.
	struct FScopedFunctionFrame
	{
		UFunction* Function = nullptr;
		uint8* Memory = nullptr;

		explicit FScopedFunctionFrame(UFunction* InFunction)
			: Function(InFunction)
		{
			if (!Function)
			{
				return;
			}
			const int32 Size = FMath::Max<int32>(Function->ParmsSize, 0);
			Memory = (uint8*)FMemory::Malloc(FMath::Max(Size, 1));
			FMemory::Memzero(Memory, FMath::Max(Size, 1));
			for (TFieldIterator<FProperty> It(Function); It && (It->PropertyFlags & CPF_Parm); ++It)
			{
				FProperty* Prop = *It;
				Prop->InitializeValue_InContainer(Memory);
			}
		}

		~FScopedFunctionFrame()
		{
			if (!Function || !Memory)
			{
				if (Memory) { FMemory::Free(Memory); Memory = nullptr; }
				return;
			}
			for (TFieldIterator<FProperty> It(Function); It && (It->PropertyFlags & CPF_Parm); ++It)
			{
				FProperty* Prop = *It;
				Prop->DestroyValue_InContainer(Memory);
			}
			FMemory::Free(Memory);
			Memory = nullptr;
		}

		FScopedFunctionFrame(const FScopedFunctionFrame&) = delete;
		FScopedFunctionFrame& operator=(const FScopedFunctionFrame&) = delete;
	};

	// Render a JSON scalar value to import-text (the form ImportText_Direct expects for a
	// primitive property). Returns false for non-scalar JSON (object/array) which the
	// caller routes to the struct path instead.
	bool JsonScalarToImportText(const TSharedPtr<FJsonValue>& Value, FString& Out)
	{
		if (!Value.IsValid()) { return false; }
		switch (Value->Type)
		{
		case EJson::Boolean:
			Out = Value->AsBool() ? TEXT("true") : TEXT("false");
			return true;
		case EJson::Number:
		{
			const double N = Value->AsNumber();
			// Emit integers without a trailing ".0" so int/byte/enum imports parse cleanly.
			if (FMath::IsNearlyEqual(N, FMath::RoundToDouble(N)) && FMath::Abs(N) < 1.0e15)
			{
				Out = FString::Printf(TEXT("%lld"), (int64)FMath::RoundToDouble(N));
			}
			else
			{
				Out = FString::SanitizeFloat(N);
			}
			return true;
		}
		case EJson::String:
			Out = Value->AsString();
			return true;
		case EJson::Null:
			Out = TEXT("None");
			return true;
		default:
			return false; // object / array — not a scalar
		}
	}

	// Marshal a JSON object whose keys are friendly UDS field names into a struct value
	// pointer. For each JSON key: resolve the friendly name to the internal FProperty via
	// the shared resolver, then import the value. v1 supports scalar fields and ONE level
	// of nested struct (a JSON object value whose own keys are friendly fields). Deeper
	// nesting is rejected with a clear error. Returns false + OutError on any failure.
	bool MarshalStructFromJson(const UScriptStruct* Struct, void* StructPtr,
		const TSharedPtr<FJsonObject>& Json, UObject* Owner, int32 Depth, FString& OutError);

	// Import one JSON value into one resolved property leaf. Scalars go through
	// ImportText_Direct; a JSON object targeting a struct property recurses (one level).
	bool ImportJsonIntoProperty(FProperty* Prop, void* ValuePtr, const TSharedPtr<FJsonValue>& Value,
		UObject* Owner, int32 Depth, FString& OutError)
	{
		// Nested struct: JSON object → struct fields (one level only).
		if (Value.IsValid() && Value->Type == EJson::Object)
		{
			const FStructProperty* StructProp = CastField<FStructProperty>(Prop);
			if (!StructProp || !StructProp->Struct)
			{
				OutError = FString::Printf(TEXT("field '%s' got a JSON object but is not a struct property"), *Prop->GetName());
				return false;
			}
			if (Depth >= 1)
			{
				OutError = FString::Printf(TEXT("field '%s' nests deeper than one struct level (v1 limit: top-level + one nested struct)"), *Prop->GetName());
				return false;
			}
			return MarshalStructFromJson(StructProp->Struct, ValuePtr, Value->AsObject(), Owner, Depth + 1, OutError);
		}

		// Scalar / string → import text.
		FString ImportText;
		if (!JsonScalarToImportText(Value, ImportText))
		{
			OutError = FString::Printf(TEXT("field '%s' has an unsupported JSON value (arrays not supported in v1)"), *Prop->GetName());
			return false;
		}
		const TCHAR* Result = Prop->ImportText_Direct(*ImportText, ValuePtr, Owner, PPF_None);
		if (Result == nullptr)
		{
			OutError = FString::Printf(TEXT("failed to import value '%s' into field '%s' (type %s)"),
				*ImportText, *Prop->GetName(), *Prop->GetCPPType(nullptr, 0u));
			return false;
		}
		return true;
	}

	bool MarshalStructFromJson(const UScriptStruct* Struct, void* StructPtr,
		const TSharedPtr<FJsonObject>& Json, UObject* Owner, int32 Depth, FString& OutError)
	{
		if (!Struct || !StructPtr || !Json.IsValid())
		{
			OutError = TEXT("internal: null struct/value/json in struct marshal");
			return false;
		}
		for (const TPair<FString, TSharedPtr<FJsonValue>>& Field : Json->Values)
		{
			// Resolve the friendly field name within THIS struct to its internal property.
			// (The shared MonolithStructField resolver needs a UObject container; a bare
			// struct value has none, so fields are resolved inline against the UScriptStruct.)
			const FProperty* FoundConst = Struct->FindPropertyByName(FName(*Field.Key));
			if (!FoundConst)
			{
				// UDS friendly-name match: iterate fields, compare authored name.
				if (const UUserDefinedStruct* UserStruct = Cast<UUserDefinedStruct>(Struct))
				{
					for (TFieldIterator<FProperty> It(UserStruct); It; ++It)
					{
						if (UserStruct->GetAuthoredNameForField(*It) == Field.Key)
						{
							FoundConst = *It;
							break;
						}
					}
				}
			}
			if (!FoundConst)
			{
				OutError = FString::Printf(TEXT("struct field '%s' not found on %s"), *Field.Key, *Struct->GetName());
				return false;
			}
			FProperty* FieldProp = const_cast<FProperty*>(FoundConst);
			void* FieldPtr = FieldProp->ContainerPtrToValuePtr<void>(StructPtr);
			if (!ImportJsonIntoProperty(FieldProp, FieldPtr, Field.Value, Owner, Depth, OutError))
			{
				return false;
			}
		}
		return true;
	}
}

// ── Registration ──────────────────────────────────────────────────────

void FMonolithPieObjectActions::RegisterActions(FMonolithToolRegistry& Registry)
{
	Registry.RegisterAction(TEXT("editor"), TEXT("pie_get_object_properties"),
		TEXT("Read live UPROPERTY values off a resolved Play-In-Editor object by dotted member path. "
		     "Resolve the target with actor_label / object_name / class_name (substring); optionally hop to a named component_name, "
		     "or set anim_instance=true to read the skeletal mesh's active anim instance. 'properties' is an array of dotted paths "
		     "(e.g. 'CharacterProperties.OrientationIntent') that descend nested structs and match UserDefinedStruct members by their "
		     "friendly (authored) name — the GUID-suffixed internal names editor python cannot read. Returns each path's JSON value "
		     "(scalars directly; enums/structs/vectors as export text). Read-only. No-ops with a clean error when PIE is not running."),
		FMonolithActionHandler::CreateStatic(&HandleGetObjectProperties),
		FParamSchemaBuilder()
			.Optional(TEXT("actor_label"), TEXT("string"), TEXT("Exact editor (Outliner) label of the target actor."))
			.Optional(TEXT("object_name"), TEXT("string"), TEXT("Exact object name of the target actor."))
			.Optional(TEXT("class_name"), TEXT("string"), TEXT("Substring of the target actor's class name (first match wins). One of actor_label/object_name/class_name is required."))
			.Optional(TEXT("component_name"), TEXT("string"), TEXT("Name of a component on the resolved actor to read from instead of the actor itself."))
			.Optional(TEXT("anim_instance"), TEXT("bool"), TEXT("If true, read from the (named or first) skeletal mesh component's active anim instance."), TEXT("false"))
			.Required(TEXT("properties"), TEXT("array"), TEXT("Dotted member paths to read (e.g. ['Movement.Speed','CharacterProperties.OrientationIntent']). Struct-member traversal only; array/map indexing not supported."))
			.Build());

	Registry.RegisterAction(TEXT("editor"), TEXT("pie_call_function"),
		TEXT("Call a BlueprintCallable function/event on a resolved live PIE object, marshalling JSON args into the UFunction parameter frame and invoking via ProcessEvent. "
		     "MUTATES LIVE PIE STATE — this executes real gameplay code, it is NOT read-only. Resolve the target like pie_get_object_properties (actor_label/object_name/class_name, optional component_name/anim_instance). "
		     "'function' is the UFunction name. 'args' is a JSON object keyed by parameter name; primitives import directly, and a struct (incl. UserDefinedStruct with GUID-suffixed fields) is built from a nested JSON object whose keys are the friendly field names. "
		     "v1 supports top-level args + one level of nested struct (deeper nesting is rejected). Requires FUNC_BlueprintCallable unless allow_non_callable=true; rejects network-replicated (FUNC_Net) and latent functions. "
		     "Returns out-params + the return value. No-ops with a clean error when PIE is not running."),
		FMonolithActionHandler::CreateStatic(&HandleCallFunction),
		FParamSchemaBuilder()
			.Optional(TEXT("actor_label"), TEXT("string"), TEXT("Exact editor label of the target actor."))
			.Optional(TEXT("object_name"), TEXT("string"), TEXT("Exact object name of the target actor."))
			.Optional(TEXT("class_name"), TEXT("string"), TEXT("Substring of the target actor's class name. One of actor_label/object_name/class_name is required."))
			.Optional(TEXT("component_name"), TEXT("string"), TEXT("Component on the resolved actor to call the function on."))
			.Optional(TEXT("anim_instance"), TEXT("bool"), TEXT("If true, call on the skeletal mesh component's active anim instance."), TEXT("false"))
			.Required(TEXT("function"), TEXT("string"), TEXT("UFunction name to call (FindFunctionByName)."))
			.Optional(TEXT("args"), TEXT("object"), TEXT("JSON object of arguments keyed by parameter name. Struct params take a nested JSON object keyed by friendly field names. v1: top-level + one nested struct level."))
			.Optional(TEXT("allow_non_callable"), TEXT("bool"), TEXT("If true, allow functions that are not flagged FUNC_BlueprintCallable. Net/latent functions are still rejected. Default false."), TEXT("false"))
			.Build());

	UE_LOG(LogMonolithPieObject, Log, TEXT("MonolithEditor: registered 2 live-PIE object actions"));
}

// ── pie_get_object_properties ──────────────────────────────────────────

FMonolithActionResult FMonolithPieObjectActions::HandleGetObjectProperties(const TSharedPtr<FJsonObject>& Params)
{
	const MonolithPieObject::FResolvedObject Resolved = MonolithPieObject::Resolve(Params);
	if (!Resolved.bSuccess)
	{
		return FMonolithActionResult::Error(Resolved.Error);
	}

	const TArray<TSharedPtr<FJsonValue>>* PropsArr = nullptr;
	if (!Params->TryGetArrayField(TEXT("properties"), PropsArr) || !PropsArr || PropsArr->Num() == 0)
	{
		return FMonolithActionResult::Error(TEXT("pie_get_object_properties requires a non-empty 'properties' array of dotted paths"));
	}

	TSharedPtr<FJsonObject> Root = MakeShared<FJsonObject>();
	Root->SetStringField(TEXT("resolved"), Resolved.ResolvedName);
	Root->SetStringField(TEXT("object"), Resolved.Object->GetName());
	Root->SetStringField(TEXT("object_class"), Resolved.Object->GetClass()->GetPathName());

	TSharedPtr<FJsonObject> ValuesObj = MakeShared<FJsonObject>();
	for (const TSharedPtr<FJsonValue>& V : *PropsArr)
	{
		FString Path;
		if (!V.IsValid() || !V->TryGetString(Path) || Path.IsEmpty()) { continue; }
		FString TypeName;
		TSharedPtr<FJsonValue> Val = MonolithPieObject::ReadDottedValue(Resolved.Object, Path, TypeName);
		if (Val.IsValid())
		{
			ValuesObj->SetField(Path, Val);
		}
		else
		{
			ValuesObj->SetStringField(Path, FString::Printf(TEXT("<%s>"), *TypeName));
		}
	}
	Root->SetObjectField(TEXT("properties"), ValuesObj);

	return FMonolithActionResult::Success(Root);
}

// ── pie_call_function ──────────────────────────────────────────────────

FMonolithActionResult FMonolithPieObjectActions::HandleCallFunction(const TSharedPtr<FJsonObject>& Params)
{
	const MonolithPieObject::FResolvedObject Resolved = MonolithPieObject::Resolve(Params);
	if (!Resolved.bSuccess)
	{
		return FMonolithActionResult::Error(Resolved.Error);
	}
	UObject* Obj = Resolved.Object;

	FString FunctionName;
	if (!Params->TryGetStringField(TEXT("function"), FunctionName) || FunctionName.IsEmpty())
	{
		return FMonolithActionResult::Error(TEXT("pie_call_function requires a 'function' name"));
	}

	UFunction* Function = Obj->GetClass()->FindFunctionByName(FName(*FunctionName));
	if (!Function)
	{
		return FMonolithActionResult::Error(FString::Printf(
			TEXT("Function '%s' not found on %s"), *FunctionName, *Obj->GetClass()->GetPathName()));
	}

	// Reject latent + network-replicated functions: ProcessEvent runs synchronously and
	// locally, so a latent function (needs a FLatentActionInfo/world-managed completion)
	// or a FUNC_Net replicated call would behave incorrectly. Latent functions are marked by
	// the "Latent" UFunction metadata (FBlueprintMetadata::MD_Latent), not a FUNC_* flag —
	// metadata is WITH_METADATA-only (always on for this Editor-type module).
#if WITH_METADATA
	if (Function->HasMetaData(TEXT("Latent")))
	{
		return FMonolithActionResult::Error(FString::Printf(
			TEXT("Function '%s' is latent — a synchronous ProcessEvent cannot drive it. Rejected."), *FunctionName));
	}
#endif
	if (Function->HasAnyFunctionFlags(FUNC_Net))
	{
		return FMonolithActionResult::Error(FString::Printf(
			TEXT("Function '%s' is network-replicated (FUNC_Net) — ProcessEvent bypasses replication routing. Rejected."), *FunctionName));
	}

	bool bAllowNonCallable = false;
	Params->TryGetBoolField(TEXT("allow_non_callable"), bAllowNonCallable);
	if (!bAllowNonCallable && !Function->HasAnyFunctionFlags(FUNC_BlueprintCallable))
	{
		return FMonolithActionResult::Error(FString::Printf(
			TEXT("Function '%s' is not FUNC_BlueprintCallable. Pass allow_non_callable=true to call it anyway."), *FunctionName));
	}

	// Build + initialise the parameter frame (RAII destroys it on scope exit).
	FScopedFunctionFrame Frame(Function);
	if (!Frame.Memory)
	{
		return FMonolithActionResult::Error(TEXT("Failed to allocate the function parameter frame"));
	}

	const TSharedPtr<FJsonObject>* ArgsObj = nullptr;
	const bool bHasArgs = Params->TryGetObjectField(TEXT("args"), ArgsObj) && ArgsObj && (*ArgsObj).IsValid();

	// Marshal each input parameter (CPF_Parm, not Return, not pure-Out) from args by name.
	for (TFieldIterator<FProperty> It(Function); It && (It->PropertyFlags & CPF_Parm); ++It)
	{
		FProperty* Prop = *It;
		// Skip return params and pure out-params (no incoming value to marshal). A
		// reference (in/out) param is still filled from args when supplied.
		if (Prop->HasAnyPropertyFlags(CPF_ReturnParm)) { continue; }
		if (Prop->HasAnyPropertyFlags(CPF_OutParm) && !Prop->HasAnyPropertyFlags(CPF_ReferenceParm)) { continue; }

		if (!bHasArgs) { continue; }
		const TSharedPtr<FJsonValue> ArgVal = (*ArgsObj)->TryGetField(Prop->GetName());
		if (!ArgVal.IsValid()) { continue; } // not supplied — leave default-initialised

		void* ValuePtr = Prop->ContainerPtrToValuePtr<void>(Frame.Memory);
		FString MarshalError;
		if (!ImportJsonIntoProperty(Prop, ValuePtr, ArgVal, Obj, /*Depth=*/0, MarshalError))
		{
			return FMonolithActionResult::Error(FString::Printf(
				TEXT("Argument marshalling failed: %s"), *MarshalError));
		}
	}

	// Invoke on the game thread (the MCP handler IS the game thread).
	Obj->ProcessEvent(Function, Frame.Memory);

	// Read back out-params + the return value.
	TSharedPtr<FJsonObject> Root = MakeShared<FJsonObject>();
	Root->SetStringField(TEXT("resolved"), Resolved.ResolvedName);
	Root->SetStringField(TEXT("object"), Obj->GetName());
	Root->SetStringField(TEXT("function"), FunctionName);
	Root->SetBoolField(TEXT("called"), true);

	TSharedPtr<FJsonObject> OutParams = MakeShared<FJsonObject>();
	TSharedPtr<FJsonValue> ReturnValue;
	for (TFieldIterator<FProperty> It(Function); It && (It->PropertyFlags & CPF_Parm); ++It)
	{
		FProperty* Prop = *It;
		const bool bReturn = Prop->HasAnyPropertyFlags(CPF_ReturnParm);
		const bool bOut = Prop->HasAnyPropertyFlags(CPF_OutParm);
		if (!bReturn && !bOut) { continue; }

		const void* ValuePtr = Prop->ContainerPtrToValuePtr<void>(Frame.Memory);
		FString TypeName;
		TSharedPtr<FJsonValue> Val = MonolithPieObject::ReadLeafValue(Prop, ValuePtr, Obj, TypeName);
		if (!Val.IsValid()) { continue; }
		if (bReturn)
		{
			ReturnValue = Val;
		}
		else
		{
			OutParams->SetField(Prop->GetName(), Val);
		}
	}
	if (ReturnValue.IsValid())
	{
		Root->SetField(TEXT("return_value"), ReturnValue);
	}
	if (OutParams->Values.Num() > 0)
	{
		Root->SetObjectField(TEXT("out_params"), OutParams);
	}

	return FMonolithActionResult::Success(Root);
}
