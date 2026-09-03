#pragma once

#include "CoreMinimal.h"
#include "Dom/JsonObject.h"
#include "Dom/JsonValue.h"
#include "UObject/UnrealType.h"
#include "UObject/Field.h"
#include "AnimGraphNode_Base.h"           // UAnimGraphNode_Base + FAnimGraphNodePropertyBinding (public)
#include "Engine/MemberReference.h"        // FMemberReference (public accessors)
#include "Kismet2/BlueprintEditorUtils.h"  // HasFunctionBlueprintThreadSafeMetaData

// ============================================================
//  MonolithAnimNodeBindingReader  (Gap 2 + Gap 12 — anim-node bindings)
//
//  Two distinct binding surfaces live on UAnimGraphNode_Base:
//
//  Gap 2 — FUNCTION bindings. Three public FMemberReference UPROPERTYs
//    (InitialUpdateFunction / BecomeRelevantFunction / UpdateFunction,
//    AnimGraphNode_Base.h:220/224/228). Linkable directly; serialized via
//    the public FMemberReference accessors (GetMemberName / GetMemberParentClass
//    / IsSelfContext) + the engine's own thread-safe gate.
//
//  Gap 12 — PIN property bindings. The node's binding object lives in the
//    `Binding` UPROPERTY (AnimGraphNode_Base.h:233, type UAnimGraphNodeBinding).
//    UAnimGraphNodeBinding is ONLY FORWARD-declared in reachable headers — its
//    defining header is in AnimGraph/Internal/, an include path not exposed to
//    non-engine plugin modules — so the type is INCOMPLETE here. We therefore must
//    NOT call GetBinding()/GetMutableBinding() (their return type is the incomplete
//    class; even an implicit conversion to UObject* needs the complete type) and must
//    NOT make any member call through a UAnimGraphNodeBinding* (even GetClass/Modify,
//    inherited from UObject, trip C2027). Instead the `Binding` UPROPERTY is read
//    reflectively as a plain UObject* (FObjectProperty::GetObjectPropertyValue_InContainer),
//    and every GetClass()/Modify() goes through that complete UObject*. The concrete
//    UAnimGraphNodeBinding_Base::PropertyBindings TMap<FName, FAnimGraphNodePropertyBinding>
//    is then reached the same way Gap 1 reaches private fields: FindFProperty on the
//    runtime class + FScriptMapHelper. The VALUE struct FAnimGraphNodePropertyBinding
//    IS public (AnimGraphNode_Base.h:138) so the value ptr is cast to it directly.
//
//  Header-only inline (the Gap-1 MonolithPropertyAccessReader pattern): MonolithCore
//  deps Engine but NOT AnimGraph, so the bodies must compile at the include site
//  (MonolithAnimation, which already deps AnimGraph + includes AnimGraphNode_Base.h).
//  No MonolithCore Build.cs dependency is added.
//
//  Degrades gracefully on engine-layout drift: a missing PropertyBindings property
//  (a non-_Base binding subclass) yields an empty list + a `note`, never an error.
//  The reflected map/field names (`PropertyBindings`) and the public struct fields
//  are an engine-layout dependency shared with the write path.
// ============================================================

namespace MonolithAnimNodeBindingReader
{
	// ---- Gap 2: function bindings ----

	// Serialize one FMemberReference into { function_name, member_parent_class,
	// is_self_context, thread_safe }. Always returns an object so callers can read
	// the shape even for an empty reference (function_name = null). `OwnerClass`
	// (the AnimBP skeleton/generated class) resolves the UFunction for the
	// thread_safe flag; may be null (thread_safe omitted then).
	inline TSharedPtr<FJsonObject> SerializeFunctionBinding(const FMemberReference& Ref, UClass* OwnerClass)
	{
		TSharedPtr<FJsonObject> Out = MakeShared<FJsonObject>();
		const FName MemberName = Ref.GetMemberName();
		if (MemberName == NAME_None)
		{
			Out->SetField(TEXT("function_name"), MakeShared<FJsonValueNull>());
			return Out;
		}

		Out->SetStringField(TEXT("function_name"), MemberName.ToString());
		Out->SetBoolField(TEXT("is_self_context"), Ref.IsSelfContext());
		if (UClass* ParentClass = Ref.GetMemberParentClass())
		{
			Out->SetStringField(TEXT("member_parent_class"), ParentClass->GetPathName());
		}
		else
		{
			Out->SetField(TEXT("member_parent_class"), MakeShared<FJsonValueNull>());
		}

		// thread_safe: resolve the UFunction against the owning class and apply the
		// engine's own gate. Omitted (rather than guessed) when unresolvable.
		if (OwnerClass)
		{
			// ResolveMember<UFunction> is a const member (MemberReference.h:329).
			const UFunction* Func = Ref.ResolveMember<UFunction>(OwnerClass);
			if (Func)
			{
				Out->SetBoolField(TEXT("thread_safe"),
					FBlueprintEditorUtils::HasFunctionBlueprintThreadSafeMetaData(Func));
			}
		}
		return Out;
	}

	// Returns true if ANY of the three function bindings on the node is non-empty.
	inline bool HasAnyFunctionBinding(UAnimGraphNode_Base* AnimNode)
	{
		if (!AnimNode) return false;
		return AnimNode->InitialUpdateFunction.GetMemberName() != NAME_None
			|| AnimNode->BecomeRelevantFunction.GetMemberName() != NAME_None
			|| AnimNode->UpdateFunction.GetMemberName() != NAME_None;
	}

	// Emit a compact { initial_update / become_relevant / update: name-or-null }
	// object onto OutNode under "bindings" — omitted entirely when all three are
	// empty (keeps get_nodes payloads lean). Returns true if it emitted.
	inline bool SerializeCompactFunctionBindings(UAnimGraphNode_Base* AnimNode, const TSharedPtr<FJsonObject>& OutNode)
	{
		if (!AnimNode || !OutNode.IsValid() || !HasAnyFunctionBinding(AnimNode))
		{
			return false;
		}

		auto NameOrNull = [](const FMemberReference& Ref) -> TSharedPtr<FJsonValue>
		{
			const FName N = Ref.GetMemberName();
			return N == NAME_None ? StaticCastSharedRef<FJsonValue>(MakeShared<FJsonValueNull>())
								  : StaticCastSharedRef<FJsonValue>(MakeShared<FJsonValueString>(N.ToString()));
		};

		TSharedPtr<FJsonObject> B = MakeShared<FJsonObject>();
		B->SetField(TEXT("initial_update"), NameOrNull(AnimNode->InitialUpdateFunction));
		B->SetField(TEXT("become_relevant"), NameOrNull(AnimNode->BecomeRelevantFunction));
		B->SetField(TEXT("update"), NameOrNull(AnimNode->UpdateFunction));
		OutNode->SetObjectField(TEXT("bindings"), B);
		return true;
	}

	// ---- Gap 12: pin property bindings ----

	// Read the node's `Binding` instanced-subobject UPROPERTY reflectively as a plain
	// UObject* (NEVER via GetBinding(), whose return type is the incomplete
	// UAnimGraphNodeBinding). Returns nullptr when the property is missing (layout
	// drift) or the binding object has not been created on this node yet. Every
	// downstream GetClass()/Modify() runs on this complete UObject*.
	inline UObject* GetBindingObject(UAnimGraphNode_Base* AnimNode)
	{
		if (!AnimNode) return nullptr;
		FObjectProperty* BindingProp = FindFProperty<FObjectProperty>(AnimNode->GetClass(), TEXT("Binding"));
		if (!BindingProp) return nullptr;
		return BindingProp->GetObjectPropertyValue_InContainer(AnimNode);
	}

	// Reflectively locate the node's PropertyBindings map. Returns the FMapProperty,
	// the live map value ptr, and the binding UObject* (all set), or false when the
	// binding object is null or carries no PropertyBindings property (non-_Base
	// subclass / layout drift).
	inline bool ResolvePropertyBindingsMap(UAnimGraphNode_Base* AnimNode, FMapProperty*& OutMapProp, void*& OutMapPtr, UObject*& OutBindingObj)
	{
		OutMapProp = nullptr;
		OutMapPtr = nullptr;
		OutBindingObj = nullptr;
		if (!AnimNode) return false;

		UObject* Binding = GetBindingObject(AnimNode);
		if (!Binding) return false;

		FMapProperty* MapProp = FindFProperty<FMapProperty>(Binding->GetClass(), TEXT("PropertyBindings"));
		if (!MapProp) return false;

		OutMapProp = MapProp;
		OutMapPtr = const_cast<void*>(MapProp->ContainerPtrToValuePtr<void>(Binding));
		OutBindingObj = Binding;
		return OutMapPtr != nullptr;
	}

	inline FString PinBindingTypeToString(EAnimGraphNodePropertyBindingType Type)
	{
		switch (Type)
		{
		case EAnimGraphNodePropertyBindingType::Property: return TEXT("Property");
		case EAnimGraphNodePropertyBindingType::Function: return TEXT("Function");
		default:                                          return TEXT("None");
		}
	}

	// Read the node's PropertyBindings map reflectively into an array of
	// { pin, path:[...], type, is_bound }. On a null binding object or a missing
	// PropertyBindings property, OutEntries is left empty and (for the missing-
	// property case where a binding object exists) OutNote is set; never errors.
	// Returns the entry count.
	inline int32 ReadPinBindings(UAnimGraphNode_Base* AnimNode, TArray<TSharedPtr<FJsonValue>>& OutEntries, FString& OutNote)
	{
		OutNote.Reset();
		if (!AnimNode) return 0;

		// Plain UObject* (never GetBinding() — incomplete return type).
		UObject* Binding = GetBindingObject(AnimNode);
		if (!Binding)
		{
			// No binding object authored yet → no pin bindings (not an error).
			return 0;
		}

		FMapProperty* MapProp = FindFProperty<FMapProperty>(Binding->GetClass(), TEXT("PropertyBindings"));
		if (!MapProp)
		{
			OutNote = FString::Printf(
				TEXT("Binding class %s has no PropertyBindings map (non-_Base subclass or layout drift)"),
				*Binding->GetClass()->GetName());
			return 0;
		}

		void* MapPtr = const_cast<void*>(MapProp->ContainerPtrToValuePtr<void>(Binding));
		if (!MapPtr) return 0;

		FStructProperty* ValueStructProp = CastField<FStructProperty>(MapProp->ValueProp);
		if (!ValueStructProp || ValueStructProp->Struct != FAnimGraphNodePropertyBinding::StaticStruct())
		{
			OutNote = TEXT("PropertyBindings value type is not FAnimGraphNodePropertyBinding");
			return 0;
		}

		FScriptMapHelper Helper(MapProp, MapPtr);
		for (FScriptMapHelper::FIterator It(Helper); It; ++It)
		{
			const void* ValuePtr = Helper.GetValuePtr(It.GetInternalIndex());
			if (!ValuePtr) continue;
			const FAnimGraphNodePropertyBinding* PinBinding = static_cast<const FAnimGraphNodePropertyBinding*>(ValuePtr);

			TSharedPtr<FJsonObject> Entry = MakeShared<FJsonObject>();
			Entry->SetStringField(TEXT("pin"), PinBinding->PropertyName.ToString());

			TArray<TSharedPtr<FJsonValue>> PathArr;
			for (const FString& Seg : PinBinding->PropertyPath)
			{
				PathArr.Add(MakeShared<FJsonValueString>(Seg));
			}
			Entry->SetArrayField(TEXT("path"), PathArr);
			Entry->SetStringField(TEXT("type"), PinBindingTypeToString(PinBinding->Type));
			Entry->SetBoolField(TEXT("is_bound"), PinBinding->bIsBound);

			OutEntries.Add(MakeShared<FJsonValueObject>(Entry));
		}
		return OutEntries.Num();
	}

	// Compact pin-binding emit for get_nodes: sets "pin_bindings": [{pin, path}]
	// onto OutNode, omitted when empty. Returns true if it emitted.
	inline bool SerializeCompactPinBindings(UAnimGraphNode_Base* AnimNode, const TSharedPtr<FJsonObject>& OutNode)
	{
		if (!AnimNode || !OutNode.IsValid()) return false;

		TArray<TSharedPtr<FJsonValue>> Full;
		FString Note;
		ReadPinBindings(AnimNode, Full, Note);
		if (Full.Num() == 0) return false;

		// Lean shape for get_nodes: just { pin, path }.
		TArray<TSharedPtr<FJsonValue>> Compact;
		for (const TSharedPtr<FJsonValue>& V : Full)
		{
			const TSharedPtr<FJsonObject>* FullObj;
			if (!V->TryGetObject(FullObj) || !FullObj->IsValid()) continue;
			TSharedPtr<FJsonObject> C = MakeShared<FJsonObject>();
			C->SetStringField(TEXT("pin"), (*FullObj)->GetStringField(TEXT("pin")));
			const TArray<TSharedPtr<FJsonValue>>* PathArr;
			if ((*FullObj)->TryGetArrayField(TEXT("path"), PathArr))
			{
				C->SetArrayField(TEXT("path"), *PathArr);
			}
			Compact.Add(MakeShared<FJsonValueObject>(C));
		}
		OutNode->SetArrayField(TEXT("pin_bindings"), Compact);
		return true;
	}
}
